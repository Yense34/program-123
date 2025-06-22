# dosya: utils/logger_config.py

import logging
import sys
import traceback
from logging.handlers import RotatingFileHandler
from PySide6.QtWidgets import QMessageBox, QApplication

def setup_logging():
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s')
    
    file_handler = RotatingFileHandler('app.log', maxBytes=5*1024*1024, backupCount=2, encoding='utf-8')
    file_handler.setFormatter(log_formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logging.info("Loglama sistemi başarıyla başlatıldı.")

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logging.critical("Yakalanmamış istisna:", exc_info=(exc_type, exc_value, exc_traceback))

    if QApplication.instance():
        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle("Kritik Hata Oluştu!")
        error_dialog.setText(
            "Programda beklenmedik bir hata oluştu.\n"
            "Yaptığınız son işlemler kaydedilmemiş olabilir."
        )
        error_dialog.setInformativeText(
            "Lütfen programı yeniden başlatın. Sorun devam ederse, teknik destek ile iletişime geçin. "
            "Hatanın detayı aşağıdaki kutuda ve 'app.log' dosyasında bulunmaktadır."
        )
        error_dialog.setDetailedText(f"Hata Tipi: {exc_type.__name__}\n\n{tb_str}")
        error_dialog.setStandardButtons(QMessageBox.Ok)
        error_dialog.exec()