import telebot
from telebot import types
import time
import threading
from dotenv import load_dotenv
import os
import pandas as pd
import matplotlib.pyplot as plt
import io
from datetime import datetime, timedelta
#from app import latest_readings_device_1, latest_readings_device_2

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# Track user states (e.g., awaiting login input), login status, failed attempts, ban times, and message IDs
user_states = {}
logged_in_users = set()
failed_attempts = {}
banned_users = {}
message_ids = {}
update_threads = {}

# Welcome message and show keyboard
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    # Create the keyboard
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [
        types.KeyboardButton('login'),
        types.KeyboardButton('update'),
        types.KeyboardButton('chart'),
        types.KeyboardButton('logout')  # Add logout button
    ]
    markup.add(*buttons)

    # Send welcome message with the keyboard
    bot.send_message(message.chat.id, "Howdy, I am Vivi! How are you doing?\nChoose an option:", reply_markup=markup)

# Handle user button selections
@bot.message_handler(func=lambda message: message.text in ['login', 'update', 'chart', 'logout'])
def handle_options(message):
    chat_id = message.chat.id
    if message.text == 'login':
        if chat_id in banned_users and datetime.now() < banned_users[chat_id]:
            bot.send_message(chat_id, "You are temporarily banned. Try again later.")
        else:
            user_states[chat_id] = 'awaiting_password'  # Set state to awaiting password
            msg = bot.send_message(chat_id, "Please enter your login password:")
            message_ids[chat_id] = (message.message_id, msg.message_id)  # Store message IDs
    elif message.text == 'update':
        if chat_id in logged_in_users:
            if chat_id not in update_threads or not update_threads[chat_id].is_alive():
                bot.send_message(chat_id, "Starting updates...")
                update_thread = threading.Thread(target=send_updates, args=(chat_id,), daemon=True)
                update_thread.start()
                update_threads[chat_id] = update_thread
            else:
                bot.send_message(chat_id, "Updates are already running.")
        else:
            bot.send_message(chat_id, "Please login first.")
    elif message.text == 'chart':
        if chat_id in logged_in_users:
            send_chart(chat_id)
        else:
            bot.send_message(chat_id, "Please login first.")
    elif message.text == 'logout':
        if chat_id in logged_in_users:
            logged_in_users.remove(chat_id)
            bot.send_message(chat_id, "You have been logged out.")
            stop_updates(chat_id)
            wipe_history(chat_id)
        else:
            bot.send_message(chat_id, "You are not logged in.")

# Handle password input for login
@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'awaiting_password')
def handle_password(message):
    chat_id = message.chat.id
    if message.text == 'yourpassword':  # Replace 'yourpassword' with the actual password
        logged_in_users.add(chat_id)
        bot.send_message(chat_id, "Login successful!")
        failed_attempts.pop(chat_id, None)  # Reset failed attempts
    else:
        failed_attempts[chat_id] = failed_attempts.get(chat_id, 0) + 1
        if failed_attempts[chat_id] >= 3:
            ban_time = datetime.now() + timedelta(hours=1)
            banned_users[chat_id] = ban_time
            bot.send_message(chat_id, "Too many failed attempts. You are banned for 1 hour.")
        else:
            bot.send_message(chat_id, "Incorrect password. Try again.")

    # Delete the login message and the bot's response
    user_msg_id, bot_msg_id = message_ids.pop(chat_id, (None, None))
    if user_msg_id:
        bot.delete_message(chat_id, user_msg_id)
    if bot_msg_id:
        bot.delete_message(chat_id, bot_msg_id)
    bot.delete_message(chat_id, message.message_id)

    user_states.pop(chat_id, None)  # Reset state

def send_updates(chat_id):
    while chat_id in logged_in_users:
        try:
            # Read the last row from the CSV file
            csv_path = '/app/data/sensor_data.csv'
            df = pd.read_csv(csv_path, names=['device', 'timestamp', 'humidity', 'temperature', 'heat'])
            last_row = df.iloc[-1]  # Get the last row

            # Format the message based on the device
            device = last_row['device']
            timestamp = last_row['timestamp']
            humidity = last_row['humidity']
            temperature = last_row['temperature']
            heat = last_row['heat']

            # Create different emoji for different devices
            device_emoji = "🔵" if device == "device01" else "🟢"

            message = (f"{device_emoji} {device} Reading:\n"
                      f"⏰ Time: {timestamp}\n"
                      f"🌡️ Temperature: {temperature}°C\n"
                      f"💧 Humidity: {humidity}%\n"
                      f"🌡️ Heat Index: {heat}")

            bot.send_message(chat_id, message)

        except Exception as e:
            print(f"Error sending updates: {e}")
            bot.send_message(chat_id, "Error reading sensor data.")

        time.sleep(30)  # Wait for 30 seconds before next update

# Stop updates for a user
def stop_updates(chat_id):
    if chat_id in update_threads:
        update_threads[chat_id].do_run = False
        update_threads[chat_id].join()
        update_threads.pop(chat_id, None)

# Wipe history for a user
def wipe_history(chat_id):
    pass


# Send chart as an image
def generate_sensor_chart():
    # Read the last 50 rows from the CSV file
    csv_path = '/app/data/sensor_data.csv'
    df = pd.read_csv(csv_path, names=['device', 'timestamp', 'humidity', 'temperature', 'heat'])
    df = df.tail(50)

    # Convert timestamp strings to datetime objects
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Create figure and axis objects with a single subplot
    plt.figure(figsize=(12, 6))

    # Plot temperature, humidity, and heat index
    plt.plot(df['timestamp'], df['temperature'], label='Temperature (°C)', color='red', marker='o')
    plt.plot(df['timestamp'], df['humidity'], label='Humidity (%)', color='blue', marker='s')
    plt.plot(df['timestamp'], df['heat'], label='Heat Index', color='green', marker='^')

    # Customize the plot
    plt.title('Sensor Data - Last 50 Readings', pad=20)
    plt.xlabel('Time')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45)

    # Adjust layout to prevent label cutoff
    plt.tight_layout()

    # Save the plot to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    buf.seek(0)
    plt.close()

    return buf

def send_chart(chat_id):
    try:
        # Generate the chart
        chart_buffer = generate_sensor_chart()

        # Send the chart
        bot.send_photo(
            chat_id, 
            chart_buffer, 
            caption="📊 Sensor Data Chart (Last 50 Readings)\n"
                    "🔴 Temperature (°C)\n"
                    "🔵 Humidity (%)\n"
                    "🟢 Heat Index"
        )

    except Exception as e:
        print(f"Error generating/sending chart: {e}")
        bot.send_message(chat_id, "Sorry, there was an error generating the chart.")

# Echo user messages (fallback)
@bot.message_handler(func=lambda message: not message.text.startswith('/'))
def echo_all(message):
    bot.reply_to(message, message.text)

__all__ = ['bot']
if __name__ == "__main__":
    # Infinite polling to handle incoming messages
    bot.infinity_polling()
