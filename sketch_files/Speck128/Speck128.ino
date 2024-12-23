#include <Crypto.h>
#include <CryptoLW.h>
#include <Speck.h>
#include <SpeckSmall.h>
#include <SpeckTiny.h>
#include <string.h>
#include <Base64.h>
#include <Wire.h>


#include <Arduino.h>
#include "DHT.h"

#include <WiFi.h>
#include <PubSubClient.h>

// WiFi settings
const char* ssid = "Kali-M";         
const char* password = "12341234ULB"; 

// MQTT settings
const char* mqtt_server = "192.168.1.1";  
const int mqtt_port = 1883;                 // Default MQTT port

WiFiClient espClient;
PubSubClient client(espClient);

#define DHTPIN 26     // Digital pin connected to the DHT sensor
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

int wLED = 33;
int rLED = 32;
int pButton1 = 27;


int packetCount = 0;

byte key[] = {0x0f, 0x0e, 0x0d, 0x0c, 0x0b, 0x0a, 0x09, 0x08,
                    0x07, 0x06, 0x05, 0x04, 0x03, 0x02, 0x01, 0x00};

Speck speck;


String convertToBase64(String input) {
  // Convert String to mutable char array
  char inputChars[input.length() + 1];  // +1 for null terminator
  input.toCharArray(inputChars, input.length() + 1);

  // Allocate a buffer to store Base64 encoded data
  char encodedData[512]; // Adjust size based on your input length

  // Encode the input string to Base64
  int len = Base64.encode(encodedData, inputChars, input.length());

  // Return the encoded string as a String object
  return String(encodedData);
}


void setup_wifi() {
  delay(10);
  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("Connected to WiFi");
}

void callback(char* topic, byte* message, unsigned int length) {
  Serial.print("Message received on topic: ");
  Serial.print(topic);
  Serial.print(". Message: ");
  for (int i = 0; i < length; i++) {
    Serial.print((char)message[i]);
  }
  Serial.println();
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Connect without username and password
    
    if (client.connect("ESP32Client")) {
      Serial.println("Connected to MQTT broker");
      client.subscribe("sensor/data");  // Subscribe to the topic
      delay(1000);
    } else {
      Serial.print("Failed, rc=");
      Serial.print(client.state());
      delay(5000);  // Wait 5 seconds before retrying
    }
  }
}


void setup() {
  Serial.begin(9600);
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);

  dht.begin();
  
  pinMode(rLED,OUTPUT);
  pinMode(wLED, OUTPUT);
  pinMode(pButton1, INPUT);

}

byte buffer[16];

String encrypt(BlockCipher *cipher, byte *plainText, size_t keySize) { 
  crypto_feed_watchdog();

  cipher->setKey(key, keySize);
  cipher->encryptBlock(buffer, plainText);

  // Serial.println("--------------Ciphers-----------------");

  String str = "";
  for (uint8_t i = 0; i < 16; i++) {
      // Serial.print("0x");
      // if (buffer[i] < 16) {
      //     Serial.print("0"); // Add leading zero for single-digit hex numbers
      // }
      // Serial.print(buffer[i], HEX); // Print byte in hexadecimal
      // Serial.print(" ");
      
      // Append to the string in "0x" format
      // str += "0x";
      if (buffer[i] < 16) {
          str += "0"; // Add leading zero for single-digit hex numbers
      }
      str += String(buffer[i], HEX);
      str += " "; // Space delimiter between bytes
  }

  // Serial.println();
  // Serial.println("Hexadecimal Cipher: " + str);

  return str; // Return the hex string for storage
}

unsigned long start = 0;

unsigned long end = 0;

unsigned execution_time = 0;


String speck_enc(String dataPacket)
{
    // Getting sensor readings
  // int altitude = 109;
  // int temperature = 230;
  // int voltage = 430;
  // String Imu = "Im Kali";

  // String dataPacket =  String(altitude) + "," + String(temperature) + "," + 
  // String(voltage) + Imu;
  
  // Serial.print("************************************");
  // Serial.print(packetCount);
  // Serial.println("************************************");
  // Serial.println(dataPacket);


  // *********************************************************************************************
  // Encryption Process
  // Serial.print(dataPacket.length());
  // Serial.print(" , DataPacketLength % 16 : ");
  // Serial.println(dataPacket.length() % 16);
  if (dataPacket.length() % 16 != 0) {
    int paddingNeeded = 16 - (dataPacket.length() % 16);
    for (int i = 0; i < paddingNeeded; i++) {
        dataPacket += '\0'; // Add padding null byte (0x00)
    }
  }


  // Converting string to bytes for encryption
  byte plain[dataPacket.length()];
  dataPacket.getBytes(plain, dataPacket.length());

  // Converting the string into blocks of 16 bytes or 128 bits
  int len = (sizeof(plain)/sizeof(plain[0]));
  // Serial.print("Data Packet Length : ");
  // Serial.println(len);
  int numberOfBlocks = len/16;
  // Serial.print("Number of blocks : ");
  // Serial.println(numberOfBlocks);
  String cipherText = "";
  byte plainText[16];
  byte cipherTextArray[16];
  for(int i = 0; i < numberOfBlocks; i++)
  {
    for(int j = 0; j < 16; j++)
    {
      plainText[j] = plain[(16*i) + j];
      // Serial.print(plainText[j]);
      // Serial.print(" , ");
      // Serial.println(dataPacket[(16*i) + j]);
    }
    cipherText = cipherText + encrypt(&speck, plainText ,16);
    // Serial.println("---------------------------------");
  }

  // Serial.print("Cipher Text : ");
  // Serial.println(cipherText);
  // end = millis();

  // Serial.print(" , Length of Cipher Text");
  // Serial.println(cipherText.length());


  // Convert the cipherText to Base64
  String base64CipherText = convertToBase64(cipherText);

  // Print the Base64 encoded result
  // Serial.println("Base64 Encoded Cipher Text: ");
  // Serial.println(base64CipherText); 

  // execution_time = end - start;

  // Serial.print("Encryption Execution Time : ");
  // Serial.print(execution_time);
  // Serial.println(" milliseconds");
  return base64CipherText;

}

void loop() {

  //  start = millis();
  digitalWrite(rLED,LOW);
  if (digitalRead(pButton1)==1){
    digitalWrite(rLED,HIGH);
  }
  float hmdt = dht.readHumidity();
  float tmpr = dht.readTemperature();

  if (isnan(hmdt) || isnan(tmpr)) {
    Serial.println(F("Failed to read from DHT sensor!"));
    return;
  }

  float hic = dht.computeHeatIndex(tmpr, hmdt, false); // Compute heat index in Celsius (isFahreheit = false)

  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  
  // Publish a message to the topic every 5 seconds
  String message = "H: " + String(hmdt) + "  T: " + String(tmpr) + " H: " + String(hic);
  String cipherMSG = speck_enc(message);
  cipherMSG.trim();
  Serial.println(cipherMSG);
  Serial.println("Cipher length: " + String(cipherMSG.length()));
  client.publish("sensor/data", (uint8_t*)cipherMSG.c_str(), cipherMSG.length());
  // client.publish("sensor/data", message.c_str());
  digitalWrite(wLED,HIGH);
  delay(500);
  digitalWrite(wLED,LOW);
  delay(4500);


  // speck_enc();
  //*********************************************************************************************************
  // Serial.println("\t\t\tEND");
  // delay(20000);
}