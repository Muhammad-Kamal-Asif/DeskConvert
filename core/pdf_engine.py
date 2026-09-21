import os
import pymupdf as fitz  # PyMuPDF
import img2pdf
from typing import List, Tuple

from core.watermark import apply_watermark
from core.metadata import strip_metadata


class PdfEngine:
    """Core engine for processing PDF and image conversions."""

    @staticmethod
    def _post_process(pdf_path: str, watermark_enabled: bool, metadata_action: str):
        """Applies watermarks and metadata stripping to output files if requested."""
        if watermark_enabled:
            apply_watermark(pdf_path)
        if metadata_action == "strip":
            strip_metadata(pdf_path)

    @staticmethod
    def pdf_to_images(cached_pdf_path: str, output_folder: str, filename_stem: str, dpi: int = 300, fmt: str = "jpg") -> List[str]:
        """Extracts every page as an image. Saves to output_folder named filename_stem_page1.jpg etc."""
        doc = fitz.open(cached_pdf_path)
        output_paths = []
        os.makedirs(output_folder, exist_ok=True)
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=dpi)
            
            # Pages are 1-indexed in the output filename
            out_filename = f"{filename_stem}_page{page_num + 1}.{fmt}"
            out_path = os.path.join(output_folder, out_filename)
            
            pix.save(out_path)
            output_paths.append(out_path)
            
        doc.close()
        return output_paths

    @staticmethod
    def merge_to_pdf(ordered_file_list: List[str], output_path: str, watermark_enabled: bool = True, metadata_action: str = "keep") -> str:
        """Merges list of cached file paths (PDFs, images, or mix) in order into single PDF."""
        import statistics
        from PIL import Image as PilImage
        
        all_pt_widths = []
        for file_path in ordered_file_list:
            _, ext = os.path.splitext(file_path)
            if ext.lower() in {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif'}:
                with PilImage.open(file_path) as img:
                    img_w, _ = img.size
                    dpi_info = img.info.get('dpi', (96, 96))
                    dpi_x = float(dpi_info[0]) if dpi_info[0] > 0 else 96.0
                all_pt_widths.append((img_w / dpi_x) * 72)
                
        ref_w = 841.89  # fallback
        if all_pt_widths:
            ref_w = min(statistics.median(all_pt_widths), 841.89)

        merged_doc = fitz.open()
        
        for file_path in ordered_file_list:
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            
            if ext == '.pdf':
                doc = fitz.open(file_path)
                merged_doc.insert_pdf(doc)
                doc.close()
            elif ext in {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif'}:
                with PilImage.open(file_path) as img:
                    img_w, img_h = img.size
                    dpi_info = img.info.get('dpi', (96, 96))
                    dpi_x = float(dpi_info[0]) if dpi_info[0] > 0 else 96.0
                    dpi_y = float(dpi_info[1]) if dpi_info[1] > 0 else 96.0

                pt_w = (img_w / dpi_x) * 72
                pt_h = (img_h / dpi_y) * 72

                aspect = pt_h / pt_w
                page_h = ref_w * aspect
                max_h = ref_w * 2
                capped = page_h > max_h
                if capped:
                    page_h = max_h

                page = merged_doc.new_page(width=ref_w, height=page_h)

                if not capped:
                    rect = fitz.Rect(0, 0, ref_w, page_h)
                    page.insert_image(rect, filename=file_path, keep_proportion=False)
                else:
                    scale = min(ref_w / pt_w, page_h / pt_h)
                    sw = pt_w * scale
                    sh = pt_h * scale
                    x0 = (ref_w - sw) / 2
                    y0 = (page_h - sh) / 2
                    rect = fitz.Rect(x0, y0, x0 + sw, y0 + sh)
                    page.insert_image(rect, filename=file_path, keep_proportion=True)
                
        merged_doc.save(output_path)
        merged_doc.close()
        
        PdfEngine._post_process(output_path, watermark_enabled, metadata_action)
        return output_path

    @staticmethod
    def split_pdf(cached_pdf_path: str, page_ranges: List[Tuple[int, int]], output_mode: str, output_path_or_folder: str, filename_stem: str, watermark_enabled: bool = True, metadata_action: str = "keep") -> List[str]:
        """
        Splits PDF based on page_ranges (1-indexed). 
        output_mode "single": combines selected ranges into one PDF at output_path_or_folder.
        output_mode "individual": saves each page as a separate PDF in output_path_or_folder folder.
        """
        doc = fitz.open(cached_pdf_path)
        output_paths = []
        
        if not page_ranges:
            page_ranges = [(1, len(doc))]
            
        if output_mode == "single":
            new_doc = fitz.open()
            for start, end in page_ranges:
                # Convert 1-indexed ranges to 0-indexed for fitz
                new_doc.insert_pdf(doc, from_page=start - 1, to_page=end - 1)
            
            new_doc.save(output_path_or_folder)
            new_doc.close()
            
            PdfEngine._post_process(output_path_or_folder, watermark_enabled, metadata_action)
            output_paths.append(output_path_or_folder)
            
        elif output_mode == "individual":
            os.makedirs(output_path_or_folder, exist_ok=True)
            for start, end in page_ranges:
                for page_num in range(start, end + 1):
                    new_doc = fitz.open()
                    # 1-indexed to 0-indexed
                    new_doc.insert_pdf(doc, from_page=page_num - 1, to_page=page_num - 1)
                    
                    out_filename = f"{filename_stem}_page{page_num}.pdf"
                    out_path = os.path.join(output_path_or_folder, out_filename)
                    
                    new_doc.save(out_path)
                    new_doc.close()
                    
                    PdfEngine._post_process(out_path, watermark_enabled, metadata_action)
                    if out_path not in output_paths:
                        output_paths.append(out_path)
                        
        doc.close()
        return output_paths

    @staticmethod
    def image_to_pdf(image_path_list: List[str], output_path: str, watermark_enabled: bool = True, metadata_action: str = "keep") -> str:
        import statistics
        from PIL import Image as PilImage

        if not image_path_list:
            raise ValueError("No images provided.")

        # Pass 1: collect dimensions
        all_pt_widths = []
        img_dims = []
        for img_path in image_path_list:
            with PilImage.open(img_path) as img:
                img_w, img_h = img.size
                dpi_info = img.info.get('dpi', (96, 96))
                dpi_x = float(dpi_info[0]) if dpi_info[0] > 0 else 96.0
                dpi_y = float(dpi_info[1]) if dpi_info[1] > 0 else 96.0
            pt_w = (img_w / dpi_x) * 72
            pt_h = (img_h / dpi_y) * 72
            all_pt_widths.append(pt_w)
            img_dims.append((pt_w, pt_h))

        # Reference width: median capped at A4 long edge
        ref_w = min(statistics.median(all_pt_widths), 841.89)

        # Pass 2: build PDF
        out_doc = fitz.open()
        for img_path, (pt_w, pt_h) in zip(image_path_list, img_dims):
            aspect = pt_h / pt_w
            page_h = ref_w * aspect
            max_h = ref_w * 2
            capped = page_h > max_h
            if capped:
                page_h = max_h

            page = out_doc.new_page(width=ref_w, height=page_h)

            if not capped:
                rect = fitz.Rect(0, 0, ref_w, page_h)
                page.insert_image(rect, filename=img_path,
                                  keep_proportion=False)
            else:
                scale = min(ref_w / pt_w, page_h / pt_h)
                sw = pt_w * scale
                sh = pt_h * scale
                x0 = (ref_w - sw) / 2
                y0 = (page_h - sh) / 2
                rect = fitz.Rect(x0, y0, x0 + sw, y0 + sh)
                page.insert_image(rect, filename=img_path,
                                  keep_proportion=True)

        out_doc.save(output_path)
        out_doc.close()

        from core.watermark import WatermarkEngine
        from core.metadata import MetadataEngine
        if watermark_enabled:
            WatermarkEngine().apply_to_pdf(output_path)
        if metadata_action == "strip":
            MetadataEngine().strip_metadata(output_path)
        return output_path

    @staticmethod
    def get_page_count(cached_pdf_path: str) -> int:
        """Returns the page count of a PDF."""
        try:
            doc = fitz.open(cached_pdf_path)
            count = len(doc)
            doc.close()
            return count
        except Exception:
            return 0
