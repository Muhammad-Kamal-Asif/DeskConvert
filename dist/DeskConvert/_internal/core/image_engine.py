import os
from PIL import Image
from typing import List, Tuple

class ImageEngine:
    """Core engine for processing Images using Pillow."""
    
    @staticmethod
    def convert_image(cached_source_path: str, output_folder: str, target_format: str) -> str:
        """
        Converts single image to target_format. 
        Saves to output_folder with original filename and new extension.
        Returns output path.
        """
        os.makedirs(output_folder, exist_ok=True)
        filename = os.path.basename(cached_source_path)
        base, _ = os.path.splitext(filename)
        
        ext = target_format.lower().lstrip('.')
        pil_format = ext.upper()
        if ext == 'jpg':
            pil_format = 'JPEG'
        elif ext == 'tif':
            pil_format = 'TIFF'
            
        out_filename = f"{base}.{ext}"
        out_path = os.path.join(output_folder, out_filename)
        
        with Image.open(cached_source_path) as img:
            # Handle alpha channel for formats that don't support transparency
            if pil_format in ('JPEG', 'BMP') and img.mode in ('RGBA', 'LA', 'P'):
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode in ('RGBA', 'LA'):
                    background.paste(img, mask=img.split()[-1])
                else:
                    background.paste(img)
                img = background
            elif img.mode == 'P' and pil_format not in ('PNG', 'GIF'):
                # General safety convert for Palettized images to RGB
                img = img.convert('RGB')
                
            img.save(out_path, format=pil_format)
            
        return out_path

    @staticmethod
    def batch_convert(cached_source_paths: List[str], output_folder: str, target_format: str) -> List[str]:
        """Runs convert_image per file. Returns list of output paths."""
        return [ImageEngine.convert_image(p, output_folder, target_format) for p in cached_source_paths]

    @staticmethod
    def get_image_size_bytes(filepath: str) -> int:
        """Returns the file size in bytes."""
        return os.path.getsize(filepath)

    @staticmethod
    def get_image_dimensions(filepath: str) -> Tuple[int, int]:
        """Returns (width, height) of the image."""
        with Image.open(filepath) as img:
            return img.size
