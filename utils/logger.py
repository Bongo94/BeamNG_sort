import logging
import os
import sys
from logging.handlers import RotatingFileHandler

class Logger:
    def __init__(self, log_file="mod_sorter.log", level=logging.DEBUG, max_logs=3):
        log_dir = os.path.dirname(log_file) or '.'
        if log_dir != '.' and not os.path.exists(log_dir):
             try:
                 os.makedirs(log_dir, exist_ok=True)
                 print(f"Created log directory: {log_dir}")
             except OSError as e:
                 print(f"Warning: Could not create log directory {log_dir}: {e}")
                 log_file = os.path.basename(log_file)

        self.logger = logging.getLogger("ModSorter")
        self.logger.setLevel(level)
        self.formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s")

        # Logger with colored console output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(self._get_colored_formatter())


        full_log_path = os.path.join(log_dir, os.path.basename(log_file))
        file_handler = RotatingFileHandler(full_log_path, maxBytes=5 * 1024 * 1024, backupCount=max_logs, encoding='utf-8')
        file_handler.setFormatter(self.formatter)

        if not self.logger.handlers:
            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)

        self._cleanup_old_logs(full_log_path, max_logs)


    def _get_colored_formatter(self):
        try:
            # pip install colorlog
            from colorlog import ColoredFormatter
            return ColoredFormatter(
                "%(log_color)s%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s%(reset)s",
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "bold_red,bg_white"
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
            log_files = [f for f in os.listdir(log_dir)
                         if f == log_basename or (f.startswith(log_basename + ".") and f.split('.')[-1].isdigit())]

            log_files.sort(key=lambda x: os.path.getmtime(os.path.join(log_dir, x)))

            files_to_keep = max_logs
            if len(log_files) > files_to_keep:
                 files_to_delete = log_files[:-files_to_keep]
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


log_directory = "logs"
logger = Logger(log_file=os.path.join(log_directory, "mod_sorter.log"), level=logging.DEBUG).get_logger()


if __name__ == "__main__":
    test_logger = Logger(log_file="test_log.log", level=logging.DEBUG).get_logger()
    test_logger.debug("Отладочное сообщение")
    test_logger.info("Информационное сообщение")
    test_logger.warning("Предупреждение")
    test_logger.error("Ошибка")
    test_logger.critical("Критическая ошибка")