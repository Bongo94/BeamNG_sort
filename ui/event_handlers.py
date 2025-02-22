# mod_sorter/ui/event_handlers.py
from abc import ABC, abstractmethod
from PyQt6.QtWidgets import QMessageBox, QFileDialog
import os
from utils.logger import logger

class EventHandler(ABC):
    @abstractmethod
    def handle(self):
        pass

class NextModHandler(EventHandler):
    def __init__(self, main_window, mod_manager, current_mod_info):
        self.main_window = main_window
        self.mod_manager = mod_manager
        self.current_mod_info = current_mod_info

    def handle(self):
        logger.debug("NextModHandler.handle()")
        current_file_path = self.mod_manager.get_current_zip_file_path()
        if not current_file_path:
            logger.warning("No current file path.")
            return

        try:
            self.mod_manager.mark_as_sorted(current_file_path, self.current_mod_info)
            self.mod_manager.increment_index()
            self.main_window.load_current_mod()
        except Exception as e:
            self.main_window._handle_error(e, "Ошибка при переходе к следующему моду")


class DeleteModHandler(EventHandler):
    def __init__(self, main_window, mod_manager):
        self.main_window = main_window
        self.mod_manager = mod_manager

    def handle(self):
        logger.debug("DeleteModHandler.handle()")
        current_file_path = self.mod_manager.get_current_zip_file_path()
        if not current_file_path:
            logger.warning("No current file path.")
            return

        try:
            file_name = os.path.basename(current_file_path)
            self.mod_manager.delete_mod(current_file_path)
            QMessageBox.information(self.main_window, "Успех", f"Файл {file_name} удален")
            self.main_window.load_current_mod()  # Refresh UI
        except Exception as e:
            self.main_window._handle_error(e, "Ошибка при удалении мода")


class MoveModHandler(EventHandler):
    def __init__(self, main_window, mod_manager, current_mod_info):
        self.main_window = main_window
        self.mod_manager = mod_manager
        self.current_mod_info = current_mod_info

    def handle(self):
        logger.debug("MoveModHandler.handle()")
        current_file_path = self.mod_manager.get_current_zip_file_path()
        if not current_file_path:
            logger.warning("No current file path.")
            return

        dest_folder = QFileDialog.getExistingDirectory(self.main_window, "Выберите папку для перемещения")
        if not dest_folder:
            logger.info("Move mod operation cancelled by user.")
            return

        try:
            type_folder = os.path.join(dest_folder, self.current_mod_info.type.value)
            self.mod_manager.move_mod(current_file_path, type_folder)
            QMessageBox.information(self.main_window, "Успех", f"Файл перемещен в {type_folder}")
            self.main_window.load_current_mod()  # Refresh UI
        except Exception as e:
            self.main_window._handle_error(e, "Ошибка при перемещении мода")

class MoveModToFolderHandler(EventHandler):
    def __init__(self, main_window, mod_manager, folder_path):
        self.main_window = main_window
        self.mod_manager = mod_manager
        self.folder_path = folder_path

    def handle(self):
        logger.debug(f"MoveModToFolderHandler.handle() - Moving to {self.folder_path}")
        current_file_path = self.mod_manager.get_current_zip_file_path()
        if not current_file_path:
            logger.warning("No current file path.")
            return

        try:
            self.mod_manager.move_mod(current_file_path, self.folder_path)
            QMessageBox.information(self.main_window, "Успех", f"Файл перемещен в {self.folder_path}")
            self.main_window.load_current_mod()
        except Exception as e:
            self.main_window._handle_error(e, f"Ошибка при перемещении мода в {self.folder_path}")