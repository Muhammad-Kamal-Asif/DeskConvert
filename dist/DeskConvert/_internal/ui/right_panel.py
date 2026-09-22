import math
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QGroupBox,
    QPushButton, QCheckBox, QLineEdit, QSpinBox, QSpacerItem, QSizePolicy,
    QScrollArea
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QDoubleValidator

from ui.settings_dialog import SettingsDialog

from utils.settings import SettingsManager


class RightPanel(QWidget):
    action_requested = pyqtSignal(str, dict)
    compression_settings_changed = pyqtSignal(int, bool)
    selection_changed = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setMinimumWidth(250)
        self.setMaximumWidth(350)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 2. DPI Info
        self.dpi_label = QLabel("Export DPI: —")
        self.dpi_label.setStyleSheet("color: #666666; font-size: 11px;")
        layout.addWidget(self.dpi_label)
        self.refresh_dpi_label(
            SettingsManager().get_dpi(), 
            SettingsManager().get_custom_dpi()
        )
        
        # 3. Actions
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        self.btn_pdf_to_img = QPushButton("PDF → Image")
        self.btn_img_to_pdf = QPushButton("Image → PDF")
        self.btn_merge = QPushButton("Merge Files")
        self.btn_split = QPushButton("Split PDF")
        self.btn_batch = QPushButton("Batch Convert Images")
        self.btn_ocr = QPushButton("OCR")
        
        self.action_buttons = [
            (self.btn_pdf_to_img, "pdf_to_img"),
            (self.btn_img_to_pdf, "img_to_pdf"),
            (self.btn_merge, "merge"),
            (self.btn_split, "split"),
            (self.btn_batch, "batch_convert"),
            (self.btn_ocr, "ocr")
        ]
        
        for btn, act in self.action_buttons:
            actions_layout.addWidget(btn)
            btn.clicked.connect(lambda checked, a=act: self.action_requested.emit(a, {}))
            
        layout.addWidget(actions_group)
        
        # 4. Compression
        comp_group = QGroupBox("Compression")
        comp_layout = QVBoxLayout(comp_group)
        
        self.compress_cb = QCheckBox("Compress Output")
        
        self.comp_controls_widget = QWidget()
        comp_controls_layout = QVBoxLayout(self.comp_controls_widget)
        comp_controls_layout.setContentsMargins(0, 0, 0, 0)
        
        self.current_size_label = QLabel("")
        self.current_size_label.setStyleSheet("color: #666666; font-size: 11px;")
        comp_controls_layout.addWidget(self.current_size_label)
        
        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("Target Size:"))
        
        self.target_edit = QLineEdit()
        self.target_edit.setValidator(QDoubleValidator(0.01, 9999.0, 2))
        self.unit_cb = QComboBox()
        self.unit_cb.addItems(["KB", "MB"])
        self.unit_cb.setCurrentText("MB")
        
        target_layout.addWidget(self.target_edit)
        target_layout.addWidget(self.unit_cb)
        
        self.suggestion_label = QLabel("Suggestion: —")
        self.suggestion_label.setStyleSheet("color: #0066cc; font-size: 11px;")
        
        self.compress_save_btn = QPushButton("Compress & Save")
        self.compress_save_btn.clicked.connect(lambda: self.action_requested.emit("compress", {}))
        
        comp_controls_layout.addLayout(target_layout)
        comp_controls_layout.addWidget(self.suggestion_label)
        comp_controls_layout.addWidget(self.compress_save_btn)
        
        self.comp_controls_widget.setVisible(False)
        
        comp_layout.addWidget(self.compress_cb)
        comp_layout.addWidget(self.comp_controls_widget)
        
        layout.addWidget(comp_group)
        
        self.compress_cb.stateChanged.connect(self._on_compress_toggled)
        self.target_edit.textChanged.connect(self._emit_compression)
        self.unit_cb.currentTextChanged.connect(self._emit_compression)
        
        # 5. Page Selection
        self.page_sel_group = QGroupBox("Page Selection")
        self.page_sel_layout = QVBoxLayout(self.page_sel_group)
        
        self.ranges_widget = QWidget()
        self.ranges_layout = QVBoxLayout(self.ranges_widget)
        self.ranges_layout.setContentsMargins(0, 0, 0, 0)
        
        self.range_rows = []
        self.pages_selected_label = QLabel("0 pages selected")
        self._add_range_row(is_primary=True)
        
        self.page_sel_layout.addWidget(self.ranges_widget)
        
        self.page_sel_layout.addWidget(self.pages_selected_label)
        
        btn_layout = QHBoxLayout()
        self.btn_add_range = QPushButton("Add Range")
        self.btn_apply_sel = QPushButton("Apply Selection")
        btn_layout.addWidget(self.btn_add_range)
        btn_layout.addWidget(self.btn_apply_sel)
        
        self.page_sel_layout.addLayout(btn_layout)
        
        self.btn_add_range.clicked.connect(lambda: self._add_range_row(is_primary=False))
        self.btn_apply_sel.clicked.connect(self._apply_selection)
        
        self.page_sel_group.setVisible(False)
        layout.addWidget(self.page_sel_group)
        
        # 6. Settings Gear
        layout.addStretch()
        
        self.settings_btn = QPushButton("⚙ Settings")
        self.settings_btn.setStyleSheet("text-align: left; padding: 5px;")
        self.settings_btn.setFlat(True)
        layout.addWidget(self.settings_btn)

        self.update_context(0, False, False)
        
    def refresh_dpi_label(self, dpi_setting: str, custom_dpi: int = 300):
        if dpi_setting == "screen":
            text = "Export DPI: 72 (Screen)"
        elif dpi_setting == "custom":
            text = f"Export DPI: {custom_dpi} (Custom)"
        else:
            text = "Export DPI: 300 (Print)"
        self.dpi_label.setText(text)

    def _on_compress_toggled(self, state):
        is_checked = (state == Qt.CheckState.Checked.value or state == True)
        if type(state) is int:
            is_checked = (state == Qt.CheckState.Checked.value)
        self.comp_controls_widget.setVisible(is_checked)
        if not is_checked:
            self.current_size_label.setText("")
        self._emit_compression()

    def _emit_compression(self, *args):
        if not self.compress_cb.isChecked():
            self.compression_settings_changed.emit(0, False)
            return
            
        try:
            val_text = self.target_edit.text().replace(',', '.')
            if not val_text:
                return
            val = float(val_text)
            multiplier = 1024 * 1024 if self.unit_cb.currentText() == "MB" else 1024
            target_bytes = int(val * multiplier)
            self.compression_settings_changed.emit(target_bytes, True)
        except ValueError:
            pass

    def _add_range_row(self, is_primary=False):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        
        spin_from = QSpinBox()
        spin_from.setMinimum(1)
        spin_from.setMaximum(9999)
        
        spin_to = QSpinBox()
        spin_to.setMinimum(1)
        spin_to.setMaximum(9999)
        
        row_layout.addWidget(QLabel("From"))
        row_layout.addWidget(spin_from)
        row_layout.addWidget(QLabel("To"))
        row_layout.addWidget(spin_to)
        
        btn_remove = None
        if not is_primary:
            btn_remove = QPushButton("X")
            btn_remove.setFixedSize(20, 20)
            btn_remove.clicked.connect(lambda: self._remove_range_row(row_widget))
            row_layout.addWidget(btn_remove)
            
        self.ranges_layout.addWidget(row_widget)
        self.range_rows.append({
            'widget': row_widget,
            'from': spin_from,
            'to': spin_to,
            'remove': btn_remove
        })
        
        spin_from.valueChanged.connect(self._update_pages_selected_label)
        spin_to.valueChanged.connect(self._update_pages_selected_label)
        self._update_pages_selected_label()
        
    def _remove_range_row(self, widget):
        for row in self.range_rows:
            if row['widget'] == widget:
                self.range_rows.remove(row)
                widget.deleteLater()
                break
        self._update_pages_selected_label()
        
    def _update_pages_selected_label(self):
        total = 0
        for row in self.range_rows:
            f = row['from'].value()
            t = row['to'].value()
            if t >= f:
                total += (t - f + 1)
        self.pages_selected_label.setText(f"{total} pages selected")
        
    def _apply_selection(self):
        ranges = []
        for row in self.range_rows:
            f = row['from'].value()
            t = row['to'].value()
            if t >= f:
                ranges.append((f, t))
        self.selection_changed.emit(ranges)

    def get_page_ranges(self) -> list[tuple[int, int]]:
        ranges = []
        for row in self.range_rows:
            from_val = row["from"].value()
            to_val = row["to"].value()
            if from_val <= to_val:
                ranges.append((from_val, to_val))
        return ranges

    def update_context(self, file_count: int, has_pdf: bool, has_single_pdf: bool):
        if file_count == 0:
            for btn, _ in self.action_buttons:
                btn.setEnabled(False)
                btn.setToolTip("")
            self.page_sel_group.setVisible(False)
            return

        if file_count == 1:
            self.btn_pdf_to_img.setEnabled(has_pdf)
            self.btn_img_to_pdf.setEnabled(not has_pdf)
            self.btn_merge.setEnabled(False)
            self.btn_split.setEnabled(has_pdf)
            self.btn_batch.setEnabled(not has_pdf)
            self.btn_ocr.setEnabled(has_single_pdf)
            
            for btn, _ in self.action_buttons:
                btn.setToolTip("")
            
            self.btn_merge.setToolTip("Requires 2+ files")
            self.page_sel_group.setVisible(has_single_pdf)
            
        else: # 2+ files
            self.btn_pdf_to_img.setEnabled(False)
            self.btn_pdf_to_img.setToolTip("Requires a single active file")
            
            self.btn_split.setEnabled(False)
            self.btn_split.setToolTip("Requires a single active file")
            
            self.btn_merge.setEnabled(True)
            self.btn_merge.setToolTip("")
            
            self.btn_img_to_pdf.setEnabled(not has_pdf)
            self.btn_img_to_pdf.setToolTip("")
            
            self.btn_batch.setEnabled(not has_pdf)
            self.btn_batch.setToolTip("")
            
            self.btn_ocr.setEnabled(False)
            self.btn_ocr.setToolTip("Requires a single active file")
            
            self.page_sel_group.setVisible(False)

    def set_compression_default(self, file_size_bytes: int):
        target = int(file_size_bytes * 0.9)
        display_kb = round(file_size_bytes / 1024, 1)
        self.current_size_label.setText(f"Current file size: {display_kb} KB")
        self.unit_cb.setCurrentText("KB")
        self.target_edit.setText(f"{target / 1024:.2f}")

    def set_page_count(self, total_pages: int):
        if self.range_rows:
            self.range_rows[0]["from"].setValue(1)
            self.range_rows[0]["to"].setValue(total_pages)
            for row in self.range_rows[1:]:
                self._remove_range_row(row)
            self.range_rows = self.range_rows[:1]
            self._update_pages_selected_label()

    def show_compression_suggestion(self, suggestion: dict):
        qual = suggestion.get('suggested_quality', '?')
        red = suggestion.get('reduction_percent', '?')
        self.suggestion_label.setText(f"Suggestion: Quality {qual} ({red}% reduction)")
        
    def get_compression_target_bytes(self) -> int:
        value = float(self.target_edit.text() or 0)
        unit = self.unit_cb.currentText()
        if unit == "MB":
            return int(value * 1024 * 1024)
        return int(value * 1024)

    def reset_panels(self):
        # Uncheck compression
        self.compress_cb.setChecked(False)
        # Reset current file size label
        if hasattr(self, 'current_size_label'):
            self.current_size_label.setText("")
        # Hide page selection (no file loaded)
        if hasattr(self, 'page_sel_group'):
            self.page_sel_group.setVisible(False)
