# dosya: utils/ui_helpers.py

from PySide6.QtWidgets import QMessageBox, QInputDialog, QLineEdit
from . import ui_texts as texts

def show_message(parent, title: str, text: str, icon: QMessageBox.Icon = QMessageBox.Information):
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(text)
    msg_box.setIcon(icon)
    msg_box.setStandardButtons(QMessageBox.Ok)
    msg_box.exec()

def show_info_message(parent, text: str, title: str = texts.TITLE_SUCCESS):
    show_message(parent, title, text, QMessageBox.Information)

def show_warning_message(parent, text: str, title: str = texts.TITLE_WARNING):
    show_message(parent, title, text, QMessageBox.Warning)

def show_critical_message(parent, text: str, title: str = texts.TITLE_ERROR):
    show_message(parent, title, text, QMessageBox.Critical)

def ask_confirmation(parent, title: str, text: str, informative_text: str = "") -> bool:
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(f"<b>{text}</b>")
    if informative_text:
        msg_box.setInformativeText(informative_text)
    msg_box.setIcon(QMessageBox.Question)
    
    yes_button = msg_box.addButton(texts.BTN_YES, QMessageBox.YesRole)
    no_button = msg_box.addButton(texts.BTN_NO, QMessageBox.NoRole)
    msg_box.setDefaultButton(no_button)
    
    msg_box.exec()
    
    return msg_box.clickedButton() == yes_button

def get_text_input(parent, title: str, label: str, initial_text: str = "") -> tuple[str | None, bool]:
    text, ok = QInputDialog.getText(parent, title, label, QLineEdit.Normal, initial_text)
    
    if ok and text.strip():
        return text.strip(), True
    
    return None, False