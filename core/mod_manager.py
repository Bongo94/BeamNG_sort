# mod_sorter/core/mod_manager.py
import os
import shutil
import zipfile
import json
import tempfile
import time # Убедись, что time импортирован
from typing import List, Optional, Dict, Any # Добавь Any
from core.mod_info import ModInfo, ModType
from utils.logger import logger
from core.mod_analyzer import ModAnalyzer

def get_mod_info_from_marker(zip_file_path: str) -> Optional[dict]:
    """Reads the .mod_sorted file from inside the ZIP and returns the data."""
    logger.debug(f"Reading mod info from marker in: {zip_file_path}")
    try:
        with zipfile.ZipFile(zip_file_path, 'r') as zf:
            marker_filename = '.mod_sorted'
            if marker_filename in zf.namelist():
                with zf.open(marker_filename) as marker_file:
                    # Добавим обработку ошибок декодирования JSON
                    try:
                        data = json.load(marker_file)
                        logger.debug(f"Marker data: {data}")
                        return data
                    except json.JSONDecodeError as json_e:
                        logger.warning(f"Error decoding JSON from marker in {zip_file_path}: {json_e}")
                        return None # Считаем, что маркера нет, если он поврежден
            else:
                logger.debug("No sorted marker found.")
                return None
    except zipfile.BadZipFile:
        logger.warning(f"Bad zip file encountered while reading marker: {zip_file_path}")
        return None # Считаем, что маркера нет, если архив поврежден
    except FileNotFoundError:
        logger.warning(f"File not found while reading marker: {zip_file_path}")
        return None
    except Exception as e:
        logger.warning(f"Error reading marker data from {zip_file_path}: {e}")
        return None


def _delete_sorted_marker(zip_file_path: str) -> None:
    """Deletes the .mod_sorted marker file from *inside* the ZIP."""
    logger.debug(f"Attempting to delete sorted marker from: {zip_file_path}")
    temp_zip_path = None # Инициализируем на случай ошибки
    try:
        marker_filename = '.mod_sorted'
        # Сначала проверим, есть ли маркер, чтобы не пересоздавать архив зря
        marker_exists = False
        try:
             with zipfile.ZipFile(zip_file_path, 'r') as zf_check:
                 marker_exists = marker_filename in zf_check.namelist()
        except (zipfile.BadZipFile, FileNotFoundError) as check_err:
             logger.warning(f"Could not check for marker before deletion in {zip_file_path}: {check_err}")
             return # Не можем проверить - не удаляем

        if not marker_exists:
             logger.debug(f"Marker {marker_filename} not found in {zip_file_path}. No need to delete.")
             return

        # Маркер есть, создаем временный файл для перезаписи
        logger.debug(f"Marker found. Proceeding with deletion via rewrite for {zip_file_path}")
        temp_zip_fd, temp_zip_path = tempfile.mkstemp(suffix='.zip')
        os.close(temp_zip_fd)

        with zipfile.ZipFile(zip_file_path, 'r') as original_zip:
            with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as temp_zip:
                # Копируем все файлы, кроме маркера
                for item in original_zip.infolist():
                    if item.filename != marker_filename:
                        buffer = original_zip.read(item.filename)
                        temp_zip.writestr(item, buffer)

        # Заменяем оригинальный ZIP-файл временным
        os.replace(temp_zip_path, zip_file_path)
        logger.info(f"Successfully deleted {marker_filename} from {zip_file_path}")

    except FileNotFoundError:
        # Эта ошибка может возникнуть, если файл удалили между проверкой и открытием
        logger.warning(f"File not found during marker deletion process: {zip_file_path}")
    except zipfile.BadZipFile:
        logger.error(f"Bad zip file during marker deletion process: {zip_file_path}")
    except Exception as e:
        logger.exception(f"Error removing {marker_filename} from {zip_file_path}: {e}")
        # Пытаемся удалить временный файл, если он был создан
        if temp_zip_path and os.path.exists(temp_zip_path):
            try:
                os.remove(temp_zip_path)
            except OSError as remove_err:
                logger.warning(f"Could not remove temporary file {temp_zip_path} after error: {remove_err}")
        raise # Перевыбрасываем исключение


def check_sorted_marker(zip_file_path: str) -> bool:
    """Checks if a .mod_sorted marker exists *inside* the ZIP."""
    logger.debug(f"Checking for sorted marker in: {zip_file_path}")
    try:
        with zipfile.ZipFile(zip_file_path, 'r') as zf:
            is_sorted = '.mod_sorted' in zf.namelist()
            logger.debug(f"Sorted marker found in {zip_file_path}: {is_sorted}")
            return is_sorted
    except zipfile.BadZipFile:
        logger.warning(f"Bad zip file encountered while checking for marker: {zip_file_path}")
        return False # Считаем не отсортированным, если архив поврежден
    except FileNotFoundError:
         logger.warning(f"File not found while checking for marker: {zip_file_path}")
         return False # Файла нет - не отсортирован
    except Exception as e:
        logger.warning(f"Error checking for sorted marker in {zip_file_path}: {e}")
        return False  # Assume not sorted if there's an error

class ModManager:
    def __init__(self, source_folder: str):
        logger.debug(f"Initializing ModManager with source folder: {source_folder}")
        self.source_folder = source_folder
        # --- Изменение: Храним больше информации о файлах ---
        self.zip_files_info: List[Dict[str, Any]] = self._load_zip_files_with_info()
        self.current_index = 0
        logger.info(f"ModManager initialized, found {len(self.zip_files_info)} zip files.")

    def _load_zip_files_with_info(self) -> List[Dict[str, Any]]:
        """Loads zip files and basic stats (name, path, size, modified time)."""
        logger.debug(f"Loading zip files and info from: {self.source_folder}")
        files_info = []
        try:
            for filename in os.listdir(self.source_folder):
                if filename.lower().endswith('.zip'):
                    full_path = os.path.join(self.source_folder, filename)
                    try:
                        stats = os.stat(full_path)
                        files_info.append({
                            "name": filename,
                            "path": full_path,
                            "size": stats.st_size,
                            "modified": stats.st_mtime # timestamp
                        })
                    except OSError as e:
                         logger.warning(f"Could not get stats for {full_path}: {e}")
                         # Все равно добавим, но без статистики
                         files_info.append({"name": filename, "path": full_path, "size": None, "modified": None})

        except FileNotFoundError:
            logger.error(f"Source folder not found during loading: {self.source_folder}")
            return []
        except Exception as e:
            logger.exception(f"Error loading zip files list from {self.source_folder}: {e}")
            return []

        logger.debug(f"Found {len(files_info)} zip files with info.")
        # Сортируем по имени файла для консистентности
        files_info.sort(key=lambda x: x['name'].lower())
        return files_info

    # --- Старый метод больше не нужен ---
    # def _load_zip_files(self) -> List[str]:
    #     logger.debug(f"Loading zip files from: {self.source_folder}")
    #     zip_files = [f for f in os.listdir(self.source_folder) if f.endswith('.zip')]
    #     logger.debug(f"Found zip files: {zip_files}")
    #     return zip_files

    def get_current_zip_file_path(self) -> Optional[str]:
        if 0 <= self.current_index < len(self.zip_files_info):
            return self.zip_files_info[self.current_index]["path"]
        logger.warning(f"Index {self.current_index} out of bounds (0-{len(self.zip_files_info)-1}). Cannot get path.")
        return None

    # --- НОВОЕ: Получение статистики текущего файла ---
    def get_current_file_stats(self) -> Optional[Dict[str, Any]]:
        """Returns size and modified time for the current file."""
        if 0 <= self.current_index < len(self.zip_files_info):
            # Возвращаем только нужные поля из кэшированной информации
            return {
                "size": self.zip_files_info[self.current_index].get("size"),
                "modified": self.zip_files_info[self.current_index].get("modified")
            }
        logger.warning(f"Index {self.current_index} out of bounds. Cannot get stats.")
        return None

    def get_current_mod_info(self) -> Optional[ModInfo]:
        zip_file_path = self.get_current_zip_file_path()
        if not zip_file_path:
            logger.warning("No current zip file path, cannot get mod info.")
            return None

        # Проверка, что файл все еще существует (на случай внешних изменений)
        if not os.path.exists(zip_file_path):
            logger.warning(f"File no longer exists: {zip_file_path}. Refreshing list.")
            self.refresh_zip_list() # Пытаемся обновить список
            # После обновления снова пытаемся получить путь
            zip_file_path = self.get_current_zip_file_path()
            if not zip_file_path:
                 logger.error("Could not find a valid file after refresh.")
                 return None # Не удалось найти файл даже после обновления

        try:
            mod_info = ModAnalyzer.analyze_zip(zip_file_path)
            return mod_info
        except Exception as e:
            logger.error(f"Error analyzing {zip_file_path}: {e}")
            # Создаем Fallback ModInfo, чтобы UI не падал
            fallback_name = os.path.basename(zip_file_path) if zip_file_path else "Unknown File"
            return ModInfo(name=f"Error Loading ({fallback_name})", author="Unknown", type=ModType.OTHER,
                           description=f"Failed to analyze mod: {e}", preview_images=[], additional_info={})

    def mark_as_sorted(self, zip_file_path: str, mod_info: ModInfo) -> None:
        """Adds a .mod_sorted marker file inside the ZIP archive using ONLY rewrite mode for debugging."""
        logger.info(f"--- DEBUG: Entering mark_as_sorted for {zip_file_path} (REWRITE ONLY) ---")  # DEBUG LOG 1
        start_time = time.time()

        if not mod_info:
            logger.warning(f"Cannot mark {zip_file_path} as sorted: mod_info is None.")
            logger.info(f"--- DEBUG: Exiting mark_as_sorted (mod_info is None) for {zip_file_path} ---") # ADDED EXIT LOG
            return

        # Проверяем маркер перед началом
        logger.debug("--- DEBUG: Checking for existing marker before rewrite ---")  # DEBUG LOG 2
        try:
            marker_already_exists = check_sorted_marker(zip_file_path)
            logger.debug(f"--- DEBUG: check_sorted_marker result: {marker_already_exists} ---") # ADDED RESULT LOG

            if marker_already_exists:
                logger.info(
                    f"--- DEBUG: Marker already exists in {zip_file_path}. Skipping rewrite. ---")  # DEBUG LOG 3
                # Log time taken even when skipping
                end_time_skip = time.time()
                logger.info(f"--- DEBUG: Exiting mark_as_sorted (marker exists, took {end_time_skip - start_time:.4f}s check) for {zip_file_path} ---") # ADDED EXIT LOG with time
                return  # Уже помечен - *** THIS RETURN IS CRUCIAL ***
        except Exception as check_err:
            # Log exception with traceback
            logger.error(
                f"--- DEBUG: Error checking marker for {zip_file_path}: {check_err}. Aborting mark. ---", exc_info=True)  # DEBUG LOG 4 + traceback
            logger.info(f"--- DEBUG: Exiting mark_as_sorted (check error) for {zip_file_path} ---") # ADDED EXIT LOG
            return  # Не можем проверить - не помечаем

        # --- If the code reaches here, it means the marker was NOT found or check failed safely ---
        logger.debug("--- DEBUG: Marker not found or check passed. Proceeding to rewrite. ---")  # DEBUG LOG 5

        marker_data = {
            "name": mod_info.name,
            "author": mod_info.author,
            "type": mod_info.type.value,
        }
        # Ensure encoding works for potential non-ascii chars
        try:
            marker_content = json.dumps(marker_data, indent=2, ensure_ascii=False).encode('utf-8')
        except Exception as json_err:
             logger.error(f"--- DEBUG: Failed to encode marker data to JSON: {json_err} ---", exc_info=True)
             logger.info(f"--- DEBUG: Exiting mark_as_sorted (JSON encode error) for {zip_file_path} ---")
             return # Cannot create marker content

        marker_filename = '.mod_sorted'

        # --- ТОЛЬКО Режим перезаписи (Rewrite Mode 'w') ---
        logger.info(f"--- DEBUG: Starting rewrite process for {zip_file_path} ---")  # DEBUG LOG 6
        temp_zip_path = None
        original_zip = None
        temp_zip = None
        try:
            # Создаем временный файл
            logger.debug("--- DEBUG: Creating temporary file... ---")  # DEBUG LOG 7
            # Use a more specific temp directory if needed, otherwise default is usually fine
            temp_zip_fd, temp_zip_path = tempfile.mkstemp(suffix='.zip', prefix='modsort_')
            os.close(temp_zip_fd)
            logger.debug(f"--- DEBUG: Temporary file created: {temp_zip_path} ---")  # DEBUG LOG 8

            # Открываем оригинальный файл для чтения
            logger.debug(f"--- DEBUG: Opening original ZIP '{zip_file_path}' for reading... ---")  # DEBUG LOG 9
            original_zip = zipfile.ZipFile(zip_file_path, 'r')
            logger.debug("--- DEBUG: Original ZIP opened. ---")  # DEBUG LOG 10

            # Открываем временный файл для записи
            logger.debug(f"--- DEBUG: Opening temporary ZIP '{temp_zip_path}' for writing (ZIP_DEFLATED)... ---")  # DEBUG LOG 11
            # Consider ZIP_STORED for faster rewrite if compression isn't critical for the temp step
            temp_zip = zipfile.ZipFile(temp_zip_path, 'w', compression=zipfile.ZIP_DEFLATED) # Specify compression
            logger.debug("--- DEBUG: Temporary ZIP opened for writing. ---")  # DEBUG LOG 12

            copied_count = 0
            logger.debug("--- DEBUG: Starting item copy loop... ---")  # DEBUG LOG 13
            item_list = original_zip.infolist()
            total_items = len(item_list)
            logger.debug(f"--- DEBUG: Found {total_items} items to potentially copy. ---")  # DEBUG LOG 14
            for i, item in enumerate(item_list):
                # Add progress logging for large archives
                if (i + 1) % 100 == 0 or i == total_items - 1: # Log every 100 items and the last one
                     logger.debug(f"--- DEBUG: Processing item {i+1}/{total_items}: {item.filename} ---")

                if item.filename != marker_filename:
                    try:
                        # Reading large files within the zip can take time
                        # logger.debug(f"--- DEBUG: Reading item: {item.filename} ({item.file_size} bytes) ---") # Potentially too verbose
                        buffer = original_zip.read(item.filename)
                        # logger.debug(f"--- DEBUG: Writing item: {item.filename} ({len(buffer)} bytes) ---") # Potentially too verbose
                        temp_zip.writestr(item, buffer)
                        copied_count += 1
                    except Exception as read_write_err:
                        # Log error with traceback
                        logger.error(f"--- DEBUG: Error copying item '{item.filename}': {read_write_err} ---", exc_info=True)
                        # Decide whether to continue or abort? For now, continue.
                        continue

            logger.debug(f"--- DEBUG: Finished copy loop. Copied {copied_count} items. ---")  # DEBUG LOG 15

            # Добавляем новый маркер
            logger.debug(f"--- DEBUG: Writing marker '{marker_filename}'... ---")  # DEBUG LOG 16
            temp_zip.writestr(marker_filename, marker_content)
            logger.debug("--- DEBUG: Marker written. ---")  # DEBUG LOG 17

            # --- Важно: Закрываем оба файла ПЕРЕД заменой ---
            logger.debug("--- DEBUG: Closing original ZIP... ---")  # DEBUG LOG 18
            original_zip.close()
            original_zip = None
            logger.debug("--- DEBUG: Closing temporary ZIP... ---")  # DEBUG LOG 19
            temp_zip.close()
            temp_zip = None
            logger.debug("--- DEBUG: Both ZIP files closed. ---")  # DEBUG LOG 20

            # Заменяем оригинальный файл временным
            logger.debug(
                f"--- DEBUG: Attempting os.replace: '{temp_zip_path}' -> '{zip_file_path}' ---")  # DEBUG LOG 21
            # Ensure target directory exists and we have permissions before replace
            target_dir = os.path.dirname(zip_file_path)
            if not os.path.exists(target_dir):
                 logger.warning(f"Target directory {target_dir} does not exist for os.replace!")
                 # Handle error appropriately, maybe raise exception
            os.replace(temp_zip_path, zip_file_path)
            logger.debug("--- DEBUG: os.replace successful. ---")  # DEBUG LOG 22
            temp_zip_path = None

            end_time = time.time()
            logger.info(
                f"--- DEBUG: Successfully marked {zip_file_path} using REWRITE mode (took {end_time - start_time:.2f}s) ---")  # DEBUG LOG 23

        except (FileNotFoundError, zipfile.BadZipFile) as file_err:
             logger.error(f"--- DEBUG: File error during rewrite for {zip_file_path}: {file_err} ---", exc_info=True)
             # No need to raise again, just log and exit the function
        except Exception as e:
            logger.exception( # Use logger.exception to include traceback automatically
                f"--- DEBUG: Rewrite method FAILED for {zip_file_path}. Error: {e} ---")  # DEBUG LOG 24 (ERROR)
            # Depending on desired behavior, you might want to raise e here or just log it.
            # raise e

        finally:
            # --- Гарантированно закрываем файлы, если они еще открыты ---
            if original_zip:
                try:
                    logger.debug("--- DEBUG: Closing original_zip in finally block. ---")
                    original_zip.close()
                except Exception as close_err:
                    logger.warning(f"--- DEBUG: Error closing original_zip in finally: {close_err} ---")
            if temp_zip:
                try:
                    logger.debug("--- DEBUG: Closing temp_zip in finally block. ---")
                    temp_zip.close()
                except Exception as close_err:
                    logger.warning(f"--- DEBUG: Error closing temp_zip in finally: {close_err} ---")

            # --- Удаляем временный файл, если замена не удалась ИЛИ если он вообще создавался ---
            if temp_zip_path and os.path.exists(temp_zip_path):
                try:
                    logger.debug(f"--- DEBUG: Removing temporary file {temp_zip_path} in finally block. ---")
                    os.remove(temp_zip_path)
                except OSError as remove_err:
                    logger.warning(
                        f"--- DEBUG: Could not remove temporary file {temp_zip_path} in finally: {remove_err} ---")
            logger.info(f"--- DEBUG: Exiting mark_as_sorted (finally block) for {zip_file_path} ---") # DEBUG LOG 25

    def _update_internal_list_after_change(self, changed_file_name: str, is_deleted: bool):
        """Helper to update self.zip_files_info and current_index after move/delete."""
        original_index = -1
        for i, info in enumerate(self.zip_files_info):
            if info['name'] == changed_file_name:
                original_index = i
                break

        if original_index != -1:
            del self.zip_files_info[original_index]
            logger.debug(f"Removed {changed_file_name} from internal list at index {original_index}.")

            # Корректируем индекс
            # Если удалили элемент ДО текущего, или сам текущий, сдвигаем индекс
            if self.current_index >= original_index:
                 # Не уменьшаем индекс, если удалили не текущий элемент,
                 # чтобы перейти к СЛЕДУЮЩЕМУ после удаленного/перемещенного.
                 # Но если удалили ПОСЛЕДНИЙ, индекс нужно сдвинуть назад.
                 if self.current_index >= len(self.zip_files_info):
                     self.current_index = max(0, len(self.zip_files_info) - 1)
                     logger.debug(f"Adjusted current index to {self.current_index} (last element or 0).")

        else:
             logger.warning(f"{changed_file_name} not found in internal list for update.")
             # На всякий случай перезагрузим список с диска, если внутренний список рассинхронизировался
             self.refresh_zip_list()

    def move_mod(self, zip_file_path: str, destination_path: str) -> None:
        """Moves a mod to the specified directory."""
        logger.debug(f"Moving {zip_file_path} to {destination_path}")
        moved_file_name = os.path.basename(zip_file_path) # Запомним имя до перемещения
        try:
            os.makedirs(destination_path, exist_ok=True)

            if check_sorted_marker(zip_file_path):
                logger.debug(f"Deleting .mod_sorted marker from {zip_file_path} before moving.")
                try:
                     _delete_sorted_marker(zip_file_path)
                except Exception as e:
                    logger.warning(f"Could not delete .mod_sorted before moving {zip_file_path}: {e}")

            dest_file_path = os.path.join(destination_path, moved_file_name)
            shutil.move(zip_file_path, dest_file_path)
            logger.info(f"Moved {zip_file_path} to {dest_file_path}")

            # Обновляем внутренний список и индекс
            self._update_internal_list_after_change(moved_file_name, is_deleted=False)

        except Exception as e:
            logger.exception(f"Failed to move {zip_file_path} to {destination_path}: {e}")
            # Проверим, исчез ли файл с исходного места, и обновим список если да
            if not os.path.exists(zip_file_path):
                self._update_internal_list_after_change(moved_file_name, is_deleted=False)
            raise

    def delete_mod(self, zip_file_path: str) -> None:
        """Deletes the specified mod."""
        logger.debug(f"Deleting {zip_file_path}")
        file_name_to_remove = os.path.basename(zip_file_path)
        try:
            os.remove(zip_file_path)
            logger.info(f"Deleted {zip_file_path}")
            # Обновляем внутренний список и индекс
            self._update_internal_list_after_change(file_name_to_remove, is_deleted=True)

        except Exception as e:
            logger.exception(f"Failed to delete {zip_file_path}: {e}")
             # Проверим, исчез ли файл, и обновим список если да
            if not os.path.exists(zip_file_path):
                 self._update_internal_list_after_change(file_name_to_remove, is_deleted=True)
            raise

    def remove_current_zip_file(self) -> None: # Используется ли этот метод? Если нет, можно удалить.
        if 0 <= self.current_index < len(self.zip_files_info):
            removed_file_info = self.zip_files_info.pop(self.current_index)
            logger.info(f"Removed zip file from list: {removed_file_info['name']}")
             # Корректируем индекс, если удалили последний
            if self.current_index >= len(self.zip_files_info):
                self.current_index = max(0, len(self.zip_files_info) - 1)
        else:
            logger.debug("No zip file to remove, current index out of range.")

    def increment_index(self) -> bool:
        """Increments index, returns True if successful, False if at the end."""
        if self.current_index < len(self.zip_files_info) - 1:
            self.current_index += 1
            logger.debug(f"Index incremented to {self.current_index}")
            return True
        else:
            logger.debug("Already at the last index.")
            return False

    # --- НОВОЕ: Метод для шага назад ---
    def decrement_index(self) -> bool:
        """Decrements index, returns True if successful, False if at the beginning."""
        if self.current_index > 0:
            self.current_index -= 1
            logger.debug(f"Index decremented to {self.current_index}")
            return True
        else:
            logger.debug("Already at the first index.")
            return False

    def reset_index(self) -> None:
        self.current_index = 0
        logger.debug("Index reset to 0.")

    def get_zip_files_count(self) -> int:
        return len(self.zip_files_info)

    def get_current_index(self) -> int:
        return self.current_index

    def set_current_index(self, index: int) -> None:
        if 0 <= index < len(self.zip_files_info):
            self.current_index = index
            logger.debug(f"Index set to {index}")
        else:
             logger.warning(f"Attempted to set invalid index: {index}. Max index is {len(self.zip_files_info)-1}")


    def get_zip_files(self) -> List[Dict[str, Any]]: # Возвращает список словарей
        return self.zip_files_info

    def get_current_zip_file_name(self) -> Optional[str]:
        if 0 <= self.current_index < len(self.zip_files_info):
            return self.zip_files_info[self.current_index]["name"]
        return None

    # --- НОВОЕ: Обновление списка файлов с диска ---
    def refresh_zip_list(self):
        """Reloads the list of zip files from the source folder."""
        logger.info("Refreshing zip file list from disk...")
        current_path = self.get_current_zip_file_path() # Запомним текущий путь
        self.zip_files_info = self._load_zip_files_with_info()
        logger.info(f"Refreshed list, found {len(self.zip_files_info)} files.")

        # Попытаемся восстановить индекс на тот же файл, если он еще существует
        new_index = -1
        if current_path:
             for i, info in enumerate(self.zip_files_info):
                 if info['path'] == current_path:
                     new_index = i
                     break

        if new_index != -1:
             self.current_index = new_index
             logger.debug(f"Restored index to {self.current_index} ({os.path.basename(current_path)}) after refresh.")
        else:
             # Если старого файла нет, или списка не было, ставим на начало или конец
             self.current_index = min(self.current_index, max(0, len(self.zip_files_info) - 1))
             logger.debug(f"Could not restore previous file index. Set index to {self.current_index} after refresh.")