# mod_sorter/ui/main_window.py
import sys
import os
import shutil
import json  # Импорт json, так как используется format_additional_info
from typing import List, Optional

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QFileDialog,
                             QMessageBox, QComboBox, QTextEdit, QScrollArea, QTabWidget, QGroupBox, QLineEdit)
from PyQt6.QtGui import QPixmap, QShortcut, QKeySequence
from PyQt6.QtCore import Qt, QSize

from core.mod_info import ModInfo, ModType
from config.app_config import AppConfig  # Import AppConfig
from core.mod_manager import ModManager # Import ModManager
from utils.logger import logger
from ui.event_handlers import NextModHandler, DeleteModHandler, MoveModHandler, MoveModToFolderHandler


class ModSorterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Расширенная сортировка модов")
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
            logger.error(f"Error decoding JSON in {config_path}: {e}.  Using default config.")
            QMessageBox.critical(self, "Ошибка конфигурации", f"Ошибка в файле конфигурации {config_path}: {e}")
            return [] # Return an empty list on error


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

        self.statusBar().showMessage("Готов к работе")

    def _create_toolbar(self):
        self.toolbar_layout = QHBoxLayout()

        # Search
        self.search_group = QGroupBox("Поиск")
        search_layout = QHBoxLayout(self.search_group)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по имени мода...")
        self.search_input.textChanged.connect(self._filter_mods)
        search_layout.addWidget(self.search_input)
        self.toolbar_layout.addWidget(self.search_group, stretch=2)

        # Filter
        self.filter_group = QGroupBox("Фильтры")
        filter_layout = QHBoxLayout(self.filter_group)
        self.mod_type_filter = QComboBox()
        self.mod_type_filter.addItems([t.value for t in ModType])
        self.mod_type_filter.addItem("All")
        self.mod_type_filter.currentTextChanged.connect(self.filter_mods)
        filter_layout.addWidget(QLabel("Тип мода:"))
        filter_layout.addWidget(self.mod_type_filter)
        self.toolbar_layout.addWidget(self.filter_group, stretch=1)

        self.main_layout.addLayout(self.toolbar_layout)

    def _create_file_info_group(self):
        self.file_info_group = QGroupBox("Текущий файл")
        file_info_layout = QVBoxLayout(self.file_info_group)
        self.file_name_label = QLabel()
        self.file_name_label.setStyleSheet("font-weight: bold;")
        file_info_layout.addWidget(self.file_name_label)
        self.main_layout.addWidget(self.file_info_group)

    def _create_tab_widget(self):
        self.tab_widget = QTabWidget()

        # Basic info tab
        self.basic_info_widget = QWidget()
        basic_info_layout = QVBoxLayout(self.basic_info_widget)

        self.info_fields_group = QGroupBox("Основная информация")
        info_fields_layout = QVBoxLayout(self.info_fields_group)
        self.name_label = QLabel()
        self.author_label = QLabel()
        self.type_label = QLabel()
        for label in [self.name_label, self.author_label, self.type_label]:
            label.setStyleSheet("font-weight: bold;")
            info_fields_layout.addWidget(label)
        basic_info_layout.addWidget(self.info_fields_group)

        self.desc_group = QGroupBox("Описание")
        desc_layout = QVBoxLayout(self.desc_group)
        self.desc_text = QTextEdit()
        self.desc_text.setReadOnly(True)
        self.desc_text.setMinimumHeight(100)
        desc_layout.addWidget(self.desc_text)
        basic_info_layout.addWidget(self.desc_group)

        self.tab_widget.addTab(self.basic_info_widget, "Основная информация")

        # Images tab
        self.images_widget = QWidget()
        images_layout = QVBoxLayout(self.images_widget)

        self.nav_group = QGroupBox("Навигация")
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

        self.image_group = QGroupBox("Предпросмотр")
        image_group_layout = QVBoxLayout(self.image_group)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(AppConfig.IMAGE_DISPLAY_WIDTH, AppConfig.IMAGE_DISPLAY_HEIGHT)
        image_group_layout.addWidget(self.image_label)
        images_layout.addWidget(self.image_group)

        self.prev_image_btn.clicked.connect(self.show_prev_image)
        self.next_image_btn.clicked.connect(self.show_next_image)
        self.tab_widget.addTab(self.images_widget, "Изображения")

        # Additional info tab
        self.additional_info_widget = QWidget()
        additional_info_layout = QVBoxLayout(self.additional_info_widget)
        self.additional_info_text = QTextEdit()
        self.additional_info_text.setReadOnly(True)
        additional_info_layout.addWidget(self.additional_info_text)
        self.tab_widget.addTab(self.additional_info_widget, "Дополнительно")

        self.main_layout.addWidget(self.tab_widget)

    def _create_action_buttons(self):
        self.actions_group = QGroupBox("Действия")
        button_layout = QHBoxLayout(self.actions_group)

        self.keep_button = QPushButton("Оставить (Ctrl+K)")
        self.delete_button = QPushButton("Удалить (Ctrl+D)")
        self.move_button = QPushButton("Переместить (Ctrl+M)")

        self.keep_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.delete_button.setStyleSheet("background-color: #f44336; color: white;")
        self.move_button.setStyleSheet("background-color: #2196F3; color: white;")

        for button in [self.keep_button, self.delete_button, self.move_button]:
            button.setMinimumWidth(150)
            button_layout.addWidget(button)

        self.keep_button.clicked.connect(self.next_mod_clicked)
        self.delete_button.clicked.connect(self.delete_mod_clicked)
        self.move_button.clicked.connect(self.move_mod_clicked)

        self.main_layout.addWidget(self.actions_group)

        # Set tab order
        QWidget.setTabOrder(self.search_input, self.mod_type_filter)
        QWidget.setTabOrder(self.mod_type_filter, self.keep_button)
        QWidget.setTabOrder(self.keep_button, self.delete_button)
        QWidget.setTabOrder(self.delete_button, self.move_button)

    def _create_dynamic_buttons(self):
        self.dynamic_buttons_group = QGroupBox("Переместить в...")
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
        self.progress_group = QGroupBox("Прогресс")
        progress_layout = QVBoxLayout(self.progress_group)
        self.counter_label = QLabel()
        self.counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(self.counter_label)
        self.main_layout.addWidget(self.progress_group)

    def _ask_skip_sorted(self):
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Пропускать отсортированные моды?")
        msg_box.setText("Хотите ли вы пропускать моды, которые уже были отсортированы?")
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)

        reply = msg_box.exec()
        self.skip_sorted = (reply == QMessageBox.StandardButton.Yes)
        logger.info(f"User chose to skip sorted mods: {self.skip_sorted}")

    def _setup_shortcuts(self):
        logger.debug("Setting up keyboard shortcuts")
        QShortcut(QKeySequence("Ctrl+K"), self, self.keep_button.click)
        QShortcut(QKeySequence("Ctrl+D"), self, self.delete_button.click)
        QShortcut(QKeySequence("Ctrl+M"), self, self.move_button.click)
        QShortcut(QKeySequence("Left"), self, self.show_prev_image)
        QShortcut(QKeySequence("Right"), self, self.show_next_image)
        logger.info("Keyboard shortcuts setup complete")

    def _handle_error(self, error: Exception, title: str = "Ошибка"):
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

        QMessageBox.information(self, "Поиск", "Моды не найдены!")
        self.mod_manager.reset_index()
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
                QMessageBox.information(self, "Фильтр", "Больше нет модов выбранного типа!")
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
            self, "Выберите папку с архивами модов"
        )

        if not source_folder:
            QMessageBox.critical(self, "Ошибка", "Папка не выбрана")
            logger.warning("No source folder selected.")
            return None

        logger.info(f"Source folder selected: {source_folder}")
        return source_folder

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

         is_sorted = self.mod_manager._check_sorted_marker(current_file_path)
         if is_sorted and self.skip_sorted:
            logger.info(f"Skipping sorted mod: {file_name}")
            self.mod_manager.increment_index()
            self.load_current_mod()
            return

         # Get mod info from ModManager
         self.current_mod_info = self.mod_manager.get_current_mod_info()
         if not self.current_mod_info:
            logger.warning(f"Could not load mod info for {file_name}")
            self.current_mod_info = ModInfo(name="Ошибка", author="Неизвестно", type=ModType.OTHER, description="Не удалось загрузить информацию о моде", preview_images=[], additional_info={})

         # Update UI elements with mod info
         if is_sorted:
            self.file_name_label.setText(f"Файл: <span style='color: green;'>{file_name} (Отсортирован)</span>")
         else:
            self.file_name_label.setText(f"Файл: {file_name}")

         self.name_label.setText(f"Имя: {self.current_mod_info.name}")
         self.author_label.setText(f"Автор: {self.current_mod_info.author}")
         self.type_label.setText(f"Тип: {self.current_mod_info.type.value}")
         self.desc_text.setText(self.current_mod_info.description)
         self.additional_info_text.setText(self.format_additional_info(self.current_mod_info))

         self.current_image_index = 0
         self.update_image_display()

         # Update counter
         current_index = self.mod_manager.get_current_index()
         zip_files_count = self.mod_manager.get_zip_files_count()
         self.counter_label.setText(f"Мод {current_index + 1} из {zip_files_count}")

    def next_mod_clicked(self):
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