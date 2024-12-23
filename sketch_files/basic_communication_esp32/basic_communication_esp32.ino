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
      client.subscribe("home/test");  // Subscribe to the topic
      delay(1000);
    } else {
      Serial.print("Failed, rc=");
      Serial.print(client.state());
      delay(5000);  // Wait 5 seconds before retrying
    }
  }
}


void setup() {
  // put your setup code here, to run once:
Serial.begin(115200);
setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);

  dht.begin();

pinMode(rLED,OUTPUT);
pinMode(wLED, OUTPUT);
pinMode(pButton1, INPUT);


}

void loop() {
  // put your main code here, to run repeatedly:
//// Blink LED
// digitalWrite(rLED,HIGH);
// digitalWrite(wLED,LOW);
// delay(1000);
// digitalWrite(rLED,LOW);
// digitalWrite(wLED,HIGH);
// Serial.println("ESP32");
// delay(1000);

////Push button turn on Red
digitalWrite(rLED,LOW);
if (digitalRead(pButton1)==1){
  digitalWrite(rLED,HIGH);
}


//// Toggle Mechanism
// int LEDstate= 0;

// if (digitalRead(pButton1)==1 && LEDstate==0){
//   digitalWrite(rLED,HIGH);
//   LEDstate = 1;
// }

//  if(digitalRead(pButton1)==1 && LEDstate==1){
//     digitalWrite(rLED,LOW);
//     LEDstate=0;
//   }

float hmdt = dht.readHumidity();
float tmpr = dht.readTemperature();

if (isnan(hmdt) || isnan(tmpr)) {
    Serial.println(F("Failed to read from DHT sensor!"));
    return;
  }

float hic = dht.computeHeatIndex(tmpr, hmdt, false); // Compute heat index in Celsius (isFahreheit = false)
  
  // Serial.print(F("Humidity: "));
  // Serial.print(hmdt);
  // Serial.print(F("%  Temperature: "));
  // Serial.print(tmpr);
  // Serial.print(F("°C "));
  // Serial.print(F(" Heat index: "));
  // Serial.print(hic);
  // Serial.print(F("°C "));
  // Serial.println("\n");

if (!client.connected()) {
    reconnect();
  }
  client.loop();
  
  // Publish a message to the topic every 5 seconds
  String message = "Humidity: " + String(hmdt) + "  Temperature: " + String(tmpr) + " Heat index: " + String(hic) + "\n";
  client.publish("home/test", message.c_str());
  digitalWrite(wLED,HIGH);
  delay(500);
  digitalWrite(wLED,LOW);
  delay(4000);
}
