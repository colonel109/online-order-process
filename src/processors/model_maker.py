from src.data_model.table_view_model import TableViewModel
from src.database.structure import ShopeeOrder
from sqlalchemy import select


def order_model(session):
    """
    Hàm này trả về datamodel chứa thông tin đơn hàng
    """
    # Kết nối
    session = session

    # Lấy data set chứa toàn bộ thông tin cần thiết từ bảng shopee_orders
    data_orders = session.scalars(select(ShopeeOrder)).all()
    
    if not data_orders:
        return

    row_count = len(data_orders)
    
    # Truyền vào view model, đây là bảng đơn hàng gốc
    columns = ["order_id", "package_id", "order_date", "order_status", "combo_name", "variant_name",
                "deal_price", "quantity","total_buyer_payment_amount", "source_file"]

    data_model = TableViewModel(
        data=data_orders,
        column_names=columns
    )

    return data_model, row_count