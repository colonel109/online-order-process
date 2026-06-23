from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from PySide6.QtWidgets import QMessageBox


class TableViewModel(QAbstractTableModel):
    """
    Class này có vai trò là model cho tất cả các view có dạng bảng
    """
    def __init__(self, data, column_names: list):
        super().__init__()
        self._data = data
        self._column_names = column_names

    def rowCount(self, /, parent = ...):
        return len(self._data)

    def columnCount(self, /, parent = ...):
        return len(self._column_names)

    def data(self, index, role):
        """
        Hàm này tự động lặp qua các ô trong data, chỉ cần hướng dẫn nó lấy dữ liệu từ ô đầu tiên
        """
        if role == Qt.ItemDataRole.DisplayRole:
            row_data = self._data[index.row()]

            # Nếu data có dạng một list hoặc tup thì chỉ cần truy cập từng phần tử trong mỗi row
            if isinstance(row_data, (tuple, list)):
                value = row_data[index.column()]
                return str(value) if value is not None else ""

            # Nếu data là các object thì 
            col_attr = self._column_names[index.column()]
            part = col_attr.split(".")
            value = row_data
            for part in part:
                value = getattr(value, part, None)
                if value is None:
                    break
            return str(value) if value is not None else ""

    def headerData(self, section, orientation, /, role = ...):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self._column_names[section]
            return str(section + 1)
        return None
    
    def refresh_data(self, new_data):
        self.beginResetModel()
        self._data = new_data
        self.endResetModel()


class ProductInputModel(QAbstractTableModel):
    """
    Class này đóng vai trò là model cho table view, dành riêng cho việc chỉnh sửa các giá trị của sản phẩm
    khi người dùng thao tác thêm combo_detail
    """

    def __init__(self, cache_data=None, product_lookup=None):
        """
        Data nhận một list các dict, mỗi dict bao gồm thông tin của 01 sản phẩm được thêm
        Biến cache_data sẽ được trích xuất từ bảng
        """
        super().__init__()
        self._data = cache_data if cache_data is not None else [] # Trỏ đến dict chưa thông tin mà hàm combo_variant_select truyền vào
        self._headers = ["product_code", "product_name", "product_price", "product_quantity"]
        self._product_lookup = product_lookup if product_lookup is not None else {}

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)
    
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self._headers[section]
            return str(section + 1)
        return None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role not in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return None
        
        row_data = self._data[index.row()]
        col = index.column()
        
        if col == 0: return row_data["product_code"]
        if col == 1: return row_data["product_name"]
        if col == 2:
            price = row_data.get("product_price", 0.0)
            return f"{int(price):,}" if price else 0.0
        if col == 3: return row_data["product_quantity"]
        return None

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if index.isValid() and role == Qt.ItemDataRole.EditRole:
            row_idx = index.row()
            row_data = self._data[row_idx]
            col = index.column()
            
            if col in (0, 1):
                if value in self._product_lookup:
                    info = self._product_lookup[value]
                    row_data["product_key"] = info["product_key"]
                    row_data["product_code"] = info["product_code"]
                    row_data["product_name"] = info["product_name"]

                    start_index = self.index(row_idx, 0)
                    end_index = self.index(row_idx, 3)
                    self.dataChanged.emit(start_index, end_index, [Qt.ItemDataRole.DisplayRole])

                    return True
                else:
                    if not value.strip():
                        return False
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Icon.Critical)
                    msg.setWindowTitle("Lỗi nhập liệu")
                    msg.setText(f"Sản phẩm '{value}' không tồn tại trong hệ thống!")
                    msg.setInformativeText("Vui lòng chọn chính xác sản phẩm từ danh sách gợi ý xổ xuống.")
                    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                    msg.exec()

            elif col ==2:
                try: row_data["product_price"] = float(value) if value else 0.0
                except ValueError: row_data["product_price"] = 0.0
            elif col ==3:
                try: row_data["product_quantity"] = int(value) if value else 0
                except ValueError: row_data["product_quantity"] = 0
            return True
        return False
    
    def flags(self, index):
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable
    
    def add_blank_row(self):
        position = len(self._data)
        self.beginInsertRows(QModelIndex(), position, position)
        self._data.append({
            "product_key": None,
            "product_code": "",
            "product_name": "",
            "product_quantity": 1,
            "product_price": 0.0
        })
        self.endInsertRows()
    
    def remove_row(self, row_index):
        if row_index < 0 or row_index >= len(self._data):
            return
        self.beginRemoveRows(QModelIndex(), row_index, row_index)
        self._data.pop(row_index)
        self.endRemoveRows()

    def update_model(self, new_data):
        self.beginResetModel()
        self._data = new_data
        self.endResetModel()