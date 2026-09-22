import os
import struct
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QLayout, QSizePolicy,
    QPushButton, QFileDialog, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRect, QSize, QUrl
from PyQt6.QtGui import QKeySequence, QShortcut, QDragEnterEvent, QDropEvent, QPixmap

from ui.thumbnail_widget import ThumbnailWidget
from ui.preview_modal import PreviewModal
from ui.notifications import NotificationManager

from utils.validators import Validators

from core.cache_manager import CacheManager
class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=10, hSpacing=10, vSpacing=10):
        super().__init__(parent)
        self._item_list = []
        self.setContentsMargins(margin, margin, margin, margin)
        self.hSpace = hSpacing
        self.vSpace = vSpacing

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self._item_list.append(item)

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self.doLayout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def doLayout(self, rect, testOnly):
        x = rect.x()
        y = rect.y()
        lineHeight = 0
        
        for item in self._item_list:
            spaceX = self.hSpace
            spaceY = self.vSpace
            nextX = x + item.sizeHint().width() + spaceX
            
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0
                
            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
                
            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())
            
        return y + lineHeight - rect.y() + self.contentsMargins().bottom()


class CenterPanel(QWidget):
    files_loaded = pyqtSignal(list)
    storyboard_reordered = pyqtSignal(list)
    page_deleted = pyqtSignal(str, int)
    selection_changed = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.cache_manager = None

    def set_cache_manager(self, cache_manager):
        self.cache_manager = cache_manager
        
        self.storyboard_items = []
        self.undo_stack = None
        self.is_single_file_mode = False
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.empty_widget = QWidget()
        self.empty_widget.setAcceptDrops(True)
        self.empty_widget.dragEnterEvent = self.dragEnterEvent
        self.empty_widget.dragLeaveEvent = self.dragLeaveEvent
        self.empty_widget.dropEvent = self.dropEvent
        empty_layout = QVBoxLayout(self.empty_widget)
        
        self.empty_label = QLabel("Drop files or folders here")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("font-size: 24px; color: #888888; font-weight: bold;")
        
        self.empty_subtext = QLabel("Supported: PDF, JPG, PNG, WebP, BMP, TIFF")
        self.empty_subtext.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_subtext.setStyleSheet("font-size: 14px; color: #AAAAAA;")
        
        self.browse_button = QPushButton("Browse Files")
        self.browse_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.browse_button.setStyleSheet("""
            QPushButton {
                border: 1px solid #AAAAAA;
                border-radius: 4px;
                padding: 6px 16px;
                background-color: transparent;
                color: #888888;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #E0E0E0;
                color: #333333;
            }
        """)
        self.browse_button.clicked.connect(self._browse_files)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.browse_button)
        btn_layout.addStretch()

        empty_layout.addStretch()
        empty_layout.addWidget(self.empty_label)
        empty_layout.addWidget(self.empty_subtext)
        empty_layout.addSpacing(15)
        empty_layout.addLayout(btn_layout)
        empty_layout.addStretch()
        
        self.layout.addWidget(self.empty_widget)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setAcceptDrops(True)
        self.scroll_area.dragEnterEvent = self.dragEnterEvent
        self.scroll_area.dragLeaveEvent = self.dragLeaveEvent
        self.scroll_area.dropEvent = self.dropEvent
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; }")
        
        self.scroll_content = QWidget()
        self.scroll_content.setAcceptDrops(True)
        self.scroll_content.dragEnterEvent = self.dragEnterEvent
        self.scroll_content.dragLeaveEvent = self.dragLeaveEvent
        self.scroll_content.dropEvent = self.dropEvent
        self.flow_layout = FlowLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)
        
        self.layout.addWidget(self.scroll_area)
        
        self.update_state()
        self._setup_shortcuts()

    def _browse_files(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Browse Files",
            "",
            "Supported Files (*.pdf *.jpg *.jpeg *.png *.webp *.bmp *.tiff *.tif);;All Files (*)"
        )
        if file_paths:
            urls = [QUrl.fromLocalFile(path) for path in file_paths]
            self.handle_file_drop(urls)

    def _setup_shortcuts(self):
        self.undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        self.undo_shortcut.activated.connect(self.undo_delete)

    def undo_delete(self):
        if self.undo_stack:
            index, item = self.undo_stack
            self.storyboard_items.insert(index, item)
            self.undo_stack = None
            self.refresh_grid()
            self.storyboard_reordered.emit(self.storyboard_items)

    def load_files(self, cached_paths: list[str], page_counts: dict):
        for path in cached_paths:
            count = page_counts.get(path, 1)
            for i in range(count):
                self.storyboard_items.append((path, i))
        self.refresh_grid()

    def clear_workspace(self):
        self.storyboard_items.clear()
        self.undo_stack = None
        self.refresh_grid()

    def highlight_pages(self, indices: list[int]):
        for i in range(self.flow_layout.count()):
            item = self.flow_layout.itemAt(i)
            if item:
                widget = item.widget()
                if isinstance(widget, ThumbnailWidget):
                    widget.set_selected(i in indices)

    def get_current_order(self) -> list[tuple[str, int]]:
        return list(self.storyboard_items)

    def update_state(self):
        has_items = len(self.storyboard_items) > 0
        self.empty_widget.setVisible(not has_items)
        self.scroll_area.setVisible(has_items)

    def refresh_grid(self):
        while self.flow_layout.count():
            item = self.flow_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                
        for path, idx in self.storyboard_items:
            pixmap = self.cache_manager.generate_thumbnail(path, idx)
                
            if pixmap is None:
                pixmap = QPixmap(100, 140)
                pixmap.fill(Qt.GlobalColor.lightGray)
                
            label = f"Page {idx + 1}" if path.lower().endswith('.pdf') else os.path.basename(path)
            
            thumb = ThumbnailWidget(pixmap, label, path, idx)
            thumb.delete_requested.connect(self.on_delete_requested)
            thumb.preview_requested.connect(self.on_preview_requested)
            
            self.flow_layout.addWidget(thumb)
            
        self.update_state()

    def on_delete_requested(self, file_path, page_idx):
        try:
            curr_index = self.storyboard_items.index((file_path, page_idx))
        except ValueError:
            return
            
        item = self.storyboard_items.pop(curr_index)
        self.undo_stack = (curr_index, item)
        self.refresh_grid()
        self.page_deleted.emit(file_path, page_idx)

        if len(self.storyboard_items) == 0:
            self.clear_workspace()
            self.files_loaded.emit([])

    def on_preview_requested(self, file_path, page_idx):
        pixmap = self.cache_manager.get_full_res_page(file_path, page_idx)
        if pixmap is None:
            pixmap = QPixmap(800, 600)
            pixmap.fill(Qt.GlobalColor.gray)
            
        label = f"Page {page_idx + 1}" if file_path.lower().endswith('.pdf') else os.path.basename(file_path)
        modal = PreviewModal(pixmap, label, self)
        modal.exec()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls() or event.mimeData().hasFormat("application/x-deskconvert-page-index"):
            self.empty_widget.setStyleSheet(".QWidget { border: 2px solid #4A90D9; background-color: #EEF4FB; }")
            self.scroll_area.setStyleSheet("QScrollArea { border: 2px solid #4A90D9; background-color: #EEF4FB; }")
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.empty_widget.setStyleSheet("")
        self.scroll_area.setStyleSheet("QScrollArea { border: none; }")
        event.accept()

    def dropEvent(self, event: QDropEvent):
        self.empty_widget.setStyleSheet("")
        self.scroll_area.setStyleSheet("QScrollArea { border: none; }")
        
        if event.mimeData().hasUrls():
            self.handle_file_drop(event.mimeData().urls())
            event.acceptProposedAction()
            
        elif event.mimeData().hasFormat("application/x-deskconvert-page-index"):
            mime = event.mimeData()
            page_data = mime.data("application/x-deskconvert-page-index").data()
            try:
                page_idx = struct.unpack('i', page_data)[0]
            except Exception:
                page_idx = int(page_data.decode('utf-8'))
                
            file_path = mime.data("application/x-deskconvert-file-path").data().decode('utf-8')
            
            drop_pos = event.position().toPoint()
            insert_index = self.get_insert_index_at(drop_pos)
            self.reorder_item(file_path, page_idx, insert_index)
            event.acceptProposedAction()

    def handle_file_drop(self, urls):
        rejected = []
        accepted = []
        
        for url in urls:
            path = url.toLocalFile()
            if os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for f in files:
                        full_path = os.path.join(root, f)
                        if Validators.is_supported_file(full_path):
                            if Validators.is_password_protected(full_path):
                                NotificationManager.show_password_protected(self, full_path)
                            else:
                                accepted.append(full_path)
                        else:
                            rejected.append(full_path)
            else:
                if Validators.is_supported_file(path):
                    if Validators.is_password_protected(path):
                        NotificationManager.show_password_protected(self, path)
                    else:
                        accepted.append(path)
                else:
                    rejected.append(path)
                    
        if rejected:
            NotificationManager.show_rejected_files(self, [os.path.basename(r) for r in rejected])
            
        if not accepted:
            return
            
        if self.is_single_file_mode and self.storyboard_items:
            if not NotificationManager.show_replace_confirm(self, accepted[0]):
                return
            self.clear_workspace()
            
        page_counts = {}
        staged = []
        for filepath in accepted:
            if self.cache_manager:
                cached_path = self.cache_manager.stage_file(filepath)
                staged.append(cached_path)
                page_counts[cached_path] = self.cache_manager.get_page_count(cached_path)
            else:
                staged.append(filepath)
                page_counts[filepath] = 1
                
        self.load_files(staged, page_counts)
        self.files_loaded.emit(accepted)

    def get_insert_index_at(self, pos: QPoint):
        content_pos = self.scroll_content.mapFrom(self, pos)
        
        for i in range(self.flow_layout.count()):
            item = self.flow_layout.itemAt(i)
            if item:
                wid = item.widget()
                if wid.geometry().contains(content_pos):
                    if content_pos.x() < wid.geometry().center().x():
                        return i
                    else:
                        return i + 1
        return len(self.storyboard_items)

    def reorder_item(self, file_path, page_idx, insert_index):
        try:
            curr_index = self.storyboard_items.index((file_path, page_idx))
        except ValueError:
            return
            
        if curr_index == insert_index or curr_index == insert_index - 1:
            return 
            
        item = self.storyboard_items.pop(curr_index)
        
        if insert_index > curr_index:
            insert_index -= 1
            
        self.storyboard_items.insert(insert_index, item)
        self.refresh_grid()
        self.storyboard_reordered.emit(self.storyboard_items)
