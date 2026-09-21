import os
from typing import List
from .settings import SettingsManager

class HistoryManager:
    def __init__(self):
        self.settings = SettingsManager()
        self.max_history = 10

    def add_entry(self, filepath: str):
        history = self.settings.get_history()
        
        if filepath in history:
            history.remove(filepath)
            
        history.insert(0, filepath)
        
        history = history[:self.max_history]
        self.settings.set_history(history)

    def remove_entry(self, filepath: str):
        history = self.settings.get_history()
        if filepath in history:
            history.remove(filepath)
            self.settings.set_history(history)

    def get_all(self) -> List[str]:
        return self.settings.get_history()

    def validate_entry(self, filepath: str) -> bool:
        return os.path.exists(filepath) and os.path.isfile(filepath)
