import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton, QMessageBox, QLabel
from PyQt6.QtCore import pyqtSignal, Qt
from utils.history import HistoryManager

class LeftPanel(QWidget):
    file_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.history_manager = HistoryManager()
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        self.title_label = QLabel("<b>Recent Files</b>")
        self.layout.addWidget(self.title_label)
        
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.layout.addWidget(self.list_widget)
        
        self.clear_btn = QPushButton("Clear History")
        self.clear_btn.clicked.connect(self._clear_history)
        self.layout.addWidget(self.clear_btn)
        
        self.refresh_list()
        
    def showEvent(self, event):
        """Refreshes list every time the panel becomes visible."""
        self.refresh_list()
        super().showEvent(event)
        
    def refresh_list(self):
        self.list_widget.clear()
        recent_files = self.history_manager.get_all()
        
        for filepath in recent_files:
            filename = os.path.basename(filepath)
            item = QListWidgetItem(filename)
            item.setToolTip(filepath)
            # Store the full path invisibly on the item
            item.setData(Qt.ItemDataRole.UserRole, filepath)
            self.list_widget.addItem(item)
            
    def _on_item_clicked(self, item: QListWidgetItem):
        filepath = item.data(Qt.ItemDataRole.UserRole)
        
        if os.path.exists(filepath):
            self.file_selected.emit(filepath)
        else:
            filename = os.path.basename(filepath)
            QMessageBox.critical(
                self,
                "Error",
                f"File not found: {filename}. It may have been moved or deleted."
            )
            
    def _clear_history(self):
        # We manually iterate through the getter to ensure all items are wiped using the manager's logic
        for f in self.history_manager.get_all():
            self.history_manager.remove_entry(f)
        self.refresh_list()
