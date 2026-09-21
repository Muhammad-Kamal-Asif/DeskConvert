from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QScrollArea, QLabel, QPushButton
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

class PreviewModal(QDialog):
    def __init__(self, pixmap: QPixmap, page_label: str, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle(f"Page Preview — {page_label}")
        self.setModal(True)
        self.setFixedSize(900, 700)
        
        layout = QVBoxLayout(self)
        
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        available_w = 860
        available_h = 600
        
        scaled = pixmap.scaled(
            available_w,
            available_h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.image_label = QLabel()
        self.image_label.setPixmap(scaled)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.scroll_area.setWidget(self.image_label)
        layout.addWidget(self.scroll_area)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        layout.addWidget(self.close_button, alignment=Qt.AlignmentFlag.AlignCenter)
