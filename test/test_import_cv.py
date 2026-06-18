import sys
from pathlib import Path
from PySide6.QtWidgets import QWidget, QApplication, QVBoxLayout, QTableView, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import QSize, Qt
import os
from sqlalchemy import select

sys.path.append(os.path.abspath(os.path.join('..')))

from src.database.structure import Combo, Variant, ComboVariant, ShopeeOrder
from src.database.connector import db_connector
from src.data_model.table_view_model import TableViewModel


# Đây là dữ liệu đơn hàng được truyển vào mỗi lần nút xử lí đơn hàng được nhấn để buộc lấy dữ liệu mới
# Các widget sẽ tự xử lí dữ liệu và hiển thị lên phần phềm

class ImportComboVariant(QWidget):
    def __init__(self):
        super().__init__()

        BASE_PATH = Path().cwd().parent
        DB_PATH = Path(BASE_PATH / "database.sqlite3")
        session = db_connector(DB_PATH)

        # Truyền session
        self.session = session
        
        # Khởi tạo các biến lưu trữ
        self.cv_version_list = [] # Lưu trữ các cặp combo variant có trong đơn hàng
        self.cv_pair_name_add = [] # Lưu trữ các cặp combo variant chuẩn bị được thêm mới

        # Chạy hàm
        self.process_data()

        # Mô hình dữ liệu
        self.cv_versions_set_model = TableViewModel(
            data=self.cv_version_list,
            column_names=["combo_name", "variant_name"]
        )
        
        self.cv_pair_name_model = TableViewModel(
            data=self.cv_pair_name_add,
            column_names=["combo_name", "variant_name"]
        )

        # Table view
        self.table_view = QTableView()
        self.table_view.setModel(self.cv_pair_name_model)

        # Layout chứa nút, thông tin

        self.info_label = QLabel()
        self.info_label.setText(f"Có {len(self.cv_pair_name_add)} nhóm combo mới sẽ được thêm vào cơ sở dữ liệu, xác nhận?")

        self.cfm_button = QPushButton("Xác nhận")
        self.cfm_button.setMaximumWidth(100)
        self.dcl_button = QPushButton("Từ chối")
        self.dcl_button.setMaximumWidth(100)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.cfm_button)
        btn_layout.addWidget(self.dcl_button)
        btn_layout.addStretch()

        info_layout = QVBoxLayout()
        info_layout.addWidget(self.info_label)
        info_layout.addLayout(btn_layout)
        
        # Layout chính 
        main_layout = QVBoxLayout()
        main_layout.addLayout(info_layout)
        main_layout.addWidget(self.table_view)
        
        # Layout chính 
        self.setLayout(main_layout)
       
        # Kích cỡ cửa sổ
        self.setMinimumSize(QSize(600, 400))

        # Kết nối
        self.init_signal()

    def init_signal(self):
        self.cfm_button.pressed.connect(self.comfirm_and_save)
        self.dcl_button.pressed.connect(self.decline_and_revert)

    def process_data(self):
        """
        Hàm này có nhiệm vụ biến đổi dữ liệu từ list các tup chứa những phiên bản khác nhau của combo variant
        Tạo ra một set các combo và variant riêng biệt
        """
        stmt = select(ShopeeOrder.combo_name, ShopeeOrder.variant_name).distinct()

        # Trả về một set các tup gồm combo_name, variant_name không trùng nhau và gán luôn vào biến lưu trữ để hiển thị
        cv_versions_set = {
            (cv.combo_name, cv.variant_name) for cv in
            self.session.execute(stmt).all()
        }

        # Chuyển về dạng list gán vào biến lưu trữ để hiển thị trong model
        self.cv_version_list.extend(list(cv_versions_set))

        # Các combo có trong đơn hàng chuẩn bị được tạo (string)
        input_combos = {c[0] for c in cv_versions_set if c[0]}
        input_variant = {v[1] for v in cv_versions_set if v[1] and v[1].strip()}

        # Truy vấn lại trong database xem combo/variant hoặc cặp đó được tạo trước đó chưa
        # Trả về dict có dạng: {Tên combo/variant: object}
        # Dict chỉ được tạo khi tên của combo/variant trùng với tên trong db
        exist_combos = {
            c.combo_name: c
            for c in self.session.scalars(select(Combo).where(Combo.combo_name.in_(input_combos))).all()
        }

        exist_variant = {
            v.variant_name: v
            for v in self.session.scalars(select(Variant).where(Variant.variant_name.in_(input_variant))).all()
        }

        # Trả về một set có dạng {(combo_key, variant_key), (...), ...} 
        created_cv_pair = {
            (cv.combo_key, cv.variant_key)
            for cv in self.session.scalars(select(ComboVariant)).all()
        }

        # Lấy một set các tup chứa các combo và variant cần import
        unique_import_cv = {
            (cv[0], cv[1]) for cv in cv_versions_set
        }

        # Lặp qua trừng combo và variant trong set unique_import_cv
        for combo_name, variant_name in unique_import_cv:
            # Trường hợp tên trong danh sách mới trùng với key (name) của dict được tạo trước đó
            # Gán luôn biến combo_obj thành obj có trong database
            if combo_name in exist_combos:
                combo_obj = exist_combos[combo_name]
            # Trường hợp chưa tạo tên biến thì gán combo_obj với một object mới và đẩy vào db 
            else:
                combo_obj = Combo(combo_name=combo_name)
                self.session.add(combo_obj)
                exist_combos[combo_name] = combo_obj # thêm luôn {Tên combo: Object} vào những combo đã tạo

            # Vì variant có thể không có dữ liệu nên object mặc định là None
            variant_obj = None

            # Nếu tìm thấy variant trong unique_import_cv thì mới tạo object
            # Xử lí tương tự như combo
            if variant_name:
                if variant_name in exist_variant:
                    variant_obj = exist_variant[variant_name]
                else:
                    variant_obj = Variant(variant_name=variant_name)
                    self.session.add(variant_obj)
                    exist_variant[variant_name] = variant_obj

            self.session.flush()

            # Đối với mỗi cặp combo và variant đang lặp, trích xuất dữ liệu từ object của chúng và ghép lại thành một tup
            current_cv_key_pair = (combo_obj.combo_key, variant_obj.variant_key if variant_obj else None) # Dùng để import vào db

            # Kiểm tra xem tup trên đã xuất hiện trong created_cv_pair đã kéo về trước đó chưa 
            if current_cv_key_pair not in created_cv_pair:
                combo_variant_obj = ComboVariant(combo_link=combo_obj, variant_link=variant_obj)
                self.session.add(combo_variant_obj)
                created_cv_pair.add(current_cv_key_pair) # Thêm luôn vào tup created để tránh trùng lặp
                self.cv_pair_name_add.append((combo_obj.combo_name, variant_obj.variant_name if variant_obj else None)) # Dùng để hiển thị các combo sắp được thêm
            else:
                pass # Bỏ qua nếu đã tạo

    def comfirm_and_save(self):
        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            print(e)
        
    def decline_and_revert(self):
        try:
            self.session.rollback()
        except Exception as e:
            print(e)


app = QApplication(sys.argv)
window = ImportComboVariant()
window.show()
app.exec()