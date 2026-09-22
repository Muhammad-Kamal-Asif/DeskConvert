from PyQt6.QtCore import QThread, pyqtSignal
from core.ocr_engine import OcrEngine

class OcrWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, cached_pdf_path: str, output_path: str, ocr_mode: str):
        super().__init__()
        self.cached_pdf_path = cached_pdf_path
        self.output_path = output_path
        self.ocr_mode = ocr_mode

    def run(self):
        try:
            self.progress.emit(10)
            
            if self.ocr_mode == "searchable_pdf":
                result = OcrEngine.to_searchable_pdf(self.cached_pdf_path, self.output_path)
            elif self.ocr_mode == "text_file":
                result = OcrEngine.to_text_file(self.cached_pdf_path, self.output_path)
            else:
                raise ValueError(f"Unknown OCR mode: {self.ocr_mode}")
                
            self.progress.emit(100)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
