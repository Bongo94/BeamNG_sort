import os
import shutil
import zipfile
import json
import tempfile
import time
from typing import List, Optional, Dict, Any
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
                    try:
                        data = json.load(marker_file)
                        logger.debug(f"Marker data: {data}")
                        return data
                    except json.JSONDecodeError as json_e:
                        logger.warning(f"Error decoding JSON from marker in {zip_file_path}: {json_e}")
                        return None
            else:
                logger.debug("No sorted marker found.")
                return None
    except zipfile.BadZipFile:
        logger.warning(f"Bad zip file encountered while reading marker: {zip_file_path}")
        return None
    except FileNotFoundError:
        logger.warning(f"File not found while reading marker: {zip_file_path}")
        return None
    except Exception as e:
        logger.warning(f"Error reading marker data from {zip_file_path}: {e}")
        return None


def _delete_sorted_marker(zip_file_path: str) -> None:
    """Deletes the .mod_sorted marker file from *inside* the ZIP."""
    logger.debug(f"Attempting to delete sorted marker from: {zip_file_path}")
    temp_zip_path = None
    try:
        marker_filename = '.mod_sorted'
        marker_exists = False
        try:
             with zipfile.ZipFile(zip_file_path, 'r') as zf_check:
                 marker_exists = marker_filename in zf_check.namelist()
        except (zipfile.BadZipFile, FileNotFoundError) as check_err:
             logger.warning(f"Could not check for marker before deletion in {zip_file_path}: {check_err}")
             return

        if not marker_exists:
             logger.debug(f"Marker {marker_filename} not found in {zip_file_path}. No need to delete.")
             return

        logger.debug(f"Marker found. Proceeding with deletion via rewrite for {zip_file_path}")
        temp_zip_fd, temp_zip_path = tempfile.mkstemp(suffix='.zip')
        os.close(temp_zip_fd)

        with zipfile.ZipFile(zip_file_path, 'r') as original_zip:
            with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as temp_zip:
                for item in original_zip.infolist():
                    if item.filename != marker_filename:
                        buffer = original_zip.read(item.filename)
                        temp_zip.writestr(item, buffer)

        os.replace(temp_zip_path, zip_file_path)
        logger.info(f"Successfully deleted {marker_filename} from {zip_file_path}")

    except FileNotFoundError:
        logger.warning(f"File not found during marker deletion process: {zip_file_path}")
    except zipfile.BadZipFile:
        logger.error(f"Bad zip file during marker deletion process: {zip_file_path}")
    except Exception as e:
        logger.exception(f"Error removing {marker_filename} from {zip_file_path}: {e}")
        if temp_zip_path and os.path.exists(temp_zip_path):
            try:
                os.remove(temp_zip_path)
            except OSError as remove_err:
                logger.warning(f"Could not remove temporary file {temp_zip_path} after error: {remove_err}")
        raise


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
        return False
    except FileNotFoundError:
         logger.warning(f"File not found while checking for marker: {zip_file_path}")
         return False
    except Exception as e:
        logger.warning(f"Error checking for sorted marker in {zip_file_path}: {e}")
        return False

class ModManager:
    def __init__(self, source_folder: str):
        logger.debug(f"Initializing ModManager with source folder: {source_folder}")
        self.source_folder = source_folder
        self.zip_files_info: List[Dict[str, Any]] = self._load_zip_files_with_info()
        self.current_index = 0
        logger.info(f"ModManager initialized, found {len(self.zip_files_info)} zip files.")

    def _load_zip_files_with_info(self) -> List[Dict[str, Any]]:
        """Loads zip files and basic stats (name, path, size, modified time) recursively from the source folder."""
        logger.debug(f"Recursively loading zip files and info from: {self.source_folder}")
        files_info = []
        try:
            for root, dirs, files in os.walk(self.source_folder):
                for filename in files:
                    if filename.lower().endswith('.zip'):
                        full_path = os.path.join(root, filename)
                        try:
                            stats = os.stat(full_path)
                            files_info.append({
                                "name": filename,
                                "path": full_path,
                                "size": stats.st_size,
                                "modified": stats.st_mtime
                            })
                        except OSError as e:
                            logger.warning(f"Could not get stats for {full_path}: {e}")
                            files_info.append({"name": filename, "path": full_path, "size": None, "modified": None})

        except FileNotFoundError:
            logger.error(f"Source folder not found during loading: {self.source_folder}")
            return []
        except Exception as e:
            logger.exception(f"Error loading zip files list from {self.source_folder}: {e}")
            return []

        logger.debug(f"Found {len(files_info)} zip files with info.")
        # Сортируем файлы по имени для консистентного порядка
        files_info.sort(key=lambda x: x['name'].lower())
        return files_info

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

    def get_current_file_stats(self) -> Optional[Dict[str, Any]]:
        """Returns size and modified time for the current file."""
        if 0 <= self.current_index < len(self.zip_files_info):
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

        if not os.path.exists(zip_file_path):
            logger.warning(f"File no longer exists: {zip_file_path}. Refreshing list.")
            self.refresh_zip_list()
            zip_file_path = self.get_current_zip_file_path()
            if not zip_file_path:
                 logger.error("Could not find a valid file after refresh.")
                 return None

        try:
            mod_info = ModAnalyzer.analyze_zip(zip_file_path)
            return mod_info
        except Exception as e:
            logger.error(f"Error analyzing {zip_file_path}: {e}")
            fallback_name = os.path.basename(zip_file_path) if zip_file_path else "Unknown File"
            return ModInfo(name=f"Error Loading ({fallback_name})", author="Unknown", type=ModType.OTHER,
                           description=f"Failed to analyze mod: {e}", preview_images=[], additional_info={})

    def mark_as_sorted(self, zip_file_path: str, mod_info: ModInfo) -> None:
        """Adds a .mod_sorted marker file inside the ZIP archive using append mode."""
        logger.info(f"--- Entering mark_as_sorted for {zip_file_path} (APPEND MODE) ---")
        start_time = time.time()

        if not mod_info:
            logger.warning(f"Cannot mark {zip_file_path} as sorted: mod_info is None.")
            logger.info(f"--- Exiting mark_as_sorted (mod_info is None) for {zip_file_path} ---")
            return

        marker_filename = '.mod_sorted'

        logger.debug("--- Checking for existing marker before append ---")
        try:
            if check_sorted_marker(zip_file_path):
                logger.info(f"--- Marker already exists in {zip_file_path}. Skipping append. ---")
                end_time_skip = time.time()
                logger.info(
                    f"--- Exiting mark_as_sorted (marker exists, check took {end_time_skip - start_time:.4f}s) for {zip_file_path} ---")
                return
        except Exception as check_err:
            logger.error(f"--- Error checking marker for {zip_file_path}: {check_err}. Aborting mark. ---",
                         exc_info=True)
            logger.info(f"--- Exiting mark_as_sorted (check error) for {zip_file_path} ---")
            return

        logger.debug("--- Marker not found. Proceeding to append. ---")
        marker_data = {
            "name": mod_info.name,
            "author": mod_info.author,
            "type": mod_info.type.value,
            "timestamp": time.time()
        }
        try:
            marker_content = json.dumps(marker_data, indent=2, ensure_ascii=False).encode('utf-8')
        except Exception as json_err:
            logger.error(f"--- Failed to encode marker data to JSON: {json_err} ---", exc_info=True)
            logger.info(f"--- Exiting mark_as_sorted (JSON encode error) for {zip_file_path} ---")
            return

        logger.info(f"--- Starting append process for {zip_file_path} ---")
        try:
            with zipfile.ZipFile(zip_file_path, 'a', compression=zipfile.ZIP_DEFLATED) as zf:
                logger.debug(f"--- Writing marker '{marker_filename}'... ---")
                zf.writestr(marker_filename, marker_content)
                logger.debug(f"--- Marker written. ---")

            end_time = time.time()
            logger.info(
                f"--- Successfully marked {zip_file_path} using APPEND mode (took {end_time - start_time:.2f}s) ---")

        except FileNotFoundError:
            logger.error(f"--- File not found during append for {zip_file_path} ---", exc_info=True)
        except zipfile.BadZipFile:
            logger.error(f"--- Bad zip file during append for {zip_file_path} ---", exc_info=True)
        except Exception as e:
            logger.exception(f"--- Append method FAILED for {zip_file_path}. Error: {e} ---")
        finally:
            logger.info(f"--- Exiting mark_as_sorted (finally block or end of try) for {zip_file_path} ---")

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


            if self.current_index >= original_index:
                 if self.current_index >= len(self.zip_files_info):
                     self.current_index = max(0, len(self.zip_files_info) - 1)
                     logger.debug(f"Adjusted current index to {self.current_index} (last element or 0).")

        else:
             logger.warning(f"{changed_file_name} not found in internal list for update.")
             self.refresh_zip_list()

    def move_mod(self, zip_file_path: str, destination_path: str) -> None:
        """Moves a mod to the specified directory."""
        logger.debug(f"Moving {zip_file_path} to {destination_path}")
        moved_file_name = os.path.basename(zip_file_path)
        start_time = time.time()
        try:
            os.makedirs(destination_path, exist_ok=True)
            dest_file_path = os.path.join(destination_path, moved_file_name)

            try:
                os.rename(zip_file_path, dest_file_path)
                logger.info(f"Moved (renamed) {zip_file_path} to {dest_file_path}")
            except OSError as e:
                logger.warning(f"os.rename failed ({e}), falling back to shutil.move for {zip_file_path}")
                shutil.move(zip_file_path, dest_file_path)
                logger.info(f"Moved (shutil.move) {zip_file_path} to {dest_file_path}")

            self._update_internal_list_after_change(moved_file_name, is_deleted=False)

        except Exception as e:
            logger.exception(f"Failed to move {zip_file_path} to {destination_path}: {e}")
            if not os.path.exists(zip_file_path):
                self._update_internal_list_after_change(moved_file_name, is_deleted=False)
            raise
        finally:
            end_time = time.time()
            logger.debug(f"Move operation for {moved_file_name} took {end_time - start_time:.2f}s")
            
    def delete_mod(self, zip_file_path: str) -> None:
        """Deletes the specified mod."""
        logger.debug(f"Deleting {zip_file_path}")
        file_name_to_remove = os.path.basename(zip_file_path)
        try:
            os.remove(zip_file_path)
            logger.info(f"Deleted {zip_file_path}")
            self._update_internal_list_after_change(file_name_to_remove, is_deleted=True)

        except Exception as e:
            logger.exception(f"Failed to delete {zip_file_path}: {e}")
            if not os.path.exists(zip_file_path):
                 self._update_internal_list_after_change(file_name_to_remove, is_deleted=True)
            raise

    def remove_current_zip_file(self) -> None:
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


    def get_zip_files(self) -> List[Dict[str, Any]]:
        return self.zip_files_info

    def get_current_zip_file_name(self) -> Optional[str]:
        if 0 <= self.current_index < len(self.zip_files_info):
            return self.zip_files_info[self.current_index]["name"]
        return None

    def refresh_zip_list(self):
        """Reloads the list of zip files from the source folder."""
        logger.info("Refreshing zip file list from disk...")
        current_path = self.get_current_zip_file_path()
        self.zip_files_info = self._load_zip_files_with_info()
        logger.info(f"Refreshed list, found {len(self.zip_files_info)} files.")

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
             self.current_index = min(self.current_index, max(0, len(self.zip_files_info) - 1))
             logger.debug(f"Could not restore previous file index. Set index to {self.current_index} after refresh.")