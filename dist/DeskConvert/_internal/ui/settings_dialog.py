from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QCheckBox, QRadioButton, QSpinBox, QFileDialog, QButtonGroup, QFrame
)
from PyQt6.QtCore import Qt

from utils.settings import SettingsManager

class Separator(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFrameShadow(QFrame.Shadow.Sunken)
        self.setStyleSheet("background-color: #E0E0E0;")

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(450, 400)
        
        self.settings = SettingsManager()
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 1. Output Directory
        out_label = QLabel("<b>Default Output Directory</b>")
        layout.addWidget(out_label)
        
        path_layout = QHBoxLayout()
        self.out_dir_edit = QLineEdit()
        self.out_dir_edit.setReadOnly(True)
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._browse_output_dir)
        
        path_layout.addWidget(self.out_dir_edit)
        path_layout.addWidget(self.browse_btn)
        layout.addLayout(path_layout)
        
        self.quick_save_cb = QCheckBox("Enable Quick Save (skip Save As dialog)")
        layout.addWidget(self.quick_save_cb)
        
        layout.addWidget(Separator())
        
        # 2. Watermark
        wm_label = QLabel("<b>Watermark</b>")
        layout.addWidget(wm_label)
        
        self.watermark_cb = QCheckBox("Add watermark to all outputs (except OCR)")
        layout.addWidget(self.watermark_cb)
        
        wm_note = QLabel("Watermark: DeskConvert | Made by Muhammad Kamal")
        wm_note.setStyleSheet("color: #666666; font-size: 11px;")
        layout.addWidget(wm_note)
        
        layout.addWidget(Separator())
        
        # 3. Metadata Handling
        meta_label = QLabel("<b>Metadata</b>")
        layout.addWidget(meta_label)
        
        self.meta_keep_rb = QRadioButton("Keep Metadata (default)")
        self.meta_strip_rb = QRadioButton("Strip Metadata (remove all author, date, EXIF data)")
        
        self.meta_bg = QButtonGroup(self)
        self.meta_bg.addButton(self.meta_keep_rb)
        self.meta_bg.addButton(self.meta_strip_rb)
        
        layout.addWidget(self.meta_keep_rb)
        layout.addWidget(self.meta_strip_rb)
        
        layout.addWidget(Separator())
        
        # 4. Export Resolution
        res_label = QLabel("<b>Export Resolution</b>")
        layout.addWidget(res_label)
        
        self.res_screen_rb = QRadioButton("Screen (72 DPI)")
        self.res_print_rb = QRadioButton("Print (300 DPI)")
        self.res_custom_rb = QRadioButton("Custom")
        
        self.res_bg = QButtonGroup(self)
        self.res_bg.addButton(self.res_screen_rb)
        self.res_bg.addButton(self.res_print_rb)
        self.res_bg.addButton(self.res_custom_rb)
        
        custom_layout = QHBoxLayout()
        self.res_spin = QSpinBox()
        self.res_spin.setRange(72, 1200)
        self.res_spin.setEnabled(False) 
        
        custom_layout.addWidget(self.res_custom_rb)
        custom_layout.addWidget(self.res_spin)
        custom_layout.addStretch()
        
        self.res_custom_rb.toggled.connect(self.res_spin.setEnabled)
        
        layout.addWidget(self.res_screen_rb)
        layout.addWidget(self.res_print_rb)
        layout.addLayout(custom_layout)
        
        layout.addStretch()
        
        # Bottom Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.save_btn = QPushButton("Save")
        self.save_btn.setMinimumWidth(80)
        self.save_btn.clicked.connect(self._save_settings)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setMinimumWidth(80)
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)
        
        self._load_settings()
        
    def _browse_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Output Directory", self.out_dir_edit.text())
        if dir_path:
            self.out_dir_edit.setText(dir_path)
            
    def _load_settings(self):
        # Output directory
        self.out_dir_edit.setText(
            self.settings.get_default_output_directory()
        )
        self.quick_save_cb.setChecked(
            self.settings.get_quick_save_enabled()
        )
        # Watermark
        self.watermark_cb.setChecked(
            self.settings.get_watermark_enabled()
        )
        # Metadata
        action = self.settings.get_metadata_action()
        if action == "strip":
            self.meta_strip_rb.setChecked(True)
        else:
            self.meta_keep_rb.setChecked(True)
        # DPI
        dpi = self.settings.get_dpi()
        if dpi == "screen":
            self.res_screen_rb.setChecked(True)
        elif dpi == "custom":
            self.res_custom_rb.setChecked(True)
            self.res_spin.setValue(
                self.settings.get_custom_dpi()
            )
        else:
            self.res_print_rb.setChecked(True)

    def _save_settings(self):
        self.settings.set_default_output_directory(
            self.out_dir_edit.text()
        )
        self.settings.set_quick_save_enabled(
            self.quick_save_cb.isChecked()
        )
        self.settings.set_watermark_enabled(
            self.watermark_cb.isChecked()
        )
        if self.meta_strip_rb.isChecked():
            self.settings.set_metadata_action("strip")
        else:
            self.settings.set_metadata_action("keep")
        if self.res_screen_rb.isChecked():
            self.settings.set_dpi("screen")
        elif self.res_custom_rb.isChecked():
            self.settings.set_dpi("custom")
            self.settings.set_custom_dpi(
                self.res_spin.value()
            )
        else:
            self.settings.set_dpi("print")
        self.accept()
