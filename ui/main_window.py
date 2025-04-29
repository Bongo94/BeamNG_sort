# mod_sorter/ui/main_window.py
import json
import math
import sys
from datetime import datetime
from typing import Optional

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QShortcut, QKeySequence
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QFileDialog,
                             QMessageBox, QComboBox, QTextEdit, QTabWidget, QGroupBox, QLineEdit)

from config.app_config import AppConfig
from core.mod_info import ModInfo, ModType
from core.mod_manager import ModManager, check_sorted_marker
from ui.event_handlers import PreviousModHandler, SkipModHandler, NextModHandler, DeleteModHandler, MoveModHandler, \
    MoveModToFolderHandler
# from ui.event_handlers import NextModHandler, DeleteModHandler, MoveModHandler, MoveModToFolderHandler
from utils.logger import logger


# --- Хелперы форматирования (можно вынести в utils, если хочется) ---
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
        # Формат можно настроить: '%Y-%m-%d %H:%M:%S' или '%d %b %Y, %H:%M' и т.д.
        return dt_object.strftime('%Y-%m-%d %H:%M')
    except Exception:
        logger.warning(f"Could not format timestamp: {timestamp}")
        return "Invalid Date"
# --- Конец хелперов ---


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
        self.source_folder = self.select_source_folder()

        if self.source_folder:
            self.mod_manager = ModManager(self.source_folder)
            self.load_current_mod()
        else:
            logger.info("No source folder selected, exiting.")
            sys.exit()

    def _load_move_folders_config(self):
        """Load the move folders configuration from a JSON file."""
        config_path = AppConfig.MOVE_FOLDERS_CONFIG
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"Loaded move folders config from: {config_path}")
            return config
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}. Using default config.")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON in {config_path}: {e}. Using default config.")
            QMessageBox.critical(self, "Configuration Error", f"Error in configuration file {config_path}: {e}")
            return []

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

        # --- НОВОЕ: Лейбл для статистики ---
        self.file_stats_label = QLabel("Size: N/A | Modified: N/A")
        self.file_stats_label.setStyleSheet("font-size: 9pt; color: gray;")

        file_info_layout.addWidget(self.file_name_label)
        file_info_layout.addWidget(self.file_stats_label) # Добавляем в layout
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

        # --- НОВЫЕ КНОПКИ ---
        self.prev_button = QPushButton("← Previous (Ctrl+B)")
        self.skip_button = QPushButton("Skip (Ctrl+S)")
        # ---

        self.keep_button = QPushButton("Keep && Next (Ctrl+K)")  # Чуть изменил текст для ясности
        self.delete_button = QPushButton("Delete (Ctrl+D)")
        self.move_button = QPushButton("Move (Ctrl+M)")

        # Стили (можно настроить)
        self.prev_button.setStyleSheet("background-color: #cccccc;")  # Серый
        self.skip_button.setStyleSheet("background-color: #ffc107;")  # Желтый/оранжевый
        self.keep_button.setStyleSheet("background-color: #4CAF50; color: white;")  # Зеленый
        self.delete_button.setStyleSheet("background-color: #f44336; color: white;")  # Красный
        self.move_button.setStyleSheet("background-color: #2196F3; color: white;")  # Синий

        # Добавляем кнопки в layout
        button_layout.addWidget(self.prev_button)
        button_layout.addWidget(self.skip_button)
        button_layout.addWidget(self.keep_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.move_button)

        for button in [self.prev_button, self.skip_button, self.keep_button, self.delete_button, self.move_button]:
            button.setMinimumWidth(120)  # Немного уменьшил мин. ширину
            # button_layout.addWidget(button) # Уже добавили выше

        # Подключаем сигналы к новым слотам
        self.prev_button.clicked.connect(self.prev_mod_clicked)
        self.skip_button.clicked.connect(self.skip_mod_clicked)
        # ---
        self.keep_button.clicked.connect(self.next_mod_clicked)
        self.delete_button.clicked.connect(self.delete_mod_clicked)
        self.move_button.clicked.connect(self.move_mod_clicked)

        self.main_layout.addWidget(self.actions_group)

        # Обновляем Tab order
        QWidget.setTabOrder(self.search_input, self.mod_type_filter)
        QWidget.setTabOrder(self.mod_type_filter, self.prev_button)
        QWidget.setTabOrder(self.prev_button, self.skip_button)
        QWidget.setTabOrder(self.skip_button, self.keep_button)
        QWidget.setTabOrder(self.keep_button, self.delete_button)
        QWidget.setTabOrder(self.delete_button, self.move_button)
        # Добавить сюда кнопки из dynamic_buttons_layout, если они есть и нужны в порядке обхода

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
        # --- НОВЫЕ ШОРТКАТЫ ---
        QShortcut(QKeySequence("Ctrl+B"), self, self.prev_button.click)  # Back
        QShortcut(QKeySequence("Ctrl+S"), self, self.skip_button.click)  # Skip
        # ---
        QShortcut(QKeySequence("Ctrl+K"), self, self.keep_button.click)  # Keep
        QShortcut(QKeySequence("Ctrl+D"), self, self.delete_button.click)  # Delete
        QShortcut(QKeySequence("Ctrl+M"), self, self.move_button.click)  # Move
        QShortcut(QKeySequence(Qt.Key.Key_Left), self, self.show_prev_image)  # Используем Qt.Key
        QShortcut(QKeySequence(Qt.Key.Key_Right), self, self.show_next_image)  # Используем Qt.Key
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
                roads = []  # Treat as empty list if not a list

            suitable_for = info.get('suitable_for', [])
            if not isinstance(suitable_for, list):
                suitable_for = []  # Treat as empty list if not a list

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

        # Analise current file path
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
        logger.debug("--- Entering load_current_mod ---")  # <<< ADDED
        if not self.mod_manager:
            logger.warning("ModManager not initialized, cannot load mod.")
            self.clear_ui()
            self.statusBar().showMessage("Error: Mod manager not ready.")
            logger.debug("--- Exiting load_current_mod (no mod_manager) ---")  # <<< ADDED
            return

        zip_files_count = self.mod_manager.get_zip_files_count()
        current_index = self.mod_manager.get_current_index()
        logger.debug(f"Zip count: {zip_files_count}, Current index: {current_index}")  # <<< ADDED

        # Проверка, есть ли вообще файлы
        if zip_files_count == 0:
            logger.info("No zip files found in the source folder.")
            self.clear_ui()
            self.counter_label.setText("Mod 0 of 0")
            self.statusBar().showMessage("No mods found in the selected folder.")
            # Деактивируем кнопки действий
            # ... (button disabling code) ...
            logger.debug("--- Exiting load_current_mod (no zip files) ---")  # <<< ADDED
            return
        else:
            # Активируем кнопки, если были деактивированы
            # ... (button enabling code) ...
            pass  # Pass added for structure

        # Индекс может быть равен zip_files_count ...
        if current_index >= zip_files_count:
            if zip_files_count > 0:
                logger.warning(
                    f"Current index {current_index} is out of bounds (0-{zip_files_count - 1}). Resetting to last.")
                self.mod_manager.set_current_index(zip_files_count - 1)
                current_index = self.mod_manager.get_current_index()
                logger.debug(f"Index reset to {current_index}")  # <<< ADDED
            else:
                QMessageBox.information(self, "Complete", "All mods have been processed!")
                logger.info("All files processed.")
                self.clear_ui()
                self.counter_label.setText(f"Mod {current_index} of {zip_files_count}")
                self.statusBar().showMessage("All mods processed!")
                logger.debug("--- Exiting load_current_mod (all processed) ---")  # <<< ADDED
                return

        logger.debug("Getting current file path and stats...")  # <<< ADDED
        current_file_path = self.mod_manager.get_current_zip_file_path()
        file_name = self.mod_manager.get_current_zip_file_name()
        file_stats = self.mod_manager.get_current_file_stats()
        logger.debug(f"File path: {current_file_path}")  # <<< ADDED

        if not current_file_path or not file_name:
            logger.error("Failed to get current file path or name even though index seems valid.")
            self.clear_ui()
            self.statusBar().showMessage("Error loading mod data.")
            if self.mod_manager:
                logger.debug("Refreshing mod manager list due to inconsistent state.")  # <<< ADDED
                self.mod_manager.refresh_zip_list()
            logger.debug("--- Exiting load_current_mod (failed get path/name) ---")  # <<< ADDED
            return

        logger.debug("Checking if mod is sorted...")  # <<< ADDED
        is_sorted = check_sorted_marker(current_file_path)
        logger.debug(f"Is sorted: {is_sorted}, Skip sorted setting: {self.skip_sorted}")  # <<< ADDED

        if is_sorted and self.skip_sorted:
            logger.info(f"Skipping already sorted mod: {file_name}")
            logger.debug("Incrementing index to skip...")  # <<< ADDED
            if self.mod_manager.increment_index():
                logger.debug("Index incremented, reloading...")  # <<< ADDED
                self.load_current_mod()
            else:
                QMessageBox.information(self, "Complete", "All remaining mods were already sorted!")
                logger.info("All remaining files were sorted.")
                self.clear_ui()
                self.counter_label.setText(f"Mod {current_index + 1} of {zip_files_count}")
                self.statusBar().showMessage("All mods processed or skipped!")
            logger.debug("--- Exiting load_current_mod (skipped sorted) ---")  # <<< ADDED
            return

        logger.debug("Getting current mod info via ModManager...")  # <<< ADDED
        self.current_mod_info = self.mod_manager.get_current_mod_info()
        if not self.current_mod_info:
            logger.error(f"Could not load mod info for {file_name} (ModManager returned None).")
            self.clear_ui()
            self.statusBar().showMessage(f"Error: Could not load data for {file_name}.")
            logger.debug("--- Exiting load_current_mod (ModManager returned None info) ---")  # <<< ADDED
            return
        logger.debug(
            f"Mod info obtained: Name='{self.current_mod_info.name}', Type='{self.current_mod_info.type}'")  # <<< ADDED

        # Обновляем UI
        logger.debug("--- Starting UI Update ---")  # <<< ADDED

        file_label_text = f"File: {file_name}"
        if is_sorted:
            file_label_text = f"File: <span style='color: green;'>{file_name} (Sorted)</span>"
        logger.debug(f"Setting file name label: '{file_label_text[:100]}...'")  # Log truncated name
        self.file_name_label.setText(file_label_text)
        logger.debug("File name label set.")  # <<< ADDED

        if file_stats:
            size_str = format_filesize(file_stats.get('size'))
            mod_str = format_timestamp(file_stats.get('modified'))
            stats_text = f"Size: {size_str} | Modified: {mod_str}"
        else:
            stats_text = "Size: N/A | Modified: N/A"
        logger.debug(f"Setting file stats label: '{stats_text}'")  # <<< ADDED
        self.file_stats_label.setText(stats_text)
        logger.debug("File stats label set.")  # <<< ADDED

        name_text = f"Name: {self.current_mod_info.name}"
        author_text = f"Author: {self.current_mod_info.author}"
        type_text = f"Type: {self.current_mod_info.type.value}"
        logger.debug(f"Setting name label: '{name_text}'")  # <<< ADDED
        self.name_label.setText(name_text)
        logger.debug("Name label set.")  # <<< ADDED
        logger.debug(f"Setting author label: '{author_text}'")  # <<< ADDED
        self.author_label.setText(author_text)
        logger.debug("Author label set.")  # <<< ADDED
        logger.debug(f"Setting type label: '{type_text}'")  # <<< ADDED
        self.type_label.setText(type_text)
        logger.debug("Type label set.")  # <<< ADDED

        desc_content = self.current_mod_info.description
        logger.debug(f"Setting description text (length: {len(desc_content)})...")  # <<< ADDED
        self.desc_text.setText(desc_content)
        logger.debug("Description text set.")  # <<< ADDED

        logger.debug("Formatting additional info...")  # <<< ADDED
        additional_content = self.format_additional_info(self.current_mod_info)
        logger.debug(f"Setting additional info text (length: {len(additional_content)})...")  # <<< ADDED
        self.additional_info_text.setText(additional_content)
        logger.debug("Additional info text set.")  # <<< ADDED

        self.current_image_index = 0
        logger.debug("Calling update_image_display...")  # <<< ADDED
        self.update_image_display()
        logger.debug("Returned from update_image_display.")  # <<< ADDED

        counter_text = f"Mod {current_index + 1} of {zip_files_count}"
        logger.debug(f"Setting counter label: '{counter_text}'")  # <<< ADDED
        self.counter_label.setText(counter_text)
        logger.debug("Counter label set.")  # <<< ADDED

        logger.debug("Setting status bar message: 'Ready'")  # <<< ADDED
        self.statusBar().showMessage("Ready")
        logger.debug("Status bar message set.")  # <<< ADDED

        logger.debug("Updating button enabled states...")  # <<< ADDED
        self.prev_button.setEnabled(current_index > 0)
        # self.skip_button.setEnabled(current_index < zip_files_count - 1) # Keep enabled
        # self.keep_button.setEnabled(current_index < zip_files_count - 1) # Keep enabled
        logger.debug("Button states updated.")  # <<< ADDED

        logger.debug("--- Finished UI Update ---")  # <<< ADDED
        logger.debug("--- Exiting load_current_mod (normal flow) ---")  # <<< ADDED

    def update_image_display(self):
        logger.debug("--- Entering update_image_display ---")  # <<< ADDED
        if not self.current_mod_info or not self.current_mod_info.preview_images:
            logger.debug("No mod info or preview images found.")  # <<< ADDED
            self.image_label.setText("No images found")
            self.image_counter_label.setText("0/0")
            self.image_name_label.setText("")
            logger.debug("Cleared image display fields.")  # <<< ADDED
            logger.debug("--- Exiting update_image_display (no images) ---")  # <<< ADDED
            return

        try:
            logger.debug(f"Attempting to display image index: {self.current_image_index}")  # <<< ADDED
            image_name, image_data = self.current_mod_info.preview_images[self.current_image_index]
            logger.debug(f"Got image: Name='{image_name}', Size={len(image_data)} bytes")  # <<< ADDED

            logger.debug("Creating QPixmap...")  # <<< ADDED
            pixmap = QPixmap()
            logger.debug("QPixmap created.")  # <<< ADDED

            logger.debug(f"Calling pixmap.loadFromData for '{image_name}'...")  # <<< ADDED
            load_success = pixmap.loadFromData(image_data)
            logger.debug(f"pixmap.loadFromData returned: {load_success}")  # <<< ADDED

            if not load_success:
                # Raise error specifically if loading failed
                raise RuntimeError(f"QPixmap.loadFromData failed for image: {image_name}")

            logger.debug("Scaling pixmap...")  # <<< ADDED
            scaled_pixmap = pixmap.scaled(
                AppConfig.IMAGE_DISPLAY_WIDTH,
                AppConfig.IMAGE_DISPLAY_HEIGHT,
                Qt.AspectRatioMode.KeepAspectRatio
            )
            logger.debug("Pixmap scaled.")  # <<< ADDED

            logger.debug("Setting pixmap on label...")  # <<< ADDED
            self.image_label.setPixmap(scaled_pixmap)
            logger.debug("Pixmap set on label.")  # <<< ADDED

            counter_text = f"{self.current_image_index + 1}/{len(self.current_mod_info.preview_images)}"
            name_text = f"File: {image_name}"
            logger.debug(f"Setting image counter label: '{counter_text}'")  # <<< ADDED
            self.image_counter_label.setText(counter_text)
            logger.debug("Image counter label set.")  # <<< ADDED
            logger.debug(f"Setting image name label: '{name_text}'")  # <<< ADDED
            self.image_name_label.setText(name_text)
            logger.debug("Image name label set.")  # <<< ADDED
            logger.debug(f"Successfully displayed image: {image_name}")

        except IndexError:
            logger.error(
                f"Image index {self.current_image_index} out of range for list size {len(self.current_mod_info.preview_images)}",
                exc_info=True)  # Log traceback
            self.image_label.setText("Error: Image index out of bounds")
            self.image_counter_label.setText("Error")
            self.image_name_label.setText("")
        except Exception as e:
            # Log the error *before* calling handle_error, in case handle_error itself fails
            logger.error(f"Exception during image display: {e}", exc_info=True)  # <<< ADDED - Log traceback
            self.handle_error(e, f"Image display error for index {self.current_image_index}")
            # Clear potentially problematic display elements
            self.image_label.setText(f"Error loading image:\n{e}")
            self.image_counter_label.setText("Error")
            self.image_name_label.setText(f"Error: {image_name}" if 'image_name' in locals() else "Error")

        logger.debug("--- Exiting update_image_display ---")  # <<< ADDED

    def clear_ui(self):
        """Clears all UI elements related to mod info."""
        logger.debug("Clearing UI fields.")
        self.file_name_label.setText("File: N/A")
        self.file_stats_label.setText("Size: N/A | Modified: N/A")  # Очищаем статистику
        self.name_label.setText("Name: N/A")
        self.author_label.setText("Author: N/A")
        self.type_label.setText("Type: N/A")
        self.desc_text.clear()
        self.additional_info_text.clear()
        self.image_label.clear()
        self.image_label.setText("No image")  # Пояснение
        self.image_counter_label.setText("0/0")
        self.image_name_label.clear()
        self.current_mod_info = None  # Сбрасываем текущую информацию
        # self.counter_label - не очищаем, его обновит load_current_mod
        self.search_input.clear()  # Очищаем поиск при полном сбросе

    # --- НОВЫЕ Слоты для кнопок ---
    def prev_mod_clicked(self):
        handler = PreviousModHandler(self, self.mod_manager)
        handler.handle()

    def skip_mod_clicked(self):
        handler = SkipModHandler(self, self.mod_manager)
        handler.handle()
    # ---

    def next_mod_clicked(self): # Keep button
        handler = NextModHandler(self, self.mod_manager, self.current_mod_info)
        handler.handle()

    def delete_mod_clicked(self):
        handler = DeleteModHandler(self, self.mod_manager)
        handler.handle()

    def move_mod_clicked(self):
        # Передаем current_mod_info, т.к. MoveModHandler его использует (хотя мог бы и сам получить)
        handler = MoveModHandler(self, self.mod_manager, self.current_mod_info)
        handler.handle()

    def move_mod_to_folder_clicked(self, folder_path):
        # MoveModToFolderHandler не использует current_mod_info напрямую
        handler = MoveModToFolderHandler(self, self.mod_manager, folder_path)
        handler.handle()