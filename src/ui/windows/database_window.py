from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTableView, QFrame, QWidget
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize, Qt

from src.data_model.table_view_model import ProductInputModel, TableViewModel
from src.ui.helper.auto_complete import ProductAutoCompleter
from src.services.combo_edit import ComboService  # Tầng nghiệp vụ DB

from resources import resources_rc

class DatabaseWindow(QMainWindow):
    def __init__(self, session):  # Nhận session từ main app
        super().__init__()

        # Khởi tạo Service layer để quản lý Logic SQL độc lập
        self.combo_service = ComboService(session)
        
        # Biến lưu trữ dữ liệu cache cục bộ của UI
        self.cache_data = []
        
        # Cache phục vụ tính năng gợi ý sản phẩm lẻ
        self.product_suggest_list = [] 
        self.product_lookup_dict = {} 

        # Giao diện chính của bảng
        self.setWindowTitle("Xử lí dữ liệu đơn hàng")
        self.setMinimumSize(QSize(1400, 700))

        self.cv_version_label = QLabel("<b>Các combo đã lưu</b>")

        self.cv_version_view = QTableView()
        self.cv_version_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        
        # Model Bảng trái
        self.cv_version_model = TableViewModel(
            data=None,
            column_names=["combo_name", "variant_name", "total_combo_value"]
        )
        self.cv_version_view.setModel(self.cv_version_model)

        cv_version_layout = QVBoxLayout()
        cv_version_layout.addWidget(self.cv_version_label)
        cv_version_layout.addWidget(self.cv_version_view)

        self.product_input_label = QLabel("<b>Các sản phẩm trong combo</b>")
        self.product_input_view = QTableView()
        
        # Model Bảng phải
        self.product_input_model = ProductInputModel(
            product_lookup=self.product_lookup_dict
        )
        self.product_input_view.setModel(self.product_input_model)

        # Thanh Toolbar nút bấm quản lý dòng lẻ
        self.add_row_btn = QPushButton()
        self.add_row_btn.setIcon(QIcon(":/resource/icons/row-insert-bottom.svg"))
        
        self.del_row_btn = QPushButton()
        self.del_row_btn.setIcon(QIcon(":/resource/icons/row-remove.svg"))
        
        self.add_new_product_btn = QPushButton()
        self.add_new_product_btn.setIcon(QIcon(":/resource/icons/package-plus.svg"))

        # Nút Lưu cập nhật dữ liệu xuống Database
        self.save_changes_btn = QPushButton("Lưu thay đổi")
        self.save_changes_btn.setStyleSheet("background-color: #4A90E2; color: white; padding: 5px; border-radius: 3px;")

        self.temp_total_value = QLabel("Tổng giá trị tạm tính")
        
        toolbar_layout = QHBoxLayout()
        toolbar_frame = QFrame()
        toolbar_frame.setObjectName("toolbar_frame")
        toolbar_frame.setLayout(toolbar_layout)
        
        toolbar_layout.addWidget(self.add_row_btn)
        toolbar_layout.addWidget(self.del_row_btn)
        toolbar_layout.addWidget(self.add_new_product_btn)
        toolbar_layout.addWidget(self.save_changes_btn) # Đưa nút lưu vào thanh công cụ
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

        # Khởi tạo tín hiệu và load cache
        self.init_signal()
        self.load_product_autocomplete_cache()
        self.refresh_all_view()

    def init_signal(self):
        """Khôi phục lại hoàn toàn các liên kết nút bấm của bạn"""
        self.cv_version_view.clicked.connect(self.combo_variant_select)
        
        # Trả lại logic tương tác dòng lẻ trên TableView cho các nút bấm
        self.add_row_btn.clicked.connect(self.add_row)
        self.del_row_btn.clicked.connect(self.delete_row)
        
        # Kết nối nút Lưu thay đổi xuống cơ sở dữ liệu
        self.save_changes_btn.clicked.connect(self.on_save_changes_clicked)
        
        # Lắng nghe thay đổi dữ liệu để tính toán lại tổng giá trị tạm tính
        self.product_input_model.dataChanged.connect(self.update_total_combo_value)
        self.product_input_model.rowsInserted.connect(self.update_total_combo_value)
        self.product_input_model.rowsRemoved.connect(self.update_total_combo_value)
        self.product_input_model.modelReset.connect(self.update_total_combo_value)

    def load_product_autocomplete_cache(self):
        """Kéo dữ liệu danh mục sản phẩm từ Service để cài đặt bộ gợi ý tự động"""
        self.product_lookup_dict.clear()
        self.product_suggest_list.clear()
        
        products = self.combo_service.fetch_product_autocomplete_list()
        for p in products:
            suggest_text = f"{p.product_code} - {p.product_name}"
            self.product_suggest_list.append(suggest_text)
            self.product_lookup_dict[suggest_text] = {
                "product_key": p.product_key,
                "product_code": p.product_code,
                "product_name": p.product_name
            }
            
        self.product_auto_complete = ProductAutoCompleter(self.product_suggest_list, self)
        self.product_input_view.setItemDelegateForColumn(0, self.product_auto_complete)
        self.product_input_view.setItemDelegateForColumn(1, self.product_auto_complete)

    def refresh_all_view(self):
        """Kéo dữ liệu mới nhất từ DB đồng bộ lên giao diện"""
        self.cache_data = self.combo_service.fetch_all_saved_combos()
        
        left_table_data = [
            [item["combo_name"], item["variant_name"], item["total_combo_value"]]
            for item in self.cache_data
        ]
        
        self.cv_version_model.refresh_data(left_table_data)
        self.product_input_model.update_model([]) 
        self.temp_total_value.setText("Tổng giá trị tạm tính")

    def combo_variant_select(self, index):
        """Lấy thông tin danh sách sản phẩm từ dòng combo được chọn đổ sang bảng phải"""
        row_index = index.row()

        if row_index < 0 or row_index >= len(self.cache_data):
            return
        
        selected_combo_variant = self.cache_data[row_index] 
        selected_product_list = selected_combo_variant["products"]

        self.product_input_model.update_model(selected_product_list)
        self.update_total_combo_value()

    def add_row(self):
        """LOGIC GỐC: Thêm dòng trống mới vào cuối bảng sản phẩm lẻ bên phải"""
        if self.cv_version_view.currentIndex().row() < 0:
            return
        self.product_input_model.add_blank_row()
        self.update_total_combo_value()

    def delete_row(self):
        """LOGIC GỐC: Xóa dòng sản phẩm lẻ đang được chọn trên bảng phải"""
        row_to_remove = self.product_input_view.currentIndex().row()
        if row_to_remove < 0:
            return
        self.product_input_model.remove_row(row_to_remove)
        self.update_total_combo_value()

    def update_total_combo_value(self):
        """Tính toán tổng tiền dựa trên các dòng sản phẩm hiển thị tại bảng phải"""
        current_products = self.product_input_model._data
        total_sum = sum(
            float(p.get("product_price", 0.0)) * int(p.get("product_quantity", 0))
            for p in current_products
        )
        total_sum_display = f"Tổng giá trị: {int(total_sum):,} đ" if total_sum else "Chưa cài giá" 
        self.temp_total_value.setText(total_sum_display)

    def on_save_changes_clicked(self):
        """Kích hoạt lưu các chỉnh sửa (thêm/sửa/xóa dòng lẻ) của Combo hiện tại xuống DB"""
        left_current_row = self.cv_version_view.currentIndex().row()
        if left_current_row < 0:
            return
            
        current_combo = self.cache_data[left_current_row]
        
        # Gửi dữ liệu cập nhật sang Service giải quyết bằng phương pháp Overwrite
        success = self.combo_service.update_single_combo(
            variant_key=current_combo["combo_variant_key"],
            composition_key=current_combo["combo_composition_key"],
            products_list=current_combo["products"]
        )
        
        if success:
            self.refresh_all_view()