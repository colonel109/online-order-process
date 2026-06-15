import sys
from PySide6.QtWidgets import QApplication

from src.ui.windows.main_window import MainWindow

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()