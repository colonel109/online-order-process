from PySide6.QtWidgets import QToolBar
from PySide6.QtCore import QSize
from PySide6.QtGui import QAction, QIcon, QColor

from resources import resources_rc
from src.database.structure import ShopeeOrder
from src.utils.svg_color_changer import get_colored_qrc_icon

from sqlalchemy import delete


class Toolbar(QToolBar):
    def __init__(self, session):
        super().__init__()

        # Kết nối với database
        self.session = session

        # Action
        self.delete_order_act = QAction(
            "Xoá dữ liệu",
            self
        ) 
        self.delete_order_act.setStatusTip("Xoá dữ liệu đơn hàng trong cơ sở dữ liệu")

        self.begin_process_data_act = QAction(
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

    def update_theme(self, is_dark_mode: bool):
        icon_color = QColor("white") if is_dark_mode else QColor("#333333")

        del_order_icon = get_colored_qrc_icon(":/resource/icons/list-x.svg", icon_color)
        begin_process_icon = get_colored_qrc_icon(":/resource/icons/sparkle-highlight.svg", icon_color)

        self.delete_order_act.setIcon(del_order_icon)
        self.begin_process_data_act.setIcon(begin_process_icon)