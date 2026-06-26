from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QTableView, QPushButton, QFrame
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
from sqlalchemy import select, update
from src.database.structure import ShopeeOrder, Combo, Variant, ComboVariant
from src.data_model.table_view_model import TableViewModel
from src.ui.widgets.message import CustomMessage
from resources import resources_rc


class AddComboVariant(QWidget):
    def __init__(self, session, parent=None):
        super().__init__(parent)

        # Kết nối với database
        self.session = session

        # Khởi tạo các biến lưu trữ
        self.order_cv_list = [] # Lưu trữ các cặp combo variant có trong đơn hàng
        self.missing_cv_list = [] # Lưu trữ các cặp combo variant chuẩn bị được thêm mới
        self.new_combo_count = None
        
        # Thông báo hiện kết quả, nút tuỳ chọn sau khi người dùng ấn nút bắt đầu
        self.custom_message_frame = CustomMessage()

        # Nút bắt đầu xử lí dữ liệu 
        noti_label = QLabel("<b>Vui lòng nhấn nút bắt đầu</b>")

        self.begin_process_frame = QFrame()
        self.begin_process_frame.setObjectName("begin_process_frame")
        begin_process_layout = QVBoxLayout(self.begin_process_frame)
        self.begin_process_btn = QPushButton(
            QIcon(":/resource/icons/zoom-scan.svg"),
            "Bắt đầu quét các cặp combo có trong đơn hàng",
            self
        )
        begin_process_layout.addWidget(noti_label)
        begin_process_layout.addWidget(self.begin_process_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        self.begin_process_frame.setStyleSheet("""
            .QFrame {
                border-radius: 4px; 
                background-color: #2a2a2a;
            }
            QPushButton {
                background-color: #73cefc;
                color: black;            
            }
            """)

        # View hiển thị các combo có trong đơn hàng
        self.cv_order_title = QLabel("Combo có trong đơn hàng")

        self.cv_order_model = TableViewModel( # Tạo model và gán vào view
            data=[],
            column_names=["combo_name", "variant_name"]
        )
        self.cv_order_view = QTableView()
        self.cv_order_view.setModel(self.cv_order_model)

        cv_order_layout = QVBoxLayout()
        cv_order_layout.addWidget(self.cv_order_title)
        cv_order_layout.addWidget(self.cv_order_view)

        # View hiển thị các combo chưa được thêm
        self.cv_missing_title = QLabel("Các cặp combo cần thêm")

        self.cv_missing_model = TableViewModel( # Tạo model và gán vào view
            data=[],
            column_names=["combo_name", "variant_name"]
        )
        self.cv_missing_view = QTableView()
        self.cv_missing_view.setModel(self.cv_missing_model)

        cv_missing_layout = QVBoxLayout()
        cv_missing_layout.addWidget(self.cv_missing_title)
        cv_missing_layout.addWidget(self.cv_missing_view)

        # Layout hiển thị
        display_layout = QHBoxLayout()
        display_layout.addLayout(cv_order_layout)
        display_layout.addLayout(cv_missing_layout)

        #Layout chính
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.custom_message_frame, stretch=0)
        main_layout.addWidget(self.begin_process_frame, stretch=0)
        main_layout.addLayout(display_layout, stretch=1)

        self.setLayout(main_layout)
        self.init_signal()

    def init_signal(self):
        self.begin_process_btn.clicked.connect(self.process_and_display_data)
        self.custom_message_frame.confirm_button.clicked.connect(self.confirm_and_save)
        self.custom_message_frame.decline_button.clicked.connect(self.decline_and_revert)
        self.custom_message_frame.continue_button.clicked.connect(self.press_and_disable)

    def process_and_display_data(self):
        """
        Hàm này có nhiệm vụ biến đổi dữ liệu từ list các tup chứa những phiên bản khác nhau của combo variant
        Tạo ra một set các combo và variant riêng biệt
        Hiển thị kết quả lên màn hình
        """
        stmt = select(ShopeeOrder.combo_name, ShopeeOrder.variant_name).distinct()

        # Trả về một set các tup gồm combo_name, variant_name không trùng nhau và gán luôn vào biến lưu trữ để hiển thị
        cv_versions_set = {
            (cv.combo_name, cv.variant_name) for cv in
            self.session.execute(stmt).all()
        }

        # Xoá dữ liệu trong biến trước khi chạy
        self.order_cv_list.clear()
        self.missing_cv_list.clear()

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

        # Hiển thị dữ liệu
        self.cv_order_model.refresh_data(self.order_cv_list) # Nạp dữ liệu mới vào model
        order_combo_count = len(self.order_cv_list)
        self.cv_order_title.setText(f"Combo có trong đơn hàng: {order_combo_count}")

        self.begin_process_frame.hide()

        if not self.missing_cv_list:
            self.write_keys()
            self.cv_missing_title.setText("Không tìm thấy combo mới")
            self.custom_message_frame.show_success_message(text="Không có combo mới")
        else:
            self.new_combo_count = len(self.missing_cv_list)
            self.cv_missing_title.setText(f"Các cặp combo cần thêm: {self.new_combo_count}")
            self.cv_missing_model.refresh_data(self.missing_cv_list)
            self.custom_message_frame.show_action_message(
                text=f"{len(self.missing_cv_list)} combo mới sẽ được thêm vào cơ sở dữ liệu, vui lòng xác nhận", 
                confirm_btn_text="Xác nhận",
                decline_button_text="Từ chối"
            )

    def confirm_and_save(self):
        try:
            self.write_keys()
            self.session.commit()

            self.cv_missing_model.refresh_data(
                self.missing_cv_list
            )
            self.cv_missing_title.setText("Đã thêm đầy đủ combo!")
            self.custom_message_frame.show_success_message(text=f"Đã thêm thành công {len(self.missing_cv_list)} combo mới vào cơ sở dữ liệu!")
            self.missing_cv_list.clear()
        except Exception as e:
            self.session.rollback()
            print(e)

    def decline_and_revert(self):
        try:
            self.session.rollback()
            self.order_cv_list.clear()
            self.missing_cv_list.clear()
            self.cv_order_title.clear()
            self.cv_missing_title.clear()

            self.cv_order_model.refresh_data(self.order_cv_list)
            self.cv_missing_model.refresh_data(self.missing_cv_list)
            self.custom_message_frame.hide()
            self.begin_process_frame.show()
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
    
    def press_and_disable(self):
        """
        Hàm này phụ trách việc tắt và đổi tên nút tiếp tục sau khi người dùng nhấn vào
        Tránh việc chạy lại dữ liệu của bước sau nhiều lần
        """
        
        self.custom_message_frame.continue_button.setText("Đã hoàn thành bước 1")
        self.custom_message_frame.continue_button.setEnabled(False)