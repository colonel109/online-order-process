import sys
from pathlib import Path
from PySide6.QtWidgets import QWidget, QApplication, QVBoxLayout, QTableView, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import QSize, Qt
import os
from sqlalchemy import select, func

sys.path.append(os.path.abspath(os.path.join('..')))

from src.database.structure import Combo, Variant, ComboVariant, ShopeeOrder, ComboDetail
from src.database.connector import db_connector
from src.data_model.table_view_model import TableViewModel #Nhận list


class ImportComboDetails(QWidget):
    def __init__(self):
        super().__init__()

        BASE_PATH = Path().cwd().parent
        DB_PATH = Path(BASE_PATH / "database.sqlite3")
        self.session = db_connector(DB_PATH)

        # Biến lưu trữ
        self.cv_cache = self.make_cache_data()


        # Thành phần UI
        # Widget hiển thị các combo chưa cài giá
        cv_version_label = QLabel("Combo chưa được cài giá")
        cv_version_view = QTableView()
        cv_version_layout = QVBoxLayout()
        cv_version_layout.addWidget(cv_version_label)
        cv_version_layout.addWidget(cv_version_view)

        # Widget hiển thị các sản phẩm trong combo
        product_add_label = QLabel("Thêm sản phẩm vào combo")
        product_add_view = QTableView()
        product_add_layout = QVBoxLayout()
        product_add_layout.addWidget(product_add_label)
        product_add_layout.addWidget(product_add_view)

        main_layout = QHBoxLayout()
        main_layout.addLayout(cv_version_layout)
        main_layout.addLayout(product_add_layout)

        # 1. Trích xuất các cột cần hiển thị ra một list mới
        display_data = [
            [
                item["combo_name"],
                item["variant_name"],
                f"{int(item["deal_price"]):,}đ"  # Định dạng tiền tệ cho đẹp mắt
            ]
            for item in  self.cv_cache
        ]

        # 2. Nạp thẳng mảng phẳng này vào TableViewModel của bạn
        self.cv_version_model = TableViewModel(
            data=display_data,
            column_names=["combo_name", "variant_name", "deal_price"]
        )
        cv_version_view.setModel(self.cv_version_model)

        self.setLayout(main_layout)
        self.setMinimumSize(QSize(1000, 700))

    def make_cache_data(self):
        # Lấy các phiên bản của combo variant đã map trong bảng combo_details
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

        # Dict này dùng để so sánh nhanh giá với dữ liệu trong đơn hàng
        # Cấu trúc {(combo_key, variant_key): total_combo_price),...}
        cv_compare_list = {}
        for version in cv_mapped_versions:
            cv_key_pair = (version.combo_key, version.variant_key)
            if cv_key_pair not in cv_compare_list:  # Nếu cặp đang được lặp qua chưa tồn tại trong dict thì gán nó làm key
                cv_compare_list[cv_key_pair] = set()  # Gán cho value của key hiện tại là một set
            cv_compare_list[cv_key_pair].add(
                version.total_combo_value)  # Nếu đã tồn tại thì gán tổng giá trị của version đó vào set (value của dict)

        # Lấy ra giá trị lớn nhất đang gán cho combo_composition_key trong database
        composition_key_available = self.session.scalar(select(func.max(ComboDetail.combo_composition_key)))

        # Khung list các dict chứa thông tin được import vào db
        cv_import_cache = []

        # Lấy các phiên bản của combo variant nằm trong bảng shopee_order
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

            # Flag đánh dấu version thiếu
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
                            "product_quantity": 0,
                            "product_price": 0.0
                        }
                    ]
                }
                cv_import_cache.append(combo_template)
        return cv_import_cache

app = QApplication(sys.argv)
window = ImportComboDetails()
window.show()
app.exec()
