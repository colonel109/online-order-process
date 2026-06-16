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
            row_object = self._data[index.row()]
            col_attr = self._column_names[index.column()]

            value = getattr(row_object, col_attr, "")
            return str(value)

    def headerData(self, section, orientation, /, role = ...):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self._column_names[section]
            return section + 1
        return None