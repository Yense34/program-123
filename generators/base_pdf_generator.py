# dosya: generators/base_pdf_generator.py

import os
import webbrowser
import logging
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from utils.helpers import sanitize_filename

class BasePdfGenerator:
    def __init__(self, sale_id: int, data: dict, settings: dict, output_dir_name: str, file_prefix: str):
        self.sale_id = sale_id
        self.data = data
        self.settings = settings
        self.output_dir_name = output_dir_name
        self.file_prefix = file_prefix

        self.width, self.height = A4
        self.font_name = "Helvetica"
        self.font_name_bold = "Helvetica-Bold"
        self._register_fonts()

    def _register_fonts(self):
        font_path = os.path.join("assets", "fonts", "Verdana.ttf")
        font_path_bold = os.path.join("assets", "fonts", "Verdanab.ttf")

        try:
            if os.path.exists(font_path) and os.path.exists(font_path_bold):
                pdfmetrics.registerFont(TTFont('Verdana', font_path))
                pdfmetrics.registerFont(TTFont('Verdana-Bold', font_path_bold))
                self.font_name = "Verdana"
                self.font_name_bold = "Verdana-Bold"
            else:
                logging.warning(f"Verdana font dosyaları 'assets/fonts/' klasöründe bulunamadı. PDF'te Türkçe karakter sorunları olabilir.")
        except Exception as e:
            logging.error(f"Fontlar kaydedilirken hata oluştu: {e}")

    def _setup_filepath(self) -> str:
        output_dir = os.path.join("CIKTILAR", self.output_dir_name)
        os.makedirs(output_dir, exist_ok=True)

        customer_name = "Rapor"
        if hasattr(self, 'report_title'):
             customer_name = self.report_title
        elif self.data and 'sale_info' in self.data:
            customer_name = self.data['sale_info'].get('musteri_adi', 'Bilinmeyen_Musteri')
            
        safe_customer_name = sanitize_filename(customer_name)
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        id_part = f"_{self.sale_id}" if self.sale_id != 0 else ""
        
        filename = f"{self.file_prefix}{id_part}_{safe_customer_name}_{date_str}.pdf"
        return os.path.join(output_dir, filename)

    def generate(self) -> tuple[bool, str]:
        try:
            self.file_path = self._setup_filepath()
            self.c = canvas.Canvas(self.file_path, pagesize=A4)
            
            self._draw()
            self.c.save()
            logging.info(f"PDF oluşturuldu: {self.file_path}")
            self._open_file()
            return True, f"{self.file_prefix} PDF'i başarıyla oluşturuldu."
        except Exception as e:
            error_msg = f"PDF oluşturulurken hata oluştu: {e}"
            logging.error(error_msg, exc_info=True)
            return False, error_msg

    def _draw(self):
        raise NotImplementedError("Bu metot alt sınıf tarafından ezilmelidir ('override').")

    def _open_file(self):
        try:
            webbrowser.open(os.path.realpath(self.file_path))
        except Exception as e:
            logging.error(f"PDF dosyası ({self.file_path}) otomatik olarak açılamadı: {e}")