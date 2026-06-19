from PySide6.QtWidgets import QFileDialog
from pathlib import Path

class OpenOrderFile(QFileDialog):
    def __init__(self, base_path):
        super().__init__()

        self.setWindowTitle("Chọn tệp đơn hàng")
        self.setDirectory(str(base_path))

        # Bộ lọc
        filters = "Tệp Excel (*.xlsx *.xls);;Tệp Csv (*.csv);;Tất cả các tệp (*)"
        self.setNameFilter(filters)

        # Cho phép chọn nhiều file
        self.setFileMode(QFileDialog.FileMode.ExistingFiles)
        self.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
    
    def get_file_list(self):
        if self.exec():
            return self.selectedFiles()
        
        return []
        

class OpenOrderFolder(QFileDialog):
    def __init__(self, base_path):
        super().__init__()

        self.setWindowTitle("Chọn thư mục chứa đơn hàng")
        self.setDirectory(str(base_path))

        self.setFileMode(QFileDialog.FileMode.Directory)
        self.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        self.setOption(QFileDialog.Option.ShowDirsOnly, True)

    def get_file_list(self):
        if self.exec():
            selected_dir = self.selectedFiles()[0]
            file_paths = [str(file) for file in Path(selected_dir).glob("*") if file.is_file()]
            return file_paths

        return [] 