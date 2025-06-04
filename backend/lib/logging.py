# lib/logging_config.py
import logging
import sys
import os

LOG_LEVEL = os.environ.get(
    "LOG_LEVEL", "INFO"
).upper()  # Example: Get level from environment


def setup_logging():
    """Configures the root logger for the application."""
    # Get the root logger
    root_logger = logging.getLogger()

    # Check if handlers are already configured (to avoid duplicates if setup is called multiple times)
    if root_logger.hasHandlers():
        # print("Root logger already configured.") # Optional debug print
        root_logger.setLevel(LOG_LEVEL)  # Ensure level is set even if handlers exist
        return

    # Set the desired overall level (e.g., INFO, DEBUG)
    root_logger.setLevel(LOG_LEVEL)

    # Create a formatter
    # Example format: Timestamp - Logger Name - Level - Message
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    # Example format with process ID:
    # formatter = logging.Formatter(
    #     "%(asctime)s - %(process)d - %(name)s - %(levelname)s - %(message)s"
    # )

    # Create a console handler (outputs to stderr by default)
    console_handler = logging.StreamHandler(
        sys.stdout
    )  # Use stdout for console output if preferred
    console_handler.setFormatter(formatter)
    # Set level for this handler if needed (e.g., only show INFO and above on console)
    # console_handler.setLevel(logging.INFO)

    # Add the handler to the root logger
    root_logger.addHandler(console_handler)

    # --- Optional: Add File Handler ---
    # try:
    #     log_file_path = "app.log"
    #     file_handler = logging.FileHandler(log_file_path)
    #     file_handler.setFormatter(formatter)
    #     # Set a different level for the file if desired (e.g., capture DEBUG)
    #     # file_handler.setLevel(logging.DEBUG)
    #     root_logger.addHandler(file_handler)
    # except Exception as e:
    #     root_logger.error(f"Failed to configure file logging to {log_file_path}: {e}")
    # --- End Optional File Handler ---

    # Prevent propagation from libraries that might misuse the root logger (optional)
    # logging.getLogger("some_noisy_library").propagate = False

    root_logger.info(f"Root logger configured with level {LOG_LEVEL}.")
