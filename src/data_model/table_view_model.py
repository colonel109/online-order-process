from PySide6.QtCore import QAbstractTableModel, Qt


class TableViewModel(QAbstractTableModel):
    """
    Class này có vai trò là model cho tất cả các view có dạng bảng
    """
    def __init__(self, data, column_names):
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

            value = getattr(row_data, col_attr, "")
            return str(value)

    def headerData(self, section, orientation, /, role = ...):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self._column_names[section]
            return str(section + 1)
        return None