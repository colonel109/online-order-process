from PySide6.QtWidgets import QDialog, QLabel, QLineEdit, QHBoxLayout, QVBoxLayout, QComboBox, QPushButton, QTableView
from PySide6.QtCore import QSize
from sqlalchemy import select

from src.database.structure import Product, ProductType
from src.data_model.table_view_model import TableViewModel

class AddProduct(QDialog):
    def __init__(self, session, parent = None):
        super().__init__(parent)

        # Kết nối tới db
        self.session = session

        # Biến lưu trữ dữ liệ
        self.exist_product_code = set(
            code[0] for code in
            self.session.execute(select(Product.product_code))
        )

        self.exist_product_name = set(
            name[0] for name in
            self.session.execute(select(Product.product_name))
        )

        self.product_type_list = [
            type for type in
            self.session.execute(select(ProductType.product_type_key, ProductType.product_type_name))
        ]

        self.cache_data = []
        self.display_preview_data = []  # Dữ liệu này dùng để hiển thi trên tableview
        self.current_index_selected = -1

        # Thành phần giao diện người dùng
        product_code_label = QLabel("Mã sản phẩm")
        self.product_code_input = QLineEdit()
        product_code_layout = QHBoxLayout()
        product_code_layout.addWidget(product_code_label)
        product_code_layout.addWidget(self.product_code_input)

        product_name_label = QLabel("Tên sản phẩm")
        self.product_name_input = QLineEdit()
        product_name_layout = QHBoxLayout()
        product_name_layout.addWidget(product_name_label)
        product_name_layout.addWidget(self.product_name_input)

        product_type_label = QLabel("Phân loại")
        self.product_type_combo = QComboBox()
        self.product_type_combo.addItems([tup[1] for tup in self.product_type_list])
        product_type_layout = QHBoxLayout()
        product_type_layout.addWidget(product_type_label)
        product_type_layout.addWidget(self.product_type_combo)

        self.add_btn = QPushButton("Thêm")
        self.add_btn.setDisabled(True)
        self.add_btn.setMaximumWidth(50)

        preview_title = QLabel("<b>Các sản phẩm sau sẽ được thêm:</b>")
        self.delete_button = QPushButton("Xoá dòng đã chọn")
        self.delete_button.setEnabled(False)
        self.preview_list_view = QTableView()
        self.preview_list_model = TableViewModel(
            data=[],
            column_names=['product_code', 'product_name', 'product_type_name']
        )

        self.preview_list_view.setModel(self.preview_list_model)
        preview_layout = QVBoxLayout()
        preview_layout.addWidget(preview_title)
        preview_layout.addWidget(self.delete_button)
        preview_layout.addWidget(self.preview_list_view)

        self.cfm_button = QPushButton("Thêm vào database")
        self.dcl_button = QPushButton("Huỷ bỏ")
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.cfm_button)
        button_layout.addWidget(self.dcl_button)

        main_layout = QVBoxLayout()
        main_layout.addLayout(product_code_layout)
        main_layout.addLayout(product_name_layout)
        main_layout.addLayout(product_type_layout)
        main_layout.addWidget(self.add_btn)
        main_layout.addLayout(preview_layout)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

        self.setMinimumSize(QSize(600, 450))
        self.setWindowTitle("Thêm sản phẩm mới")

        self.init_signal()

    def init_signal(self):
        self.add_btn.clicked.connect(self.add_to_temp_list)
        self.product_code_input.textChanged.connect(self.data_validation)
        self.product_name_input.textChanged.connect(self.data_validation)
        self.delete_button.pressed.connect(self.remove_record)
        self.preview_list_view.clicked.connect(self.remove_btn_status)
        self.cfm_button.clicked.connect(self.process_and_import)
        self.dcl_button.clicked.connect(self.reject)

    def remove_btn_status(self):
        self.current_index_selected = self.preview_list_view.currentIndex().row()
        if self.current_index_selected >= 0:
            self.delete_button.setDisabled(False)

    def remove_record(self):
        self.current_index_selected = self.preview_list_view.currentIndex().row()
        if self.current_index_selected >= 0:
            code_removed = self.cache_data[self.current_index_selected]["product_code"]
            self.exist_product_code.remove(code_removed)

            name_removed = self.cache_data[self.current_index_selected]["product_name"]
            self.exist_product_name.remove(name_removed)

            self.cache_data.pop(self.current_index_selected)
            self.delete_button.setDisabled(True)
            self.refresh_preview_data()

    def data_validation(self):
        current_code_input = self.product_code_input.text().strip()
        current_name_input = self.product_name_input.text().strip()

        dup_condition = (current_code_input in self.exist_product_code) or (
                    current_name_input in self.exist_product_name)
        null_conditon = len(current_code_input) == 0 or len(current_name_input) == 0

        if dup_condition or null_conditon:
            self.add_btn.setDisabled(True)
        else:
            self.add_btn.setDisabled(False)

    def add_to_temp_list(self):
        current_product_code = str(self.product_code_input.text())
        current_product_name = str(self.product_name_input.text())
        current_type_key = self.product_type_list[self.product_type_combo.currentIndex()][0]
        self.cache_data.append({
            "product_code": current_product_code,
            "product_name": current_product_name,
            "product_type_key": current_type_key,
            "product_type_name": self.product_type_combo.currentText()
        })
        self.refresh_preview_data()
        self.add_btn.setDisabled(True)

        self.exist_product_code.add(current_product_code)
        self.exist_product_name.add(current_product_name)

        self.product_code_input.clear()
        self.product_name_input.clear()

    def refresh_preview_data(self):
        """
        Hàm này được sử dụng để trích xuất dữ liệu mới nhất từ cache và tạo dataset cho model sử dụng
        """
        data = [(d['product_code'], d['product_name'], d['product_type_name']) for d in self.cache_data]
        self.preview_list_model.refresh_data(
            new_data=data
        )

    def process_and_import(self):
        """
        Hàm này có nhiệm vụ lấy lọc ra các thông tin cần thiết trong biến cache và import vào database
        """
        keep_key = ["product_code", "product_name", "product_type_key"]
        import_data = [
            {k: dict[k] for k in keep_key if k in dict}
            for dict in self.cache_data
        ]
        self.session.bulk_insert_mappings(Product, import_data)
        self.session.commit()
        self.cache_data.clear()
        self.refresh_preview_data()