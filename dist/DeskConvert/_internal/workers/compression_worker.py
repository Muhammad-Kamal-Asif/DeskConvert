import os
from PyQt6.QtCore import QThread, pyqtSignal
from core.compression import CompressionEngine
from core.export import ExportEngine

class CompressionWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, cached_source_paths: list, output_folder: str, target_bytes: int, batch_mode: bool):
        super().__init__()
        self.cached_source_paths = cached_source_paths
        self.output_folder = output_folder
        self.target_bytes = target_bytes
        self.batch_mode = batch_mode

    def run(self):
        try:
            self.progress.emit(5)
            
            if not self.cached_source_paths:
                raise ValueError("No files provided for compression.")
                
            results = []
            
            if not self.batch_mode:
                file_to_process = self.cached_source_paths[0]
                _, ext = os.path.splitext(file_to_process)
                stem, _ = os.path.splitext(os.path.basename(file_to_process))
                out_path = ExportEngine.safe_output_path(self.output_folder, stem, ext)
                
                self.progress.emit(20)
                res = CompressionEngine.compress(file_to_process, out_path, self.target_bytes)
                results.append(res)
                
                self.progress.emit(100)
                
            else:
                total_files = len(self.cached_source_paths)
                for i, file_path in enumerate(self.cached_source_paths):
                    _, ext = os.path.splitext(file_path)
                    stem, _ = os.path.splitext(os.path.basename(file_path))
                    out_path = ExportEngine.safe_output_path(self.output_folder, stem, ext)
                    
                    CompressionEngine.compress(file_path, out_path, self.target_bytes)
                    results.append(out_path)
                    
                    prog = int(5 + ((i + 1) / total_files) * 90)
                    self.progress.emit(prog)
                    
                self.progress.emit(100)
                
            self.finished.emit(results)
            
        except Exception as e:
            self.error.emit(str(e))
