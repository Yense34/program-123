# dosya: views/user_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QComboBox, QHBoxLayout, QWidget
)
from utils import ui_texts as texts
from utils.themed_widgets import SuccessButton, NeutralButton

class UserDialog(QDialog):
    def __init__(self, parent=None, user_data=None, roles=None):
        super().__init__(parent)
        self.is_edit_mode = user_data is not None
        title = "Kullanıcı Düzenle" if self.is_edit_mode else texts.USER_DIALOG_TITLE
        self.setWindowTitle(title)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText(texts.USER_DIALOG_USERNAME_PLACEHOLDER)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText(texts.USER_DIALOG_PASSWORD_PLACEHOLDER)
        
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setPlaceholderText(texts.USER_DIALOG_CONFIRM_PASSWORD_PLACEHOLDER)
        
        self.role_combo = QComboBox()
        if roles:
            for rol in roles:
                self.role_combo.addItem(rol['ad'], rol['id'])

        form_layout.addRow(texts.USER_DIALOG_USERNAME_LABEL, self.username_input)
        
        if not self.is_edit_mode:
            form_layout.addRow(texts.USER_DIALOG_PASSWORD_LABEL, self.password_input)
            form_layout.addRow(texts.USER_DIALOG_CONFIRM_PASSWORD_LABEL, self.confirm_password_input)

        form_layout.addRow(texts.USER_DIALOG_ROLE_LABEL, self.role_combo)

        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 15, 0, 0)
        button_layout.addStretch()
        
        self.cancel_button = NeutralButton(texts.BTN_CANCEL)
        self.save_button = SuccessButton(texts.BTN_SAVE)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)

        layout.addLayout(form_layout)
        layout.addWidget(button_container)
        
        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        if self.is_edit_mode and user_data:
            self.username_input.setText(user_data.get('kullanici_adi'))
            self.username_input.setReadOnly(True)
            rol_id = user_data.get('rol_id')
            if rol_id is not None:
                index = self.role_combo.findData(rol_id)
                if index >= 0:
                    self.role_combo.setCurrentIndex(index)
        
        self.username_input.setFocus()

    def get_data(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()

        if not self.is_edit_mode:
            if len(username) < 4 or len(password) < 4:
                return "short"
            if password != confirm_password:
                return "mismatch"
            
        return {
            "username": username,
            "password": password,
            "role_id": self.role_combo.currentData()
        }