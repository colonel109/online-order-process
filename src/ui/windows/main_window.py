from PySide6.QtWidgets import QMainWindow, QWidget, QStackedLayout
from PySide6.QtCore import QSize
from pathlib import Path

from sqlalchemy import select

from src.database.structure import ShopeeOrder
from resources import resources_rc
from src.ui.widgets.order_display import OrderDisplayer
from src.ui.widgets.import_mask import ImportMask
from src.ui.widgets.toolbar import Toolbar 
from src.ui.widgets.menubar import Menubar
from src.ui.widgets.statusbar import StatusBar
from src.processors.file_loaders import ConfigLoader, OrderLoader
from src.ui.windows.data_process_window import DataProcessWindow


class MainWindow(QMainWindow):
    def __init__(self, session, base_path, config_path, database_path):
        super().__init__()

        # Đường dẫn
        self.base_path = base_path
        self.config_path = config_path 
        self.database_path = database_path 

        # Kết nối với database
        self.session = session

        # Cửa sổ xử lí dữ liệu
        self.data_process_window = DataProcessWindow(session=self.session)

        # Khởi tạo các loader
        self.config_loader = ConfigLoader(config_file=self.config_path)
        self.order_loader = OrderLoader(
            rename_dict=self.config_loader.get_rename_dict(),
            dtype_dict=self.config_loader.get_dtype_dict(),
            db_path=self.database_path
        )

        # Thành phần UI
        self.order_display_widget = OrderDisplayer(session=self.session)
        self.import_mask_widget = ImportMask(base_path=self.base_path)
        
        self.menubar = Menubar(base_path=self.base_path)
        self.toolbar = Toolbar(session)
        self.statusbar = StatusBar()

        # Kích cỡ cửa sổ
        self.setWindowTitle("Cửa sổ chính")
        self.setMinimumSize(QSize(1200, 800))

        # Container chính
        self.setMenuBar(self.menubar)
        self.addToolBar(self.toolbar)
        self.setStatusBar(self.statusbar)
        self.main_layout = QStackedLayout()
        self.main_layout.addWidget(self.import_mask_widget)
        self.main_layout.addWidget(self.order_display_widget)
        container = QWidget()
        container.setLayout(self.main_layout)
        self.setCentralWidget(container)

        # Chạy hàm 
        self.init_signal()
        self.change_window_state()

    def change_window_state(self):
        stmt = select(ShopeeOrder).exists()
        result = self.session.scalar(select(stmt))

        buttons = [self.toolbar.delete_order_act, self.toolbar.begin_process_data_act]

        for btn in buttons:
            if not result:
                btn.setEnabled(False)           
                self.main_layout.setCurrentIndex(0)

            else:
                self.order_display_widget.set_model()
                self.main_layout.setCurrentIndex(1)
                btn.setEnabled(True)

    def init_signal(self):
        """
        Hàm này có nhiệm vụ kết nối slot với signal
        """
        self.toolbar.delete_order_act.triggered.connect(self.change_window_state)
        self.menubar.file_selected_signal.connect(self.process_imported_files)
        self.import_mask_widget.file_selected_signal.connect(self.process_imported_files)
        self.toolbar.begin_process_data_act.triggered.connect(self.open_data_process_window)

    def process_imported_files(self, paths):
        self.order_loader.data_processor(paths)
        self.change_window_state()

    def open_data_process_window(self):
        if self.data_process_window.isHidden():
            self.data_process_window.show()