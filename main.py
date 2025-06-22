import sys
import logging
from PySide6.QtWidgets import QApplication, QDialog

from utils.logger_config import setup_logging, handle_exception
from database import database_manager as db
from views.login_dialog import LoginDialog
from controllers.login_controller import LoginController
from styles.base_stylesheet import BASE_STYLESHEET
from utils.signals import app_signals

def main():
    try:
        setup_logging()
        sys.excepthook = handle_exception
        db.create_tables()
        
        app_signals.app_closed.connect(db.perform_automatic_backup)
        
        app = QApplication(sys.argv)
        
        app.setStyleSheet(BASE_STYLESHEET)
        
        login_dialog = LoginDialog()
        _ = LoginController(login_dialog)
        
        if login_dialog.exec() == QDialog.Accepted:
            from views.main_window import MainWindow
            from controllers.app_controller import AppController
            
            main_window = MainWindow()
            _ = AppController(main_window)
            main_window.show()
            
            sys.exit(app.exec())
        else:
            sys.exit(0)

    except Exception as e:
        logging.critical("Uygulama başlatılırken kritik bir hata oluştu!", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()