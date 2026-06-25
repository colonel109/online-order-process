from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from PySide6.QtWidgets import QMessageBox
from PySide6.QtGui import QColor


class TableViewModel(QAbstractTableModel):
    """
    Class này có vai trò là model cho tất cả các view có dạng bảng
    """
    def __init__(self, data, column_names: list, cache=None):
        super().__init__()
        self._data = data if data else []
        self._column_names = column_names
        if cache is not None:
            self._cache_reference = cache

    def rowCount(self, /, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, /, parent=QModelIndex()):
        return len(self._column_names)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        """
        Hàm này tự động lặp qua các ô trong dữ liệu để vẽ giao diện và nhuộm màu sắc
        """
        if not index.isValid():
            return None

        row_idx = index.row()
        col_idx = index.column()

        if row_idx >= len(self._data):
            return None

        row_data = self._data[row_idx]

        if role == Qt.ItemDataRole.DisplayRole:
            if isinstance(row_data, (tuple, list)):
                value = row_data[col_idx]
                return str(value) if value is not None else ""

            col_attr = self._headers[col_idx] if hasattr(self, "_headers") else self._column_names[col_idx]
            parts = col_attr.split(".")
            value = row_data
            for part in parts:
                value = getattr(value, part, None)
                if value is None:
                    break
            return str(value) if value is not None else ""

        elif role == Qt.ItemDataRole.BackgroundRole:
            if index.column() == 2:
                if hasattr(self, "_cache_reference") and row_idx < len(self._cache_reference):
                    combo_item = self._cache_reference[row_idx]
                    product_list = combo_item.get("products", [])
                    has_empty_code = (
                        len(product_list) == 0 or
                        any(not str(p.get("product_code", "")).strip() for p in product_list)

                    )

                    deal_price = float(combo_item.get("deal_price", 0.0))

                    total_config_value = sum(
                        float(p.get("product_price", 0.0)) * int(p.get("product_quantity", 0))
                        for p in combo_item.get("products", [])
                    )

                    if abs(total_config_value - deal_price) < 0.01 and not has_empty_code:
                        return QColor("#467235")
                    else:
                        return QColor("#AA1C41")

        return None

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
                    target_code = info["product_code"]

                    for i, existing_row in enumerate(self._data):
                        if i != row_idx and existing_row.get("product_code") == target_code:
                            msg = QMessageBox()
                            msg.setIcon(QMessageBox.Icon.Warning)
                            msg.setWindowTitle("Trùng lặp sản phẩm")
                            msg.setText(f"Sản phẩm với mã '{target_code}' đã được thêm vào combo này!")
                            msg.setInformativeText(
                                "Vui lòng không nhập trùng một sản phẩm nhiều lần. Thay vào đó hãy tăng số lượng của dòng đã có.")
                            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                            msg.exec()

                            return False

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
            start_index = self.index(row_idx, 0)
            end_index = self.index(row_idx, 3)
            self.dataChanged.emit(start_index, end_index, [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole])
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