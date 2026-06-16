from PySide6.QtWidgets import QMainWindow, QWidget, QTableView, QFileDialog
from PySide6.QtCore import QSize
from PySide6.QtGui import QAction

from src.loader.file_loaders import ConfigLoader, OrderLoader

class MainWindow(QMainWindow):
    def __init__(self, session, base_path):
        super().__init__()

        # Kết nối với database
        self.session = session

        # Đường dẫn gốc
        self.base_path = base_path

        # Khởi tạo các loader
        self.config = ConfigLoader(config_file=base_path / "config_shopee.json")
        self.order = OrderLoader(
            rename_dict=self.config.get_rename_dict(),
            dtype_dict=self.config.get_dtype_dict(),
            db_path=base_path / "database.sqlite3"
        )

        # Kích cỡ cửa sổ
        self.setWindowTitle("Cửa sổ chính")
        self.setMinimumSize(QSize(900, 600))

        # View model
        self.table_view = QTableView()

        # Thanh menu bar
        menu = self.menuBar()

        # Menu tệp
        file_menu = menu.addMenu("Tệp")

        # Action mở tệp đơn hàng
        self.open_file_act = QAction(
            "Mở tệp",
            self
        )
        file_menu.addAction(self.open_file_act)

        # Action mở thư mục chứa đơn hàng
        self.open_folder_act = QAction(
            "Mở thư mục",
            self
        )
        file_menu.addAction(self.open_folder_act)

        # Container chính
        container = QWidget()
        self.setCentralWidget(container)

        # Kết nối slot với signal
        self.init_signal()

    def init_signal(self):
        """
        Hàm này có nhiệm vụ kết nối slot với signal
        """
        self.open_file_act.triggered.connect(self.get_order_file)
        self.open_folder_act.triggered.connect(self.get_folder)

    def get_order_file(self):
        filters = "Tệp Excel (*.xlsx; *.xls);; Tệp Csv (*.csv);; Tất cả các tệp (*)"
        selected_files, file_type = QFileDialog.getOpenFileNames(
            self,
            caption="Chọn tệp",
            dir=str(self.base_path),
            filter=filters
        )
        self.order.data_processor(selected_files)
        self.order.load_data()

    def get_folder(self):
        selected_folder = QFileDialog.getExistingDirectory(
            self,
            caption="Chọn thư mục",
            dir=str(self.base_path)
        )
        # Lấy danh sách file từ dir vừa chọn
        file_list = self.order.dir_to_list(selected_folder)
        self.order.data_processor(file_list)
        self.order.load_data()