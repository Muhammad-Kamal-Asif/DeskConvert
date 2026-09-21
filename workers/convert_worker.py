import os
from PyQt6.QtCore import QThread, pyqtSignal
from core.pdf_engine import PdfEngine
from core.image_engine import ImageEngine

class ConvertWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, cached_file_path: str, output_path_or_folder: str, mode: str, dpi: int, output_format: str, watermark_enabled: bool, metadata_action: str, batch_paths=None):
        super().__init__()
        self.cached_file_path = cached_file_path
        self.output_path_or_folder = output_path_or_folder
        self.mode = mode
        self.dpi = dpi
        self.output_format = output_format
        self.watermark_enabled = watermark_enabled
        self.metadata_action = metadata_action
        self.batch_paths = batch_paths or []

    def run(self):
        try:
            self.progress.emit(10)
            result = None
            
            if self.mode == "pdf_to_image":
                filename = os.path.basename(self.cached_file_path)
                stem, _ = os.path.splitext(filename)
                
                self.progress.emit(30)
                result = PdfEngine.pdf_to_images(
                    self.cached_file_path, 
                    self.output_path_or_folder, 
                    stem, 
                    dpi=self.dpi, 
                    fmt=self.output_format
                )
                
                # Apply post-processing if necessary
                self.progress.emit(80)
                for path in result:
                    if self.watermark_enabled:
                        from core.watermark import apply_watermark
                        apply_watermark(path)
                    if self.metadata_action == "strip":
                        from core.metadata import strip_metadata
                        strip_metadata(path)
                        
            elif self.mode == "image_to_pdf":
                self.progress.emit(50)
                # image_to_pdf expects a list of paths
                result = PdfEngine.image_to_pdf(
                    [self.cached_file_path],
                    self.output_path_or_folder,
                    self.watermark_enabled,
                    self.metadata_action
                )
                
            elif self.mode == "image_to_image":
                self.progress.emit(50)
                result = ImageEngine.convert_image(
                    self.cached_file_path, 
                    self.output_path_or_folder, 
                    self.output_format
                )
                if self.watermark_enabled:
                    from core.watermark import apply_watermark
                    apply_watermark(result)
                if self.metadata_action == "strip":
                    from core.metadata import strip_metadata
                    strip_metadata(result)
            elif self.mode == "batch_image":
                from core.image_engine import ImageEngine
                engine = ImageEngine()
                batch_paths = getattr(self, "batch_paths", 
                                      [self.cached_file_path])
                results = []
                for i, path in enumerate(batch_paths):
                    res = engine.convert_image(
                        path,
                        self.output_path_or_folder,
                        self.output_format
                    )
                    results.append(res)
                    self.progress.emit(
                        int((i + 1) / len(batch_paths) * 100)
                    )
                self.finished.emit(results)
                return
            else:
                raise ValueError(f"Unknown conversion mode: {self.mode}")

            self.progress.emit(100)
            self.finished.emit(result)
            
        except Exception as e:
            self.error.emit(str(e))
