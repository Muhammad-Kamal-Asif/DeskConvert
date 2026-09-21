import os
import shutil
import tempfile
import uuid
import io
import pymupdf as fitz  # PyMuPDF
from PIL import Image
from typing import Dict, Optional, List

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QImage

class CacheManager:
    def __init__(self):
        # Creates temp directory via tempfile.mkdtemp() — OS temp directory only
        self.temp_dir = tempfile.mkdtemp(prefix="deskconvert_")
        self.file_map: Dict[str, str] = {}  # original_path -> cached_path
        
    def stage_file(self, source_filepath: str) -> str:
        """Copies source file into temp directory. Returns cached copy path."""
        # Return existing staged file if already present
        if source_filepath in self.file_map and os.path.exists(self.file_map[source_filepath]):
            return self.file_map[source_filepath]
            
        filename = os.path.basename(source_filepath)
        base, ext = os.path.splitext(filename)
        
        # Unique name to avoid collisions
        unique_name = f"{base}_{uuid.uuid4().hex[:8]}{ext}"
        cached_path = os.path.join(self.temp_dir, unique_name)
        
        shutil.copy2(source_filepath, cached_path)
        self.file_map[source_filepath] = cached_path
        return cached_path
        
    def stage_files(self, file_list: List[str]) -> Dict[str, str]:
        """Stages multiple files. Returns {original_path: cached_path}."""
        return {f: self.stage_file(f) for f in file_list}
        
    def get_cached_path(self, original_path: str) -> Optional[str]:
        return self.file_map.get(original_path)
        
    def generate_thumbnail(self, cached_filepath: str, page_number: int = 0) -> QPixmap:
        """
        Low-res preview, max 200px wide.
        PDFs: PyMuPDF at 72 DPI for the specified page.
        Images: Pillow thumbnail.
        Returns QPixmap for PyQt6 display.
        """
        _, ext = os.path.splitext(cached_filepath)
        if ext.lower() == '.pdf':
            doc = fitz.open(cached_filepath)
            safe_page = max(0, min(page_number, len(doc) - 1)) if len(doc) > 0 else 0
            page = doc.load_page(safe_page)
            
            pix = page.get_pixmap(dpi=72, alpha=False)
            
            qimage = QImage(
                pix.samples,
                pix.width,
                pix.height,
                pix.stride,
                QImage.Format.Format_RGB888
            )
            
            pixmap = QPixmap.fromImage(qimage)
            doc.close()
            
            if pixmap.width() > 200:
                pixmap = pixmap.scaledToWidth(200, Qt.TransformationMode.SmoothTransformation)
            return pixmap
        else:
            img = Image.open(cached_filepath)
            img.thumbnail((200, 99999), Image.Resampling.LANCZOS)
            img = img.convert("RGB")
            data = img.tobytes("raw", "RGB")
            
            qimg = QImage(
                data,
                img.width,
                img.height,
                img.width * 3,
                QImage.Format.Format_RGB888
            )
            return QPixmap.fromImage(qimg)
            
    def get_full_res_page(self, cached_filepath: str, page_number: int = 0) -> QPixmap:
        """
        Full resolution — 300 DPI for PDFs. Used for preview modal only.
        """
        _, ext = os.path.splitext(cached_filepath)
        if ext.lower() == '.pdf':
            doc = fitz.open(cached_filepath)
            safe_page = max(0, min(page_number, len(doc) - 1)) if len(doc) > 0 else 0
            page = doc.load_page(safe_page)
            
            mat = fitz.Matrix(300/72, 300/72)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            # Use RGB colorspace explicitly to avoid channel swap issues
            qimage = QImage(
                pix.samples,
                pix.width,
                pix.height,
                pix.stride,
                QImage.Format.Format_RGB888
            )
            
            pixmap = QPixmap.fromImage(qimage)
            doc.close()
            return pixmap
        else:
            img = Image.open(cached_filepath)
            img = img.convert("RGB")
            data = img.tobytes("raw", "RGB")
            
            qimg = QImage(
                data,
                img.width,
                img.height,
                img.width * 3,
                QImage.Format.Format_RGB888
            )
            return QPixmap.fromImage(qimg)

    def get_page_count(self, cached_filepath: str) -> int:
        """PDF: actual page count. Image: returns 1."""
        _, ext = os.path.splitext(cached_filepath)
        if ext.lower() == '.pdf':
            try:
                doc = fitz.open(cached_filepath)
                count = len(doc)
                doc.close()
                return count if count > 0 else 1
            except Exception:
                return 1
        return 1
        
    def clear_cache(self):
        """Deletes all files in temp directory. Called on app exit."""
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except Exception:
            pass
        self.file_map.clear()
