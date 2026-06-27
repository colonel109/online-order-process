from PySide6.QtWidgets import QMenuBar, QFileDialog
from PySide6.QtGui import QAction, QIcon, QColor, QPixmap
from PySide6.QtCore import Signal

from src.ui.dialogs.open_file_folder import OpenOrderFile, OpenOrderFolder
from src.utils.svg_color_changer import get_colored_qrc_icon
from resources import resources_rc

class Menubar(QMenuBar):
    """
    Class này chỉ đóng vai trò ghi list các file mà người dùng chọn, loader ở mainwindow sẽ truy cập
    biến đó và xử lí tiếp dữ liệu
    """
    file_selected_signal = Signal(list)

    def __init__(self, base_path):
        super().__init__()

        self.base_path = base_path
        file_menu = self.addMenu("Tệp")

        self.get_file_dialog = OpenOrderFile(base_path=self.base_path)
        self.get_folder_dialog = OpenOrderFolder(base_path=self.base_path)

        self.open_file_act = QAction("Mở tệp", self)
        self.open_file_act.setStatusTip("Lấy dữ liệu đơn hàng từ một hoặc nhiều tệp cùng loại")
        file_menu.addAction(self.open_file_act)

        self.open_folder_act = QAction("Mở thư mục", self)
        self.open_folder_act.setStatusTip("Lấy dữ liệu từ tất cả các tệp đơn hàng cùng loại trong một thư mục")
        file_menu.addAction(self.open_folder_act)

        data_menu = self.addMenu("Dữ liệu")
        self.open_database_act = QAction("Mở dữ liệu đã lưu")
        data_menu.addAction(self.open_database_act)

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

    def update_theme(self, is_dark_mode: bool):
        icon_color = QColor("white") if is_dark_mode else QColor("#333333")

        file_icon = get_colored_qrc_icon(":/resource/icons/file-plus-corner.svg", icon_color)
        folder_icon = get_colored_qrc_icon(":/resource/icons/folder-plus.svg", icon_color)

        self.open_file_act.setIcon(file_icon)
        self.open_folder_act.setIcon(folder_icon)