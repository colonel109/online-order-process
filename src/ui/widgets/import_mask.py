from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QGridLayout, QHBoxLayout, QFrame
from PySide6.QtCore import Signal, Qt

from src.ui.dialogs.open_file_folder import OpenOrderFile, OpenOrderFolder
from resources import resources_rc


class ImportMask(QWidget):
    """
    Class này chỉ đóng vai trò ghi list các file mà người dùng chọn, loader ở mainwindow sẽ truy cập
    biến đó và xử lí tiếp dữ liệu
    """
    # Phát và gửi kèm danh sách file với tín hiệu khi người dùng chọn xong
    file_selected_signal = Signal(list)

    def __init__(self, base_path):
        super().__init__()

        # Đường dẫn gốc
        self.base_path = base_path

        # Các dialog mở file và folder 
        self.get_file_dialog = OpenOrderFile(base_path=self.base_path)
        self.get_folder_dialog = OpenOrderFolder(base_path=self.base_path)

        self.import_file_btn = QPushButton("Mở tệp")
        file_btn_layout = QHBoxLayout()

        self.import_folder_btn = QPushButton("Mở thư mục")
        label = QLabel("<b>Không tìm thấy dữ liệu đơn hàng, vui lòng nhập dữ liệu:</b>")

        container_layout = QVBoxLayout()
        container_layout.addWidget(label)
        container_layout.addWidget(self.import_file_btn)
        container_layout.addWidget(self.import_folder_btn)

        container = QFrame()
        container.setObjectName("child_container")
        # container.setStyleSheet(
        #     """
        #     QFrame#child_container {
        #         border: 0.5px solid #e0dcce;
        #         border-radius: 15px;
        #     }
        #     """
        # )
        container.setLayout(container_layout)
        
        main_layout = QGridLayout()
        main_layout.addWidget(container, 0, 0, Qt.AlignmentFlag.AlignCenter)
        self.setLayout(main_layout)

        # Kết nối tín hiệu
        self.init_signal()

    def init_signal(self):
        self.import_file_btn.clicked.connect(self.open_file_dialog)
        self.import_folder_btn.clicked.connect(self.open_folder_dialog)

    def open_file_dialog(self):
        selected_files = self.get_file_dialog.get_file_list()
        if selected_files:
            self.file_selected_signal.emit(selected_files)

    def open_folder_dialog(self):
        selected_files = self.get_folder_dialog.get_file_list()
        if selected_files:
            self.file_selected_signal.emit(selected_files)