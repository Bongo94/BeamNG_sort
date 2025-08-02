![BNGSorter_icon.ico](resources/BNGSorter_icon.ico)
## BeamNG Mod Sorter

This application helps you sort your BeamNG.drive mods more efficiently. It analyzes `.zip` files, extracts key information, displays previews, and allows you to categorize and manage your mods.

**Key Features:**

*   **Automated Mod Analysis:** Identifies the type of mod (vehicle, map, or other) by analyzing the contents of `.zip` files and their internal `info.json` files.
*   **Automatic Folder Detection:** On first launch, it automatically finds your BeamNG.drive `mods` folder, simplifying setup.
*   **Image Previews:** Shows preview images from inside the mod archives, helping you quickly identify each mod.
*   **Easy Categorization:** Allows you to move mods into predefined folders with a single click.
*   **Sorting Markers:** Marks processed mods with a `.mod_sorted` file *inside* the zip archive, making it easy to skip already-sorted files in future sessions.
*   **Search & Filter:** Quickly find specific mods by name or filter the list by mod type.
*   **Comprehensive Logging:** Keeps a detailed log file for troubleshooting and debugging.
*   **Keyboard Shortcuts:** Navigate and perform all major actions quickly using keyboard shortcuts for maximum efficiency.

**Installation:**

1.  **Download:** Download the latest executable (`.exe`) from the [Releases](https://github.com/Bongo94/BeamNG_sort/releases) page.
2.  **Run:** Execute the downloaded `.exe` file. No installation is required.

**Usage:**

1.  **Select Mod Folder:** The application will try to find your mods folder automatically. If it succeeds, confirm the path. Otherwise, you will be prompted to select the folder containing your BeamNG.drive mod `.zip` files.
2.  **Review Mod Information:** The application displays the mod's name, author, type, description, and any available previews.
3.  **Take Action:** Use the buttons at the bottom to manage the current mod:
    *   **Previous:** Go back to the previous mod.
    *   **Skip:** Go to the next mod without taking any action.
    *   **Keep & Next:** Marks the mod as sorted and proceeds to the next one.
    *   **Delete:** Permanently deletes the mod `.zip` file (with confirmation).
    *   **Move:** Opens a dialog to choose a custom destination folder.
    *   **Move to...:** Use the one-click buttons to move the mod to a predefined folder (configurable in `config/move_folders.json`).
4.  **Navigate Images:** Use the Left and Right arrow keys to cycle through available preview images.

**Keyboard Shortcuts:**

*   **Ctrl+B:** Previous Mod
*   **Ctrl+S:** Skip Mod
*   **Ctrl+K:** Keep & Next (mark as sorted)
*   **Ctrl+D:** Delete Mod
*   **Ctrl+M:** Move Mod (to a custom folder)
*   **Left Arrow:** Previous Image
*   **Right Arrow:** Next Image

**Configuration:**

*   **Skip Sorted Mods:** At startup, you will be asked if you want to skip mods that have been marked as sorted.
*   **Custom Move Folders:** You can customize the "Move to..." buttons by editing the `config/move_folders.json` file before building the application from source.

**Building from Source:**

If you prefer to build the application from source:

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/Bongo94/BeamNG_sort.git
    cd BeamNG_sort
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Application:**
    ```bash
    python main.py
    ```

**Dependencies:**

*   [PyQt6](https://www.riverbankcomputing.com/software/pyqt/intro)
*   [colorlog](https://pypi.org/project/colorlog/) (for colored console logging)
*   [packaging](https://pypi.org/project/packaging/) (for version comparison)

**Planned Features:**

*   **Runtime Folder Configuration:** Allow users to configure the destination folders for each mod type directly within the app.
*   **Command-Line Arguments:** Support for CLI arguments, e.g., to force skipping sorted mods.
*   **UI/UX Improvements:** General enhancements to the user interface.
*   **Multi-language Support:** Add localization for different languages.

**Contributing:**

Contributions are welcome! If you find a bug, have a feature request, or want to contribute code, please open an issue or submit a pull request on GitHub.

**License:**

This project is licensed under the [MIT License](LICENSE).

**Important Considerations:**

*   **Backup:** **Always back up your mods folder before using this or any other mod management tool.**
*   **Invalid Mods:** This tool is designed to help sort valid mods. While it attempts to handle malformed archives, it may not succeed with all types of corrupted files.
*   **`.mod_sorted` files:** Do NOT manually edit or delete these files from inside the archives. The tool relies on them for its sorting logic.

---
--- RU ---
## BeamNG Mod Sorter

Это приложение поможет вам более эффективно сортировать ваши моды для BeamNG.drive. Оно анализирует `.zip` файлы, извлекает ключевую информацию, показывает превью и позволяет вам классифицировать и управлять вашими модами.

**Основные возможности:**

*   **Автоматический анализ модов:** Определяет тип мода (транспортное средство, карта или другое) путем анализа содержимого `.zip` файлов и их внутренних файлов `info.json`.
*   **Автоматическое определение папки:** При первом запуске приложение автоматически находит вашу папку `mods` для BeamNG.drive, упрощая настройку.
*   **Просмотр изображений:** Показывает изображения-превью изнутри архивов модов, помогая вам быстро идентифицировать каждый мод.
*   **Простая категоризация:** Позволяет перемещать моды в предопределенные папки одним щелчком мыши.
*   **Маркеры сортировки:** Отмечает обработанные моды файлом `.mod_sorted` *внутри* zip-архива, что позволяет легко пропускать уже отсортированные файлы в будущих сессиях.
*   **Поиск и фильтрация:** Быстрый поиск определенных модов по имени или фильтрация списка по типу мода.
*   **Подробное логирование:** Ведет детальный лог-файл для отладки и устранения неполадок.
*   **Горячие клавиши:** Навигация и выполнение всех основных действий с помощью горячих клавиш для максимальной эффективности.

**Установка:**

1.  **Скачать:** Скачайте последнюю версию исполняемого файла (`.exe`) со страницы [Releases](https://github.com/Bongo94/BeamNG_sort/releases).
2.  **Запустить:** Запустите скачанный `.exe` файл. Установка не требуется.

**Использование:**

1.  **Выберите папку с модами:** Приложение попытается найти вашу папку с модами автоматически. Если это удастся, подтвердите путь. В противном случае вам будет предложено выбрать папку с вашими `.zip` файлами модов для BeamNG.drive.
2.  **Просмотрите информацию о моде:** Приложение отобразит имя мода, автора, тип, описание и все доступные превью.
3.  **Выполните действие:** Используйте кнопки внизу для управления текущим модом:
    *   **Previous:** Вернуться к предыдущему моду.
    *   **Skip:** Перейти к следующему моду, не выполняя никаких действий.
    *   **Keep & Next:** Отмечает мод как отсортированный и переходит к следующему.
    *   **Delete:** Безвозвратно удаляет `.zip` файл мода (с подтверждением).
    *   **Move:** Открывает диалог для выбора произвольной папки назначения.
    *   **Move to...:** Используйте кнопки быстрого доступа для перемещения мода в предопределенную папку (настраивается в `config/move_folders.json`).
4.  **Навигация по изображениям:** Используйте клавиши со стрелками Влево и Вправо для переключения между доступными изображениями-превью.

**Горячие клавиши:**

*   **Ctrl+B:** Предыдущий мод
*   **Ctrl+S:** Пропустить мод
*   **Ctrl+K:** Оставить и к следующему (отметить как отсортированный)
*   **Ctrl+D:** Удалить мод
*   **Ctrl+M:** Переместить мод (в произвольную папку)
*   **Стрелка влево:** Предыдущее изображение
*   **Стрелка вправо:** Следующее изображение

**Настройка:**

*   **Пропускать отсортированные моды:** При запуске вам будет предложено, хотите ли вы пропускать моды, которые уже были отмечены как отсортированные.
*   **Пользовательские папки для перемещения:** Вы можете настроить кнопки "Move to...", отредактировав файл `config/move_folders.json` перед сборкой приложения из исходного кода.

**Сборка из исходного кода:**

1.  **Клонируйте репозиторий:**
    ```bash
    git clone https://github.com/Bongo94/BeamNG_sort.git
    cd BeamNG_sort
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
*   [colorlog](https://pypi.org/project/colorlog/) (для цветного вывода в консоль)
*   [packaging](https://pypi.org/project/packaging/) (для сравнения версий)

**Планируемые функции:**

*   **Настройка папок в рантайме:** Позволить пользователям настраивать папки назначения непосредственно в приложении.
*   **Аргументы командной строки:** Поддержка аргументов командной строки, например, для принудительного пропуска отсортированных модов.
*   **Улучшения UI/UX:** Общие улучшения пользовательского интерфейса.
*   **Многоязычная поддержка:** Добавление локализации для разных языков.

**Вклад:**

Приветствуется вклад в проект! Если вы обнаружите ошибку, у вас есть запрос на добавление функции или вы хотите внести код, пожалуйста, откройте `issue` или отправьте `pull request` на GitHub.

**Лицензия:**

Этот проект лицензирован в соответствии с [MIT License](LICENSE).

**Важные соображения:**

*   **Резервное копирование:** **Всегда делайте резервную копию вашей папки с модами перед использованием этого или любого другого инструмента управления модами.**
*   **Недействительные моды:** Этот инструмент предназначен для помощи в сортировке действительных модов. Хотя он пытается обрабатывать некорректно сформированные архивы, он может не справиться со всеми типами поврежденных файлов.
*   **Файлы `.mod_sorted`:** НЕ редактируйте и НЕ удаляйте эти файлы вручную из архивов. Инструмент полагается на них для своей логики сортировки.