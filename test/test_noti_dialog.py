import sys
import os 
sys.path.append(os.path.abspath(os.path.join('..')))

from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout, QApplication, QStackedLayout, QVBoxLayout, QPushButton
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

from resources import resources_rc


class SuccessFailNoti(QFrame):
    """
    Qframe này được sử dụng để hiện thông báo thành công / cảnh báo và các nút điều hướng khi thao tác trong cửa sổ xử lí dữ liệu
    """
    
    def __init__(self):
        super().__init__()
       
        # Layout chính
        self.main_layout = QStackedLayout()
        self.setLayout(self.main_layout)

        self.init_success_container()
        self.init_caution_container()
        
        self.main_layout.addWidget(self.success_container)
        self.main_layout.addWidget(self.caution_container)

    def init_success_container(self):
        icon_label = QLabel()
        icon_label.setPixmap(QPixmap(":/resource/icons/circle-check.svg"))
        self.success_message = QLabel()

        # Layout thông báo
        label_layout = QHBoxLayout()
        label_layout.addWidget(icon_label)
        label_layout.addWidget(self.success_message)
        label_layout.addStretch()

        # Nút tiếp tục (thông báo thành công mặc định chỉ có một nút tiếp tục)
        self.continue_button = QPushButton("Tới bước tiếp theo")
    
        self.success_container = QFrame()
        main_layout = QVBoxLayout(self.success_container)
        main_layout.addLayout(label_layout)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.continue_button, alignment=Qt.AlignmentFlag.AlignLeft)

        self.success_container.setStyleSheet("""
            QFrame {
                border-radius: 4px; 
                background-color: #233D4D; 
                color: #000000;
            }
            QPushButton {
                background-color: #73cefc;
                color: black;
            } 
            QLabel {
                color: #ffffff;
                text-align: left;
            }
        """)

    def init_caution_container(self):
        icon_label = QLabel()
        icon_label.setPixmap(QPixmap(":/resource/icons/exclamation-circle.svg"))
        self.caution_message = QLabel()

        # Layout thông báo
        label_layout = QHBoxLayout()
        label_layout.addWidget(icon_label)
        label_layout.addWidget(self.caution_message)
        label_layout.addStretch()
 
        self.caution_container = QFrame()
        main_layout = QVBoxLayout(self.caution_container)
        main_layout.addLayout(label_layout)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.caution_container.setStyleSheet("""
            QFrame {
                border-radius: 4px; 
                background-color: #E89951; 
                color: #000000;
            }
            QPushButton {
                background-color: #73cefc;
                color: black;
            } 
            QLabel {
                color: #000000;
                text-align: left;
            }
        """)

    def show_success_message(self, text):
        self.success_message.setText(text)
        self.main_layout.setCurrentIndex(0)
    
    def show_caution_message(self, text):
        self.caution_message.setText(text)
        self.main_layout.setCurrentIndex(1)
        

app = QApplication(sys.argv)
window = SuccessFailNoti()
window.show()
app.exec()