from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import QSize
from sqlalchemy import select

from src.database.structure import Product

class MainWindow(QMainWindow):
    def __init__(self, session):
        super().__init__()

        self.session = session

        self.setWindowTitle("Cửa sổ chính")
        self.setMinimumSize(QSize(900, 600))