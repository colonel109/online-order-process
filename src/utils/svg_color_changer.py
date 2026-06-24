# utils.py
from functools import lru_cache
from PySide6.QtCore import QByteArray, QSize
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

@lru_cache(maxsize=128)
def _get_cached_icon(qrc_path: str, color_hex: str, size_tuple: tuple) -> QIcon:
    """
    Hàm lõi thực hiện việc vẽ và nhuộm màu SVG, kết quả được lưu vào cache.
    Vì @lru_cache yêu cầu các tham số truyền vào phải không thay đổi được (immutable),
    nên ta chuyển QColor thành chuỗi Hex và QSize thành bộ Tuple.
    """
    # 1. Khởi tạo bộ dựng SVG từ đường dẫn QRC
    renderer = QSvgRenderer(qrc_path)
    if not renderer.isValid():
        return QIcon()

    # 2. Tạo một QPixmap trống với kích thước yêu cầu
    size = QSize(*size_tuple)
    pixmap = QPixmap(size)
    pixmap.fill(QColor(0, 0, 0, 0)) # Đặt nền trong suốt

    # 3. Sử dụng QPainter để vẽ và "nhuộm" màu
    painter = QPainter(pixmap)
    renderer.render(painter)
    
    # Kỹ thuật SourceIn: Giữ lại vùng hình dáng của SVG và lấp đầy bằng màu mới
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), QColor(color_hex))
    painter.end()

    return QIcon(pixmap)


def get_colored_qrc_icon(qrc_path: str, color: QColor, size: QSize = QSize(24, 24)) -> QIcon:
    """
    Hàm tiện ích chính được gọi từ các file giao diện (như Menubar).
    Chuyển đổi kiểu dữ liệu của Qt sang kiểu cơ bản của Python để tận dụng Cache.
    """
    color_hex = color.name()                      
    size_tuple = (size.width(), size.height())      
    
    return _get_cached_icon(qrc_path, color_hex, size_tuple)