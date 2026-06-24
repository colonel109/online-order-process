from PySide6.QtWidgets import QMainWindow, QStackedLayout, QWidget, QVBoxLayout, QProgressBar, QLabel
from PySide6.QtGui import QGuiApplication
from PySide6.QtCore import QSize, Qt
from src.ui.widgets.process_step_one import AddComboVariant
from src.ui.widgets.process_step_two import AddComboDetail


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
        label = QLabel("Tiến trình")

        self.current_step = 0
        self.max_stop = 3
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(self.current_step)
        self.progress_bar.setMaximum(3)
        progress_layout = QVBoxLayout()

        progress_layout.addWidget(label)
        progress_layout.addWidget(self.progress_bar)
        progress_container = QWidget()
        progress_container.setLayout(progress_layout)

        # Layout hiển thị
        self.display_layout = QStackedLayout()
        self.display_layout.addWidget(self.step_one)
        self.display_layout.addWidget(self.step_two)

        # Layout chính
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(progress_container)
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

    def init_signal(self):
        self.step_one.next_step_btn.clicked.connect(self.move_forward)   
    
    def move_forward(self):
        self.current_step += 1
        self.display_layout.setCurrentIndex(self.current_step)
    
    def on_theme_changed(self, scheme):
        is_dark = (scheme == Qt.ColorScheme.Dark)
        self.step_two.update_theme(is_dark_mode=is_dark)