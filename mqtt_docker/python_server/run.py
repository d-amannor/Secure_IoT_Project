import threading
from app import app
from telegrambot import bot
import time
import logging
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
running = True

def signal_handler(signum, frame):
    global running
    logger.info("Received shutdown signal, stopping threads...")
    running = False
    sys.exit(0)

def run_flask():
    try:
        logger.info("Starting Flask server...")
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"Flask server error: {e}")
        if running:  # Only log if not in shutdown
            logger.info("Attempting to restart Flask server...")

def run_telegram():
    try:
        logger.info("Starting Telegram bot...")
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        logger.error(f"Telegram bot error: {e}")
        if running:  # Only log if not in shutdown
            logger.info("Attempting to restart Telegram bot...")

if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create threads for Flask and Telegram bot
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    telegram_thread = threading.Thread(target=run_telegram, daemon=True)

    # Start both threads
    telegram_thread.start()
    logger.info("Telegram thread started")
    flask_thread.start()
    logger.info("Flask thread started")

    # Keep the main thread running
    try:
        while running:
            time.sleep(1)
            # Check if threads are still alive
            if running and not flask_thread.is_alive():
                logger.error("Flask thread died, restarting...")
                flask_thread = threading.Thread(target=run_flask, daemon=True)
                flask_thread.start()
            if running and not telegram_thread.is_alive():
                logger.error("Telegram thread died, restarting...")
                telegram_thread = threading.Thread(target=run_telegram, daemon=True)
                telegram_thread.start()
    except KeyboardInterrupt:
        running = False
        logger.info("Shutting down...")
    finally:
        # Cleanup
        running = False
        logger.info("Waiting for threads to finish...")
        flask_thread.join(timeout=5)
        telegram_thread.join(timeout=5)
        logger.info("Shutdown complete")
