from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTableView, QFrame, QWidget
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize

from src.data_model.table_view_model import ProductInputModel
from src.ui.helper.auto_complete import ProductAutoCompleter

from resources import resources_rc


class DatabaseWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Xử lí dữ liệu đơn hàng")
        self.setMinimumSize(QSize(1400, 700))

        self.cv_version_label = QLabel("<b>Các combo đã lưu</b>")

        self.cv_version_view = QTableView()
        self.cv_version_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

        cv_version_layout = QVBoxLayout()
        cv_version_layout.addWidget(self.cv_version_label)
        cv_version_layout.addWidget(self.cv_version_view)

        self.product_input_label = QLabel("<b>Các sản phẩm trong combo</b>")
        self.product_input_view = QTableView()

        self.add_row_btn = QPushButton()
        self.add_row_btn.setIcon(QIcon(":/resource/icons/row-remove.svg"))
        self.del_row_btn = QPushButton()
        self.del_row_btn.setIcon(QIcon(":/resource/icons/package-plus.svg"))
        self.add_new_product_btn = QPushButton()
        self.add_new_product_btn.setIcon(QIcon(":/resource/icons/package-plus.svg"))

        # Frame hiển thị giá trị tạm thời của đơn hàng được tính toán khi người dùng thay đổi thông tin trong biểu mẫu
        self.temp_total_value = QLabel("Tổng giá trị tạm tính")
        toolbar_layout = QHBoxLayout()
        toolbar_frame = QFrame()
        toolbar_frame.setObjectName("toolbar_frame")
        toolbar_frame.setLayout(toolbar_layout)
        toolbar_layout.addWidget(self.add_row_btn)
        toolbar_layout.addWidget(self.del_row_btn)
        toolbar_layout.addWidget(self.add_new_product_btn)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.temp_total_value)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)

        toolbar_frame.setStyleSheet("""
            QLabel {
                border-radius: 5px;
                background-color: #233D4D;
                padding: 5px;
                color: #ffffff;
            }                            
        """)

        product_input_layout = QVBoxLayout()
        product_input_layout.addWidget(self.product_input_label)
        product_input_layout.addWidget(toolbar_frame)
        product_input_layout.addWidget(self.product_input_view)

        display_layout = QHBoxLayout()
        display_layout.addLayout(cv_version_layout)
        display_layout.addLayout(product_input_layout)

        main_layout = QVBoxLayout()
        main_layout.addLayout(display_layout)

        main_container = QWidget()
        main_container.setLayout(main_layout)
        self.setCentralWidget(main_container)