import os
import pymupdf as fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont

class WatermarkEngine:
    """Core engine for applying watermarks to PDFs and images."""
    
    TEXT = "DeskConvert | Made by Muhammad Kamal"
    FONT_SIZE = 8
    COLOR = (170, 170, 170)
    MARGIN = 10
    OPACITY = 0.3  # 30%

    @staticmethod
    def apply_to_pdf(pdf_path: str) -> None:
        """Applies watermark in-place to output file."""
        doc = fitz.open(pdf_path)
        for page in doc:
            rect = page.rect
            # Calculate text width for placement
            tw = fitz.get_text_length(WatermarkEngine.TEXT, fontname="helv", fontsize=WatermarkEngine.FONT_SIZE)
            
            # Position: bottom-right corner, 10px margin
            x = rect.width - tw - WatermarkEngine.MARGIN
            y = rect.height - WatermarkEngine.MARGIN
            
            p = fitz.Point(x, y)
            
            # fitz uses 0-1 scale for RGB
            color = (WatermarkEngine.COLOR[0]/255, WatermarkEngine.COLOR[1]/255, WatermarkEngine.COLOR[2]/255)
            
            page.insert_text(
                p, 
                WatermarkEngine.TEXT, 
                fontname="helv", 
                fontsize=WatermarkEngine.FONT_SIZE,
                color=color, 
                fill_opacity=WatermarkEngine.OPACITY
            )
            
        # Save to temp and replace to ensure atomic write and avoid locking issues
        temp_path = pdf_path + ".tmp"
        doc.save(temp_path)
        doc.close()
        os.replace(temp_path, pdf_path)

    @staticmethod
    def apply_to_image(image_path: str) -> None:
        """Applies watermark in-place to output file."""
        with Image.open(image_path) as img:
            original_mode = img.mode
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
                
            overlay = Image.new('RGBA', img.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(overlay)
            
            try:
                # 8pt is approx 11px on standard 96dpi displays
                font = ImageFont.truetype("arial.ttf", 11) 
            except IOError:
                font = ImageFont.load_default()
                
            left, top, right, bottom = draw.textbbox((0, 0), WatermarkEngine.TEXT, font=font)
            tw = right - left
            th = bottom - top
            
            x = img.width - tw - WatermarkEngine.MARGIN
            y = img.height - th - WatermarkEngine.MARGIN
            
            # Apply opacity to alpha channel: 30% of 255 = 76
            fill_color = WatermarkEngine.COLOR + (int(255 * WatermarkEngine.OPACITY),)
            
            draw.text((x, y), WatermarkEngine.TEXT, font=font, fill=fill_color)
            
            watermarked = Image.alpha_composite(img, overlay)
            
            # Convert back to original format safely
            if original_mode in ('RGB', 'P', 'L'):
                bg = Image.new("RGB", watermarked.size, (255, 255, 255))
                bg.paste(watermarked, mask=watermarked.split()[3])
                watermarked = bg
                if original_mode == 'P':
                    watermarked = watermarked.quantize()
            elif original_mode != 'RGBA':
                watermarked = watermarked.convert(original_mode)
                
            watermarked.save(image_path)

    @staticmethod
    def apply(file_path: str) -> None:
        """Detects type by extension, routes to correct method."""
        _, ext = os.path.splitext(file_path)
        if ext.lower() == '.pdf':
            WatermarkEngine.apply_to_pdf(file_path)
        else:
            WatermarkEngine.apply_to_image(file_path)


# Expose an alias so it seamlessly matches the logic requested in pdf_engine.py
apply_watermark = WatermarkEngine.apply
