from PyQt6.QtWidgets import QMessageBox

class NotificationManager:
    @staticmethod
    def show_error(parent, title: str, message: str):
        QMessageBox.critical(parent, title, message)

    @staticmethod
    def show_info(parent, title: str, message: str):
        QMessageBox.information(parent, title, message)

    @staticmethod
    def show_rejected_files(parent, rejected_filenames: list[str]):
        title = "Unsupported Files Skipped"
        message = "\n".join(rejected_filenames)
        QMessageBox.warning(parent, title, message)

    @staticmethod
    def show_replace_confirm(parent, current_filename: str) -> bool:
        title = "Replace Current File?"
        message = f"Replace {current_filename}? Any unsaved layout changes or page deletions will be lost."
        
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        
        replace_btn = msg_box.addButton("Replace", QMessageBox.ButtonRole.AcceptRole)
        cancel_btn = msg_box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        msg_box.setDefaultButton(cancel_btn)
        
        msg_box.exec()
        return msg_box.clickedButton() == replace_btn

    @staticmethod
    def show_password_protected(parent, filename: str):
        title = "Password Protected"
        message = f"Cannot open {filename}. This file is password-protected."
        QMessageBox.warning(parent, title, message)

    @staticmethod
    def show_file_missing(parent, filename: str):
        title = "File Not Found"
        message = f"File not found: {filename}. It may have been moved or deleted."
        QMessageBox.warning(parent, title, message)

    @staticmethod
    def show_compression_invalid(parent):
        title = "Invalid Target Size"
        message = "Target size must be at least 10% less than the current file size."
        QMessageBox.warning(parent, title, message)
