import os
from typing import Dict, List

class ExportEngine:
    """Core engine for computing safe output paths and resolving target directories."""
    
    @staticmethod
    def safe_output_path(directory: str, stem: str, extension: str) -> str:
        """
        Returns path that won't overwrite existing files.
        Appends _converted_01, _converted_02 etc. Example: report_converted_01.pdf
        """
        if not extension.startswith('.'):
            extension = f".{extension}"
            
        counter = 1
        while True:
            filename = f"{stem}_converted_{counter:02d}{extension}"
            full_path = os.path.join(directory, filename)
            if not os.path.exists(full_path):
                return full_path
            counter += 1

    @staticmethod
    def get_default_directory(settings_manager) -> str:
        """Returns configured default output directory if set and exists. Otherwise returns user's Desktop path."""
        configured = settings_manager.get_default_output_directory()
        if configured and os.path.isdir(configured):
            return configured
            
        # fallback to Desktop
        desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
        if os.path.isdir(desktop):
            return desktop
            
        return os.path.expanduser('~')

    @staticmethod
    def batch_output_paths(directory: str, source_paths: List[str], target_extension: str) -> Dict[str, str]:
        """
        For each source path generates a safe output path in directory with target_extension.
        Returns {source_path: safe_output_path}
        """
        result = {}
        if not target_extension.startswith('.'):
            target_extension = f".{target_extension}"
            
        for src in source_paths:
            filename = os.path.basename(src)
            stem, _ = os.path.splitext(filename)
            
            counter = 1
            while True:
                out_name = f"{stem}_converted_{counter:02d}{target_extension}"
                out_path = os.path.join(directory, out_name)
                
                # We check the disk AND our own result array to ensure no collisions in the same batch mapping
                if not os.path.exists(out_path) and out_path not in result.values():
                    result[src] = out_path
                    break
                counter += 1
                
        return result
