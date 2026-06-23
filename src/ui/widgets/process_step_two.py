from PySide6.QtWidgets import QWidget, QLabel, QTableView, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize, Qt
from sqlalchemy import func, select

from src.database.structure import ComboVariant, ComboDetail, ShopeeOrder, Product, ProductType
from src.data_model.table_view_model import ProductInputModel, TableViewModel
from src.ui.helper.auto_complete import ProductAutoCompleter
from resources import resources_rc

class AddComboDetail(QWidget):
    def __init__(self, session, parent=None):
        super().__init__()

        # Kết nối tới database
        self.session = session

        # Các biến lưu trữ dữ liệu
        self._cv_detail_cache = self.make_cache_data() # Lưu dữ dữ liệu cache tổng hợp
        self.product_suggest_list = [] # Lưu các cặp mã sản phẩm - tên sản phẩm để người dùng chọn trên giao diện
        self.product_lookup_dict = {} # Từ điển dạng {(product_code, product_name): {các key}} để điền ngược lại vào cache 

        # Đưa dữ liệu vào biến
        self.make_product_cache()

        # Thành phần giao diện
        # Bên trái - hiển thị các cặp combo - variant có trong file đơn hàng chưa map đúng giá
        cv_version_label = QLabel("Combo chưa được cài giá")
        cv_version_model = TableViewModel(
            data=self.make_cv_version_data(),
            column_names=["combo_name", "variant", "deal_price"],
            cache=self._cv_detail_cache
        )
        self.cv_version_view = QTableView() #Các cặp combo có trong file order
        self.cv_version_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows) 
        self.cv_version_view.setModel(cv_version_model)

        cv_version_layout = QVBoxLayout()
        cv_version_layout.addWidget(cv_version_label)
        cv_version_layout.addWidget(self.cv_version_view)
       
        # Bên phải - hiển thị các sản phẩm, số lượng, giá của các cặp combo - variant khi được chọn 
        self.product_input_label = QLabel("Thêm sản phẩm vào combo")
        self.product_input_view = QTableView()
        self.product_input_model = ProductInputModel(product_lookup=self.product_lookup_dict)
        self.product_input_view.setModel(self.product_input_model)
        
        self.product_auto_complete = ProductAutoCompleter(self.product_suggest_list, self)
        self.product_input_view.setItemDelegateForColumn(0, self.product_auto_complete)
        self.product_input_view.setItemDelegateForColumn(1, self.product_auto_complete)

        self.add_row_btn = QPushButton(
            QIcon(":/resource/icons/row-insert-bottom.svg"),
            ""
        )
        self.add_row_btn.setIconSize(QSize(17, 17))
        self.del_row_btn = QPushButton(
            QIcon(":/resource/icons/row-remove.svg"),
            ""
        )
        self.del_row_btn.setIconSize(QSize(17, 17))
        self.add_new_product_btn = QPushButton(
            QIcon(":resource/icons/package-plus.svg"),
            ""
        )
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_row_btn)
        button_layout.addWidget(self.del_row_btn)
        button_layout.addStretch(1)
        button_layout.addWidget(self.add_new_product_btn)

        product_input_layout = QVBoxLayout()
        product_input_layout.addWidget(self.product_input_label)
        product_input_layout.addLayout(button_layout)
        product_input_layout.addWidget(self.product_input_view)

        main_layout = QHBoxLayout()
        main_layout.addLayout(cv_version_layout)
        main_layout.addLayout(product_input_layout)

        self.setLayout(main_layout)

        # Chạy hàm
        self.init_signal()
    
    def init_signal(self):
        self.cv_version_view.clicked.connect(self.combo_variant_select)
        self.add_row_btn.clicked.connect(self.add_row)
        self.del_row_btn.clicked.connect(self.delete_row)
        self.product_input_model.dataChanged.connect(self.update_total_combo_value)
        self.product_input_model.modelReset.connect(self.update_total_combo_value)

    def make_cache_data(self):
        """
        Hàm này trích xuất dữ liệu từ database và tạo ra một dict chứa toàn bộ thông tin cho quá trình hiển thị
        và xử lí dữ liệu 
        """
        mapped_cv_stmt = (
            select(
                ComboVariant.combo_key,
                ComboVariant.variant_key,
                func.sum(ComboDetail.product_price * ComboDetail.product_quantity).label("total_combo_value")
            )
            .join(ComboVariant, ComboDetail.combo_variant_key == ComboVariant.combo_variant_key)
            .group_by(ComboVariant.combo_key, ComboVariant.variant_key, ComboDetail.combo_composition_key)
        )
        mapped_cv_versions = self.session.execute(mapped_cv_stmt).all() # List các tuple chứa thông tin
        
        # Tạo danh sách dict có dạng {(combo_key, variant_key): {total_combo_value}} để so sánh nhanh mức giá với cặp trong order
        cv_mapped_compare_list = {}
        for version in mapped_cv_versions:
            cv_key_pair = (version.combo_key, version.variant_key)
            if cv_key_pair not in cv_mapped_compare_list: # Kiểm tra xem set đã có trong dict vừa toạ chưa để gán vào key với value là một set rỗng
                cv_mapped_compare_list[cv_key_pair] = set()
            cv_mapped_compare_list[cv_key_pair].add(version.total_combo_value)
            
        # Lấy combo_composition_key lớn nhất trong database để gán vào trong dict
        max_composition_key = self.session.scalar(select(func.max(ComboDetail.combo_composition_key)))
        composition_key_available = max_composition_key if max_composition_key is not None else 0 # Trả 0 nếu chưa có key nào được tạo   
        
        # List chứa các dict, mỗi dict gồm thông tin về cặp combo variant, các sản phẩm được thêm vào các cặp đó
        cv_detail_list = []

        order_cv_stmt = select(
            ShopeeOrder.combo_key,
            ShopeeOrder.variant_key,
            ShopeeOrder.combo_name,
            ShopeeOrder.variant_name,
            ShopeeOrder.deal_price
        ).distinct()
        order_cv_versions = self.session.execute(order_cv_stmt).all()

        for order in order_cv_versions:
            cv_key_pair = (order.combo_key, order.variant_key) # Tạo cặp (combo, varinant) để so sánh với các cặp đã map
            order_price = order.deal_price

            # Điều kiện: cặp cv_key_pair trong order chưa được map hoặc giá của nó không khớp với giá của cặp cv đã map
            is_missing = (cv_key_pair not in cv_mapped_compare_list) or (order_price not in cv_mapped_compare_list[cv_key_pair])

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
                    "deal_price": float(order_price),
                    "variant_name": order.variant_name if order.variant_name else "-",
                    "combo_variant_key": cv_key,
                    "combo_composition_key": composition_key_available,
                    "products": [
                        {
                            "product_key": None,
                            "product_code": "",
                            "product_name": "",
                            "product_quantity": 1,
                            "product_price": 0.0
                        }
                    ]
                }
                cv_detail_list.append(combo_template)

        return cv_detail_list

    def make_cv_version_data(self):
        """
        Hàm này phụ trách trích xuất dữ liệu combo, variant, deal_price từ cache và truyền vào biến lưu trữ để hiển thị trên view
        """
        cv_version_data = []
        
        for item in self._cv_detail_cache:
            version = [
                item["combo_name"],
                item["variant_name"],
                item["deal_price"]
            ]
            cv_version_data.append(version)

        return cv_version_data
    
    def combo_variant_select(self, index):
        """
        Hàm này có nhiệm vụ lấy index của cặp combo - variant mà người dùng đang chọn
        sau đó lấy thông tin sản phẩm tương ứng được trích xuất từ cache
        """
        row_index = index.row()

        if row_index < 0 or row_index >= len(self._cv_detail_cache):
            return
        
        selected_combo_variant = self._cv_detail_cache[row_index] 
        selected_product_list = selected_combo_variant["products"]

        self.product_input_model.update_model(selected_product_list)

    def delete_row(self):
        """
        Hàm này nhận tín hiệu từ nút, xoá dòng mà người dùng đang chọn trên view và viết lại vào cache 
        """
        row_to_remove =  self.product_input_view.currentIndex().row()
        if row_to_remove < 0:
            return
        self.product_input_model.remove_row(row_to_remove)
        self.update_total_combo_value()
   
    def add_row(self):
        """
        Hàm này nhận tín hiệu từ nút, thêm dòng mới vào cuối danh sách và viết lại vào cache
        """
        if self.cv_version_view.currentIndex().row() < 0:
            return
        self.product_input_model.add_blank_row()
        self.update_total_combo_value()

    def make_product_cache(self):
        stmt = select(Product.product_key, Product.product_code, Product.product_name, Product.product_type_key) 
        data = self.session.execute(stmt).all()

        for p in data:
            suggest_text = f"{p.product_code} - {p.product_name}"
            self.product_suggest_list.append(suggest_text)
            self.product_lookup_dict[suggest_text] = {
                "product_key": p.product_key,
                "product_code": p.product_code,
                "product_name": p.product_name
            }

    def update_total_combo_value(self):
        """
        Quét qua toàn bộ sản phẩm lẻ của combo hiện tại trong Model để tính tổng tiền
        """
        current_products = self.product_input_model._data

        total_sum = sum(
            float(p.get("product_price", 0.0)) * int(p.get("product_quantity", 0))
            for p in current_products
        )