from PySide6.QtWidgets import QWidget, QTableView, QVBoxLayout, QLabel, QHBoxLayout
from PySide6.QtCore import Qt
from sqlalchemy import select
from src.data_model.table_view_model import TableViewModel
from src.database.structure import ShopeeOrder


class OrderDisplayer(QWidget):
    def __init__(self, session):
        super().__init__()

        # View và kết nối
        self.view = QTableView()
        self.session = session

        # Data model
        self.order_data_model = None

        # Layout
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel("<b>Danh sách đơn hàng</b>"))
        self.order_count_displayer = QLabel()
        info_layout.addWidget(self.order_count_displayer, alignment=Qt.AlignmentFlag.AlignRight)

        layout = QVBoxLayout()
        layout.addLayout(info_layout)
        layout.addWidget(self.view)
        self.setLayout(layout)

    def fetch_order_data(self):
        """
        Hàm này có nhiệm vụ lấy thông tin từ bảng shopee_orders sau đó lấy các list chứa những 
        combo, variant và price độc nhất để truyền vào view model
        """

        # Lấy data set chứa toàn bộ thông tin cần thiết từ bảng shopee_orders
        data_orders = self.session.scalars(select(ShopeeOrder)).all()
        
        if not data_orders:
            return
        
        # Hiển thị số đơn hàng được tải
        order_count = len(data_orders)
        self.order_count_displayer.setText(f"Đã tải {order_count} đơn hàng")    

        # Truyền vào view model, đây là bảng đơn hàng gốc
        columns = ["order_id", "package_id", "order_date", "order_status", "combo_name", "variant_name",
                   "deal_price", "quantity","total_buyer_payment_amount", "source_file"]

        self.order_data_model = TableViewModel(
            data=data_orders,
            column_names=columns
        )

        # Set model cho view chính
        self.view.setModel(self.order_data_model)
        
        return data_orders