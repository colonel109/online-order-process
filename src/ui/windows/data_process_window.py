from PySide6.QtWidgets import QMainWindow, QStackedLayout, QWidget, QVBoxLayout, QProgressBar, QLabel
from PySide6.QtCore import QSize, Qt
from src.ui.widgets.process_step_one import AddComboVariant


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
        self.setMinimumSize(QSize(1000, 700))

        # Các layer
        self.step_one = AddComboVariant(session=self.session, parent=self)

        # Layout tiến trình
        label = QLabel("Tiến trình")

        self.current_step = 1
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
        display_layout = QStackedLayout()
        display_layout.addWidget(self.step_one)

        # Layout chính
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(progress_container)
        main_layout.addLayout(display_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)