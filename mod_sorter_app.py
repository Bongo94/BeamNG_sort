# mod_sorter_app.py
import tempfile
import zipfile
from dataclasses import dataclass
from typing import List, Optional

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QFileDialog,
                             QMessageBox, QComboBox, QTextEdit, QScrollArea, QTabWidget, QGroupBox, QLineEdit)
from PyQt6.QtGui import QPixmap, QShortcut, QKeySequence
from PyQt6.QtCore import Qt, QSize
import sys
import os
import shutil
import json  # Импорт json, так как используется format_additional_info
from mod_info import ModInfo, ModType  # Импорт из mod_info.py
from mod_analyzer import ModAnalyzer  # Импорт из mod_analyzer.py
from utils.logger import logger  # Import the logger


@dataclass
class AppConfig:
    """Configuration constants for the application"""
    WINDOW_MIN_WIDTH = 1000
    WINDOW_MIN_HEIGHT = 800
    IMAGE_DISPLAY_WIDTH = 600
    IMAGE_DISPLAY_HEIGHT = 400
    MARKER_EXTENSION = ".mod_sorted"


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

    def get_current_mod(self) -> Optional[ModInfo]:
        if self.current_index >= len(self.zip_files):
            logger.debug("Current index out of range, no more mods.")
            return None
        current_file = os.path.join(self.source_folder, self.zip_files[self.current_index])
        logger.debug(f"Analyzing zip file: {current_file}")
        try:
            return ModAnalyzer.analyze_zip(current_file)
        except Exception as e:
            logger.exception(f"Error analyzing zip file: {current_file}")
            return None

    def mark_as_sorted(self, file_path: str, mod_info: ModInfo) -> None:
        """Marks a mod as sorted by adding a .mod_sorted file *inside* the ZIP."""
        logger.debug(f"Marking as sorted: {file_path}")
        try:
            if self._check_sorted_marker(file_path):  # Add this check
                logger.info(f"{file_path} is already marked as sorted.")
                return  # Exit if already sorted

            with zipfile.ZipFile(file_path, 'a') as zf:
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
            logger.info(f"Successfully marked {file_path} as sorted.")
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

    def _delete_sorted_marker(self, zip_file_path: str) -> None:
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

    def get_mod_info_from_marker(self, zip_file_path: str) -> Optional[dict]:
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

    def remove_current_zip_file(self) -> Optional[str]:  # Remove from ModManager's list
        if self.current_index < len(self.zip_files):
            removed_file = self.zip_files.pop(self.current_index)
            logger.info(f"Removed zip file from list: {removed_file}")
            return removed_file
        logger.debug("No zip file to remove, current index out of range.")
        return None

    def get_current_zip_file_name(self) -> Optional[str]:
        if self.current_index < len(self.zip_files):
            return self.zip_files[self.current_index]
        return None

    def get_current_zip_file_path(self) -> Optional[str]:
        if self.current_index < len(self.zip_files):
            return os.path.join(self.source_folder, self.zip_files[self.current_index])
        return None

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


class ModSorterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Расширенная сортировка модов")
        self.setMinimumSize(QSize(AppConfig.WINDOW_MIN_WIDTH, AppConfig.WINDOW_MIN_HEIGHT))

        self.mod_manager = None  # Initialize mod_manager to None initially
        self.current_mod_info = None
        self.current_image_index = 0

        self.skip_sorted = False  # Default: do NOT skip sorted mods
        self._ask_skip_sorted()  # Ask the user at startup

        self._setup_ui()
        self._setup_shortcuts()
        self.source_folder = self.select_source_folder()  # Get source folder first
        if self.source_folder:  # Only initialize ModManager and load if folder is selected
            self.mod_manager = ModManager(self.source_folder)
            self.load_current_mod()
        else:
            logger.info("No source folder selected, exiting.")
            sys.exit()  # Exit if no folder selected

    def _setup_ui(self):
        """Initialize all UI components with proper layouts and configurations"""
        logger.debug("Setting up UI")

        # Main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Top toolbar with search and filter
        toolbar_layout = QHBoxLayout()

        # Search bar
        search_group = QGroupBox("Поиск")
        search_layout = QHBoxLayout(search_group)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по имени мода...")
        self.search_input.textChanged.connect(self._filter_mods)
        search_layout.addWidget(self.search_input)

        # Filter dropdown
        filter_group = QGroupBox("Фильтры")
        filter_layout = QHBoxLayout(filter_group)
        self.mod_type_filter = QComboBox()
        self.mod_type_filter.addItems([t.value for t in ModType])
        self.mod_type_filter.addItem("All")
        self.mod_type_filter.currentTextChanged.connect(self.filter_mods)
        filter_layout.addWidget(QLabel("Тип мода:"))
        filter_layout.addWidget(self.mod_type_filter)

        toolbar_layout.addWidget(search_group, stretch=2)
        toolbar_layout.addWidget(filter_group, stretch=1)
        main_layout.addLayout(toolbar_layout)

        # Current file info
        file_info_group = QGroupBox("Текущий файл")
        file_info_layout = QVBoxLayout(file_info_group)
        self.file_name_label = QLabel()
        self.file_name_label.setStyleSheet("font-weight: bold;")
        file_info_layout.addWidget(self.file_name_label)
        main_layout.addWidget(file_info_group)

        # Create tab widget
        self.tab_widget = QTabWidget()

        # Basic info tab
        basic_info_widget = QWidget()
        basic_info_layout = QVBoxLayout(basic_info_widget)

        # Info fields
        info_fields_group = QGroupBox("Основная информация")
        info_fields_layout = QVBoxLayout(info_fields_group)

        self.name_label = QLabel()
        self.author_label = QLabel()
        self.type_label = QLabel()
        for label in [self.name_label, self.author_label, self.type_label]:
            label.setStyleSheet("font-weight: bold;")
            info_fields_layout.addWidget(label)

        # Description
        desc_group = QGroupBox("Описание")
        desc_layout = QVBoxLayout(desc_group)
        self.desc_text = QTextEdit()
        self.desc_text.setReadOnly(True)
        self.desc_text.setMinimumHeight(100)
        desc_layout.addWidget(self.desc_text)

        basic_info_layout.addWidget(info_fields_group)
        basic_info_layout.addWidget(desc_group)
        self.tab_widget.addTab(basic_info_widget, "Основная информация")

        # Images tab
        images_widget = QWidget()
        images_layout = QVBoxLayout(images_widget)

        # Image navigation
        nav_group = QGroupBox("Навигация")
        image_nav_layout = QHBoxLayout(nav_group)

        self.prev_image_btn = QPushButton("←")
        self.next_image_btn = QPushButton("→")
        self.image_counter_label = QLabel()
        self.image_name_label = QLabel()

        image_nav_layout.addWidget(self.prev_image_btn)
        image_nav_layout.addWidget(self.image_counter_label)
        image_nav_layout.addWidget(self.next_image_btn)

        images_layout.addWidget(nav_group)
        images_layout.addWidget(self.image_name_label)

        # Image display
        image_group = QGroupBox("Предпросмотр")
        image_group_layout = QVBoxLayout(image_group)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(AppConfig.IMAGE_DISPLAY_WIDTH, AppConfig.IMAGE_DISPLAY_HEIGHT)
        image_group_layout.addWidget(self.image_label)

        images_layout.addWidget(image_group)

        # Connect image navigation buttons
        self.prev_image_btn.clicked.connect(self.show_prev_image)
        self.next_image_btn.clicked.connect(self.show_next_image)

        self.tab_widget.addTab(images_widget, "Изображения")

        # Additional info tab
        additional_info_widget = QWidget()
        additional_info_layout = QVBoxLayout(additional_info_widget)

        self.additional_info_text = QTextEdit()
        self.additional_info_text.setReadOnly(True)
        additional_info_layout.addWidget(self.additional_info_text)

        self.tab_widget.addTab(additional_info_widget, "Дополнительно")

        main_layout.addWidget(self.tab_widget)

        # Action buttons
        actions_group = QGroupBox("Действия")
        button_layout = QHBoxLayout(actions_group)

        # Create buttons with icons and shortcuts
        self.keep_button = QPushButton("Оставить (Ctrl+K)")
        self.delete_button = QPushButton("Удалить (Ctrl+D)")
        self.move_button = QPushButton("Переместить (Ctrl+M)")

        # Style buttons
        self.keep_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.delete_button.setStyleSheet("background-color: #f44336; color: white;")
        self.move_button.setStyleSheet("background-color: #2196F3; color: white;")

        # Add buttons to layout
        for button in [self.keep_button, self.delete_button, self.move_button]:
            button.setMinimumWidth(150)
            button_layout.addWidget(button)

        # Connect button signals
        self.keep_button.clicked.connect(self.next_mod)
        self.delete_button.clicked.connect(self.delete_mod)
        self.move_button.clicked.connect(self.move_mod)

        main_layout.addWidget(actions_group)

        # Progress bar
        progress_group = QGroupBox("Прогресс")
        progress_layout = QVBoxLayout(progress_group)

        self.counter_label = QLabel()
        self.counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(self.counter_label)

        main_layout.addWidget(progress_group)

        # Status bar
        self.statusBar().showMessage("Готов к работе")

        # Set tab order
        QWidget.setTabOrder(self.search_input, self.mod_type_filter)
        QWidget.setTabOrder(self.mod_type_filter, self.keep_button)
        QWidget.setTabOrder(self.keep_button, self.delete_button)
        QWidget.setTabOrder(self.delete_button, self.move_button)

        logger.info("UI setup complete")

    def _ask_skip_sorted(self):
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Пропускать отсортированные моды?")
        msg_box.setText("Хотите ли вы пропускать моды, которые уже были отсортированы?")
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)  # Default is NO

        reply = msg_box.exec()
        self.skip_sorted = (reply == QMessageBox.StandardButton.Yes)
        logger.info(f"User chose to skip sorted mods: {self.skip_sorted}")

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        logger.debug("Setting up keyboard shortcuts")
        QShortcut(QKeySequence("Ctrl+K"), self, self.keep_button.click)
        QShortcut(QKeySequence("Ctrl+D"), self, self.delete_button.click)
        QShortcut(QKeySequence("Ctrl+M"), self, self.move_button.click)
        QShortcut(QKeySequence("Left"), self, self.show_prev_image)
        QShortcut(QKeySequence("Right"), self, self.show_next_image)
        logger.info("Keyboard shortcuts setup complete")

    def _handle_error(self, error: Exception, title: str = "Ошибка"):
        """Centralized error handling"""
        logger.error(f"Error: {title} - {error}")  # Log error
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
        """Updated image display with proper resource management"""
        if not self.current_mod_info or not self.current_mod_info.preview_images:
            self.image_label.setText("Изображения не найдены")
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
            self.image_name_label.setText(f"Файл: {image_name}")
            logger.debug(f"Displayed image: {image_name}")

        except Exception as e:
            self._handle_error(e, "Ошибка отображения изображения")

    def _filter_mods(self):
        """Filter mods by name"""
        search_text = self.search_input.text().lower()
        logger.debug(f"Filtering mods by name: {search_text}")
        if not search_text:
            self.load_current_mod()
            return

        if not self.mod_manager:  # Check if mod_manager is initialized
            logger.warning("ModManager not initialized, cannot filter.")
            return

        current_index = self.mod_manager.get_current_index()
        zip_files = self.mod_manager.get_zip_files()

        while current_index < len(zip_files):
            if search_text in zip_files[current_index].lower():
                self.mod_manager.set_current_index(current_index)  # Update index in ModManager
                logger.debug(f"Found matching mod, setting index to: {current_index}")
                self.load_current_mod()
                return
            current_index += 1
            self.mod_manager.increment_index()  # Increment index for next iteration

        QMessageBox.information(self, "Поиск", "Моды не найдены!")
        self.mod_manager.reset_index()  # Reset index in ModManager
        logger.info("No mods found matching search criteria, resetting index.")
        self.load_current_mod()

    def format_additional_info(self, mod_info: ModInfo) -> str:
        logger.debug(f"Formatting additional info for mod type: {mod_info.type}")
        if mod_info.type == ModType.VEHICLE:
            configs = mod_info.additional_info.get('configurations', [])
            paints = mod_info.additional_info.get('paints', {})

            info_parts = [
                "Конфигурации:",
                ", ".join(configs) or "Нет",
                "\nДоступные окраски:",
                ", ".join(paints.keys()) if paints else "Нет"
            ]

            if 'raw_info' in mod_info.additional_info:
                raw = mod_info.additional_info['raw_info']
                if 'Tuning' in raw:
                    info_parts.extend([
                        "\nДоступный тюнинг:",
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
                f"Точки спавна: {len(info.get('spawn_points', []))}\n"
                f"Дороги: {', '.join(roads)}\n"
                f"Подходит для: {', '.join(suitable_for)}\n"
                f"\nПолная информация:\n"
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

        if not self.mod_manager:  # Check if mod_manager is initialized
            logger.warning("ModManager not initialized, cannot filter.")
            return

        current_index = self.mod_manager.get_current_index()
        zip_files = self.mod_manager.get_zip_files()

        current_file_path = self.mod_manager.get_current_zip_file_path()
        if not current_file_path:  # Handle case when no zip file path (e.g., no files)
            logger.warning("No current zip file path, cannot filter.")
            return

        try:
            current_mod = ModAnalyzer.analyze_zip(current_file_path)
        except Exception as e:
            self._handle_error(e, "Ошибка при анализе мода")
            return

        while current_mod.type.value != selected_type:
            current_index += 1
            self.mod_manager.increment_index()  # Increment index in ModManager
            if current_index >= len(zip_files):
                QMessageBox.information(self, "Фильтр", "Больше нет модов выбранного типа!")
                self.mod_manager.reset_index()  # Reset index in ModManager
                logger.info("No more mods of selected type, resetting index.")
                break

            current_file_path = self.mod_manager.get_current_zip_file_path()
            if not current_file_path:  # Handle case when no zip file path (e.g., end of files)
                logger.warning("No current zip file path, cannot filter.")
                return
            try:
                current_mod = ModAnalyzer.analyze_zip(current_file_path)
            except Exception as e:
                self._handle_error(e, "Ошибка при анализе мода")
                return

        self.load_current_mod()

    def select_source_folder(self):
        logger.debug("Selecting source folder")
        source_folder = QFileDialog.getExistingDirectory(
            self, "Выберите папку с архивами модов"
        )

        if not source_folder:
            QMessageBox.critical(self, "Ошибка", "Папка не выбрана")
            logger.warning("No source folder selected.")
            return None  # Return None if no folder selected

        logger.info(f"Source folder selected: {source_folder}")
        return source_folder  # Return the selected folder path

    def load_current_mod(self):
        if not self.mod_manager:
            logger.warning("ModManager not initialized, cannot load mod.")
            return

        if self.mod_manager.get_current_index() >= self.mod_manager.get_zip_files_count():
            QMessageBox.information(self, "Завершено", "Все файлы просмотрены!")
            logger.info("All files processed, exiting.")
            sys.exit()

        current_file_path = self.mod_manager.get_current_zip_file_path()
        file_name = self.mod_manager.get_current_zip_file_name()

        if not current_file_path or not file_name:
            logger.warning("No current file path or name, cannot load mod.")
            return

        try:
            is_sorted = self.mod_manager._check_sorted_marker(current_file_path)  # Store result
            if is_sorted and self.skip_sorted:
                logger.info(f"Skipping sorted mod: {file_name}")
                self.mod_manager.increment_index()
                self.load_current_mod()
                return  # Skip to next mod

            if is_sorted:
                self.file_name_label.setText(
                    f"Файл: <span style='color: green;'>{file_name} (Отсортирован)</span>")
                # Try to load mod info from the marker
                marker_data = self.mod_manager.get_mod_info_from_marker(current_file_path)
                if marker_data:
                    # If marker data is found, use it (but still analyze to get fresh data)
                    self.current_mod_info = ModInfo(
                        name=marker_data.get('name', 'Unknown'),
                        author=marker_data.get('author', 'Unknown'),
                        type=ModType(marker_data.get('type', 'OTHER')),
                        description=marker_data.get('description', ''),
                        preview_images=[],
                        additional_info=marker_data.get('additional_info', {})
                    )
                    logger.debug(f"Loaded mod info from marker: {self.current_mod_info.name}")
            else:
                self.file_name_label.setText(f"Файл: {file_name}")
                logger.debug(f"Mod not sorted: {file_name}")
                # Always analyze to get the *latest* data (in case the ZIP changed externally)
                self.current_mod_info = ModAnalyzer.analyze_zip(current_file_path)
                logger.debug(f"Analyzed mod: {self.current_mod_info.name}")
            # Always analyze to get the *latest* data (in case the ZIP changed externally)
            if not self.mod_manager._check_sorted_marker(current_file_path):
                self.current_mod_info = ModAnalyzer.analyze_zip(current_file_path)

        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка при анализе мода {current_file_path}: {e}.\n"
                                                f"Возможно, файл info.json поврежден.")
            self.current_mod_info = ModInfo(
                name="Error",
                author="Error",
                type=ModType.OTHER,
                description=str(e),
                preview_images=[],
                additional_info={}
            )
            logger.warning(f"Error analyzing mod {current_file_path}: {e}")

        # Update UI
        self.name_label.setText(f"Имя: {self.current_mod_info.name}")
        self.author_label.setText(f"Автор: {self.current_mod_info.author}")
        self.type_label.setText(f"Тип: {self.current_mod_info.type.value}")
        self.desc_text.setText(self.current_mod_info.description)

        # Reset image index and update display
        self.current_image_index = 0
        self.update_image_display()

        # Update additional info
        self.additional_info_text.setText(self.format_additional_info(self.current_mod_info))

        # Update counter
        current_index = self.mod_manager.get_current_index()
        zip_files_count = self.mod_manager.get_zip_files_count()
        self.counter_label.setText(f"Мод {current_index + 1} из {zip_files_count}")

    def next_mod(self):
        if not self.mod_manager:
            logger.warning("ModManager not initialized, cannot proceed to next mod.")
            return

        current_file_path = self.mod_manager.get_current_zip_file_path()
        if current_file_path:
            self.mod_manager.mark_as_sorted(current_file_path, self.current_mod_info)  # Pass mod_info
            logger.info(f"Marked as sorted and moving to next mod: {current_file_path}")
        self.mod_manager.increment_index()
        self.load_current_mod()

    def delete_mod(self):
        if not self.mod_manager:
            logger.warning("ModManager not initialized, cannot delete mod.")
            return

        current_file_path = self.mod_manager.get_current_zip_file_path()
        if not current_file_path:
            logger.warning("No current file path, cannot delete mod.")
            return

        try:
            try:
                os.remove(current_file_path)
                QMessageBox.information(self, "Успех", f"Файл {current_file_path} удален")
                self.mod_manager.remove_current_zip_file()  # Remove from ModManager's list
                logger.info(f"Deleted mod: {current_file_path}")
                self.load_current_mod()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении файла: {e}")
                logger.exception(f"Error deleting mod: {current_file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении файла: {e}")
            logger.exception(f"Error deleting mod: {current_file_path}")

    def move_mod(self):
        if not self.mod_manager:  # Check if mod_manager is initialized
            logger.warning("ModManager not initialized, cannot move mod.")
            return

        dest_folder = QFileDialog.getExistingDirectory(
            self, "Выберите папку для перемещения"
        )

        if not dest_folder:
            logger.info("Move mod operation cancelled by user.")
            return

        current_file_path = self.mod_manager.get_current_zip_file_path()
        if not current_file_path:
            logger.warning("No current file path, cannot move mod.")
            return

        try:
            type_folder = os.path.join(dest_folder, self.current_mod_info.type.value)
            os.makedirs(type_folder, exist_ok=True)
            new_file_path = os.path.join(type_folder, os.path.basename(current_file_path))
            shutil.move(current_file_path, type_folder)
            QMessageBox.information(self, "Успех", f"Файл перемещен в {type_folder}")
            self.mod_manager.mark_as_sorted(new_file_path, self.current_mod_info)  # Pass mod_info
            self.mod_manager.remove_current_zip_file()  # Remove from ModManager's list
            logger.info(f"Moved mod to {type_folder}: {current_file_path}")
            self.load_current_mod()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при перемещении файла: {e}")
            logger.exception(f"Error moving mod: {current_file_path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = ModSorterApp()
    ex.show()
    sys.exit(app.exec())