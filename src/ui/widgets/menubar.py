from PySide6.QtWidgets import QMenuBar, QFileDialog
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import Signal

from src.ui.dialogs.open_file_folder import OpenOrderFile, OpenOrderFolder
from resources import resources_rc

class Menubar(QMenuBar):
    """
    Class này chỉ đóng vai trò ghi list các file mà người dùng chọn, loader ở mainwindow sẽ truy cập
    biến đó và xử lí tiếp dữ liệu
    """
    # Phát và gửi kèm danh sách file với tín hiệu khi người dùng chọn xong
    file_selected_signal = Signal(list)

    def __init__(self, base_path):
        super().__init__()

        # Đường dẫn
        self.base_path = base_path

        # File menu
        file_menu = self.addMenu("Tệp")

        # Các dialog mở file và folder 
        self.get_file_dialog = OpenOrderFile(base_path=self.base_path)
        self.get_folder_dialog = OpenOrderFolder(base_path=self.base_path)

        # Action mở tệp đơn hàng
        self.open_file_act = QAction(
            QIcon(":/resource/icons/file-plus-corner.svg"),
            "Mở tệp",
            self
        )
        self.open_file_act.setStatusTip("Lấy dữ liệu đơn hàng từ một hoặc nhiều tệp cùng loại")
        file_menu.addAction(self.open_file_act)

        # Action mở thư mục chứa đơn hàng
        self.open_folder_act = QAction(
            QIcon(":/resource/icons/folder-plus.svg"),
            "Mở thư mục",
            self
        )
        self.open_folder_act.setStatusTip("Lấy dữ liệu từ tất cả các tệp đơn hàng cùng loại trong một thư mục")
        file_menu.addAction(self.open_folder_act)

        self.init_signal()

    def init_signal(self):
        self.open_file_act.triggered.connect(self.open_file_dialog)
        self.open_folder_act.triggered.connect(self.open_folder_dialog)

    def open_file_dialog(self):
        selected_files = self.get_file_dialog.get_file_list()
        if selected_files:
            self.file_selected_signal.emit(selected_files)

    def open_folder_dialog(self):
        selected_files = self.get_folder_dialog.get_file_list()
        if selected_files:
            self.file_selected_signal.emit(selected_files)