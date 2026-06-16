from PySide6.QtWidgets import QMainWindow, QWidget, QTableView, QFileDialog, QVBoxLayout, QToolBar
from PySide6.QtCore import QSize
from PySide6.QtGui import QAction, QIcon

from sqlalchemy import select, delete

from src.loader.file_loaders import ConfigLoader, OrderLoader
from src.database.structure import ShopeeOrder
from src.data_model.table_view_model import TableViewModel
from resources import resources_rc


class MainWindow(QMainWindow):
    def __init__(self, session, base_path):
        super().__init__()

        # Kết nối với database
        self.session = session
        self.order_data_model = None

        # Data model và view model
        self.model = None
        self.table_view = QTableView()

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

        # Toolbar
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(17, 17))
        self.addToolBar(toolbar)

        self.fetch_order_act = QAction(
            QIcon(":/resource/icons/list-view.svg"),
            "&Lấy dữ liệu",
            self
        )
        toolbar.addAction(self.fetch_order_act)

        self.delete_order_act = QAction(
            QIcon(":/resource/icons/list-x.svg"),
            "&Lấy dữ liệu",
            self
        )
        toolbar.addAction(self.delete_order_act)

        # Thanh menu bar
        menu = self.menuBar()

        # Menu tệp
        file_menu = menu.addMenu("Tệp")

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

        # Container chính
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.table_view)
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Kết nối slot với signal
        self.init_signal()

    def init_signal(self):
        """
        Hàm này có nhiệm vụ kết nối slot với signal
        """
        self.open_file_act.triggered.connect(self.get_order_file)
        self.open_folder_act.triggered.connect(self.get_folder)
        self.fetch_order_act.triggered.connect(self.fetch_order_data)
        self.delete_order_act.triggered.connect(self.delete_order_data)

    def fetch_order_data(self):
        data = self.session.scalars(select(ShopeeOrder)).all()
        columns = ["order_id", "package_id", "order_date", "order_status", "combo_name", "variant_name",
                    "deal_price", "quantity","total_buyer_payment_amount", "source_file"]
        self.model = TableViewModel(
            data=data,
            column_names=columns
        )
        self.table_view.setModel(self.model)

    def delete_order_data(self):
        statement = delete(ShopeeOrder)
        self.session.execute(statement)
        self.session.commit()

    def get_order_file(self):
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
        self.order.data_processor(selected_files)
        self.order.load_data()
        self.fetch_order_data()

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
        file_list = self.order.dir_to_list(selected_folder)
        self.order.data_processor(file_list)
        self.order.load_data()
        self.fetch_order_data()