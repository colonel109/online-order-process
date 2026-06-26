from PySide6.QtWidgets import QWidget, QLabel, QTableView, QVBoxLayout, QHBoxLayout, QPushButton, QFrame
from PySide6.QtGui import QColor
from PySide6.QtCore import QSize, Qt
from sqlalchemy import func, select
from datetime import datetime

from src.database.structure import ComboVariant, ComboDetail, ShopeeOrder, Product
from src.data_model.table_view_model import ProductInputModel, TableViewModel
from src.ui.helper.auto_complete import ProductAutoCompleter
from src.utils.svg_color_changer import get_colored_qrc_icon
from src.ui.widgets.message import CustomMessage
from resources import resources_rc

class AddComboDetail(QWidget):
    def __init__(self, session, parent=None):
        super().__init__()

        # Kết nối tới database
        self.session = session

        # Các biến lưu trữ dữ liệu
        self._cv_detail_cache = [] # Lưu dữ dữ liệu cache tổng hợp
        self.product_suggest_list = [] # Lưu các cặp mã sản phẩm - tên sản phẩm để người dùng chọn trên giao diện
        self.product_lookup_dict = {} # Từ điển dạng {(product_code, product_name): {các key}} để điền ngược lại vào cache 

        # Thông báo hiện kết quả, nút tuỳ chọn
        self.custom_message_frame = CustomMessage()

        # Thành phần giao diện
        # Bên trái - hiển thị các cặp combo - variant có trong file đơn hàng chưa map đúng giá
        self.cv_version_label = QLabel("<b>Combo chưa được cài giá</b>")
        self.cv_version_model = TableViewModel(
            data=None,
            column_names=["combo_name", "variant", "deal_price"]
        )

        self.cv_version_view = QTableView() #Các cặp combo có trong file order
        self.cv_version_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows) 
        self.cv_version_view.setModel(self.cv_version_model)

        cv_version_layout = QVBoxLayout()
        cv_version_layout.addWidget(self.cv_version_label)
        cv_version_layout.addWidget(self.cv_version_view)
       
        # Bên phải - hiển thị các sản phẩm, số lượng, giá của các cặp combo - variant khi được chọn 
        self.product_input_label = QLabel("<b>Thêm sản phẩm vào combo</b>")
        self.product_input_view = QTableView()
        self.product_input_model = ProductInputModel(
            product_lookup=self.product_lookup_dict
        )
        self.product_input_view.setModel(self.product_input_model)
        self.import_product_input_btn = QPushButton("Thêm vào database")
        self.import_product_input_btn.setEnabled(False)
        
        self.product_auto_complete = ProductAutoCompleter(self.product_suggest_list, self)
        self.product_input_view.setItemDelegateForColumn(0, self.product_auto_complete)
        self.product_input_view.setItemDelegateForColumn(1, self.product_auto_complete)

        self.add_row_btn = QPushButton()
        self.del_row_btn = QPushButton()
        self.add_new_product_btn = QPushButton()
        
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
        product_input_layout.addWidget(self.import_product_input_btn)

        display_layout = QHBoxLayout()
        display_layout.addLayout(cv_version_layout)
        display_layout.addLayout(product_input_layout)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.custom_message_frame, stretch=0)
        main_layout.addLayout(display_layout, stretch=1)

        self.setLayout(main_layout)

        # Chạy hàm
        self.init_signal()

    def init_signal(self):
        self.cv_version_view.clicked.connect(self.combo_variant_select)
        self.add_row_btn.clicked.connect(self.add_row)
        self.del_row_btn.clicked.connect(self.delete_row)
        self.import_product_input_btn.clicked.connect(self.import_cache_to_combo_detail)

        self.product_input_model.dataChanged.connect(self.refresh_cv_table)
        self.product_input_model.rowsInserted.connect(self.refresh_cv_table)
        self.product_input_model.rowsRemoved.connect(self.refresh_cv_table)
        self.product_input_model.modelReset.connect(self.refresh_cv_table)

        self.product_input_model.dataChanged.connect(self.update_total_combo_value)
        self.product_input_model.rowsInserted.connect(self.update_total_combo_value)
        self.product_input_model.rowsRemoved.connect(self.update_total_combo_value)
        self.product_input_model.modelReset.connect(self.update_total_combo_value)

    def process_and_display(self):
        """
        Hàm này được gọi khi bắt đầu trích xuất và hiển thị dữ liệu
        """
        try:
            self._cv_detail_cache = self.make_cache_data()
            self.make_product_cache()

            self.cv_version_model._cache_reference = self._cv_detail_cache

            self.cv_version_model.refresh_data(self.make_cv_version_data())
        except Exception as e:
            print(e)

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
                    "variant_name": order.variant_name if order.variant_name else "",
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
        
        if cv_detail_list:
            self.custom_message_frame.show_action_message(
                text=f"Có {len(cv_detail_list)} phân nhóm giá của combo chưa được cài giá",
                confirm_btn_text="Thêm vào cơ sở dữ liệu",
                decline_button_text="Huỷ"
            )
            self.custom_message_frame.confirm_button.setEnabled(False) # Tạm thời tắt khi mới khởi tạo

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
        total_sum_display = f"Tổng giá trị: {int(total_sum):,} đ" if total_sum else "Chưa cài giá" 
        self.temp_total_value.setText(str(total_sum_display))

    def update_theme(self, is_dark_mode: bool):
        icon_color = QColor("white") if is_dark_mode else QColor("#333333")
        icon_size = QSize(17, 17)

        add_row_icon = get_colored_qrc_icon(":/resource/icons/row-insert-bottom.svg", icon_color, icon_size)
        del_row_icon = get_colored_qrc_icon(":/resource/icons/row-remove.svg", icon_color, icon_size)
        add_product_icon = get_colored_qrc_icon(":/resource/icons/package-plus.svg", icon_color, icon_size)

        self.add_row_btn.setIcon(add_row_icon)
        self.del_row_btn.setIcon(del_row_icon)
        self.add_new_product_btn.setIcon(add_product_icon)

    def import_cache_to_combo_detail(self):
            """
            Hàm bóc tách dữ liệu từ self._cv_detail_cache và tạo các bản ghi vào db
            """
            current_time = datetime.now()
            combo_detail_objects = []

            # 1. Duyệt qua dữ liệu cache đang lưu ở thuộc tính của lớp
            for item in self._cv_detail_cache:
                combo_variant_key = item.get("combo_variant_key")
                combo_composition_key = item.get("combo_composition_key")
                products = item.get("products", [])

                # 2. Duyệt qua danh sách các sản phẩm cấu thành bên trong combo đó
                for prod in products:
                    # Bỏ qua nếu dòng sản phẩm này chưa điền hoặc trống key (đảm bảo tính toàn vẹn)
                    if not prod.get("product_key"):
                        continue

                    # Tạo instance mới cho từng dòng trong bảng combo_detail
                    detail_obj = ComboDetail(
                        combo_variant_key=combo_variant_key,
                        combo_composition_key=combo_composition_key,
                        product_key=prod["product_key"],
                        product_price=prod["product_price"],
                        product_quantity=prod["product_quantity"],
                        created_date=current_time,
                        updated_date=current_time
                    )
                    combo_detail_objects.append(detail_obj)

            # 3. Sử dụng ORM để đẩy toàn bộ danh sách vào database
            if combo_detail_objects:
                try:
                    self.session.add_all(combo_detail_objects)
                    self.session.commit()
                    print(f"Đã import thành công {len(combo_detail_objects)} bản ghi vào combo_detail!")
                    
                    # Làm sạch cache hoặc view sau khi lưu thành công nếu cần thiết
                    self._cv_detail_cache.clear()
                    self.cv_version_model.refresh_data([])
                    self.product_input_model.update_model([])
                    
                    return True
                except Exception as e:
                    self.session.rollback()
                    print(f"Lỗi khi import combo_detail: {e}")
            else:
                print("Không có dữ liệu sản phẩm hợp lệ nào để import.")
                return False

    def check_all_combo_valid(self):
        if not self._cv_detail_cache:
            self.import_product_input_btn.setEnabled(False)
            return

        # Giả định ban đầu là TẤT CẢ các combo đều hợp lệ
        all_valid = True

        for combo in self._cv_detail_cache:
            # SỬA LỖI: Đảm bảo đúng tên key "products" (có chữ s) giống như trong template cache của bạn
            product_list = combo.get("products", [])

            # Kiểm tra điều kiện lỗi 1: Không có sản phẩm hoặc có sản phẩm trống mã code
            has_empty_code = (
                    len(product_list) == 0 or
                    any(not str(p.get("product_code", "")).strip() for p in product_list)
            )

            # Kiểm tra điều kiện lỗi 2: Bị lệch giá deal
            deal_price = float(combo.get("deal_price", 0.0))
            total_config_value = sum(
                float(p.get("product_price", 0.0)) * int(p.get("product_quantity", 0))
                for p in product_list
            )
            is_price_mismatched = abs(total_config_value - deal_price) >= 0.01

            # SỬA LOGIC: Nếu phát hiện Trống mã HOẶC Lệch giá -> Combo này KHÔNG hợp lệ
            if has_empty_code or is_price_mismatched:
                all_valid = False
                break  # Chỉ cần 1 combo hỏng là dừng vòng lặp ngay lập tức, không quét tiếp nữa

        # Cập nhật trạng thái nút bấm dựa trên kết quả kiểm tra toàn cục
        if all_valid:
            self.import_product_input_btn.setEnabled(True)  # Mở khóa nút khi tất cả đều xanh
        else:
            self.import_product_input_btn.setEnabled(False)  # Khóa nút khi còn ô đỏ

    def refresh_cv_table(self, *args):
        self.update_total_combo_value()

        current_left_index = self.cv_version_view.currentIndex()
        if current_left_index.isValid():
            row = current_left_index.row()
            target_cell_index = self.cv_version_model.index(row, 2)

            self.cv_version_model.dataChanged.emit(
                target_cell_index,
                target_cell_index,
                [Qt.ItemDataRole.BackgroundRole]
            )
        else:
            self.cv_version_model.layoutChanged.emit()

        self.cv_version_view.viewport().update()
        self.check_all_combo_valid()