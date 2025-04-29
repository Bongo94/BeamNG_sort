# core/mod_cache.py
import json
import os
import time
from typing import Dict, Optional, Any
from config.app_config import AppConfig
from utils.logger import logger
from core.mod_info import ModType # Import ModType if needed for cache structure

CACHE_VERSION = 1 # Increment if cache structure changes significantly

class ModCache:
    """Manages an external cache for mod analysis results."""

    def __init__(self, cache_file_path: str = AppConfig.CACHE_FILE_PATH):
        self.cache_file_path = cache_file_path
        self.cache_data: Dict[str, Dict[str, Any]] = self._load_cache()
        logger.info(f"ModCache initialized. Loaded {len(self.cache_data)} entries from {self.cache_file_path}")

    def _load_cache(self) -> Dict[str, Dict[str, Any]]:
        """Loads cache data from the JSON file."""
        if not os.path.exists(self.cache_file_path):
            logger.info(f"Cache file not found at {self.cache_file_path}. Starting with empty cache.")
            return {"_version": CACHE_VERSION} # Initialize with version

        try:
            with open(self.cache_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Basic version check (optional but recommended)
                if data.get("_version") != CACHE_VERSION:
                    logger.warning(f"Cache file version mismatch (expected {CACHE_VERSION}, found {data.get('_version')}). Discarding old cache.")
                    return {"_version": CACHE_VERSION}
                # Remove version info before returning data part
                if "_version" in data:
                    del data["_version"]
                return data
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding cache file {self.cache_file_path}: {e}. Starting with empty cache.")
            return {"_version": CACHE_VERSION}
        except Exception as e:
            logger.exception(f"Failed to load cache file {self.cache_file_path}: {e}. Starting with empty cache.")
            return {"_version": CACHE_VERSION}

    def _save_cache(self):
        """Saves the current cache data to the JSON file."""
        try:
            # Add version info before saving
            save_data = {"_version": CACHE_VERSION, **self.cache_data}
            with open(self.cache_file_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Cache saved successfully to {self.cache_file_path}")
        except Exception as e:
            logger.exception(f"Failed to save cache file {self.cache_file_path}: {e}")

    def get_cached_info(self, filename: str, file_mod_time: Optional[float]) -> Optional[Dict[str, Any]]:
        """
        Gets cached info for a file if it exists and the modification time matches.

        Args:
            filename: The base name of the zip file (e.g., "my_mod.zip").
            file_mod_time: The last modification timestamp (os.stat().st_mtime) of the zip file.

        Returns:
            The cached dictionary if valid, otherwise None.
        """
        if filename in self.cache_data:
            cached_entry = self.cache_data[filename]
            cached_mod_time = cached_entry.get('mod_time')

            # Check if modification times match (handle None cases)
            if file_mod_time is not None and cached_mod_time is not None and abs(file_mod_time - cached_mod_time) < 1e-6: # Compare floats carefully
                logger.debug(f"Cache hit for '{filename}'.")
                return cached_entry
            elif file_mod_time is None or cached_mod_time is None:
                 logger.debug(f"Cache hit for '{filename}', but modification time missing. Treating as valid (re-analysis might be needed if file changed).")
                 return cached_entry # Or return None if you want to force re-analysis when times are missing
            else:
                logger.info(f"Cache outdated for '{filename}' (mod time mismatch: file={file_mod_time}, cache={cached_mod_time}). Needs re-analysis.")
                return None # Outdated
        logger.debug(f"Cache miss for '{filename}'.")
        return None # Not in cache

    def update_cache(self, filename: str, file_mod_time: Optional[float], mod_info_dict: Dict[str, Any]):
        """
        Updates or adds an entry to the cache and saves it.

        Args:
            filename: The base name of the zip file.
            file_mod_time: The last modification timestamp of the zip file.
            mod_info_dict: A dictionary containing the basic info to cache
                           (e.g., {'name': ..., 'author': ..., 'type': ..., 'analyzed_time': ...}).
        """
        logger.debug(f"Updating cache for '{filename}'.")
        entry = mod_info_dict.copy() # Avoid modifying the original dict
        entry['mod_time'] = file_mod_time
        entry['analyzed_time'] = time.time() # Record when analysis was done
        self.cache_data[filename] = entry
        self._save_cache()

    def remove_from_cache(self, filename: str):
        """Removes an entry from the cache (e.g., if the file is deleted) and saves."""
        if filename in self.cache_data:
            logger.debug(f"Removing '{filename}' from cache.")
            del self.cache_data[filename]
            self._save_cache()

    def is_analyzed(self, filename: str, file_mod_time: Optional[float]) -> bool:
        """Checks if a file has a valid, up-to-date entry in the cache."""
        return self.get_cached_info(filename, file_mod_time) is not None