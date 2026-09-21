import os
import pytesseract
from pdf2image import convert_from_path
import pymupdf as fitz  # PyMuPDF

class OcrEngine:
    """Core engine for OCR extraction via Tesseract."""
    
    @staticmethod
    def _check_tesseract():
        """Validates if Tesseract is installed and in PATH."""
        try:
            pytesseract.get_tesseract_version()
        except Exception:
            raise RuntimeError("Tesseract OCR is not installed or not found in PATH. Please install Tesseract and add it to your system PATH.")

    @staticmethod
    def to_searchable_pdf(cached_pdf_path: str, output_path: str) -> str:
        """
        Converts scanned PDF to searchable PDF. 
        Original layout preserved, invisible OCR text layer added underneath.
        Returns output path.
        """
        OcrEngine._check_tesseract()
        
        try:
            images = convert_from_path(cached_pdf_path)
        except Exception as e:
            if "poppler" in str(e).lower() or "not installed" in str(e).lower():
                raise RuntimeError("Poppler is missing or not in PATH. Please install Poppler for Windows.")
            raise e
        
        merged_doc = fitz.open()
        
        for img in images:
            # pytesseract returns a single-page PDF bytearray containing the image and the invisible text layer
            pdf_page_bytes = pytesseract.image_to_pdf_or_hocr(img, extension='pdf')
            doc = fitz.open("pdf", pdf_page_bytes)
            merged_doc.insert_pdf(doc)
            doc.close()
            
        merged_doc.save(output_path)
        merged_doc.close()
        
        return output_path

    @staticmethod
    def to_text_file(cached_pdf_path: str, output_path: str) -> str:
        """
        Extracts all text via pytesseract into a single .txt file.
        Pages separated by: "--- Page N ---\n"
        Returns output path.
        """
        OcrEngine._check_tesseract()
        
        try:
            images = convert_from_path(cached_pdf_path)
        except Exception as e:
            if "poppler" in str(e).lower() or "not installed" in str(e).lower():
                raise RuntimeError("Poppler is missing or not in PATH. Please install Poppler for Windows.")
            raise e
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, img in enumerate(images, start=1):
                text = pytesseract.image_to_string(img)
                f.write(f"--- Page {i} ---\n")
                f.write(text)
                f.write("\n\n")
                
        return output_path
