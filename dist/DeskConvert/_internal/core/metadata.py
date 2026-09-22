import os
import pymupdf as fitz  # PyMuPDF
from PIL import Image

class MetadataEngine:
    """Core engine for preserving or scrubbing metadata from files."""

    @staticmethod
    def keep_metadata(source_cached_path: str, output_path: str) -> None:
        """
        Copies metadata from cached source to output if formats are compatible.
        PDFs: copies PyMuPDF info dict.
        Images: copies EXIF data via Pillow.
        """
        _, ext_out = os.path.splitext(output_path)
        _, ext_src = os.path.splitext(source_cached_path)
        
        # Only attempt to copy if both are same core type (PDF -> PDF or Image -> Image)
        if ext_out.lower() == '.pdf' and ext_src.lower() == '.pdf':
            src_doc = fitz.open(source_cached_path)
            out_doc = fitz.open(output_path)
            
            out_doc.set_metadata(src_doc.metadata)
            
            temp_path = output_path + ".tmp"
            out_doc.save(temp_path)
            out_doc.close()
            src_doc.close()
            os.replace(temp_path, output_path)
            
        elif ext_out.lower() in {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.webp'} and \
             ext_src.lower() in {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.webp'}:
            with Image.open(source_cached_path) as src_img:
                exif = src_img.info.get("exif")
                if exif:
                    with Image.open(output_path) as out_img:
                        out_img.save(output_path, exif=exif)

    @staticmethod
    def strip_metadata(output_path: str) -> None:
        """
        Strips all metadata from the output file.
        PDFs: writes blank information dictionary.
        Images: re-saves without any EXIF data.
        """
        _, ext = os.path.splitext(output_path)
        
        if ext.lower() == '.pdf':
            doc = fitz.open(output_path)
            empty_metadata = {
                'format': '',
                'title': '',
                'author': '',
                'subject': '',
                'keywords': '',
                'creator': '',
                'producer': '',
                'creationDate': '',
                'modDate': '',
                'trapped': ''
            }
            doc.set_metadata(empty_metadata)
            
            temp_path = output_path + ".tmp"
            doc.save(temp_path)
            doc.close()
            os.replace(temp_path, output_path)
            
        else:
            # Images: re-saves via Pillow without any EXIF data
            with Image.open(output_path) as img:
                # Create a completely fresh canvas and paste the pixel data
                # This guarantees zero metadata bleed-over from the original info dict
                img_clean = Image.new(img.mode, img.size)
                img_clean.paste(img)
                
                if img.mode == 'P':
                    palette = img.getpalette()
                    if palette:
                        img_clean.putpalette(palette)
                
                save_kwargs = {}
                if 'transparency' in img.info:
                    save_kwargs['transparency'] = img.info['transparency']
                    
                img_clean.save(output_path, **save_kwargs)

# Expose an alias so it seamlessly matches the logic requested in pdf_engine.py
strip_metadata = MetadataEngine.strip_metadata
