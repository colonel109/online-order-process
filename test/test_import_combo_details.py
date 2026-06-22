import sys
from pathlib import Path
from PySide6.QtWidgets import QWidget, QApplication, QVBoxLayout, QTableView, QLabel, QPushButton, QHBoxLayout, QDialog, QLineEdit, QComboBox
from PySide6.QtCore import QSize, Qt, QModelIndex
import os
from sqlalchemy import select, func

sys.path.append(os.path.abspath(os.path.join('..')))

from src.database.structure import Combo, Variant, ComboVariant, ShopeeOrder, ComboDetail, Product, ProductType
from src.database.connector import db_connector
from src.data_model.table_view_model import TableViewModel # Nhận list

from PySide6.QtCore import QAbstractTableModel


class AddProduct(QDialog):
    def __init__(self, session):
        super().__init__()

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
        self.display_preview_data = [] # Dữ liệu này dùng để hiển thi trên tableview
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
            data = [],
            column_names = ['product_code', 'product_name', 'product_type_name']
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
        self.product_code_input.textEdited.connect(self.data_validation)
        self.product_name_input.textEdited.connect(self.data_validation)
        self.delete_button.pressed.connect(self.remove_record)
        self.preview_list_view.clicked.connect(self.remove_btn_status)
        self.cfm_button.clicked.connect(self.process_and_import)

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

        dup_condition = (current_code_input in self.exist_product_code) or (current_name_input in self.exist_product_name)
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
        data = [(d['product_name'], d['product_code'], d['product_type_name']) for d in self.cache_data]
        self.preview_list_model.refresh_data(
            new_data = data
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


class ProductInputModel(QAbstractTableModel):
    def __init__(self, products_cache_list=None):
        super().__init__()
        # Liên kết trực tiếp tới mảng "products" của combo đang chọn trong RAM
        self.products = products_cache_list if products_cache_list is not None else []
        # 🌟 Nắn lại tiêu đề cho đúng thứ tự index dưới hàm data()
        self.headers = ["Mã sản phẩm", "Tên sản phẩm", "Giá gốc", "Số lượng"]

    def rowCount(self, parent=QModelIndex()):
        return len(self.products)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.headers[section]
        return None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role not in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return None
        
        row_data = self.products[index.row()]
        col = index.column()
        
        # Ánh xạ từ Dictionary ra các cột hiển thị trên TableView
        if col == 0: return row_data["product_code"]
        if col == 1: return row_data["product_name"]
        if col == 2: return row_data["product_price"]
        if col == 3: return row_data["product_quantity"]
        return None

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        """Hàm này kích hoạt khi người dùng gõ sửa trực tiếp trên ô của bảng"""
        if index.isValid() and role == Qt.ItemDataRole.EditRole:
            row_data = self.products[index.row()]
            col = index.column()
            
            # Ghi trực tiếp vào Dictionary trên RAM
            if col == 0: row_data["product_code"] = value
            elif col == 1: row_data["product_name"] = value
            elif col == 2: row_data["product_price"] = float(value) if value else 0.0
            elif col == 3: row_data["product_quantity"] = int(value) if value else 0
            
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])
            return True
        return False

    def flags(self, index):
        # Cho phép người dùng click đúp để sửa ô dữ liệu
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable

    def update_model(self, new_products_list):
        """Thay đổi 'sợi dây liên kết' sang mảng sản phẩm của combo khác"""
        self.beginResetModel()
        self.products = new_products_list
        self.endResetModel()

    # 🌟 ĐƯA LOGIC THÊM/XÓA DÒNG VÀO TRONG MODEL CHO ĐÚNG CHUẨN MVC AN TOÀN
    def add_blank_row(self):
        position = len(self.products)
        # Sử dụng QModelIndex() chuẩn của Qt thay vì .parent() để tránh crash khi bảng rỗng
        self.beginInsertRows(QModelIndex(), position, position)
        self.products.append({
            "product_key": None,
            "product_code": "",
            "product_name": "",
            "product_quantity": 1, # Mặc định số lượng thêm mới là 1
            "product_price": 0.0
        })
        self.endInsertRows()

    def remove_row(self, row_idx):
        if row_idx < 0 or row_idx >= len(self.products):
            return
        self.beginRemoveRows(QModelIndex(), row_idx, row_idx)
        self.products.pop(row_idx)
        self.endRemoveRows()
        
        
class ImportComboDetails(QWidget):
    def __init__(self):
        super().__init__()

        BASE_PATH = Path().cwd().parent
        DB_PATH = Path(BASE_PATH / "database.sqlite3")
        self.session = db_connector(DB_PATH)

        # Biến lưu trữ
        self.cv_import_cache = self.make_cache_data()

        # Thành phần UI
        # Widget hiển thị các combo chưa cài giá
        cv_version_label = QLabel("Combo chưa được cài giá")
        self.cv_version_view = QTableView()
        self.cv_version_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows) # Chọn cả dòng
        self.add_new_product_dlg = AddProduct(session=self.session)
        
        cv_version_layout = QVBoxLayout()
        cv_version_layout.addWidget(cv_version_label)
        cv_version_layout.addWidget(self.cv_version_view)

        # Widget hiển thị các sản phẩm trong combo
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

        # 1. Trích xuất các cột cần hiển thị ra một list mới
        display_data = [
            [
                item["combo_name"],
                item["variant_name"],
                f"{int(item['deal_price']):,}đ"  # Định dạng tiền tệ cho đẹp mắt
            ]
            for item in self.cv_import_cache
        ]

        # 2. Nạp thẳng mảng phẳng này vào TableViewModel của bạn
        self.cv_version_model = TableViewModel(
            data=display_data,
            column_names=["combo_name", "variant_name", "deal_price"]
        )
        self.cv_version_view.setModel(self.cv_version_model)

        self.setLayout(main_layout)
        self.setMinimumSize(QSize(1300, 700))
        
        self.product_add_model = ProductInputModel()
        self.product_add_view.setModel(self.product_add_model)

        self.init_signal()

    def make_cache_data(self):
        get_cv_mapped = (
            select(
                ComboVariant.combo_key,
                ComboVariant.variant_key,
                func.sum(ComboDetail.product_price * ComboDetail.product_quantity).label("total_combo_value")
            )
            .join(ComboVariant, ComboDetail.combo_variant_key == ComboVariant.combo_variant_key)
            .group_by(ComboVariant.combo_key, ComboVariant.variant_key, ComboDetail.combo_composition_key)
        )
        cv_mapped_versions = self.session.execute(get_cv_mapped).all()

        cv_compare_list = {}
        for version in cv_mapped_versions:
            cv_key_pair = (version.combo_key, version.variant_key)
            if cv_key_pair not in cv_compare_list:
                cv_compare_list[cv_key_pair] = set()
            cv_compare_list[cv_key_pair].add(version.total_combo_value)

        # Xử lý nếu DB trống, ép max về số 0
        max_composition_key = self.session.scalar(select(func.max(ComboDetail.combo_composition_key)))
        composition_key_available = max_composition_key if max_composition_key is not None else 0

        cv_import_cache = []

        get_cv_order = select(
            ShopeeOrder.combo_key,
            ShopeeOrder.variant_key,
            ShopeeOrder.combo_name,
            ShopeeOrder.variant_name,
            ShopeeOrder.deal_price
        ).distinct()
        cv_order_versions = self.session.execute(get_cv_order).all()

        for order in cv_order_versions:
            cv_key_pair = (order.combo_key, order.variant_key)
            order_price = order.deal_price

            is_missing = (cv_key_pair not in cv_compare_list) or (order_price not in cv_compare_list[cv_key_pair])

            if is_missing:
                composition_key_available += 1
                cv_key = self.session.scalar(
                    select(ComboVariant.combo_variant_key)
                    .where(ComboVariant.combo_key == order.combo_key)
                    .where(ComboVariant.variant_key == order.variant_key)
                )

                combo_template = {
                    "combo_key": order.combo_key,
                    "variant_key": order.variant_key,
                    "combo_name": order.combo_name,
                    "variant_name": order.variant_name if order.variant_name else "-",
                    "deal_price": float(order_price),
                    "combo_variant_key": cv_key,
                    "combo_composition_key": composition_key_available,
                    "products": [
                        {
                            "product_key": None,
                            "product_code": "",
                            "product_name": "",
                            "product_quantity": 1, # Đổi mặc định thành 1 dòng mẫu
                            "product_price": 0.0
                        }
                    ]
                }
                cv_import_cache.append(combo_template)
        return cv_import_cache

    def init_signal(self):
        # Sử dụng .clicked.connect đồng bộ cho cả 3 nút tương tác
        self.cv_version_view.clicked.connect(self.on_combo_changed)
        self.add_row_btn.clicked.connect(self.add_product_row)
        self.del_row_btn.clicked.connect(self.remove_product_row)
        self.add_new_product_btn.clicked.connect(self.open_product_add_dialog)

    def open_product_add_dialog(self):
        self.add_new_product_dlg.show()

    def on_combo_changed(self, index):
        row_index = index.row()
        if row_index < 0 or row_index >= len(self.cv_import_cache):
            return
            
        selected_combo = self.cv_import_cache[row_index]
        current_product_list = selected_combo["products"]
        
        # Bẻ lái con trỏ sang cụm sản phẩm lẻ của combo được click
        self.product_add_model.update_model(current_product_list)

    def add_product_row(self):
        """Nút Thêm dòng: Kiểm tra xem người dùng đã chọn combo chưa rồi mới đẻ dòng mới"""
        if self.cv_version_view.currentIndex().row() < 0:
            return
        self.product_add_model.add_blank_row()

    def remove_product_row(self):
        """Nút Xóa dòng: Bốc trích xuất dòng bôi xanh bên bảng phải để xóa"""
        row_to_remove = self.product_add_view.currentIndex().row()
        if row_to_remove <0:
            return
        self.product_add_model.remove_row(row_to_remove)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImportComboDetails()
    window.show()
    sys.exit(app.exec())