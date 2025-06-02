# utils/logger.py

import logging
import os
import sys
# Assuming config.py is in the parent directory or accessible in PYTHONPATH
# If config.py is in the root, and utils is a subdirectory:
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from config import LOGGING_LEVEL, LOG_FILE_PATH
except ModuleNotFoundError:
    # Fallback if config is not found (e.g. during isolated testing of this module)
    # Or if the script is run directly in a way that sys.path modification doesn't work as expected
    print("Warning: config.py not found. Using default logging settings.")
    LOGGING_LEVEL = "INFO"
    LOG_FILE_PATH = "logs/bot_errors.log"


def setup_logger(name: str = 'TelegramCaseBot') -> logging.Logger:
    """
    Configures and returns a logger instance.

    Args:
        name (str): The name for the logger.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)

    # Prevent duplicate handlers if logger is already configured
    if logger.hasHandlers():
        return logger

    logger.setLevel(LOGGING_LEVEL)

    # Create formatter
    # As per README 5.2: "Логирование ограничено технической информацией:
    # коды ошибок, статусы выполнения задач, временные метки и идентификаторы запросов."
    # "Логи не содержат чувствительной информации, такой как личные данные пользователей или содержимое загруженных документов."
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s'
    )

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Create file handler
    # Ensure the logs directory exists
    try:
        log_dir = os.path.dirname(LOG_FILE_PATH)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(LOG_FILE_PATH, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.info(f"File logging configured to: {LOG_FILE_PATH}")

    except Exception as e:
        # If file handler fails, log to console and continue
        logger.error(f"Failed to configure file logging to {LOG_FILE_PATH}: {e}", exc_info=True)


    # Test log messages (optional, can be removed)
    # logger.debug("This is a debug message.")
    # logger.info("This is an info message.")
    # logger.warning("This is a warning message.")
    # logger.error("This is an error message.")
    # logger.critical("This is a critical message.")

    return logger

# Initialize a default logger instance for easy import
# This logger can be used by other modules directly: from utils.logger import logger
logger = setup_logger()

if __name__ == '__main__':
    # Example of using the logger
    logger.info("Logger setup complete. This is an example info message from logger.py.")

    # Example of how other modules would use the logger
    another_logger = setup_logger("AnotherModule")
    another_logger.info("This is a message from another module's logger.")

    try:
        1 / 0
    except ZeroDivisionError:
        logger.error("A handled error occurred: Division by zero.", exc_info=False) # Set exc_info=True to log stack trace

    logger.info(f"Logging level is set to: {LOGGING_LEVEL}")
    logger.info(f"Log file path is: {LOG_FILE_PATH}")
    # Demonstrate that sensitive data should not be logged
    user_document_content = "This is a very sensitive document text."
    user_id = "user_12345"
    # Correct logging:
    logger.info(f"Processing document for user_id: {user_id}, document_length: {len(user_document_content)}")
    # Incorrect logging (AVOID THIS):
    # logger.info(f"User {user_id} submitted document: {user_document_content}")
