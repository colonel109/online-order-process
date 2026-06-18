from PySide6.QtWidgets import QMainWindow, QWidget, QTableView, QFileDialog, QVBoxLayout, QToolBar, QStackedLayout
from PySide6.QtCore import QSize
from PySide6.QtGui import QAction, QIcon

from sqlalchemy import select, delete

from src.loader.file_loaders import ConfigLoader, OrderLoader
from src.database.structure import ShopeeOrder
from src.data_model.table_view_model import TableViewModel
from resources import resources_rc
from src.ui.widgets.order_display import OrderDisplayer
from src.ui.widgets.import_mask import ImportMask


class MainWindow(QMainWindow):
    def __init__(self, session, base_path):
        super().__init__()

        # Kết nối với database
        self.session = session

        # Các layout của main windows
        self.order_display_widget = OrderDisplayer(session=self.session)
        self.import_mask = ImportMask()

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
        self.delete_order_act = QAction(
            QIcon(":/resource/icons/list-x.svg"),
            "Xoá dữ liệu",
            self
        )

        self.begin_process_data_act = QAction(
            QIcon(":/resource/icons/square-chevron-right.svg"),
            "Bắt đầu xử lí dữ liệu",
            self
        )
        
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(17, 17))

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
        self.main_layout = QStackedLayout()
        self.main_layout.addWidget(self.import_mask)
        self.main_layout.addWidget(self.order_display_widget)
        container = QWidget()
        container.setLayout(self.main_layout)
        self.setCentralWidget(container)

        # Chạy hàm 
        self.init_signal()
        self.change_btn_state()
        self.order_display_widget.fetch_order_data()


    def change_btn_state(self):
        stmt = select(ShopeeOrder).exists()
        result = self.session.scalar(select(stmt))

        buttons = [self.delete_order_act, self.begin_process_data_act]

        for btn in buttons:
            if not result:
                btn.setEnabled(False)           
                self.main_layout.setCurrentIndex(0)

            else:
                self.main_layout.setCurrentIndex(1)
                btn.setEnabled(True)

    def init_signal(self):
        """
        Hàm này có nhiệm vụ kết nối slot với signal
        """
        self.import_mask.import_file_btn.clicked.connect(self.get_order_file)
        self.import_mask.import_folder_btn.clicked.connect(self.get_folder)
        self.open_file_act.triggered.connect(self.get_order_file)
        self.open_folder_act.triggered.connect(self.get_folder)
        self.delete_order_act.triggered.connect(self.delete_order_data)

        self.delete_order_act.triggered.connect(self.change_btn_state)

    def delete_order_data(self):
        statement = delete(ShopeeOrder)
        self.session.execute(statement)
        self.session.commit()
        self.change_btn_state()

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
        self.order_display_widget.fetch_order_data()
        self.change_btn_state()

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
        self.order_display_widget.fetch_order_data()
        self.change_btn_state()