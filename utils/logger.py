# utils/logger.py (or wherever this code is)
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

class Logger:
    # CHANGE THE DEFAULT LEVEL HERE
    def __init__(self, log_file="mod_sorter.log", level=logging.DEBUG, max_logs=3): # << CHANGED TO DEBUG
        # --- Create logs directory if it doesn't exist ---
        log_dir = os.path.dirname(log_file) or '.' # Use specified dir or current
        if log_dir != '.' and not os.path.exists(log_dir):
             try:
                 os.makedirs(log_dir, exist_ok=True)
                 print(f"Created log directory: {log_dir}") # Simple print confirmation
             except OSError as e:
                 print(f"Warning: Could not create log directory {log_dir}: {e}")
                 log_file = os.path.basename(log_file) # Fallback to current dir
        # ---

        self.logger = logging.getLogger("ModSorter")
        # Set level EARLY so handlers inherit it if not set explicitly
        self.logger.setLevel(level)
        self.formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s")

        # Консольный логер с цветами
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(self._get_colored_formatter())
        # Optional: Set console level separately if you want less verbose console output
        # console_handler.setLevel(logging.INFO)

        # Файловый логер с ротацией
        # Ensure the log file path includes the directory
        full_log_path = os.path.join(log_dir, os.path.basename(log_file))
        file_handler = RotatingFileHandler(full_log_path, maxBytes=5 * 1024 * 1024, backupCount=max_logs, encoding='utf-8') # Use full_log_path
        file_handler.setFormatter(self.formatter)
        # File handler will log everything from DEBUG upwards since logger level is DEBUG

        # Prevent adding handlers multiple times if logger already exists
        if not self.logger.handlers:
            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)

        self._cleanup_old_logs(full_log_path, max_logs) # Use full_log_path

    # ... (rest of the Logger class: _get_colored_formatter, _cleanup_old_logs, get_logger) ...

    def _get_colored_formatter(self):
        # ... (your existing implementation) ...
        try:
            # pip install colorlog
            from colorlog import ColoredFormatter
            return ColoredFormatter(
                "%(log_color)s%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s%(reset)s", # Added reset
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "bold_red,bg_white" # Example bg color
                },
                secondary_log_colors={},
                style='%'
            )
        except ImportError:
            print("colorlog module not found, using standard formatter for console.")
            return self.formatter

    def _cleanup_old_logs(self, log_file, max_logs):
        log_basename = os.path.basename(log_file)
        log_dir = os.path.dirname(log_file) or '.'
        try:
            # List files matching the pattern log_basename or log_basename.N
            log_files = [f for f in os.listdir(log_dir)
                         if f == log_basename or (f.startswith(log_basename + ".") and f.split('.')[-1].isdigit())]

            # Sort by modification time (oldest first)
            log_files.sort(key=lambda x: os.path.getmtime(os.path.join(log_dir, x)))

            # We want to keep the main log file + (max_logs - 1) backups
            files_to_keep = max_logs
            if len(log_files) > files_to_keep:
                 files_to_delete = log_files[:-files_to_keep] # Files to delete are the oldest ones
                 self.logger.debug(f"Found {len(log_files)} log files. Keeping {files_to_keep}. Deleting {len(files_to_delete)}.")
                 for old_log in files_to_delete:
                    full_path = os.path.join(log_dir, old_log)
                    try:
                        os.remove(full_path)
                        self.logger.debug(f"Removed old log file: {full_path}")
                    except Exception as e:
                        self.logger.warning(f"Could not remove old log file {full_path}: {e}")
        except FileNotFoundError:
             self.logger.debug(f"Log directory {log_dir} not found during cleanup check.")
        except Exception as e:
            self.logger.error(f"Error during log cleanup in {log_dir}: {e}", exc_info=True)


    def get_logger(self):
        return self.logger


# Использование (creates log file in the same directory as the script by default)
# logger = Logger().get_logger() # Now defaults to DEBUG

# OR better, specify a logs directory:
log_directory = "logs"
logger = Logger(log_file=os.path.join(log_directory, "mod_sorter.log"), level=logging.DEBUG).get_logger()


if __name__ == "__main__":
    # Example when running logger.py directly
    test_logger = Logger(log_file="test_log.log", level=logging.DEBUG).get_logger()
    test_logger.debug("Отладочное сообщение")
    test_logger.info("Информационное сообщение")
    test_logger.warning("Предупреждение")
    test_logger.error("Ошибка")
    test_logger.critical("Критическая ошибка")