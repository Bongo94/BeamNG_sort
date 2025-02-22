# main.py
import sys
from PyQt6.QtWidgets import QApplication
from mod_sorter_app import ModSorterApp # Импорт из mod_sorter_app.py


def main():
    app = QApplication(sys.argv)
    window = ModSorterApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()