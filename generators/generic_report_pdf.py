# dosya: generators/generic_report_pdf.py

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from datetime import datetime
from .base_pdf_generator import BasePdfGenerator

HEADER_COLOR = colors.HexColor("#34495E")
ROW_COLORS = [colors.HexColor("#F8F9FA"), colors.HexColor("#FFFFFF")]
GRID_COLOR = colors.HexColor("#BDC3C7")

class GenericReportGenerator(BasePdfGenerator):
    def __init__(self, report_title: str, headers: list, data: list, file_prefix: str, summary_line: str = None):
        mock_data_for_base = {'sale_info': {'musteri_adi': 'Rapor'}}
        super().__init__(sale_id=0, data=mock_data_for_base, settings={}, output_dir_name="Raporlar", file_prefix=file_prefix)

        self.report_title = report_title
        self.headers = headers
        self.data = data
        self.summary_line = summary_line
        
        self.file_path = self._setup_filepath()

    def _setup_filepath(self) -> str:
        from utils.helpers import sanitize_filename
        import os

        output_dir = os.path.join("CIKTILAR", self.output_dir_name)
        os.makedirs(output_dir, exist_ok=True)
        
        safe_title = sanitize_filename(self.report_title)
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        filename = f"{self.file_prefix}_{safe_title}_{date_str}.pdf"
        return os.path.join(output_dir, filename)

    def _draw(self):
        self._draw_header()
        table_y_pos = self._draw_table()
        if self.summary_line:
            self._draw_summary(table_y_pos)
            
    def _draw_header(self):
        self.c.setFont(self.font_name_bold, 16)
        self.c.drawCentredString(self.width / 2.0, self.height - 1.5 * cm, self.report_title)
        
        self.c.setFont(self.font_name, 9)
        date_str = datetime.now().strftime('%d.%m.%Y %H:%M')
        self.c.drawString(2 * cm, self.height - 2.5 * cm, f"Rapor Tarihi: {date_str}")
        self.c.line(2 * cm, self.height - 2.8 * cm, self.width - 2 * cm, self.height - 2.8 * cm)
        
    def _draw_table(self):
        table_data = [self.headers] + self.data
        
        table = Table(table_data, repeatRows=1)
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HEADER_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), self.font_name_bold),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, GRID_COLOR),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), ROW_COLORS),
        ])
        table.setStyle(style)

        table.wrapOn(self.c, self.width - 4 * cm, self.height - 4 * cm)
        table_y_pos = self.height - 3.5 * cm - table._height
        table.drawOn(self.c, 2 * cm, table_y_pos)
        
        return table_y_pos

    def _draw_summary(self, table_y_pos):
        self.c.setFont(self.font_name_bold, 10)
        self.c.drawRightString(self.width - 2 * cm, table_y_pos - 1 * cm, self.summary_line)