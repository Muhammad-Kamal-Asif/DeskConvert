from PyQt6.QtCore import QThread, pyqtSignal
from core.pdf_engine import PdfEngine

class SplitWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, cached_pdf_path: str, page_ranges: list, output_mode: str, output_path_or_folder: str, filename_stem: str, watermark_enabled: bool, metadata_action: str):
        super().__init__()
        self.cached_pdf_path = cached_pdf_path
        self.page_ranges = page_ranges
        self.output_mode = output_mode
        self.output_path_or_folder = output_path_or_folder
        self.filename_stem = filename_stem
        self.watermark_enabled = watermark_enabled
        self.metadata_action = metadata_action

    def run(self):
        try:
            self.progress.emit(10)
            
            result = PdfEngine.split_pdf(
                self.cached_pdf_path,
                self.page_ranges,
                self.output_mode,
                self.output_path_or_folder,
                self.filename_stem,
                self.watermark_enabled,
                self.metadata_action
            )
            
            self.progress.emit(100)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
