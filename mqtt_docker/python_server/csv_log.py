# csv_log.py
import csv
import aiofiles
import asyncio
from datetime import datetime
import os
from io import StringIO
from asyncio import Lock

# Create a global file lock
file_lock = Lock()

async def store_device_data_to_csv_async(device_id, data, filename='/app/data/sensor_data.csv'):
    """
    Asynchronously store device data to a CSV file.
    """
    async with file_lock:  # Use lock for file access
        timestamp, humidity, temperature, heat = data
        print(f"Writing to file: {os.path.abspath(filename)}")

        try:
            timestamp_dt = datetime.fromisoformat(timestamp)
            formatted_timestamp = timestamp_dt.strftime('%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            formatted_timestamp = timestamp

        row_data = {
            'device_id': device_id,
            'timestamp': formatted_timestamp,
            'humidity': humidity,
            'temperature': temperature,
            'heat_index': heat
        }

        fieldnames = ['device_id', 'timestamp', 'humidity', 'temperature', 'heat_index']
        file_exists = os.path.exists(filename)

        try:
            async with aiofiles.open(filename, mode='a', newline='') as file:
                if not file_exists:
                    await file.write(','.join(fieldnames) + '\n')

                # Create CSV row string manually
                row_values = [str(row_data[field]) for field in fieldnames]
                await file.write(','.join(row_values) + '\n')
                await file.flush()  # Ensure data is written to disk

        except Exception as e:
            print(f"Error writing to file: {e}")
