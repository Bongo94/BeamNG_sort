import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import ModSorterApp

def main():
    app = QApplication(sys.argv)
    window = ModSorterApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()