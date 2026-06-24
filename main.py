import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QGuiApplication, Qt

from src.ui.windows.main_window import MainWindow
from src.database.connector import db_connector

# Tạm thời sử dụng db ở base path
BASE_PATH = Path(__file__).parent
DATABASE_PATH = Path(BASE_PATH / "database.sqlite3")
CONFIG_PATH = Path(BASE_PATH / "config_shopee.json")

# Thiết lập kết nối với database
session = db_connector(DATABASE_PATH)

app = QApplication(sys.argv)
QGuiApplication.styleHints().setColorScheme(Qt.ColorScheme.Dark)
window = MainWindow(session=session, base_path=BASE_PATH, config_path=CONFIG_PATH, database_path=DATABASE_PATH)
window.show()
app.exec()