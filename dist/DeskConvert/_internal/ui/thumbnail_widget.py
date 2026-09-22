from PyQt6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget
from PyQt6.QtGui import QPixmap, QDrag, QMouseEvent, QCursor
from PyQt6.QtCore import pyqtSignal, Qt, QMimeData, QByteArray
import struct

class ThumbnailImageLabel(QLabel):
    clicked = pyqtSignal()
    drag_started = pyqtSignal(QMouseEvent)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._drag_start_position = None

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_position = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        
        if self._drag_start_position is None:
            return
            
        if (event.pos() - self._drag_start_position).manhattanLength() > 5:
            self.drag_started.emit(event)
            self._drag_start_position = None
            
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._drag_start_position is not None:
                self.clicked.emit()
            self._drag_start_position = None
        super().mouseReleaseEvent(event)


class ThumbnailWidget(QFrame):
    delete_requested = pyqtSignal(str, int)
    preview_requested = pyqtSignal(str, int)

    def __init__(self, pixmap: QPixmap, label: str, file_path: str, page_index: int, parent=None):
        super().__init__(parent)
        
        self.file_path = file_path
        self.page_index = page_index
        self.is_selected = False
        
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
        self.setObjectName("ThumbnailWidget")
        
        self.update_style()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        top_container = QWidget()
        top_layout = QVBoxLayout(top_container)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)
        
        close_btn_layout = QHBoxLayout()
        close_btn_layout.addStretch()
        
        self.close_btn = QPushButton("X")
        self.close_btn.setFixedSize(16, 16)
        self.close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #555555;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                color: #D13438;
            }
        """)
        self.close_btn.clicked.connect(self._on_close_clicked)
        close_btn_layout.addWidget(self.close_btn)
        top_layout.addLayout(close_btn_layout)
        
        self.image_label = ThumbnailImageLabel()
        if pixmap.width() > 150:
            scaled_pixmap = pixmap.scaledToWidth(150, Qt.TransformationMode.SmoothTransformation)
        else:
            scaled_pixmap = pixmap
            
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.clicked.connect(self._on_preview_clicked)
        self.image_label.drag_started.connect(self._start_drag)
        
        top_layout.addWidget(self.image_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(top_container)
        
        self.text_label = QLabel(label)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setStyleSheet("color: #333333; font-size: 11px;")
        self.text_label.setWordWrap(True)
        self.text_label.setMaximumWidth(150)
        
        layout.addWidget(self.text_label, alignment=Qt.AlignmentFlag.AlignCenter)

    def _on_close_clicked(self):
        self.delete_requested.emit(self.file_path, self.page_index)

    def _on_preview_clicked(self):
        self.preview_requested.emit(self.file_path, self.page_index)

    def _start_drag(self, event: QMouseEvent):
        drag = QDrag(self)
        mime_data = QMimeData()
        
        # Serialize the integer for drag and drop
        byte_array = QByteArray(struct.pack('i', self.page_index))
        mime_data.setData("application/x-deskconvert-page-index", byte_array)
        
        byte_array_fp = QByteArray(self.file_path.encode('utf-8'))
        mime_data.setData("application/x-deskconvert-file-path", byte_array_fp)
        
        drag.setMimeData(mime_data)
        
        if self.image_label.pixmap():
            drag.setPixmap(self.image_label.pixmap())
            drag.setHotSpot(event.pos())
            
        drag.exec(Qt.DropAction.MoveAction)

    def set_selected(self, selected: bool):
        self.is_selected = selected
        self.update_style()

    def update_style(self):
        if self.is_selected:
            self.setStyleSheet("ThumbnailWidget { border: 2px solid #0078D7; background-color: #E5F1FB; }")
        else:
            self.setStyleSheet("""
                ThumbnailWidget { 
                    border: 1px solid #D3D3D3; 
                    background-color: #FFFFFF; 
                }
                ThumbnailWidget:hover { 
                    border: 1px solid #888888; 
                }
            """)
