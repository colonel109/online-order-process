from PySide6.QtWidgets import QToolBar
from PySide6.QtCore import QSize
from PySide6.QtGui import QAction, QIcon

from resources import resources_rc
from src.database.structure import ShopeeOrder

from sqlalchemy import delete


class Toolbar(QToolBar):
    def __init__(self, session):
        super().__init__()

        # Kết nối với database
        self.session = session

        # Action
        self.delete_order_act = QAction(
            QIcon(":/resource/icons/list-x.svg"),
            "Xoá dữ liệu",
            self
        ) 
        self.delete_order_act.setStatusTip("Xoá dữ liệu đơn hàng trong cơ sở dữ liệu")

        self.begin_process_data_act = QAction(
            QIcon(":/resource/icons/square-chevron-right.svg"),
            "Bắt đầu xử lí dữ liệu",
            self
        )
        self.begin_process_data_act.setStatusTip("Bắt đầu quy trình xử lí các đơn hàng đang được hiển thị trên màn hình")
       
        # Thanh công cụ
        self.setIconSize(QSize(17, 17))
        
        self.addAction(self.delete_order_act)
        self.addSeparator()
        self.addAction(self.begin_process_data_act)

        # Kết nối slot với signal
        self.init_signal()

    def init_signal(self):
        self.delete_order_act.triggered.connect(self.delete_order_data)
    
    def delete_order_data(self):
        statement = delete(ShopeeOrder)
        self.session.execute(statement)
        self.session.commit()