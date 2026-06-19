from PySide6.QtWidgets import QMenuBar, QFileDialog
from PySide6.QtGui import QAction, QIcon

from resources import resources_rc
from src.loader.file_loaders import ConfigLoader, OrderLoader

class Menubar(QMenuBar):
    def __init__(self, base_path):
        super().__init__()

        # Lấy đường dẫn gốcs
        self.base_path = base_path

        # Khởi tạo các loader
        self.config_loader = ConfigLoader(config_file=self.base_path / "config_shopee.json")
        self.order_loader = OrderLoader(
            rename_dict=self.config_loader.get_rename_dict(),
            dtype_dict=self.config_loader.get_dtype_dict(),
            db_path=self.base_path / "database.sqlite3"
        )

        # File menu
        file_menu = self.addMenu("Tệp")

        # Action mở tệp đơn hàng
        self.open_file_act = QAction(
            QIcon(":/resource/icons/file.svg"),
            "Mở tệp",
            self
        )
        file_menu.addAction(self.open_file_act)

        # Action mở thư mục chứa đơn hàng
        self.open_folder_act = QAction(
            QIcon(":/resource/icons/folder.svg"),
            "Mở thư mục",
            self
        )
        file_menu.addAction(self.open_folder_act)

        # Kết nối tín hiệu
        self.init_signal()

    def init_signal(self):
        self.open_file_act.triggered.connect(self.get_file)
        self.open_folder_act.triggered.connect(self.get_folder)

    def get_file(self):
        """
        Hàm này lấy đường dẫn của các tệp đơn hàng được chọn
        """
        filters = "Tệp Excel (*.xlsx; *.xls);; Tệp Csv (*.csv);; Tất cả các tệp (*)"
        selected_files, file_type = QFileDialog.getOpenFileNames(
            self,
            caption="Chọn tệp",
            dir=str(self.base_path),
            filter=filters
        )
        self.order_loader.data_processor(selected_files)
        self.order_loader.load_data()

    def get_folder(self):
        """
        Hàm này lấy đường dẫn của thư mục được chọn và trích xuất đường dẫn của các file trong đó
        """
        selected_folder = QFileDialog.getExistingDirectory(
            self,
            caption="Chọn thư mục",
            dir=str(self.base_path)
        )
        # Lấy danh sách file từ dir vừa chọn
        file_list = self.order_loader.dir_to_list(selected_folder)
        self.order_loader.data_processor(file_list)
        self.order_loader.load_data()