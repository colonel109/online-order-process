from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex


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

    def __init__(self, cache_data=None):
        """
        Data nhận một list các dict, mỗi dict bao gồm thông tin của 01 sản phẩm được thêm
        Biến cache_data sẽ được trích xuất từ bảng
        """
        super().__init__()
        self._data = cache_data if cache_data is not None else []
        self._headers = ["product_code", "product_name", "product_price", "product_quantity"]

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)
    
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._headers[section]
        return None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role not in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return None
        
        row_data = self._data[index.row()]
        col = index.column()
        
        if col == 0: return row_data["product_code"]
        if col == 1: return row_data["product_name"]
        if col == 2: return row_data["product_price"]
        if col == 3: return row_data["product_quantity"]
        return None

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if index.isValid() and role == Qt.ItemDataRole.EditRole:
            row_data = self._data[index.row()]
            col = index.column()
            
            if col == 0: row_data["product_code"] = value
            elif col == 1: row_data["product_name"] = value
            elif col == 2: row_data["product_price"] = float(value) if value else 0.0
            elif col == 3: row_data["product_quantity"] = int(value) if value else 0
            
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])
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