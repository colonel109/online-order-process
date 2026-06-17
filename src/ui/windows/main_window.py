from PySide6.QtWidgets import QMainWindow, QWidget, QTableView, QFileDialog, QVBoxLayout, QToolBar, QStackedLayout
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
        self.table_view = QTableView() # Tạo view model

        # Đường dẫn gốc
        self.base_path = base_path

        # Khởi tạo các loader
        self.config_loader = ConfigLoader(config_file=base_path / "config_shopee.json")
        self.order_loader = OrderLoader(
            rename_dict=self.config_loader.get_rename_dict(),
            dtype_dict=self.config_loader.get_dtype_dict(),
            db_path=base_path / "database.sqlite3"
        )

        # Kích cỡ cửa sổ
        self.setWindowTitle("Cửa sổ chính")
        self.setMinimumSize(QSize(900, 600))

        # Thanh công cụ
        self.fetch_order_act = QAction(
            QIcon(":/resource/icons/list-view.svg"),
            "Lấy dữ liệu",
            self
        )

        self.delete_order_act = QAction(
            QIcon(":/resource/icons/list-x.svg"),
            "Xoá dữ liệu",
            self
        )
        self.delete_order_act.setEnabled(False)

        self.begin_process_data_act = QAction(
            QIcon(":/resource/icons/square-chevron-right.svg"),
            "Bắt đầu xử lí dữ liệu",
            self
        )
        
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(17, 17))

        toolbar.addAction(self.fetch_order_act)
        toolbar.addAction(self.delete_order_act)
        toolbar.addSeparator()
        toolbar.addAction(self.begin_process_data_act)

        self.addToolBar(toolbar)

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
        """
        Hàm này có nhiệm vụ lấy thông tin từ bảng shopee_orders sau đó lấy các list chứa những combo, variant và price độc nhất để truyền vào view model
        """

        # Lấy data set chứa toàn bộ thông tin cần thiết từ bảng shopee_orders
        data_orders = self.session.scalars(select(ShopeeOrder)).all()
        
        if not data_orders:
            return
        
        # Truyền vào view model, đây là bảng đơn hàng gốc
        columns = ["order_id", "package_id", "order_date", "order_status", "combo_name", "variant_name",
                    "deal_price", "quantity","total_buyer_payment_amount", "source_file"]
        self.order_data_model = TableViewModel(
            data=data_orders,
            column_names=columns
        )

        # Tạo một instance mới chứa thông tin về các combo, variant, price độc nhất
        data_cvp_set = set() # Tạo một set hứng các giá trị từ data_orders 
        for object in data_orders:
            data_cvp_set.add((object.combo_name, object.variant_name, object.deal_price))

        data_cvp_list = list(data_cvp_set)     
        
        self.combo_variant_model = TableViewModel(
            data=data_cvp_list,
            column_names=["combo_name", "variant_name", "deal_price"] 
        )

        # Set model cho view chính
        self.table_view.setModel(self.order_data_model)
        self.delete_order_act.setEnabled(True)

    def delete_order_data(self):
        statement = delete(ShopeeOrder)
        self.session.execute(statement)
        self.session.commit()

        data = self.session.scalars(select(ShopeeOrder)).all()
        self.order_data_model.refresh_data(data)
        self.delete_order_act.setEnabled(False)

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
        self.order_loader.data_processor(selected_files)
        self.order_loader.load_data()
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
        file_list = self.order_loader.dir_to_list(selected_folder)
        self.order_loader.data_processor(file_list)
        self.order_loader.load_data()
        self.fetch_order_data()