from PyQt6.QtWidgets import QStatusBar, QLabel, QWidget, QHBoxLayout
from PyQt6.QtCore import Qt

class StatusBar(QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.operation_label = QLabel("Ready")
        self.file_count_label = QLabel("0 files loaded")
        self.export_path_label = QLabel("")
        
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(10, 0, 10, 0)
        
        # Left side
        self.operation_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.operation_label, stretch=1)
        
        # Center
        self.file_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.file_count_label, stretch=1)
        
        # Right side
        self.export_path_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.export_path_label, stretch=1)
        
        # Taking up the full status bar width using a permanent widget overlay
        self.addPermanentWidget(container, stretch=1)
        
        self.branding_label = QLabel("Made by Muhammad Kamal")
        self.branding_label.setStyleSheet(
            "color: #AAAAAA; font-size: 10px; padding-right: 8px;"
        )
        self.addPermanentWidget(self.branding_label)
        
    def set_operation(self, message: str):
        self.operation_label.setText(message)
        
    def set_file_count(self, count: int):
        if count == 1:
            self.file_count_label.setText("1 file loaded")
        else:
            self.file_count_label.setText(f"{count} files loaded")
            
    def set_last_export(self, path: str):
        metrics = self.export_path_label.fontMetrics()
        # Truncates from the left to keep filename visible (e.g., .../Documents/file.pdf)
        elided = metrics.elidedText(path, Qt.TextElideMode.ElideLeft, 300)
        
        self.export_path_label.setText(elided)
        self.export_path_label.setToolTip(path)
        
    def clear(self):
        self.set_operation("Ready")
        self.file_count_label.setText("0 files loaded")
        self.export_path_label.setText("")
        self.export_path_label.setToolTip("")
