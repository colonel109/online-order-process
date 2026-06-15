from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import QSize

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Cửa sổ chính")
        self.setMinimumSize(QSize(900, 600))