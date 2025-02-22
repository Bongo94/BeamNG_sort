import logging
import os
import sys
from logging.handlers import RotatingFileHandler


class Logger:
    def __init__(self, log_file="mod_sorter.log", level=logging.INFO, max_logs=3):
        self.logger = logging.getLogger("ModSorter")
        self.logger.setLevel(level)
        self.formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s")

        # Консольный логер с цветами
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(self._get_colored_formatter())

        # Файловый логер с ротацией
        file_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=max_logs)
        file_handler.setFormatter(self.formatter)

        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

        self._cleanup_old_logs(log_file, max_logs)

    def _get_colored_formatter(self):
        try:
            from colorlog import ColoredFormatter
            return ColoredFormatter(
                "%(log_color)s%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s",
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "bold_red"
                }
            )
        except ImportError:
            return self.formatter  # Без цветного вывода, если нет colorlog

    def _cleanup_old_logs(self, log_file, max_logs):
        log_dir = os.path.dirname(log_file) or '.'
        log_files = sorted([f for f in os.listdir(log_dir) if f.startswith(os.path.basename(log_file))],
                           key=lambda x: os.path.getctime(os.path.join(log_dir, x)))

        while len(log_files) > max_logs:
            oldest_log = log_files.pop(0)
            try:
                os.remove(os.path.join(log_dir, oldest_log))
            except Exception as e:
                self.logger.warning(f"Не удалось удалить старый лог {oldest_log}: {e}")

    def get_logger(self):
        return self.logger


# Использование
logger = Logger().get_logger()

if __name__ == "__main__":
    logger.debug("Отладочное сообщение")
    logger.info("Информационное сообщение")
    logger.warning("Предупреждение")
    logger.error("Ошибка")
    logger.critical("Критическая ошибка")
