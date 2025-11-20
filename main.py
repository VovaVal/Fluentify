from PyQt6.QtWidgets import QApplication
import sys
from src.words_window import WordsWindow


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = WordsWindow()
    window.show()
    sys.exit(app.exec())