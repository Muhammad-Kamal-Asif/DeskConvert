import os
import io
import pymupdf as fitz  # PyMuPDF
from PIL import Image

class CompressionEngine:
    """Core engine for compressing PDFs and images with strict file-size guardrails."""

    @staticmethod
    def analyze(cached_file_path: str, target_bytes: int) -> dict:
        """Analyzes size difference and estimates quality heuristics."""
        current_size = os.path.getsize(cached_file_path)
        if target_bytes >= current_size:
            raise ValueError("Target size must be less than current file size.")
            
        reduction_percent = ((current_size - target_bytes) / current_size) * 100.0
        
        # Estimate quality drop (heuristics)
        suggested_quality = max(10, int(100 - reduction_percent))
        estimated_output = int(current_size * (suggested_quality / 100.0))
        
        return {
            "current_size_bytes": current_size,
            "target_size_bytes": target_bytes,
            "suggested_quality": suggested_quality,
            "estimated_output_bytes": estimated_output,
            "reduction_percent": round(reduction_percent, 2)
        }

    @staticmethod
    def compress_image(cached_source_path: str, output_path: str, target_bytes: int) -> str:
        """Uses binary search on quality parameter to find closest result at or under target_bytes."""
        current_size = os.path.getsize(cached_source_path)
        if target_bytes >= current_size:
            raise ValueError("Target size must be less than current file size.")
            
        _, ext = os.path.splitext(output_path)
        ext = ext.lower()
        
        save_format = 'JPEG'
        if ext == '.webp':
            save_format = 'WEBP'
        elif ext in ('.png', '.bmp', '.tiff', '.tif'):
            save_format = ext.lstrip('.').upper()
            
        with Image.open(cached_source_path) as img:
            # Flatten transparency to white if converting to JPEG
            if save_format == 'JPEG' and img.mode in ('RGBA', 'P', 'LA'):
                bg = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode in ('RGBA', 'LA'):
                    bg.paste(img, mask=img.split()[-1])
                else:
                    bg.paste(img.convert('RGBA'))
                img = bg
            elif img.mode == 'P':
                img = img.convert('RGB')
                
            low = 5
            high = 95
            best_bytes = None
            
            while low <= high:
                mid = (low + high) // 2
                buffer = io.BytesIO()
                
                save_kwargs = {'format': save_format}
                if save_format in ('JPEG', 'WEBP'):
                    save_kwargs['quality'] = mid
                if save_format == 'JPEG':
                    save_kwargs['optimize'] = True
                    
                img.save(buffer, **save_kwargs)
                size = buffer.tell()
                
                if size <= target_bytes:
                    best_bytes = buffer.getvalue()
                    low = mid + 1  # We met the target, try to safely increase quality
                else:
                    high = mid - 1 # Too big, reduce quality
                    
            if best_bytes:
                with open(output_path, 'wb') as f:
                    f.write(best_bytes)
            else:
                # Target was too aggressive, use lowest possible quality natively supported
                save_kwargs = {'format': save_format}
                if save_format in ('JPEG', 'WEBP'):
                    save_kwargs['quality'] = 5
                img.save(output_path, **save_kwargs)
                
        return output_path

    @staticmethod
    def compress_pdf(cached_source_path: str, output_path: str, target_bytes: int) -> str:
        """Uses PyMuPDF garbage collection and deflation to compress lossless streams."""
        current_size = os.path.getsize(cached_source_path)
        if target_bytes >= current_size:
            raise ValueError("Target size must be less than current file size.")
            
        doc = fitz.open(cached_source_path)
        doc.save(
            output_path,
            garbage=4,     # Remove unused objects, deduplicate streams
            deflate=True,  # Compress raw streams
            clean=True
        )
        doc.close()
        
        return output_path

    @staticmethod
    def compress(cached_source_path: str, output_path: str, target_bytes: int) -> str:
        """Detects file type, routes to correct method."""
        _, ext = os.path.splitext(cached_source_path)
        if ext.lower() == '.pdf':
            return CompressionEngine.compress_pdf(cached_source_path, output_path, target_bytes)
        else:
            return CompressionEngine.compress_image(cached_source_path, output_path, target_bytes)
