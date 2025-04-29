# mod_sorter/ui/event_handlers.py
from abc import ABC, abstractmethod
from PyQt6.QtWidgets import QMessageBox, QFileDialog
import os
from utils.logger import logger

class EventHandler(ABC):
    @abstractmethod
    def handle(self):
        pass

# --- НОВЫЙ Обработчик для кнопки "Previous" ---
class PreviousModHandler(EventHandler):
    def __init__(self, main_window, mod_manager):
        self.main_window = main_window
        self.mod_manager = mod_manager

    def handle(self):
        logger.debug("PreviousModHandler.handle()")
        try:
            if self.mod_manager.decrement_index():
                self.main_window.load_current_mod()
            else:
                # Опционально: Сообщение или звук, что достигнуто начало списка
                 self.main_window.statusBar().showMessage("Already at the first mod.", 2000) # Показать на 2 сек
        except Exception as e:
            self.main_window.handle_error(e, "Error going to previous mod")

# --- НОВЫЙ Обработчик для кнопки "Skip" ---
class SkipModHandler(EventHandler):
    def __init__(self, main_window, mod_manager):
        self.main_window = main_window
        self.mod_manager = mod_manager

    def handle(self):
        logger.debug("SkipModHandler.handle()")
        try:
            # Просто увеличиваем индекс и загружаем следующий
            if self.mod_manager.increment_index():
                self.main_window.load_current_mod()
            else:
                # Если это был последний, показываем сообщение о завершении
                self.main_window.load_current_mod() # Попытка загрузить (покажет сообщение "Complete")
        except Exception as e:
            self.main_window.handle_error(e, "Error skipping mod")


class NextModHandler(EventHandler): # Keep button
    def __init__(self, main_window, mod_manager, current_mod_info):
        self.main_window = main_window
        self.mod_manager = mod_manager
        self.current_mod_info = current_mod_info

    def handle(self):
        logger.debug("--- Entering NextModHandler.handle() ---") # <<< ADDED
        current_file_path = self.mod_manager.get_current_zip_file_path()
        logger.debug(f"Current file path: {current_file_path}") # <<< ADDED

        if not current_file_path:
            logger.warning("No current file path in NextModHandler.")
            QMessageBox.warning(self.main_window, "Error", "No current file selected.")
            logger.debug("--- Exiting NextModHandler.handle() (no path) ---") # <<< ADDED
            return

        if not self.current_mod_info:
             logger.warning("No current mod info available to mark as sorted in NextModHandler.")
             QMessageBox.warning(self.main_window, "Warning", "Mod information not loaded. Cannot mark as sorted. Skipping.")
             logger.debug("Attempting to increment index after missing mod info...") # <<< ADDED
             try: # Wrap index increment and load in try/except
                 if self.mod_manager.increment_index():
                     logger.debug("Index incremented. Calling load_current_mod...") # <<< ADDED
                     self.main_window.load_current_mod()
                 else:
                     logger.debug("Already at last index. Calling load_current_mod (will show complete)...") # <<< ADDED
                     self.main_window.load_current_mod() # Покажет сообщение о завершении
             except Exception as e_inner:
                 logger.error(f"Exception during load_current_mod after missing info: {e_inner}", exc_info=True)
                 self.main_window.handle_error(e_inner, "Error loading next mod after skip")
             logger.debug("--- Exiting NextModHandler.handle() (no mod info) ---") # <<< ADDED
             return

        try:
            logger.debug(f"Calling mod_manager.mark_as_sorted for {current_file_path}...") # <<< ADDED
            # Ensure mod_info is passed correctly
            self.mod_manager.mark_as_sorted(current_file_path, self.current_mod_info)
            logger.debug(f"Returned from mod_manager.mark_as_sorted for {current_file_path}.") # <<< ADDED

            logger.debug("Attempting to increment index after marking...") # <<< ADDED
            increment_successful = self.mod_manager.increment_index()
            logger.debug(f"Index increment successful: {increment_successful}") # <<< ADDED

            if increment_successful:
                 logger.debug("Index incremented. Calling load_current_mod for next item...") # <<< ADDED
                 self.main_window.load_current_mod()
                 logger.debug("Returned from load_current_mod call (next item).") # <<< ADDED
            else:
                logger.debug("Already at last index after marking. Calling load_current_mod (will show complete)...") # <<< ADDED
                self.main_window.load_current_mod() # Покажет сообщение о завершении
                logger.debug("Returned from load_current_mod call (complete).") # <<< ADDED

        except Exception as e:
            # Log exception with traceback for better diagnosis
            logger.error(f"Exception in NextModHandler.handle(): {e}", exc_info=True) # <<< ADDED traceback
            self.main_window.handle_error(e, "Error marking mod as sorted or moving to next")

        logger.debug("--- Exiting NextModHandler.handle() (normal flow) ---") # <<< ADDED


class DeleteModHandler(EventHandler):
    def __init__(self, main_window, mod_manager):
        self.main_window = main_window
        self.mod_manager = mod_manager

    def handle(self):
        logger.debug("DeleteModHandler.handle()")
        current_file_path = self.mod_manager.get_current_zip_file_path()
        if not current_file_path:
            logger.warning("No current file path.")
            QMessageBox.warning(self.main_window, "Error", "No file selected to delete.")
            return

        file_name = os.path.basename(current_file_path)

        # --- ИЗМЕНЕНИЕ: Добавляем подтверждение ---
        reply = QMessageBox.question(
            self.main_window,
            "Confirm Delete",
            f"Are you sure you want to permanently delete '{file_name}'?\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No # Кнопка по умолчанию - "Нет"
        )

        if reply == QMessageBox.StandardButton.Yes:
            logger.debug(f"User confirmed deletion of {file_name}")
            try:
                self.mod_manager.delete_mod(current_file_path)
                # Сообщение об успехе можно убрать, т.к. UI обновится
                # QMessageBox.information(self.main_window, "Success", f"File {file_name} deleted")
                self.main_window.statusBar().showMessage(f"File {file_name} deleted", 3000) # Показать в статус баре
                self.main_window.load_current_mod()  # Обновить UI
            except Exception as e:
                self.main_window.handle_error(e, f"Error deleting mod: {file_name}")
        else:
            logger.debug("User cancelled deletion.")
            self.main_window.statusBar().showMessage("Delete cancelled", 2000)


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
            # type_folder = os.path.join(dest_folder, self.current_mod_info.type.value) #удаляем строку
            self.mod_manager.move_mod(current_file_path, dest_folder) #меняем type_folder на dest_folder
            QMessageBox.information(self.main_window, "Успех", f"Файл перемещен в {dest_folder}")
            self.main_window.load_current_mod()  # Refresh UI
        except Exception as e:
            self.main_window.handle_error(e, "Ошибка при перемещении мода")

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
            #Определяем путь к папке относительно source_folder
            destination_path = os.path.join(self.main_window.source_folder, self.folder_path)
            self.mod_manager.move_mod(current_file_path, destination_path)
            QMessageBox.information(self.main_window, "Успех", f"Файл перемещен в {destination_path}")
            self.main_window.load_current_mod()
        except Exception as e:
            self.main_window.handle_error(e, f"Ошибка при перемещении мода в {self.folder_path}")