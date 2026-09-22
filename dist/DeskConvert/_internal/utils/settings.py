from typing import List
from PyQt6.QtCore import QSettings

class SettingsManager:
    def __init__(self):
        self._s = QSettings("MuhammadKamal", "DeskConvert")

    def get_default_output_directory(self) -> str:
        return str(self._s.value("default_output_directory", ""))

    def set_default_output_directory(self, value: str):
        self._s.setValue("default_output_directory", value)
        self._s.sync()

    def get_watermark_enabled(self) -> bool:
        val = self._s.value("watermark_enabled", True)
        if isinstance(val, str):
            return val.lower() == "true"
        return bool(val)

    def set_watermark_enabled(self, value: bool):
        self._s.setValue("watermark_enabled", value)
        self._s.sync()

    def get_metadata_action(self) -> str:
        return str(self._s.value("metadata_action", "keep"))

    def set_metadata_action(self, value: str):
        self._s.setValue("metadata_action", value)
        self._s.sync()

    def get_dpi(self) -> str:
        return str(self._s.value("dpi", "print"))

    def set_dpi(self, value: str):
        self._s.setValue("dpi", value)
        self._s.sync()

    def get_custom_dpi(self) -> int:
        return int(self._s.value("custom_dpi", 300))

    def set_custom_dpi(self, value: int):
        self._s.setValue("custom_dpi", value)
        self._s.sync()

    def get_quick_save_enabled(self) -> bool:
        val = self._s.value("quick_save_enabled", False)
        if isinstance(val, str):
            return val.lower() == "true"
        return bool(val)

    def set_quick_save_enabled(self, value: bool):
        self._s.setValue("quick_save_enabled", value)
        self._s.sync()

    def get_history(self) -> List[str]:
        val = self._s.value("history", [])
        if val is None:
            return []
        if isinstance(val, str):
            return [val]
        if isinstance(val, (list, tuple)):
            return [str(x) for x in val]
        return []

    def set_history(self, history: List[str]):
        self._s.setValue("history", history)
        self._s.sync()
