import sys
from PyQt6.QtWidgets import QApplication
from core.cache_manager import CacheManager

from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("DeskConvert")
    app.setOrganizationName("MuhammadKamal")
    
    # Safely instantiate the MainWindow
    try:
        window = MainWindow()
    except TypeError:
        # Fallback in case MainWindow is implemented without accepting the cache_manager arg
        window = MainWindow()
        
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
