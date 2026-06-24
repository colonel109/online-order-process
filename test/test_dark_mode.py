import sys
from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap, QGuiApplication
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel

# Hàm đổi màu SVG từ Cách 1 (Sử dụng QByteArray thay vì đường dẫn QRC để tiện test)
def get_colored_svg_icon(svg_data: bytes, color: QColor, size: QSize = QSize(48, 48)) -> QIcon:
    renderer = QSvgRenderer(QByteArray(svg_data))
    if not renderer.isValid():
        return QIcon()

    pixmap = QPixmap(size)
    pixmap.fill(QColor(0, 0, 0, 0)) # Nền trong suốt

    painter = QPainter(pixmap)
    renderer.render(painter)
    
    # Nhuộm màu SVG theo màu truyền vào
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), color)
    painter.end()

    return QIcon(pixmap)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Auto Dark/Light SVG")
        self.resize(300, 200)

        # Dữ liệu SVG của một icon "Cài đặt" (Gear) mẫu dưới dạng chuỗi bytes
        self.svg_icon_data = b"""
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
            <path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"/>
            <path fill-rule="evenodd" d="M11.25 2.5a.75.75 0 0 1 1.5 0v1.306a7.514 7.514 0 0 1 2.37.982l.923-.923a.75.75 0 1 1 1.06 1.06l-.923.923c.433.666.768 1.404.982 2.19h1.338a.75.75 0 0 1 0 1.5h-1.338a7.525 7.525 0 0 1-.982 2.19l.923.923a.75.75 0 1 1-1.06 1.06l-.923-.923a7.514 7.514 0 0 1-2.37.982v1.306a.75.75 0 0 1-1.5 0v-1.306a7.514 7.514 0 0 1-2.37-.982l-.923.923a.75.75 0 1 1-1.06-1.06l.923-.923a7.525 7.525 0 0 1-.982-2.19H2.5a.75.75 0 0 1 0-1.5h1.338a7.525 7.525 0 0 1 .982-2.19l-.923-.923a.75.75 0 1 1 1.06-1.06l.923.923c.666-.433 1.404-.768 2.19-.982V2.5z" clip-rule="evenodd"/>
        </svg>
        """

        # Giao diện đơn giản
        layout = QVBoxLayout()
        
        self.label_status = QLabel("Đang kiểm tra giao diện hệ thống...", self)
        self.label_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label_status)

        self.btn_icon = QPushButton(" Icon Demo", self)
        self.btn_icon.setIconSize(QSize(32, 32))
        layout.addWidget(self.btn_icon)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Lắng nghe sự thay đổi giao diện của Hệ điều hành
        app = QGuiApplication.instance()
        app.styleHints().colorSchemeChanged.connect(self.on_theme_changed)
        
        # Gọi lần đầu để thiết lập màu icon theo trạng thái hiện tại lúc mở app
        self.on_theme_changed(app.styleHints().colorScheme())

    def on_theme_changed(self, scheme):
        """Hàm này tự động chạy khi bạn đổi Dark/Light mode trên máy tính"""
        if scheme == Qt.ColorScheme.Dark:
            self.label_status.setText("Hệ thống: 🌙 DARK MODE")
            # Nếu hệ thống là Dark, nhuộm icon thành màu TRẮNG (hoặc màu vàng, xanh tùy bạn)
            icon_color = QColor("white")
        else:
            self.label_status.setText("Hệ thống: ☀️ LIGHT MODE")
            # Nếu hệ thống là Light, nhuộm icon thành màu ĐEN/XÁM ĐẬM
            icon_color = QColor("#333333")

        # Cập nhật lại icon cho nút bấm
        updated_icon = get_colored_svg_icon(self.svg_icon_data, icon_color)
        self.btn_icon.setIcon(updated_icon)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())