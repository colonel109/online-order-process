from PySide6.QtWidgets import QWidget, QTableView, QVBoxLayout, QLabel, QHBoxLayout
from PySide6.QtCore import Qt
from src.processors.model_maker import order_model 


class OrderDisplayer(QWidget):
    def __init__(self, session):
        super().__init__()

        # View và kết nối
        self.view = QTableView()
        self.session = session

        # Data model
        self.order_data_model = None 

        # Layout
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel("<b>Danh sách đơn hàng</b>"))
        self.order_count_displayer = QLabel()
        info_layout.addWidget(self.order_count_displayer, alignment=Qt.AlignmentFlag.AlignRight)

        layout = QVBoxLayout()
        layout.addLayout(info_layout)
        layout.addWidget(self.view)
        self.setLayout(layout)

    def set_model(self):
        """
        Gọi hàm này để tiến hành lấy data và gán vào view
        """
         # Data model
        data_model, row_count = order_model(session=self.session)

        self.order_data_model = data_model
        self.view.setModel(self.order_data_model)
        self.order_count_displayer.setText(f"Đã tải {row_count} đơn hàng")