import os
from typing import List
import pymupdf as fitz  # PyMuPDF

class Validators:
    SUPPORTED_PDF = {'.pdf'}
    SUPPORTED_IMAGE = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif'}
    SUPPORTED_ALL = SUPPORTED_PDF | SUPPORTED_IMAGE

    @staticmethod
    def is_supported_file(filepath: str) -> bool:
        _, ext = os.path.splitext(filepath)
        return ext.lower() in Validators.SUPPORTED_ALL

    @staticmethod
    def is_pdf(filepath: str) -> bool:
        _, ext = os.path.splitext(filepath)
        return ext.lower() in Validators.SUPPORTED_PDF

    @staticmethod
    def is_image(filepath: str) -> bool:
        _, ext = os.path.splitext(filepath)
        return ext.lower() in Validators.SUPPORTED_IMAGE

    @staticmethod
    def is_password_protected(filepath: str) -> bool:
        if not Validators.is_pdf(filepath):
            return False
            
        try:
            doc = fitz.open(filepath)
            is_encrypted = doc.needs_pass
            doc.close()
            return is_encrypted
        except Exception:
            return False

    @staticmethod
    def compression_target_valid(target_bytes: int, current_bytes: int) -> bool:
        """True only if target is at least 10% less than current."""
        return target_bytes <= (current_bytes * 0.9)

    @staticmethod
    def get_rejected_files(file_list: List[str]) -> List[str]:
        """Returns filenames (not full paths) that are unsupported types."""
        return [os.path.basename(f) for f in file_list if not Validators.is_supported_file(f)]
