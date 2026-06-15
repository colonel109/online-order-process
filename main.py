import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication

from src.ui.windows.main_window import MainWindow
from src.database.connector import db_connector

# Tạm thời sử dụng db ở base path
BASE_PATH = Path(__file__).parent
DATABASE_PATH = Path(BASE_PATH / "database.sqlite3")

# Thiết lập kết nối với database
session = db_connector(DATABASE_PATH)

app = QApplication(sys.argv)
window = MainWindow(session=session)
window.show()
app.exec()