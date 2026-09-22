import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFileDialog, QInputDialog, QMessageBox, QStatusBar, QPushButton
)
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtCore import Qt, pyqtSignal, QObject

from ui.center_panel import CenterPanel
from ui.right_panel import RightPanel
from ui.notifications import NotificationManager
from ui.settings_dialog import SettingsDialog

from ui.left_panel import LeftPanel
from ui.status_bar import StatusBar

from core.cache_manager import CacheManager
from core.export import ExportEngine
from utils.settings import SettingsManager
from utils.history import HistoryManager
from core.compression import CompressionEngine

from workers.convert_worker import ConvertWorker
from workers.merge_worker import MergeWorker
from workers.split_worker import SplitWorker
from workers.ocr_worker import OcrWorker
from workers.compression_worker import CompressionWorker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DeskConvert")
        self.setMinimumSize(1100, 700)
        
        self._active_workers = []
        self.current_worker = None
        self.settings_manager = SettingsManager()
        self.history_manager = HistoryManager()
        self.cache_manager = CacheManager()
        self.export_engine = ExportEngine()
        self.compression_engine = CompressionEngine()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Top bar
        top_bar_widget = QWidget()
        top_bar_widget.setFixedHeight(36)
        top_bar = QHBoxLayout(top_bar_widget)
        top_bar.setContentsMargins(5, 4, 0, 4)
        top_bar.setSpacing(0)
        
        self.history_toggle_btn = QPushButton("History")
        self.history_toggle_btn.setFixedWidth(80)
        self.history_toggle_btn.setFixedHeight(28)
        self.history_toggle_btn.clicked.connect(self._toggle_history)
        
        top_bar.addWidget(self.history_toggle_btn)
        top_bar.addStretch()
        
        main_layout.addWidget(top_bar_widget)
        
        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(0)
        
        self.left_panel = LeftPanel(self)
        self.left_panel.setVisible(False)
        self.left_panel.setFixedWidth(200)
        content_row.addWidget(self.left_panel)
        
        self.center_panel = CenterPanel(self)
        self.center_panel.set_cache_manager(self.cache_manager)
        content_row.addWidget(self.center_panel)
        
        self.right_panel = RightPanel(self)
        self.right_panel.setFixedWidth(280)
        content_row.addWidget(self.right_panel)
        
        main_layout.addLayout(content_row)
        
        self.status_bar = StatusBar(self)
        self.setStatusBar(self.status_bar)
        
        self._wire_signals()
        self._setup_shortcuts()
        
    def _wire_signals(self):
        self.left_panel.file_selected.connect(self._on_left_panel_file_selected)
        
        self.center_panel.files_loaded.connect(self._on_center_panel_files_loaded)
        self.center_panel.storyboard_reordered.connect(self._update_right_panel_context)
        
        self.right_panel.action_requested.connect(self._on_action_requested)
        self.right_panel.selection_changed.connect(self._on_selection_changed)
        self.right_panel.compression_settings_changed.connect(self._on_compression_settings_changed)
        self.right_panel.settings_btn.clicked.connect(self._open_settings)
        
    def _open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()
        # Refresh UI to reflect any saved changes
        self.right_panel.refresh_dpi_label(
            self.settings_manager.get_dpi(),
            self.settings_manager.get_custom_dpi()
        )
        
    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+Z"), self).activated.connect(self.center_panel.undo_delete)
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self._trigger_current_export)
        QShortcut(QKeySequence("Delete"), self).activated.connect(self._delete_selected_thumbnail)

    def _toggle_history(self):
        visible = self.left_panel.isVisible()
        self.left_panel.setVisible(not visible)

    def _get_current_settings(self) -> dict:
        return {
            "watermark_enabled": 
                self.settings_manager.get_watermark_enabled(),
            "metadata_action": 
                self.settings_manager.get_metadata_action(),
            "dpi": self.settings_manager.get_dpi(),
            "custom_dpi": self.settings_manager.get_custom_dpi(),
        }

    def _get_dpi_value(self) -> int:
        dpi_setting = self.settings_manager.get_dpi()
        if dpi_setting == "screen":
            return 72
        elif dpi_setting == "custom":
            return self.settings_manager.get_custom_dpi()
        else:
            return 300  # print default

    def get_unique_files(self):
        order = self.center_panel.get_current_order()
        seen = set()
        unique = []
        for fp, _ in order:
            if fp not in seen:
                seen.add(fp)
                unique.append(fp)
        return unique

    def _update_right_panel_context(self, _=None):
        files = self.get_unique_files()
        has_pdf = any(f.lower().endswith('.pdf') for f in files)
        has_single_pdf = (len(files) == 1 and has_pdf)
        self.right_panel.update_context(len(files), has_pdf, has_single_pdf)
        if hasattr(self.status_bar, 'set_file_count'):
            self.status_bar.set_file_count(len(files))
        if len(files) == 0:
            self.right_panel.reset_panels()

    def _on_left_panel_file_selected(self, file_path):
        try:
            page_counts = self.cache_manager.stage_file(file_path)
            if not page_counts:
                page_counts = {file_path: 1}
        except Exception:
            page_counts = {file_path: 1}
            
        self.center_panel.load_files([file_path], page_counts)
        self._update_right_panel_context()
        self.history_manager.add_entry(file_path)

    def _on_center_panel_files_loaded(self, files):
        self._update_right_panel_context()
        order = self.center_panel.get_current_order()
        if order:
            first_cached_path = order[0][0]
            import os
            file_size = os.path.getsize(first_cached_path)
            self.right_panel.set_compression_default(file_size)
            
            page_count = self.cache_manager.get_page_count(first_cached_path)
            self.right_panel.set_page_count(page_count)
        
    def _on_selection_changed(self, ranges):
        indices = []
        for f, t in ranges:
            indices.extend(range(f - 1, t))
        self.center_panel.highlight_pages(indices)
        
    def _on_compression_settings_changed(self, target_bytes, is_enabled):
        order = self.center_panel.get_current_order()
        if not order or not is_enabled:
            return
            
        cached_file_path = order[0][0]
        try:
            suggestion = self.compression_engine.analyze(
                cached_file_path, target_bytes
            )
            self.right_panel.show_compression_suggestion(suggestion)
        except ValueError:
            from ui.notifications import NotificationManager
            NotificationManager.show_compression_invalid(self)
            return
        
    def _on_action_requested(self, action, params):
        if action == "pdf_to_img": action = "pdf_to_image"
        if action == "img_to_pdf": action = "image_to_pdf"
        
        quick_save = self.settings_manager.get_quick_save_enabled()
        out_dir = self.settings_manager.get_default_output_directory()
            
        if not out_dir:
            out_dir = ExportEngine.get_default_directory(self.settings_manager)
            
        def get_save_file(filter_str):
            if quick_save:
                return ExportEngine.safe_output_path(out_dir, action, ".pdf")
            path, _ = QFileDialog.getSaveFileName(self, "Save As", out_dir, filter_str)
            return path
            
        def get_save_dir():
            if quick_save:
                return out_dir
            path = QFileDialog.getExistingDirectory(self, "Select Output Folder", out_dir)
            return path

        dest = None
        worker = None
        
        files = self.get_unique_files()
        if not files:
            return
            
        dpi = self._get_dpi_value()
        watermark = self.settings_manager.get_watermark_enabled()
        metadata = self.settings_manager.get_metadata_action()
        
        if action == "pdf_to_image":
            try:
                dest = get_save_dir()
                if dest:
                    fmt_items = ["JPG", "PNG"]
                    fmt_choice, ok = QInputDialog.getItem(
                        self,
                        "Select Image Format",
                        "Convert pages to:",
                        fmt_items, 0, False
                    )
                    if not ok:
                        return
                    output_format = fmt_choice.lower()
                    worker = ConvertWorker(files[0], dest, action, dpi, output_format, watermark, metadata)
            except Exception as e:
                NotificationManager.show_error(self, "Error", str(e))
            
        elif action == "image_to_pdf":
            dest = get_save_file("PDF Files (*.pdf)")
            if dest: worker = ConvertWorker(files[0], dest, action, dpi, "pdf", watermark, metadata)
            
        elif action == "merge":
            dest = get_save_file("PDF Files (*.pdf)")
            if dest: worker = MergeWorker(files, dest, watermark, metadata)
            
        elif action == "split":
            page_ranges = self.right_panel.get_page_ranges()
            if not page_ranges:
                NotificationManager.show_error(
                    self, "No Pages Selected",
                    "Please set a page range before splitting."
                )
                return
            
            import os
            stem = os.path.splitext(
                os.path.basename(files[0])
            )[0]
            
            output_path, _ = QFileDialog.getSaveFileName(
                self, "Save Split PDF",
                ExportEngine.get_default_directory(self.settings_manager),
                "PDF Files (*.pdf)"
            )
            if not output_path:
                return
            
            worker = SplitWorker(
                cached_pdf_path=files[0],
                page_ranges=page_ranges,
                output_mode="single",
                output_path_or_folder=output_path,
                filename_stem=stem,
                watermark_enabled=watermark,
                metadata_action=metadata
            )
            dest = output_path
            
        elif action == "batch_convert":
            order = self.center_panel.get_current_order()
            if not order:
                return
            
            # Get only image files from current session
            import os
            cached_image_paths = [
                path for path, _ in order
                if not path.lower().endswith(".pdf")
            ]
            
            if not cached_image_paths:
                NotificationManager.show_error(
                    self, "No Images",
                    "Batch Convert requires image files. "
                    "No images are currently loaded."
                )
                return
            
            # Ask user for target format
            target_format, ok = QInputDialog.getItem(
                self,
                "Select Output Format",
                "Convert all images to:",
                ["PNG", "JPG", "WEBP", "BMP", "TIFF"],
                0, False
            )
            if not ok:
                return
            
            # Ask user for output folder
            out_dir = QFileDialog.getExistingDirectory(
                self,
                "Select Output Folder",
                ExportEngine.get_default_directory(self.settings_manager)
            )
            if not out_dir:
                return
            
            # Launch CompressionWorker — actually use ConvertWorker 
            # with ImageEngine directly via a dedicated worker
            # Use CompressionWorker pattern but for image conversion

            worker = ConvertWorker(
                cached_file_path=cached_image_paths[0],
                output_path_or_folder=out_dir,
                mode="batch_image",
                dpi=self._get_dpi_value(),
                output_format=target_format.lower(),
                watermark_enabled=self.settings_manager.get_watermark_enabled(),
                metadata_action=self.settings_manager.get_metadata_action(),
                batch_paths=cached_image_paths
            )
            self._active_workers.append(worker)
            worker.progress.connect(
                lambda p: self.status_bar.set_operation(
                    f"Converting... {p}%"
                )
            )
            worker.finished.connect(
                lambda result: self._on_worker_finished(result, out_dir)
            )
            worker.error.connect(
                lambda e: NotificationManager.show_error(
                    self, "Conversion Error", e
                )
            )
            worker.start()
            
        elif action == "ocr":
            items = ["Searchable PDF", "Text File"]
            choice, ok = QInputDialog.getItem(self, "OCR Output Format", "Select format:", items, 0, False)
            if not ok: return
            if choice == "Searchable PDF":
                dest = get_save_file("PDF Files (*.pdf)")
                ocr_mode = "searchable_pdf"
            else:
                dest = get_save_file("Text Files (*.txt)")
                ocr_mode = "text_file"
            if dest: worker = OcrWorker(files[0], dest, ocr_mode)
            
        elif action == "compress":
            order = self.center_panel.get_current_order()
            if not order:
                return
            cached_file_path = order[0][0]
            
            # Get compression settings from right panel
            target_bytes = self.right_panel.get_compression_target_bytes()
            
            # Determine output path
            if self.settings_manager.get_quick_save_enabled():
                out_dir = ExportEngine.get_default_directory(
                    self.settings_manager
                )
            else:
                out_dir = QFileDialog.getExistingDirectory(
                    self,
                    "Select Output Folder",
                    ExportEngine.get_default_directory(self.settings_manager)
                )
                if not out_dir:
                    return
            
            import os
            stem = os.path.splitext(
                os.path.basename(cached_file_path)
            )[0]
            extension = os.path.splitext(cached_file_path)[1].lstrip(".")
            output_path = ExportEngine.safe_output_path(
                out_dir, stem, extension
            )
            
            worker = CompressionWorker(
                cached_source_paths=[cached_file_path],
                output_folder=out_dir,
                target_bytes=target_bytes,
                batch_mode=False
            )
            worker.progress.connect(
                lambda p: self.status_bar.set_operation(
                    f"Compressing... {p}%"
                )
            )
            worker.finished.connect(
                lambda result: self._on_worker_finished(
                    result, output_path
                )
            )
            worker.error.connect(
                lambda e: NotificationManager.show_error(
                    self, "Compression Error", e
                )
            )
            self._active_workers.append(worker)
            worker.start()
            
        if worker and dest:
            self._launch_worker(worker, action, dest)

    def _launch_worker(self, worker, action, dest):
        if hasattr(worker, 'progress'):
            worker.progress.connect(self._on_worker_progress)
        if hasattr(worker, 'finished'):
            worker.finished.connect(lambda result: self._on_worker_finished(result, dest))
        if hasattr(worker, 'error'):
            worker.error.connect(self._on_worker_error)
            
        if hasattr(worker, 'start'):
            self._active_workers.append(worker)
            worker.start()
        self.current_worker = worker

    def _on_worker_progress(self, percentage: int):
        if hasattr(self.status_bar, 'set_operation'):
            self.status_bar.set_operation(f"Processing... {percentage}%")

    def _on_worker_finished(self, result, dest):
        self._active_workers = [
            w for w in self._active_workers if w.isRunning()
        ]
        if hasattr(self.status_bar, 'set_last_export'):
            self.status_bar.set_last_export(dest)
        self.history_manager.add_entry(dest)
        NotificationManager.show_info(self, "Success", f"Export finished successfully:\n{dest}")

    def _on_worker_error(self, err_msg):
        self._active_workers = [
            w for w in self._active_workers if w.isRunning()
        ]
        NotificationManager.show_error(self, "Error", err_msg)

    def _trigger_current_export(self):
        files = self.get_unique_files()
        if not files: return
        if len(files) > 1:
            self._on_action_requested("merge", {})
        else:
            has_pdf = files[0].lower().endswith('.pdf')
            if has_pdf:
                self._on_action_requested("pdf_to_image", {})
            else:
                self._on_action_requested("image_to_pdf", {})

    def _delete_selected_thumbnail(self):
        for i in reversed(range(self.center_panel.flow_layout.count())):
            item = self.center_panel.flow_layout.itemAt(i)
            if item:
                widget = item.widget()
                if hasattr(widget, 'is_selected') and widget.is_selected:
                    self.center_panel.on_delete_requested(widget.file_path, widget.page_index)
