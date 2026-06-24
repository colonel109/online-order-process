from PySide6.QtWidgets import QWidget, QProgressBar, QVBoxLayout, QHBoxLayout, QLabel, QPushButton

class ProgressDisplay(QWidget):
    def __init__(self, max_step):
        super().__init__()

        self.max_step = max_step

        # Layout hiển thị thanh trạng thái
        self.label = QLabel("Tiến trình") 
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(self.max_step)

        progress_layout = QVBoxLayout()
        progress_layout.addWidget(self.label)
        progress_layout.addWidget(self.progress_bar)

        # Layout hiển thị các nút điều khiển
        self.backward_btn = QPushButton("Quay lại")
        self.forward_btn = QPushButton("Tiếp tục")
        self.backward_btn.setEnabled(False)
        
        control_layout = QHBoxLayout()
        control_layout.addWidget(self.backward_btn)
        control_layout.addWidget(self.forward_btn)
        control_layout.addStretch()

        # Layout chính
        main_layout = QVBoxLayout()
        main_layout.addLayout(progress_layout)
        main_layout.addLayout(control_layout)
        self.setLayout(main_layout)