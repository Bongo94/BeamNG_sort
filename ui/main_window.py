import json
import math
import os
import sys
from datetime import datetime
from typing import Optional

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QShortcut, QKeySequence
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QFileDialog,
                             QMessageBox, QComboBox, QTextEdit, QTabWidget, QGroupBox, QLineEdit)
from packaging.version import Version, InvalidVersion

from config.app_config import AppConfig
from core.mod_info import ModInfo, ModType
from core.mod_manager import ModManager, check_sorted_marker
from ui.event_handlers import PreviousModHandler, SkipModHandler, NextModHandler, DeleteModHandler, MoveModHandler, \
    MoveModToFolderHandler
from utils.logger import logger


# Format
def format_filesize(size_bytes: Optional[int]) -> str:
    """Converts bytes to a human-readable string (KB, MB, GB)."""
    if size_bytes is None or size_bytes < 0:
        return "N/A"
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

def format_timestamp(timestamp: Optional[float]) -> str:
    """Converts a Unix timestamp to a readable date/time string."""
    if timestamp is None:
        return "N/A"
    try:
        dt_object = datetime.fromtimestamp(timestamp)
        return dt_object.strftime('%Y-%m-%d %H:%M')
    except Exception:
        logger.warning(f"Could not format timestamp: {timestamp}")
        return "Invalid Date"


class ModSorterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BeamNG Mod Sorter")
        self.setMinimumSize(QSize(AppConfig.WINDOW_MIN_WIDTH, AppConfig.WINDOW_MIN_HEIGHT))

        self.mod_manager = None
        self.current_mod_info = None
        self.current_image_index = 0
        self.skip_sorted = False
        self.move_folders_config = self._load_move_folders_config()

        self._ask_skip_sorted()
        self._setup_ui()
        self._setup_shortcuts()
        # self.source_folder = self.select_source_folder()
        self.source_folder = self._initialize_source_folder()

        if self.source_folder:
            self.mod_manager = ModManager(self.source_folder)
            self.load_current_mod()
        else:
            logger.info("No source folder selected, exiting.")
            sys.exit()

    def _initialize_source_folder(self) -> Optional[str]:
        """Tries to auto-detect the mods folder and asks the user, falling back to manual selection."""
        detected_path = self._find_beamng_mods_folder()

        if detected_path:
            logger.info(f"Auto-detected BeamNG mods folder: {detected_path}")
            reply = QMessageBox.question(
                self,
                    "Mods folder not found",
                    f"The mods folder was automatically detected:\n\n"
                    f"{detected_path}\n\n"
                    f"Do you want to use it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )

            if reply == QMessageBox.StandardButton.Yes:
                return detected_path

        logger.info("Falling back to manual folder selection.")
        return self.select_source_folder()

    def _find_beamng_mods_folder(self) -> Optional[str]:
        """
        Scans for the latest BeamNG.drive version folder in AppData
        and returns the path to the 'mods' subdirectory if it exists.
        """
        logger.debug("Attempting to auto-detect BeamNG mods folder.")
        try:
            base_path = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'BeamNG.drive')

            if not os.path.isdir(base_path):
                logger.debug(f"BeamNG base path not found at: {base_path}")
                return None

            version_folders = []
            for item in os.listdir(base_path):
                item_path = os.path.join(base_path, item)
                if os.path.isdir(item_path):
                    try:
                        Version(item)
                        version_folders.append(item)
                    except InvalidVersion:
                        continue

            if not version_folders:
                logger.debug("No version-like folders found in BeamNG directory.")
                return None

            version_folders.sort(key=Version, reverse=True)
            latest_version = version_folders[0]
            logger.debug(f"Found latest version folder: {latest_version}")

            mods_path = os.path.join(base_path, latest_version, 'mods')
            if os.path.isdir(mods_path):
                logger.info(f"Successfully found mods path: {mods_path}")
                return mods_path
            else:
                logger.warning(f"Mods folder does not exist at the expected path: {mods_path}")
                return None

        except FileNotFoundError:
            logger.info("BeamNG.drive directory not found. Cannot auto-detect.")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during mods folder detection: {e}", exc_info=True)
            return None

    def _load_move_folders_config(self):
        """Returns a hardcoded list of dictionaries for the move buttons."""
        logger.info("Loading hardcoded move folders configuration.")
        return [
            {
                "name": "Move to Repo",
                "path": "repo"
            },
            {
                "name": "Move to Real Cars",
                "path": "real_cars"
            },
            {
                "name": "Move to Maps",
                "path": "maps"
            },
            {
                "name": "Move to Utils",
                "path": "utils"
            },
            {
                "name": "Move to Tuning",
                "path": "tuning"
            },
            {
                "name": "Move to Other",
                "path": "other"
            }
        ]
    def _setup_ui(self):
        logger.debug("Setting up UI")

        # Main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        self._create_toolbar()
        self._create_file_info_group()
        self._create_tab_widget()
        self._create_action_buttons()
        self._create_dynamic_buttons()
        self._create_progress_bar()

        self.statusBar().showMessage("Ready")

    def _create_toolbar(self):
        self.toolbar_layout = QHBoxLayout()

        # Search
        self.search_group = QGroupBox("Search")
        search_layout = QHBoxLayout(self.search_group)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by mod name...")
        self.search_input.textChanged.connect(self._filter_mods)
        search_layout.addWidget(self.search_input)
        self.toolbar_layout.addWidget(self.search_group, stretch=2)

        # Filter
        self.filter_group = QGroupBox("Filters")
        filter_layout = QHBoxLayout(self.filter_group)
        self.mod_type_filter = QComboBox()
        self.mod_type_filter.addItems([t.value for t in ModType])
        self.mod_type_filter.addItem("All")
        self.mod_type_filter.currentTextChanged.connect(self.filter_mods)
        filter_layout.addWidget(QLabel("Mod Type:"))
        filter_layout.addWidget(self.mod_type_filter)
        self.toolbar_layout.addWidget(self.filter_group, stretch=1)

        self.main_layout.addLayout(self.toolbar_layout)

    def _create_file_info_group(self):
        self.file_info_group = QGroupBox("Current File")
        file_info_layout = QVBoxLayout(self.file_info_group)
        self.file_name_label = QLabel("File: N/A") # Начальное значение
        self.file_name_label.setStyleSheet("font-weight: bold;")
        self.file_name_label.setWordWrap(True) # Перенос длинных имен

        # Statistics
        self.file_stats_label = QLabel("Size: N/A | Modified: N/A")
        self.file_stats_label.setStyleSheet("font-size: 9pt; color: gray;")

        file_info_layout.addWidget(self.file_name_label)
        file_info_layout.addWidget(self.file_stats_label)
        self.main_layout.addWidget(self.file_info_group)

    def _create_tab_widget(self):
        self.tab_widget = QTabWidget()

        # Basic info tab
        self.basic_info_widget = QWidget()
        basic_info_layout = QVBoxLayout(self.basic_info_widget)

        self.info_fields_group = QGroupBox("Basic Information")
        info_fields_layout = QVBoxLayout(self.info_fields_group)
        self.name_label = QLabel()
        self.author_label = QLabel()
        self.type_label = QLabel()
        for label in [self.name_label, self.author_label, self.type_label]:
            label.setStyleSheet("font-weight: bold;")
            info_fields_layout.addWidget(label)
        basic_info_layout.addWidget(self.info_fields_group)

        self.desc_group = QGroupBox("Description")
        desc_layout = QVBoxLayout(self.desc_group)
        self.desc_text = QTextEdit()
        self.desc_text.setReadOnly(True)
        self.desc_text.setMinimumHeight(100)
        desc_layout.addWidget(self.desc_text)
        basic_info_layout.addWidget(self.desc_group)

        self.tab_widget.addTab(self.basic_info_widget, "Basic Information")

        # Images tab
        self.images_widget = QWidget()
        images_layout = QVBoxLayout(self.images_widget)

        self.nav_group = QGroupBox("Navigation")
        image_nav_layout = QHBoxLayout(self.nav_group)
        self.prev_image_btn = QPushButton("←")
        self.next_image_btn = QPushButton("→")
        self.image_counter_label = QLabel()
        self.image_name_label = QLabel()
        image_nav_layout.addWidget(self.prev_image_btn)
        image_nav_layout.addWidget(self.image_counter_label)
        image_nav_layout.addWidget(self.next_image_btn)
        images_layout.addWidget(self.nav_group)
        images_layout.addWidget(self.image_name_label)

        self.image_group = QGroupBox("Preview")
        image_group_layout = QVBoxLayout(self.image_group)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(AppConfig.IMAGE_DISPLAY_WIDTH, AppConfig.IMAGE_DISPLAY_HEIGHT)
        image_group_layout.addWidget(self.image_label)
        images_layout.addWidget(self.image_group)

        self.prev_image_btn.clicked.connect(self.show_prev_image)
        self.next_image_btn.clicked.connect(self.show_next_image)
        self.tab_widget.addTab(self.images_widget, "Images")

        # Additional info tab
        self.additional_info_widget = QWidget()
        additional_info_layout = QVBoxLayout(self.additional_info_widget)
        self.additional_info_text = QTextEdit()
        self.additional_info_text.setReadOnly(True)
        additional_info_layout.addWidget(self.additional_info_text)
        self.tab_widget.addTab(self.additional_info_widget, "Additional Info")

        self.main_layout.addWidget(self.tab_widget)

    def _create_action_buttons(self):
        self.actions_group = QGroupBox("Actions")
        button_layout = QHBoxLayout(self.actions_group)


        self.prev_button = QPushButton("← Previous (Ctrl+B)")
        self.skip_button = QPushButton("Skip (Ctrl+S)")


        self.keep_button = QPushButton("Keep && Next (Ctrl+K)")
        self.delete_button = QPushButton("Delete (Ctrl+D)")
        self.move_button = QPushButton("Move (Ctrl+M)")

        # Styles
        self.prev_button.setStyleSheet("background-color: #cccccc;")
        self.skip_button.setStyleSheet("background-color: #ffc107;")
        self.keep_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.delete_button.setStyleSheet("background-color: #f44336; color: white;")
        self.move_button.setStyleSheet("background-color: #2196F3; color: white;")


        button_layout.addWidget(self.prev_button)
        button_layout.addWidget(self.skip_button)
        button_layout.addWidget(self.keep_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.move_button)

        for button in [self.prev_button, self.skip_button, self.keep_button, self.delete_button, self.move_button]:
            button.setMinimumWidth(120)

        # Подключаем сигналы к новым слотам
        self.prev_button.clicked.connect(self.prev_mod_clicked)
        self.skip_button.clicked.connect(self.skip_mod_clicked)
        # ---
        self.keep_button.clicked.connect(self.next_mod_clicked)
        self.delete_button.clicked.connect(self.delete_mod_clicked)
        self.move_button.clicked.connect(self.move_mod_clicked)

        self.main_layout.addWidget(self.actions_group)

        # Tab order
        QWidget.setTabOrder(self.search_input, self.mod_type_filter)
        QWidget.setTabOrder(self.mod_type_filter, self.prev_button)
        QWidget.setTabOrder(self.prev_button, self.skip_button)
        QWidget.setTabOrder(self.skip_button, self.keep_button)
        QWidget.setTabOrder(self.keep_button, self.delete_button)
        QWidget.setTabOrder(self.delete_button, self.move_button)

    def _create_dynamic_buttons(self):
        self.dynamic_buttons_group = QGroupBox("Move to...")
        self.dynamic_buttons_layout = QHBoxLayout(self.dynamic_buttons_group)

        if not self.move_folders_config:
            logger.warning("No move folders configured.")
            return

        for button_config in self.move_folders_config:
            name = button_config.get('name')
            path = button_config.get('path')

            if not name or not path:
                logger.warning(f"Invalid button config: {button_config}")
                continue

            button = QPushButton(name)
            button.clicked.connect(lambda checked, p=path: self.move_mod_to_folder_clicked(p))
            self.dynamic_buttons_layout.addWidget(button)

        self.main_layout.addWidget(self.dynamic_buttons_group)

    def _create_progress_bar(self):
        self.progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(self.progress_group)
        self.counter_label = QLabel()
        self.counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(self.counter_label)
        self.main_layout.addWidget(self.progress_group)

    def _ask_skip_sorted(self):
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Skip Sorted Mods?")
        msg_box.setText("Do you want to skip mods that have already been sorted?")
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)

        reply = msg_box.exec()
        self.skip_sorted = (reply == QMessageBox.StandardButton.Yes)
        logger.info(f"User chose to skip sorted mods: {self.skip_sorted}")

    def _setup_shortcuts(self):
        logger.debug("Setting up keyboard shortcuts")
        QShortcut(QKeySequence("Ctrl+B"), self, self.prev_button.click)
        QShortcut(QKeySequence("Ctrl+S"), self, self.skip_button.click)
        QShortcut(QKeySequence("Ctrl+K"), self, self.keep_button.click)
        QShortcut(QKeySequence("Ctrl+D"), self, self.delete_button.click)
        QShortcut(QKeySequence("Ctrl+M"), self, self.move_button.click)
        QShortcut(QKeySequence(Qt.Key.Key_Left), self, self.show_prev_image)
        QShortcut(QKeySequence(Qt.Key.Key_Right), self, self.show_next_image)
        logger.info("Keyboard shortcuts setup complete")

    def handle_error(self, error: Exception, title: str = "Error"):
        logger.error(f"Error: {title} - {error}")
        QMessageBox.critical(self, title, str(error))

    def show_prev_image(self):
        if not self.current_mod_info or not self.current_mod_info.preview_images:
            return
        self.current_image_index = (self.current_image_index - 1) % len(self.current_mod_info.preview_images)
        self.update_image_display()

    def show_next_image(self):
        if not self.current_mod_info or not self.current_mod_info.preview_images:
            return
        self.current_image_index = (self.current_image_index + 1) % len(self.current_mod_info.preview_images)
        self.update_image_display()

    def update_image_display(self):
        if not self.current_mod_info or not self.current_mod_info.preview_images:
            self.image_label.setText("No images found")
            self.image_counter_label.setText("0/0")
            self.image_name_label.setText("")
            return

        try:
            image_name, image_data = self.current_mod_info.preview_images[self.current_image_index]
            pixmap = QPixmap()

            if not pixmap.loadFromData(image_data):
                raise RuntimeError(f"Failed to load image: {image_name}")

            scaled_pixmap = pixmap.scaled(
                AppConfig.IMAGE_DISPLAY_WIDTH,
                AppConfig.IMAGE_DISPLAY_HEIGHT,
                Qt.AspectRatioMode.KeepAspectRatio
            )

            self.image_label.setPixmap(scaled_pixmap)
            self.image_counter_label.setText(
                f"{self.current_image_index + 1}/{len(self.current_mod_info.preview_images)}"
            )
            self.image_name_label.setText(f"File: {image_name}")
            logger.debug(f"Displayed image: {image_name}")

        except Exception as e:
            self.handle_error(e, "Image display error")

    def _filter_mods(self):
        search_text = self.search_input.text().lower()
        logger.debug(f"Filtering mods by name: {search_text}")
        if not search_text:
            self.load_current_mod()
            return

        if not self.mod_manager:
            logger.warning("ModManager not initialized, cannot filter.")
            return

        current_index = self.mod_manager.get_current_index()
        zip_files = self.mod_manager.get_zip_files()

        while current_index < len(zip_files):
            if search_text in zip_files[current_index].lower():
                self.mod_manager.set_current_index(current_index)
                logger.debug(f"Found matching mod, setting index to: {current_index}")
                self.load_current_mod()
                return
            current_index += 1
            self.mod_manager.increment_index()

        QMessageBox.information(self, "Search", "No mods found!")
        self.mod_manager.reset_index()
        logger.info("No mods found matching search criteria, resetting index.")
        self.load_current_mod()

    @staticmethod
    def format_additional_info(mod_info: ModInfo) -> str:
        logger.debug(f"Formatting additional info for mod type: {mod_info.type}")
        if mod_info.type == ModType.VEHICLE:
            configs = mod_info.additional_info.get('configurations', [])
            paints = mod_info.additional_info.get('paints', {})

            info_parts = [
                "Configurations:",
                ", ".join(configs) or "None",
                "\nAvailable Paints:",
                ", ".join(paints.keys()) if paints else "None"
            ]

            if 'raw_info' in mod_info.additional_info:
                raw = mod_info.additional_info['raw_info']
                if 'Tuning' in raw:
                    info_parts.extend([
                        "\nAvailable Tuning:",
                        json.dumps(raw['Tuning'], indent=2, ensure_ascii=False)
                    ])

            formatted_info = "\n".join(info_parts)
            logger.debug(f"Formatted vehicle info: {formatted_info}")
            return formatted_info

        elif mod_info.type == ModType.MAP:
            info = mod_info.additional_info
            roads = info.get('roads', [])
            if not isinstance(roads, list):
                roads = []

            suitable_for = info.get('suitable_for', [])
            if not isinstance(suitable_for, list):
                suitable_for = []

            formatted_info = (
                f"Spawn Points: {len(info.get('spawn_points', []))}\n"
                f"Roads: {', '.join(roads)}\n"
                f"Suitable for: {', '.join(suitable_for)}\n"
                f"\nFull Information:\n"
                f"{json.dumps(info.get('raw_info', {}), indent=2, ensure_ascii=False)}"
            )
            logger.debug(f"Formatted map info: {formatted_info}")
            return formatted_info

        formatted_info = json.dumps(mod_info.additional_info, indent=2, ensure_ascii=False)
        logger.debug(f"Formatted other info: {formatted_info}")
        return formatted_info

    def filter_mods(self):
        selected_type = self.mod_type_filter.currentText()
        logger.debug(f"Filtering mods by type: {selected_type}")
        if selected_type == "All":
            self.load_current_mod()
            return

        if not self.mod_manager:
            logger.warning("ModManager not initialized, cannot filter.")
            return

        current_index = self.mod_manager.get_current_index()
        zip_files = self.mod_manager.get_zip_files()

        current_file_path = self.mod_manager.get_current_zip_file_path()
        if not current_file_path:
            logger.warning("No current zip file path, cannot filter.")
            return

        current_mod = self.mod_manager.get_current_mod_info()
        if not current_mod:
            logger.warning("No current mod info, cannot filter.")
            return

        while current_mod.type.value != selected_type:
            current_index += 1
            self.mod_manager.increment_index()
            if current_index >= len(zip_files):
                QMessageBox.information(self, "Filter", "No more mods of selected type!")
                self.mod_manager.reset_index()
                logger.info("No more mods of selected type, resetting index.")
                break

            current_mod = self.mod_manager.get_current_mod_info()
            if not current_mod:
                logger.warning("No current mod info, cannot filter.")
                return

        self.load_current_mod()

    def select_source_folder(self):
        source_folder = QFileDialog.getExistingDirectory(
            self, "Select the directory with mod archives"
        )

        if not source_folder:
            QMessageBox.critical(self, "Error", "Directory not selected")
            logger.warning("No source folder selected.")
            return None

        logger.info(f"Source folder selected: {source_folder}")
        return source_folder

    def load_current_mod(self):
        logger.debug("--- Entering load_current_mod ---")
        if not self.mod_manager:
            logger.warning("ModManager not initialized, cannot load mod.")
            self.clear_ui()
            self.statusBar().showMessage("Error: Mod manager not ready.")
            logger.debug("--- Exiting load_current_mod (no mod_manager) ---")
            return

        zip_files_count = self.mod_manager.get_zip_files_count()
        current_index = self.mod_manager.get_current_index()
        logger.debug(f"Zip count: {zip_files_count}, Current index: {current_index}")

        if zip_files_count == 0:
            logger.info("No zip files found in the source folder.")
            self.clear_ui()
            self.counter_label.setText("Mod 0 of 0")
            self.statusBar().showMessage("No mods found in the selected folder.")
            logger.debug("--- Exiting load_current_mod (no zip files) ---")
            return
        else:
            pass

        if current_index >= zip_files_count:
            if zip_files_count > 0:
                logger.warning(
                    f"Current index {current_index} is out of bounds (0-{zip_files_count - 1}). Resetting to last.")
                self.mod_manager.set_current_index(zip_files_count - 1)
                current_index = self.mod_manager.get_current_index()
                logger.debug(f"Index reset to {current_index}")
            else:
                QMessageBox.information(self, "Complete", "All mods have been processed!")
                logger.info("All files processed.")
                self.clear_ui()
                self.counter_label.setText(f"Mod {current_index} of {zip_files_count}")
                self.statusBar().showMessage("All mods processed!")
                logger.debug("--- Exiting load_current_mod (all processed) ---")
                return

        logger.debug("Getting current file path and stats...")
        current_file_path = self.mod_manager.get_current_zip_file_path()
        file_name = self.mod_manager.get_current_zip_file_name()
        file_stats = self.mod_manager.get_current_file_stats()
        logger.debug(f"File path: {current_file_path}")

        if not current_file_path or not file_name:
            logger.error("Failed to get current file path or name even though index seems valid.")
            self.clear_ui()
            self.statusBar().showMessage("Error loading mod data.")
            if self.mod_manager:
                logger.debug("Refreshing mod manager list due to inconsistent state.")
                self.mod_manager.refresh_zip_list()
            logger.debug("--- Exiting load_current_mod (failed get path/name) ---")
            return

        logger.debug("Checking if mod is sorted...")
        is_sorted = check_sorted_marker(current_file_path)
        logger.debug(f"Is sorted: {is_sorted}, Skip sorted setting: {self.skip_sorted}")

        if is_sorted and self.skip_sorted:
            logger.info(f"Skipping already sorted mod: {file_name}")
            logger.debug("Incrementing index to skip...")
            if self.mod_manager.increment_index():
                logger.debug("Index incremented, reloading...")
                self.load_current_mod()
            else:
                QMessageBox.information(self, "Complete", "All remaining mods were already sorted!")
                logger.info("All remaining files were sorted.")
                self.clear_ui()
                self.counter_label.setText(f"Mod {current_index + 1} of {zip_files_count}")
                self.statusBar().showMessage("All mods processed or skipped!")
            logger.debug("--- Exiting load_current_mod (skipped sorted) ---")
            return

        logger.debug("Getting current mod info via ModManager...")
        self.current_mod_info = self.mod_manager.get_current_mod_info()
        if not self.current_mod_info:
            logger.error(f"Could not load mod info for {file_name} (ModManager returned None).")
            self.clear_ui()
            self.statusBar().showMessage(f"Error: Could not load data for {file_name}.")
            logger.debug("--- Exiting load_current_mod (ModManager returned None info) ---")
            return
        logger.debug(
            f"Mod info obtained: Name='{self.current_mod_info.name}', Type='{self.current_mod_info.type}'")

        # Update UI
        logger.debug("--- Starting UI Update ---")

        file_label_text = f"File: {file_name}"
        if is_sorted:
            file_label_text = f"File: <span style='color: green;'>{file_name} (Sorted)</span>"
        logger.debug(f"Setting file name label: '{file_label_text[:100]}...'")
        self.file_name_label.setText(file_label_text)
        logger.debug("File name label set.")

        if file_stats:
            size_str = format_filesize(file_stats.get('size'))
            mod_str = format_timestamp(file_stats.get('modified'))
            stats_text = f"Size: {size_str} | Modified: {mod_str}"
        else:
            stats_text = "Size: N/A | Modified: N/A"
        logger.debug(f"Setting file stats label: '{stats_text}'")
        self.file_stats_label.setText(stats_text)
        logger.debug("File stats label set.")

        name_text = f"Name: {self.current_mod_info.name}"
        author_text = f"Author: {self.current_mod_info.author}"
        type_text = f"Type: {self.current_mod_info.type.value}"
        logger.debug(f"Setting name label: '{name_text}'")
        self.name_label.setText(name_text)
        logger.debug("Name label set.")
        logger.debug(f"Setting author label: '{author_text}'")
        self.author_label.setText(author_text)
        logger.debug("Author label set.")
        logger.debug(f"Setting type label: '{type_text}'")
        self.type_label.setText(type_text)
        logger.debug("Type label set.")

        desc_content = self.current_mod_info.description
        logger.debug(f"Setting description text (length: {len(desc_content)})...")
        self.desc_text.setText(desc_content)
        logger.debug("Description text set.")

        logger.debug("Formatting additional info...")
        additional_content = self.format_additional_info(self.current_mod_info)
        logger.debug(f"Setting additional info text (length: {len(additional_content)})...")
        self.additional_info_text.setText(additional_content)
        logger.debug("Additional info text set.")

        self.current_image_index = 0
        logger.debug("Calling update_image_display...")
        self.update_image_display()
        logger.debug("Returned from update_image_display.")

        counter_text = f"Mod {current_index + 1} of {zip_files_count}"
        logger.debug(f"Setting counter label: '{counter_text}'")
        self.counter_label.setText(counter_text)
        logger.debug("Counter label set.")

        logger.debug("Setting status bar message: 'Ready'")
        self.statusBar().showMessage("Ready")
        logger.debug("Status bar message set.")

        logger.debug("Updating button enabled states...")
        self.prev_button.setEnabled(current_index > 0)
        # self.skip_button.setEnabled(current_index < zip_files_count - 1)
        # self.keep_button.setEnabled(current_index < zip_files_count - 1)
        logger.debug("Button states updated.")

        logger.debug("--- Finished UI Update ---")
        logger.debug("--- Exiting load_current_mod (normal flow) ---")

    def clear_ui(self):
        """Clears all UI elements related to mod info."""
        logger.debug("Clearing UI fields.")
        self.file_name_label.setText("File: N/A")
        self.file_stats_label.setText("Size: N/A | Modified: N/A")
        self.name_label.setText("Name: N/A")
        self.author_label.setText("Author: N/A")
        self.type_label.setText("Type: N/A")
        self.desc_text.clear()
        self.additional_info_text.clear()
        self.image_label.clear()
        self.image_label.setText("No image")
        self.image_counter_label.setText("0/0")
        self.image_name_label.clear()
        self.current_mod_info = None
        # self.counter_label
        self.search_input.clear()


    def prev_mod_clicked(self):
        handler = PreviousModHandler(self, self.mod_manager)
        handler.handle()

    def skip_mod_clicked(self):
        handler = SkipModHandler(self, self.mod_manager)
        handler.handle()

    def next_mod_clicked(self): # Keep button
        handler = NextModHandler(self, self.mod_manager, self.current_mod_info)
        handler.handle()

    def delete_mod_clicked(self):
        handler = DeleteModHandler(self, self.mod_manager)
        handler.handle()

    def move_mod_clicked(self):
        handler = MoveModHandler(self, self.mod_manager, self.current_mod_info)
        handler.handle()

    def move_mod_to_folder_clicked(self, folder_path):
        handler = MoveModToFolderHandler(self, self.mod_manager, folder_path)
        handler.handle()