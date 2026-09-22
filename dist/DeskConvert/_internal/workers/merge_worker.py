from PyQt6.QtCore import QThread, pyqtSignal
from core.pdf_engine import PdfEngine

class MergeWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, ordered_cached_file_list: list, output_path: str, watermark_enabled: bool, metadata_action: str):
        super().__init__()
        self.ordered_cached_file_list = ordered_cached_file_list
        self.output_path = output_path
        self.watermark_enabled = watermark_enabled
        self.metadata_action = metadata_action

    def run(self):
        try:
            self.progress.emit(10)
            
            result = PdfEngine.merge_to_pdf(
                self.ordered_cached_file_list,
                self.output_path,
                self.watermark_enabled,
                self.metadata_action
            )
            
            self.progress.emit(100)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
