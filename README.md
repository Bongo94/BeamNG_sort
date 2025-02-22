## BeamNG Mod Sorter

This application helps you sort your BeamNG.drive mods more efficiently. It analyzes `.zip` files, extracts key information, displays previews, and allows you to categorize mods into different folders.

**Key Features:**

*   **Automated Mod Analysis:**  Identifies the type of mod (vehicle, map, or other) by analyzing the contents of `.zip` files, extracting information from `info.json` files within.
*   **Preview Display:** Shows images and previews from inside the mod archives, helping you quickly identify the mod.
*   **Categorization:**  Allows you to easily move mods into type-specific folders (Vehicles, Maps, etc.).
*   **Sorting Markers:**  Marks sorted mods with a `.mod_sorted` file *inside* the zip archive, making it easy to skip already-processed files.
*   **Search & Filter:**  Quickly find specific mods by name or filter by mod type.
*   **Keyboard Shortcuts:** Navigate and perform actions quickly using keyboard shortcuts.
*   **Logging:** Comprehensive logging to a file, helping with debugging and troubleshooting.

**Installation:**

1.  **Download:** Download the latest executable (`.exe`) from the [Releases](https://github.com/Bongo94/BeamNG_sort/releases) page.
2.  **Run:** Execute the downloaded `.exe` file.

**Usage:**

1.  **Select Mod Folder:** The application will prompt you to select the folder containing your BeamNG.drive mod `.zip` files.
2.  **Review Mod Information:** The application will display the mod's name, author, type, description, and previews.
3.  **Categorize or Delete:** Use the buttons at the bottom to:
    *   **Keep:**  Marks the mod as sorted and proceeds to the next mod.
    *   **Delete:** Deletes the mod `.zip` file.
    *   **Move:** Moves the mod to a folder corresponding to its type (Vehicle, Map, Other). You will be prompted to choose a destination folder.
4.  **Navigation:** Use the arrow keys or the navigation buttons to view different images if available.
5.  **Search and Filter:** Use the search bar to filter mods by name. Use the filter dropdown to filter by mod type.

**Keyboard Shortcuts:**

*   **Ctrl+K:** Keep (mark as sorted and go to next mod)
*   **Ctrl+D:** Delete
*   **Ctrl+M:** Move
*   **Left Arrow:** Previous Image
*   **Right Arrow:** Next Image

**Configuration:**

*   **Skip Sorted Mods:** At startup, you will be asked if you want to skip already sorted mods. This option can also be configured via the command line (Not Yet Implemented).

**Building from Source:**

If you prefer to build the application from source:

1.  **Clone the Repository:**

    ```bash
    git clone https://github.com/Bongo94/BeamNG_sort.git
    cd YOUR_REPO_NAME
    ```

2.  **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

    (You will need a `requirements.txt` file listing dependencies like PyQt6)

3.  **Run the Application:**

    ```bash
    python main.py
    ```

**Dependencies:**

*   [PyQt6](https://www.riverbankcomputing.com/software/pyqt/intro)
*   [dataclasses](https://docs.python.org/3/library/dataclasses.html) (Standard in Python 3.7+)
*   [typing](https://docs.python.org/3/library/typing.html) (Standard in Python 3.5+)
*   [zipfile](https://docs.python.org/3/library/zipfile.html) (Standard Python Library)
*   [json](https://docs.python.org/3/library/json.html) (Standard Python Library)
*   [os](https://docs.python.org/3/library/os.html) (Standard Python Library)
*   [shutil](https://docs.python.org/3/library/shutil.html) (Standard Python Library)
*   [logging](https://docs.python.org/3/library/logging.html) (Standard Python Library)

**Planned Features:**

*   **Custom Destination Folders:** Allow users to configure the destination folders for each mod type.
*   **More Robust Error Handling:** Improve error reporting and handling for corrupted or malformed mod archives.
*   **Command-Line Arguments:** Support command-line arguments for configuration options, such as skipping sorted mods.
*   **UI Improvements:** Enhancements to the user interface for better usability and visual appeal.
*   **Multi-language Support:** Allow users to select their language preferences.
*   **Online Database Integration:** Potentially integrate with an online mod database to fetch more detailed mod information.

**Contributing:**

Contributions are welcome! If you find a bug, have a feature request, or want to contribute code, please open an issue or submit a pull request on GitHub.

**License:**

This project is licensed under the [MIT License](LICENSE).

**Important Considerations:**

*   **Backup:** Always back up your mods folder before using this or any mod management tool.
*   **Invalid Mods:** This tool is designed to help sort valid mods.  It may not be able to handle all types of corrupted or unusual mod archives.
*   **.mod_sorted files:** Do NOT manually edit or delete these files!  The tool relies on their presence and contents for proper operation.

```
PyQt6
```


--- RU ---
## BeamNG Mod Sorter

Это приложение поможет вам более эффективно сортировать ваши моды для BeamNG.drive. Оно анализирует `.zip` файлы, извлекает ключевую информацию, показывает превью и позволяет вам классифицировать моды по различным папкам.

**Основные возможности:**

*   **Автоматический анализ модов:** Определяет тип мода (транспортное средство, карта или другое) путем анализа содержимого `.zip` файлов, извлекая информацию из `info.json` файлов внутри.
*   **Отображение превью:** Показывает изображения и превью изнутри архивов модов, помогая вам быстро идентифицировать мод.
*   **Категоризация:** Позволяет вам легко перемещать моды в папки, соответствующие их типу (Vehicles, Maps и т.д.).
*   **Маркеры сортировки:** Отмечает отсортированные моды файлом `.mod_sorted` *внутри* zip-архива, что позволяет легко пропускать уже обработанные файлы.
*   **Поиск и фильтрация:** Быстрый поиск определенных модов по имени или фильтрация по типу мода.
*   **Горячие клавиши:** Навигация и выполнение действий с помощью горячих клавиш.
*   **Логирование:** Подробное ведение журнала в файл, помогающее при отладке и устранении неполадок.

**Установка:**

1.  **Скачать:** Скачайте последнюю версию исполняемого файла (`.exe`) со страницы [Releases](https://github.com/Bongo94/BeamNG_sort/releases).
2.  **Запустить:** Запустите скачанный `.exe` файл.

**Использование:**

1.  **Выберите папку с модами:** Приложение предложит вам выбрать папку, содержащую ваши `.zip` файлы с модами BeamNG.drive.
2.  **Просмотрите информацию о моде:** Приложение отобразит имя мода, автора, тип, описание и превью.
3.  **Категоризируйте или удалите:** Используйте кнопки внизу, чтобы:
    *   **Оставить:** Отмечает мод как отсортированный и переходит к следующему моду.
    *   **Удалить:** Удаляет `.zip` файл мода.
    *   **Переместить:** Перемещает мод в папку, соответствующую его типу (Vehicle, Map, Other). Вам будет предложено выбрать целевую папку.
4.  **Навигация:** Используйте клавиши со стрелками или кнопки навигации для просмотра разных изображений, если они доступны.
5.  **Поиск и фильтрация:** Используйте строку поиска для фильтрации модов по имени. Используйте выпадающий список фильтров для фильтрации по типу мода.

**Горячие клавиши:**

*   **Ctrl+K:** Оставить (отметить как отсортированный и перейти к следующему моду)
*   **Ctrl+D:** Удалить
*   **Ctrl+M:** Переместить
*   **Стрелка влево:** Предыдущее изображение
*   **Стрелка вправо:** Следующее изображение

**Настройка:**

*   **Пропускать отсортированные моды:** При запуске вам будет предложено указать, хотите ли вы пропускать уже отсортированные моды. Эту опцию также можно настроить с помощью аргументов командной строки (пока не реализовано).

**Сборка из исходного кода:**

Если вы предпочитаете собрать приложение из исходного кода:

1.  **Клонируйте репозиторий:**

    ```bash
    git clone https://github.com/Bongo94/BeamNG_sort.git
    cd YOUR_REPO_NAME
    ```

2.  **Установите зависимости:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Запустите приложение:**

    ```bash
    python main.py
    ```

**Зависимости:**

*   [PyQt6](https://www.riverbankcomputing.com/software/pyqt/intro)
*   [dataclasses](https://docs.python.org/3/library/dataclasses.html) (Стандартный модуль в Python 3.7+)
*   [typing](https://docs.python.org/3/library/typing.html) (Стандартный модуль в Python 3.5+)
*   [zipfile](https://docs.python.org/3/library/zipfile.html) (Стандартная библиотека Python)
*   [json](https://docs.python.org/3/library/json.html) (Стандартная библиотека Python)
*   [os](https://docs.python.org/3/library/os.html) (Стандартная библиотека Python)
*   [shutil](https://docs.python.org/3/library/shutil.html) (Стандартная библиотека Python)
*   [logging](https://docs.python.org/3/library/logging.html) (Стандартная библиотека Python)

**Планируемые функции:**

*   **Пользовательские папки назначения:** Разрешить пользователям настраивать папки назначения для каждого типа мода.
*   **Более надежная обработка ошибок:** Улучшить отчетность об ошибках и обработку поврежденных или неправильно сформированных архивов модов.
*   **Аргументы командной строки:** Поддержка аргументов командной строки для параметров конфигурации, таких как пропуск отсортированных модов.
*   **Улучшения пользовательского интерфейса:** Улучшения пользовательского интерфейса для повышения удобства использования и визуальной привлекательности.
*   **Многоязычная поддержка:** Позволить пользователям выбирать языковые предпочтения.
*   **Интеграция онлайн-базы данных:** Возможна интеграция с онлайн-базой данных модов для получения более подробной информации о моде.

**Вклад:**

Приветствуются соучастники проекта! Если вы обнаружите ошибку, у вас есть запрос на добавление функции или вы хотите внести код, откройте проблему или отправьте запрос на включение на GitHub.

**Лицензия:**

Этот проект лицензирован в соответствии с [MIT License](LICENSE).

**Важные соображения:**

*   **Резервное копирование:** Всегда делайте резервную копию папки с модами перед использованием этого или любого другого инструмента управления модами.
*   **Недействительные моды:** Этот инструмент предназначен для помощи в сортировке действительных модов. Он может не справиться со всеми типами поврежденных или необычных архивов модов.
*   **Файлы .mod_sorted:** НЕ редактируйте и НЕ удаляйте эти файлы вручную! Инструмент полагается на их присутствие и содержимое для правильной работы.
