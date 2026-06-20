from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import QSize, Qt


class DataProcessWindow(QMainWindow):
    """
    Cửa sổ này chỉ hiển thị khi người dùng chọn xử lí dữ liệu, người dùng sẽ không thể tương tác với main_window
    khi nó được kích hoạt
    """
    def __init__(self, session):
        super().__init__()

        # Kết nối tới database
        self.session = session

        # Tuỳ chỉnh cửa sổ
        self.setWindowTitle("Xử lí dữ liệu đơn hàng")
        self.setMinimumSize(QSize(1000, 700))

        self.setWindowModality(Qt.WindowModality.ApplicationModal)