from PySide6.QtWidgets import QMainWindow, QWidget, QFileDialog, QStackedLayout
from PySide6.QtCore import QSize

from sqlalchemy import select

from src.database.structure import ShopeeOrder
from resources import resources_rc
from src.ui.widgets.order_display import OrderDisplayer
from src.ui.widgets.import_mask import ImportMask
from src.ui.widgets.toolbar import Toolbar 
from src.ui.widgets.menubar import Menubar


class MainWindow(QMainWindow):
    def __init__(self, session, base_path):
        super().__init__()

        # Đường dẫn gốc
        self.base_path = base_path
        
        # Kết nối với database
        self.session = session

        # Thành phần UI
        self.order_display_widget = OrderDisplayer(session=self.session)
        self.import_mask_widget = ImportMask()
        
        self.menubar = Menubar(base_path=self.base_path)
        self.toolbar = Toolbar(session)

        # Kích cỡ cửa sổ
        self.setWindowTitle("Cửa sổ chính")
        self.setMinimumSize(QSize(900, 600))

        # Container chính
        self.setMenuBar(self.menubar)
        self.addToolBar(self.toolbar)
        self.main_layout = QStackedLayout()
        self.main_layout.addWidget(self.import_mask_widget)
        self.main_layout.addWidget(self.order_display_widget)
        container = QWidget()
        container.setLayout(self.main_layout)
        self.setCentralWidget(container)

        # Chạy hàm 
        self.init_signal()
        self.change_window_state()
        self.order_display_widget.fetch_order_data()


    def change_window_state(self):
        stmt = select(ShopeeOrder).exists()
        result = self.session.scalar(select(stmt))

        buttons = [self.toolbar.delete_order_act, self.toolbar.begin_process_data_act]

        for btn in buttons:
            if not result:
                btn.setEnabled(False)           
                self.main_layout.setCurrentIndex(0)

            else:
                self.order_display_widget.fetch_order_data()
                self.main_layout.setCurrentIndex(1)
                btn.setEnabled(True)

    def init_signal(self):
        """
        Hàm này có nhiệm vụ kết nối slot với signal
        """
        self.menubar.open_file_act.triggered.connect(self.change_window_state)
        self.menubar.open_folder_act.triggered.connect(self.change_window_state)
        self.toolbar.delete_order_act.triggered.connect(self.change_window_state)