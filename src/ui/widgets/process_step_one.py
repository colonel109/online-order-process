from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QTableView, QPushButton
from sqlalchemy import select, update
from src.database.structure import ShopeeOrder, Combo, Variant, ComboVariant
from src.data_model.table_view_model import TableViewModel


class AddComboVariant(QWidget):
    def __init__(self, session, parent=None):
        super().__init__(parent)

        # Kết nối với database
        self.session = session

        # Khởi tạo các biến lưu trữ
        self.order_cv_list = [] # Lưu trữ các cặp combo variant có trong đơn hàng
        self.missing_cv_list = [] # Lưu trữ các cặp combo variant chuẩn bị được thêm mới
        self.new_combo_count = None

        # Thông tin và các nút điều khiển
        self.noti_label = QLabel()
        self.cfm_button = QPushButton("Thêm vào database")
        self.cfm_button.setMaximumWidth(150)
        self.dcl_button = QPushButton("Huỷ")
        self.dcl_button.setMaximumWidth(150)
        self.next_step_btn = QPushButton("Sang bước tiếp theo")
        self.next_step_btn.setVisible(False)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.cfm_button)
        btn_layout.addWidget(self.dcl_button)
        btn_layout.addWidget(self.next_step_btn)
        btn_layout.addStretch()

        control_info_layout = QVBoxLayout()
        control_info_layout.addWidget(self.noti_label)
        control_info_layout.addLayout(btn_layout)

        # View hiển thị các combo có trong đơn hàng
        self.cv_order_title = QLabel()
        self.cv_order_model = None
        self.cv_order_view = QTableView()
        cv_order_layout = QVBoxLayout()
        cv_order_layout.addWidget(self.cv_order_title)
        cv_order_layout.addWidget(self.cv_order_view)

        # View hiển thị các combo chưa được thêm
        self.cv_missing_title = QLabel()
        self.cv_missing_model = None
        self.cv_missing_view = QTableView()
        self.cv_import_success = QLabel("Toàn bộ combo mới đã được nhập thành công!")
        cv_missing_layout = QVBoxLayout()
        cv_missing_layout.addWidget(self.cv_missing_title)
        cv_missing_layout.addWidget(self.cv_missing_view)

        # Layout hiển thị
        display_layout = QHBoxLayout()
        display_layout.addLayout(cv_order_layout)
        display_layout.addLayout(cv_missing_layout)

        #Layout chính
        main_layout = QVBoxLayout()
        main_layout.addLayout(control_info_layout)
        main_layout.addLayout(display_layout)

        self.setLayout(main_layout)
        self.init_signal()
        self.process_data()

    def init_signal(self):
        self.cfm_button.pressed.connect(self.confirm_and_save)
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
        self.order_cv_list.extend(list(cv_versions_set))

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
                exist_combos[combo_name] = combo_obj  # thêm luôn {Tên combo: Object} vào những combo đã tạo

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
            current_cv_key_pair = (combo_obj.combo_key,
                                   variant_obj.variant_key if variant_obj else None)  # Dùng để import vào db

            # Kiểm tra xem tup trên đã xuất hiện trong created_cv_pair đã kéo về trước đó chưa
            if current_cv_key_pair not in created_cv_pair:
                combo_variant_obj = ComboVariant(combo_link=combo_obj, variant_link=variant_obj)
                self.session.add(combo_variant_obj)
                created_cv_pair.add(current_cv_key_pair)  # Thêm luôn vào tup created để tránh trùng lặp
                self.missing_cv_list.append((combo_obj.combo_name,
                                              variant_obj.variant_name if variant_obj else None))  # Dùng để hiển thị các combo sắp được thêm
            else:
                pass  # Bỏ qua nếu đã tạo

        # Tạo model và gán vào view sau khi đã xử lí xong
        self.cv_order_model = TableViewModel(
            data=self.order_cv_list,
            column_names=["combo_name", "variant_name"]
        )
        self.cv_order_view.setModel(self.cv_order_model)
        order_combo_count = len(self.order_cv_list)
        self.cv_order_title.setText(f"Combo có trong đơn hàng: {order_combo_count}")

        if not self.missing_cv_list:
            self.noti_label.setText("Không có combo mới cần thêm, hãy tiếp tục")
            self.cv_missing_title.setText("Không tìm thấy combo mới")
            self.write_keys()
            self.next_step_btn.setVisible(True)
            self.cfm_button.setVisible(False)
            self.dcl_button.setVisible(False)
        else:
            self.cv_missing_model = TableViewModel(
                data=self.missing_cv_list,
                column_names=["combo_name", "variant_name"]
            )
            self.cv_missing_view.setModel(self.cv_missing_model)
            self.new_combo_count = len(self.missing_cv_list)
            self.cv_missing_title.setText(f"Combo cần được thêm: {self.new_combo_count}")
            self.noti_label.setText(f"Phát hiện {self.new_combo_count} combo cần thêm")

    def confirm_and_save(self):
        try:
            self.session.commit()
            self.write_keys()
            self.missing_cv_list.clear()
            self.next_step_btn.setVisible(True)
            self.cfm_button.setVisible(False)
            self.dcl_button.setVisible(False)
            self.noti_label.setText(f"Đã thêm {self.new_combo_count} combo mới!")
            self.cv_missing_title.setText("Không tìm thấy combo mới")
        except Exception as e:
            self.session.rollback()
            print(e)

    def decline_and_revert(self):
        try:
            self.session.rollback()
        except Exception as e:
            print(e)

    def write_keys(self):
        """
        Hàm này được dùng để update các key của combo và variant vừa tạo vào database
        """
        subquery_combo = (
            select(Combo.combo_key)
            .where(Combo.combo_name == ShopeeOrder.combo_name)
            .scalar_subquery()
        )

        self.session.execute(
            update(ShopeeOrder)
            .where(ShopeeOrder.combo_key.is_(None))  # Chỉ cập nhật dòng chưa có ID
            .values(combo_key=subquery_combo)
        )

        subquery_variant = (
            select(Variant.variant_key)
            .where(Variant.variant_name == ShopeeOrder.variant_name)
            .scalar_subquery()
        )

        self.session.execute(
            update(ShopeeOrder)
            .where(ShopeeOrder.variant_key.is_(None))
            .where(ShopeeOrder.variant_name.is_not(None))
            .values(variant_key=subquery_variant)
        )

        self.session.commit()