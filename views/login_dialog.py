# dosya: views/login_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction
import qtawesome as qta
from utils.themed_widgets import PrimaryButton, DangerButton, NeutralButton

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Giriş Paneli")
        self.setModal(True)
        self.setObjectName("LoginDialog")
        
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setContentsMargins(30, 25, 30, 25)
        main_layout.setSpacing(18)

        logo_layout = QHBoxLayout()
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setScaledContents(True)
        self.logo_label.setMaximumHeight(60)
        self.logo_label.setVisible(False) 
        
        logo_layout.addStretch()
        logo_layout.addWidget(self.logo_label)
        logo_layout.addStretch()
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Kullanıcı Adı")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Şifre")
        self.password_input.setEchoMode(QLineEdit.Password)

        self.toggle_password_action = QAction(self)
        self.eye_icon = qta.icon('fa5s.eye')
        self.eye_slash_icon = qta.icon('fa5s.eye-slash')
        self.toggle_password_action.setIcon(self.eye_slash_icon)
        self.password_input.addAction(self.toggle_password_action, QLineEdit.TrailingPosition)
        self.toggle_password_action.triggered.connect(self._toggle_password_visibility)

        self.error_label = QLabel("")
        self.error_label.setObjectName("ErrorLabel")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.setVisible(False)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.cancel_button = NeutralButton("Vazgeç")
        self.login_button = PrimaryButton("Giriş Yap")
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.login_button)
        
        self.prompt_label = QLabel("Lütfen giriş yapınız.")
        self.prompt_label.setObjectName("DialogPromptLabel")
        self.prompt_label.setAlignment(Qt.AlignCenter)
        
        main_layout.addLayout(logo_layout)
        main_layout.addWidget(self.prompt_label)
        main_layout.addWidget(self.username_input)
        main_layout.addWidget(self.password_input)
        main_layout.addWidget(self.error_label)
        main_layout.addLayout(button_layout)
        
        self.password_input.returnPressed.connect(self.login_button.click)
        self.cancel_button.clicked.connect(self.reject)
        self.username_input.setFocus()

    def _toggle_password_visibility(self):
        if self.password_input.echoMode() == QLineEdit.Password:
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.toggle_password_action.setIcon(self.eye_icon)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.toggle_password_action.setIcon(self.eye_slash_icon)