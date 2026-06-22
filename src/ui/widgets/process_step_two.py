from PySide6.QtWidgets import QWidget, QLabel, QTableView, QVBoxLayout, QHBoxLayout, QPushButton 

class AddComboDetail(QWidget):
    def __init__(self, session, parent=None):
        super().__init__()

        # Kết nối tới database
        self.session = session
        
        # Thành phần giao diện
        # Bên trái - hiển thị các cặp combo - variant có trong file đơn hàng chưa map đúng giá
        cv_version_label = QLabel("Combo chưa được cài giá")
        self.cv_version_view = QTableView() #Các cặp combo có trong file order
        self.cv_version_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows) 
        cv_version_layout = QVBoxLayout()
        cv_version_layout.addWidget(cv_version_label)
        cv_version_layout.addWidget(self.cv_version_view)

        # Bên phải - hiển thị các sản phẩm, số lượng, giá của các cặp combo - variant khi được chọn 
        self.product_add_label = QLabel("Thêm sản phẩm vào combo")
        self.product_add_view = QTableView()
        self.add_row_btn = QPushButton("Thêm dòng mới")
        self.del_row_btn = QPushButton("Xoá dòng đang chọn")
        self.add_new_product_btn = QPushButton("Thêm sản phẩm mới")
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_row_btn)
        button_layout.addWidget(self.del_row_btn)
        button_layout.addWidget(self.add_new_product_btn)

        product_add_layout = QVBoxLayout()
        product_add_layout.addWidget(self.product_add_label)
        product_add_layout.addLayout(button_layout)
        product_add_layout.addWidget(self.product_add_view)

        main_layout = QHBoxLayout()
        main_layout.addLayout(cv_version_layout)
        main_layout.addLayout(product_add_layout)

        self.setLayout(main_layout)