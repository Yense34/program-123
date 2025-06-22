# dosya: controllers/login_controller.py

import os
import logging
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

from database import database_manager as db
from services.session_manager import session
from utils import ui_texts as texts

class LoginController:
    def __init__(self, view):
        self.view = view
        self._connect_signals()
        self._load_company_logo()

    def _connect_signals(self):
        self.view.login_button.clicked.connect(self.handle_login)

    def _load_company_logo(self):
        logo_path = db.get_setting('company_logo_path')
        if logo_path and os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                self.view.logo_label.setPixmap(pixmap)
                self.view.logo_label.setVisible(True)

    def handle_login(self):
        username = self.view.username_input.text().strip()
        password = self.view.password_input.text()

        if not username or not password:
            self.view.error_label.setText(texts.LOGIN_MSG_EMPTY_FIELDS)
            self.view.error_label.setVisible(True)
            return

        user_row = db.check_user(username, password)

        if user_row:
            session.login(dict(user_row))
            self.view.accept()
        else:
            logging.warning(f"Başarısız giriş denemesi: Kullanıcı Adı='{username}'")
            self.view.error_label.setText(texts.LOGIN_MSG_INVALID_CREDENTIALS)
            self.view.error_label.setVisible(True)