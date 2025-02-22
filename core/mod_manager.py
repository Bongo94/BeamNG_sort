# mod_sorter/core/mod_manager.py
import os
import shutil
import zipfile
import json
import tempfile
from typing import List, Optional
from core.mod_info import ModInfo
from utils.logger import logger  # Import the logger
from core.mod_analyzer import ModAnalyzer


def get_mod_info_from_marker(zip_file_path: str) -> Optional[dict]:
    """Reads the .mod_sorted file from inside the ZIP and returns the data."""
    logger.debug(f"Reading mod info from marker in: {zip_file_path}")
    try:
        with zipfile.ZipFile(zip_file_path, 'r') as zf:
            if '.mod_sorted' in zf.namelist():
                with zf.open('.mod_sorted') as marker_file:
                    data = json.load(marker_file)
                    logger.debug(f"Marker data: {data}")
                    return data
            else:
                logger.debug("No sorted marker found.")
                return None
    except Exception as e:
        logger.warning(f"Error reading marker data from {zip_file_path}: {e}")
        return None


def _delete_sorted_marker(zip_file_path: str) -> None:
    """Deletes the .mod_sorted marker file from *inside* the ZIP."""
    logger.debug(f"Deleting sorted marker from: {zip_file_path}")
    try:
        with zipfile.ZipFile(zip_file_path, 'r') as original_zip:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_zip_file:
                temp_zip_path = temp_zip_file.name  # Get the temporary file path
                with zipfile.ZipFile(temp_zip_file, 'w') as temp_zip:
                    # Copy all files except the marker
                    for item in original_zip.infolist():
                        if item.filename != '.mod_sorted':
                            buffer = original_zip.read(item.filename)
                            temp_zip.writestr(item, buffer)

        # Replace the original ZIP file with the temporary one
        os.replace(temp_zip_path, zip_file_path)
        logger.info(f"Successfully deleted .mod_sorted from {zip_file_path}")

    except FileNotFoundError:
        logger.warning(f".mod_sorted not found in {zip_file_path}")  # Log if marker not found
    except Exception as e:
        logger.exception(f"Error removing .mod_sorted from {zip_file_path}: {e}")


def _check_sorted_marker(zip_file_path: str) -> bool:
    """Checks if a .mod_sorted marker exists *inside* the ZIP."""
    logger.debug(f"Checking for sorted marker in: {zip_file_path}")
    try:
        with zipfile.ZipFile(zip_file_path, 'r') as zf:
            is_sorted = '.mod_sorted' in zf.namelist()
            logger.debug(f"Sorted marker found: {is_sorted}")
            return is_sorted
    except Exception as e:
        logger.warning(f"Error checking for sorted marker in {zip_file_path}: {e}")
        return False  # Assume not sorted if there's an error


def move_mod(zip_file_path: str, destination_path: str) -> None:
    """Moves a mod to the specified directory."""
    logger.debug(f"Moving {zip_file_path} to {destination_path}")
    try:
        os.makedirs(destination_path, exist_ok=True)
        shutil.move(zip_file_path, destination_path)
        logger.info(f"Moved {zip_file_path} to {destination_path}")
    except Exception as e:
        logger.exception(f"Failed to move {zip_file_path} to {destination_path}: {e}")
        raise  # Re-raise the exception for the UI to handle


class ModManager:
    """Business logic for mod management"""

    def __init__(self, source_folder: str):
        logger.debug(f"Initializing ModManager with source folder: {source_folder}")
        self.source_folder = source_folder
        self.zip_files = self._load_zip_files()
        self.current_index = 0
        logger.info(f"ModManager initialized, found {len(self.zip_files)} zip files.")

    def _load_zip_files(self) -> List[str]:
        logger.debug(f"Loading zip files from: {self.source_folder}")
        zip_files = [f for f in os.listdir(self.source_folder) if f.endswith('.zip')]
        logger.debug(f"Found zip files: {zip_files}")
        return zip_files

    def get_current_zip_file_path(self) -> Optional[str]:
        if self.current_index < len(self.zip_files):
            return os.path.join(self.source_folder, self.zip_files[self.current_index])
        return None

    def get_current_mod_info(self) -> Optional[ModInfo]:
        """Gets ModInfo for the current zip file"""
        zip_file_path = self.get_current_zip_file_path()
        if not zip_file_path:
            logger.warning("No current zip file path, cannot get mod info.")
            return None

        try:
            mod_info = ModAnalyzer.analyze_zip(zip_file_path)
            return mod_info
        except Exception as e:
            logger.error(f"Error analyzing {zip_file_path}: {e}")
            return None

    def mark_as_sorted(self, zip_file_path: str, mod_info: ModInfo) -> None:
        """Marks a mod as sorted by adding a .mod_sorted file *inside* the ZIP."""
        logger.debug(f"Marking as sorted: {zip_file_path}")
        try:
            if _check_sorted_marker(zip_file_path):  # Add this check
                logger.info(f"{zip_file_path} is already marked as sorted.")
                return  # Exit if already sorted

            with zipfile.ZipFile(zip_file_path, 'a') as zf:
                # Convert ModInfo to a dictionary, handling ModType
                mod_info_dict = {
                    'name': mod_info.name,
                    'author': mod_info.author,
                    'type': mod_info.type.value,  # Store the value of the enum
                    'description': mod_info.description,
                    # You *could* store preview image names, but not the image data itself
                    'additional_info': mod_info.additional_info
                }
                marker_data = json.dumps(mod_info_dict, indent=4).encode('utf-8')
                zf.writestr('.mod_sorted', marker_data, compress_type=zipfile.ZIP_DEFLATED)
            logger.info(f"Successfully marked {zip_file_path} as sorted.")
        except Exception as e:
            logger.exception(f"Failed to create marker file inside ZIP: {e}")
            raise RuntimeError(f"Failed to create marker file inside ZIP: {e}")


    def _check_sorted_marker(self, zip_file_path: str) -> bool:
        """Checks if a .mod_sorted marker exists *inside* the ZIP."""
        logger.debug(f"Checking for sorted marker in: {zip_file_path}")
        try:
            with zipfile.ZipFile(zip_file_path, 'r') as zf:
                is_sorted = '.mod_sorted' in zf.namelist()
                logger.debug(f"Sorted marker found: {is_sorted}")
                return is_sorted
        except Exception as e:
            logger.warning(f"Error checking for sorted marker in {zip_file_path}: {e}")
            return False  # Assume not sorted if there's an error

    def delete_mod(self, zip_file_path: str) -> None:
        """Deletes the specified mod."""
        logger.debug(f"Deleting {zip_file_path}")
        try:
            os.remove(zip_file_path)
            logger.info(f"Deleted {zip_file_path}")
            self.zip_files.remove(os.path.basename(zip_file_path)) # Remove from list
        except Exception as e:
            logger.exception(f"Failed to delete {zip_file_path}: {e}")
            raise # Re-raise the exception

    def remove_current_zip_file(self) -> None:  # Remove from ModManager's list
        if self.current_index < len(self.zip_files):
            removed_file = self.zip_files.pop(self.current_index)
            logger.info(f"Removed zip file from list: {removed_file}")
        else:
            logger.debug("No zip file to remove, current index out of range.")

    def increment_index(self) -> None:
        self.current_index += 1

    def decrement_index(self) -> None:
        self.current_index -= 1

    def reset_index(self) -> None:
        self.current_index = 0

    def get_zip_files_count(self) -> int:
        return len(self.zip_files)

    def get_current_index(self) -> int:
        return self.current_index

    def set_current_index(self, index: int) -> None:
        self.current_index = index

    def get_zip_files(self) -> List[str]:
        return self.zip_files

    def get_current_zip_file_name(self) -> Optional[str]:
        if self.current_index < len(self.zip_files):
            return self.zip_files[self.current_index]
        return None