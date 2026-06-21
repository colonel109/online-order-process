import sys
from pathlib import Path
import os
from PySide6.QtWidgets import QWidget, QApplication, QVBoxLayout, QTableView, QLabel, QHBoxLayout
from PySide6.QtCore import QSize, Qt
from sqlalchemy import select, func

sys.path.append(os.path.abspath(os.path.join('..')))

from src.database.structure import Combo, Variant, ComboVariant, ShopeeOrder, ComboDetail
from src.database.connector import db_connector
from src.data_model.table_view_model import TableViewModel  # Nhận list


class ImportComboDetails(QWidget):
    def __init__(self):
        super().__init__()

        BASE_PATH = Path().cwd().parent
        DB_PATH = Path(BASE_PATH / "database.sqlite3")
        session = db_connector(DB_PATH)

        # Truyền session
        self.session = session

        # Biến lưu trữ danh sách các combo thiếu định mức giá để nạp vào Model
        self.required_new_composition = []

        # Thành phần UI
        # Widget hiển thị các combo chưa cài giá
        self.cv_version_label = QLabel("Combo chưa được cài giá")
        self.cv_version_view = QTableView()
        # Cho phép chọn full dòng để trải nghiệm người dùng tốt hơn
        self.cv_version_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

        cv_version_layout = QVBoxLayout()
        cv_version_layout.addWidget(self.cv_version_label)
        cv_version_layout.addWidget(self.cv_version_view)

        # Widget hiển thị các sản phẩm trong combo
        self.product_add_label = QLabel("Thêm sản phẩm vào combo (Hãy chọn một combo bên trái)")
        self.product_add_view = QTableView()
        product_add_layout = QVBoxLayout()
        product_add_layout.addWidget(self.product_add_label)
        product_add_layout.addWidget(self.product_add_view)

        main_layout = QHBoxLayout()
        main_layout.addLayout(cv_version_layout)
        main_layout.addLayout(product_add_layout)

        self.setLayout(main_layout)
        self.setMinimumSize(QSize(1000, 700))

        # Khởi chạy xử lý dữ liệu và cấu hình sự kiện
        self.process_data()
        self.init_signals()

    def process_data(self):
        """
        Đối soát dữ liệu giữa ShopeeOrder và ComboDetail đa phiên bản
        Lọc ra các combo có giá bán Shopee chưa được cấu hình định mức hệ thống.
        """
        # 1. Truy vấn định mức giá hiện tại của hệ thống (Gom nhóm theo phiên bản công thức)
        stmt2 = (
            select(
                ComboVariant.combo_key,
                ComboVariant.variant_key,
                ComboDetail.combo_variant_key,
                Combo.combo_name,
                Variant.variant_name,
                func.sum(ComboDetail.product_price * ComboDetail.product_quantity).label("total_combo_price")
            )
            .join(ComboVariant, ComboDetail.combo_variant_key == ComboVariant.combo_variant_key)
            .join(Combo, ComboVariant.combo_key == Combo.combo_key)
            .outerjoin(Variant, ComboVariant.variant_key == Variant.variant_key)
            .group_by(
                ComboVariant.combo_key,
                ComboVariant.variant_key,
                ComboDetail.combo_variant_key,
                ComboDetail.combo_composition_key,  # Gom theo phiên bản định mức lẻ
                Combo.combo_name,
                Variant.variant_name
            )
        )
        result_system = self.session.execute(stmt2).all()

        # Tổ chức kho tra cứu nhanh bằng Dictionary
        system_prices = {}
        cv_info_map = {}

        for r in result_system:
            key_pair = (r.combo_key, r.variant_key)
            if key_pair not in system_prices:
                system_prices[key_pair] = set()
                cv_info_map[key_pair] = {
                    "combo_variant_key": r.combo_variant_key,
                    "combo_name": r.combo_name,
                    "variant_name": r.variant_name
                }
            system_prices[key_pair].add(r.total_combo_price)

        # 2. Lấy dữ liệu các tổ hợp giá độc nhất từ đơn hàng Shopee
        stmt3 = select(
            ShopeeOrder.combo_key,
            ShopeeOrder.variant_key,
            ShopeeOrder.combo_name,
            ShopeeOrder.variant_name,
            ShopeeOrder.deal_price
        ).distinct()
        result_order = self.session.execute(stmt3).all()

        # 3. Logic đối soát tìm giá thiếu/lệch
        self.required_new_composition.clear()

        for order in result_order:
            key_pair = (order.combo_key, order.variant_key)
            shopee_price = order.deal_price

            # Trường hợp đã từng cài giá định mức -> Check xem khớp phiên bản nào không
            if key_pair in system_prices:
                if shopee_price not in system_prices[key_pair]:
                    info = cv_info_map[key_pair]
                    self.required_new_composition.append((
                        info["combo_variant_key"],
                        order.combo_name,
                        order.variant_name if order.variant_name else "-",
                        shopee_price
                    ))
            # Trường hợp mới tinh -> Bảng ComboDetail trống trơn
            else:
                cv_key = self.session.scalar(
                    select(ComboVariant.combo_variant_key)
                    .where(ComboVariant.combo_key == order.combo_key)
                    .where(ComboVariant.variant_key == order.variant_key)
                )
                if cv_key:  # Đề phòng đơn hàng chứa combo chưa tạo ComboVariant
                    self.required_new_composition.append((
                        cv_key,
                        order.combo_name,
                        order.variant_name if order.variant_name else "-",
                        shopee_price
                    ))

        # 4. Đổ danh sách thiếu giá lên TableView bên trái
        # Tạo list hiển thị chỉ gồm chữ phục vụ người dùng (Ẩn id số đi)
        display_list = [
            [row[1], row[2], f"{int(row[3]):,}đ"]
            for row in self.required_new_composition
        ]

        self.cv_version_model = TableViewModel(
            data=display_list,
            column_names=["Tên Combo", "Phân loại", "Mức giá Shopee yêu cầu cài"]
        )
        self.cv_version_view.setModel(self.cv_version_model)
        self.cv_version_label.setText(f"Combo chưa được cài giá: {len(display_list)} mã")

    def init_signals(self):
        """Kết nối sự kiện khi người dùng click tương tác trên bảng"""
        self.cv_version_view.clicked.connect(self.on_combo_selected)

    def on_combo_selected(self, index):
        """Hành động xảy ra khi click chọn một dòng combo thiếu giá"""
        row_idx = index.row()
        if row_idx < 0 or row_idx >= len(self.required_new_composition):
            return

        # Bốc ra các dữ liệu thực tế (bao gồm ID ẩn) của dòng được chọn
        selected_cv = self.required_new_composition[row_idx]
        combo_variant_key = selected_cv[0]
        combo_name = selected_cv[1]
        variant_name = selected_cv[2]
        deal_price = selected_cv[3]

        # Thay đổi nhãn thông báo bên bảng phải để chuẩn bị thêm sản phẩm
        info_text = f"Đang cài định mức cho: {combo_name} [{variant_name}] với mục tiêu tổng giá: {int(deal_price):,}đ"
        self.product_add_label.setText(info_text)

        # 💡 Chỗ này bạn có thể nạp Model danh sách sản phẩm lẻ để chuẩn bị tích chọn
        print(f"DEBUG: Người dùng muốn nạp sản phẩm cho combo_variant_key={combo_variant_key} với giá {deal_price}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImportComboDetails()
    window.show()
    sys.exit(app.exec())