from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout, QStackedLayout, QVBoxLayout, QPushButton
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

from resources import resources_rc


class CustomMessage(QFrame):
    """
    Qframe này được sử dụng để hiện thông báo thành công / cảnh báo và các nút điều hướng khi thao tác trong cửa sổ xử lí dữ liệu
    """
    
    def __init__(self):
        super().__init__()
       
        # Layout chính
        self.main_layout = QStackedLayout()
        self.setLayout(self.main_layout)

        # Setup giao diện
        self.init_success_container()
        self.init_action_container()
        
        self.main_layout.addWidget(self.success_container)
        self.main_layout.addWidget(self.action_container)

        self.hide()

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
        main_layout.addWidget(self.continue_button, alignment=Qt.AlignmentFlag.AlignLeft)

        self.success_container.setStyleSheet("""
            QFrame {
                border-radius: 4px; 
                background-color: #233D4D; 
                color: #000000;
            }
            QPushButton:enabled {
                background-color: #73cefc;
                color: black;
            } 
            QPushButton:disabled {
                background-color: #555555;  
                color: #888888;
            }            
            QLabel {
                color: #ffffff;
                text-align: left;
                font-weight: bold
            }
        """)

    def init_action_container(self):
        icon_label = QLabel()
        icon_label.setPixmap(QPixmap(":/resource/icons/exclamation-circle.svg"))
        self.action_message = QLabel()

        # Layout thông báo
        label_layout = QHBoxLayout()
        label_layout.addWidget(icon_label)
        label_layout.addWidget(self.action_message)
        label_layout.addStretch()

        # Layout nút
        self.confirm_button = QPushButton()
        self.confirm_button.setObjectName("confirm_button")
        self.decline_button = QPushButton()
        self.decline_button.setObjectName("decline_button")

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.confirm_button)
        button_layout.addWidget(self.decline_button)
        button_layout.addStretch()

        self.action_container = QFrame()
        main_layout = QVBoxLayout(self.action_container)
        main_layout.addLayout(label_layout)
        main_layout.addLayout(button_layout)

        self.action_container.setStyleSheet("""
            QFrame {
                border-radius: 4px; 
                background-color: #F08D39; 
                color: #000000;
            }
            #confirm_button:enabled {
                background-color: #73cefc;
                color: black;
            } 
            #confirm_button:disabled {
                background-color: #555555;  
                color: #888888;
            } 
            #decline_button {
                background-color: #EEEEEE;
                color: black;
            }
            QLabel {
                color: #000000;
                text-align: left;
                font-weight: bold;
            }
        """)

    def show_success_message(self, text):
        self.show()
        self.success_message.setText(text)
        self.main_layout.setCurrentIndex(0)
    
    def show_action_message(self, text, confirm_btn_text, decline_button_text):
        self.show()
        self.action_message.setText(text)
        self.confirm_button.setText(confirm_btn_text)
        self.decline_button.setText(decline_button_text)
        self.main_layout.setCurrentIndex(1)