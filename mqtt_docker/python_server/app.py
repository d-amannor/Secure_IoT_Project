from flask import Flask, render_template, jsonify
from flask_mqtt import Mqtt
from collections import deque
import requests
from datetime import datetime
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor

import json
from queue import Queue
from telegrambot import bot
from decryption_algo import decrypt_msg
from verify import verify_challenge
from csv_log import store_device_data_to_csv_async

executor = ThreadPoolExecutor(max_workers=1)
async_loop = asyncio.new_event_loop()
def run_async(coro):
    """Helper function to run coroutines in the background"""
    asyncio.set_event_loop(async_loop)
    return async_loop.run_until_complete(coro)
    

app = Flask(__name__)
app.config['PROPAGATE_EXCEPTIONS'] = True

def run_telegram_bot():
    """Function to run the Telegram bot"""
    try:
        print("Starting Telegram bot...")
        bot.infinity_polling(timeout=20, long_polling_timeout=10)
    except Exception as e:
        print(f"Telegram bot error: {e}")
        
        
# Flask-MQTT Configuration
app.config['MQTT_BROKER_URL'] = 'mosquitto'  # Service name from Docker Compose
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_KEEPALIVE'] = 60
app.config['MQTT_USERNAME'] = ''
app.config['MQTT_PASSWORD'] = ''
app.config['MQTT_REFRESH_TIME'] = 1.0  # seconds

mqtt = Mqtt(app)

# Store sensor data for each device
sensor_data_device_1 = deque(maxlen=100)
sensor_data_device_2 = deque(maxlen=100)

latest_readings_device_1 = Queue()
latest_readings_device_2 = Queue()
__all__ = ['latest_readings_device_1', 'latest_readings_device_2']

@app.route('/')
def index():
    return render_template('chart.html')

@app.route('/data')
def data():
    return jsonify({
        'device_1': list(sensor_data_device_1),
        'device_2': list(sensor_data_device_2)
    })

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"}), 200

@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker")
        mqtt.subscribe('sensor/data')
    else:
        print(f"Failed to connect to MQTT broker, return code {rc}")
        #send_telegram_alert(f"Failed to connect to MQTT broker, return code {rc}")

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    payload = message.payload.decode('utf-8')
    print(f"Received payload: {payload}")

    try:
        ciphertext, nonce = verify_challenge(payload)
        if ciphertext:
            decrypted_payload = decrypt_msg(ciphertext)
            print(f"Decrypted payload: {decrypted_payload}")

            parsed_data = parse_sensor_data(decrypted_payload)
            device_id = 'device01' if 'Device 1' in decrypted_payload else 'device02'

            # Run async CSV writing in the thread pool
            executor.submit(run_async, store_device_data_to_csv_async(device_id, parsed_data))

            if 'Device 1' in decrypted_payload:
                sensor_data_device_1.append(parsed_data)
                while not latest_readings_device_1.empty():
                    latest_readings_device_1.get()
                latest_readings_device_1.put(parsed_data)
            elif 'Device 2' in decrypted_payload:
                sensor_data_device_2.append(parsed_data)
                while not latest_readings_device_2.empty():
                    latest_readings_device_2.get()
                latest_readings_device_2.put(parsed_data)
            print(f"Appended data: {parsed_data}")
        else:
            print("Not Authenticated")
    except Exception as e:
        print(f"Unexpected error: {e}")



def parse_sensor_data(data_string):
    """
    Parse sensor data string and return [timestamp, humidity, temperature, heat]

    Args:
        data_string (str): String in format "Device 1: H: 53.00  T: 21.80 Heat: 21.42"

    Returns:
        list: [timestamp, humidity, temperature, heat]
    """
    try:
        # Regular expression pattern to extract values
        pattern = r'H: (\d+\.\d+)\s+T: (\d+\.\d+)\s+Heat: (\d+\.\d+)'

        # Find matches in the string
        matches = re.search(pattern, data_string)

        if matches:
            timestamp = datetime.now().isoformat()
            humidity = float(matches.group(1))
            temperature = float(matches.group(2))
            heat = float(matches.group(3))

            return [timestamp, humidity, temperature, heat]
        else:
            raise ValueError("Could not parse sensor data string")

    except Exception as e:
        print(f"Error parsing sensor data: {e}")
        return None

def cleanup():
    executor.shutdown(wait=True)
    async_loop.close()

if __name__ == '__main__':
    try:
        # Start Telegram bot in a separate thread
        telegram_thread = threading.Thread(target=run_telegram_bot, daemon=True)
        telegram_thread.start()
        print("Telegram bot thread started")

        # Run Flask app
        app.run(host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        cleanup()
