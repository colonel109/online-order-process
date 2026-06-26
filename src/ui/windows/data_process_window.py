from PySide6.QtWidgets import QMainWindow, QStackedLayout, QWidget, QVBoxLayout, QProgressBar, QLabel
from PySide6.QtGui import QGuiApplication
from PySide6.QtCore import QSize, Qt

from src.ui.widgets.process_step_one import AddComboVariant
from src.ui.widgets.process_step_two import AddComboDetail
from src.ui.widgets.progress_display import ProgressDisplay


class DataProcessWindow(QMainWindow):
    """
    Cửa sổ này chỉ hiển thị khi người dùng chọn xử lí dữ liệu, người dùng sẽ không thể tương tác với main_window
    khi nó được kích hoạt
    """
    def __init__(self, session):
        super().__init__()

        # Kết nối tới database
        self.session = session

        # Tuỳ chỉnh cửa sổ
        self.setWindowTitle("Xử lí dữ liệu đơn hàng")
        self.setMinimumSize(QSize(1400, 700))

        # Các layer
        self.step_one = AddComboVariant(session=self.session, parent=self)
        self.step_two = AddComboDetail(session=self.session, parent=self)

        # Layout tiến trình
        self.progress_displayer= ProgressDisplay(
            max_step=3
        )

        # Layout hiển thị
        self.display_layout = QStackedLayout()
        self.display_layout.addWidget(self.step_one)
        self.display_layout.addWidget(self.step_two)
        self.current_step = 0

        # Layout chính
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.progress_displayer)
        main_layout.addLayout(self.display_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        # Kết nối với hệ thống để tự đổi giao diện

        app = QGuiApplication.instance()
        app.styleHints().colorSchemeChanged.connect(self.on_theme_changed)
        self.on_theme_changed(app.styleHints().colorScheme())

        # Kết nối signal với slot
        self.init_signal()
        self.update_button_state()

    def init_signal(self):
        self.progress_displayer.forward_btn.pressed.connect(self.move_forward)
        self.progress_displayer.backward_btn.pressed.connect(self.move_backward)
        self.step_one.custom_message_frame.continue_button.clicked.connect(self.move_forward)
        self.step_one.custom_message_frame.continue_button.clicked.connect(self.step_two.process_and_display)

    def move_forward(self):
        current_index = self.display_layout.currentIndex()
        total_widgets = self.display_layout.count()

        if current_index < total_widgets -1:
            self.current_step += 1
            self.display_layout.setCurrentIndex(self.current_step)
            self.update_button_state()

        elif current_index == total_widgets -1:
            self.update_button_state()
            pass

    def move_backward(self):
        current_index = self.display_layout.currentIndex()
        if current_index > 0:
            self.current_step -= 1
            self.display_layout.setCurrentIndex(self.current_step)
            self.update_button_state()

    def update_button_state(self):
        current_index = self.display_layout.currentIndex()
        total_widgets = self.display_layout.count()

        self.progress_displayer.backward_btn.setEnabled(current_index > 0)
        self.progress_displayer.forward_btn.setEnabled(current_index < total_widgets - 1)

    def on_theme_changed(self, scheme):
        is_dark = (scheme == Qt.ColorScheme.Dark)
        self.step_two.update_theme(is_dark_mode=is_dark)