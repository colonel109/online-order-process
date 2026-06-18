from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton

class ImportMask(QWidget):
    def __init__(self):
        super().__init__()

        self.import_file_btn = QPushButton("Mở tệp")
        self.import_folder_btn = QPushButton("Mở đơn hàng")
        label = QLabel("Chưa có dữ liệu, vui lòng thêm dữ liệu")

        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(self.import_file_btn)
        layout.addWidget(self.import_folder_btn)
        self.setLayout(layout)