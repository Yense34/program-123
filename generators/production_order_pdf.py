# dosya: generators/production_order_pdf.py

from datetime import datetime
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from .base_pdf_generator import BasePdfGenerator
import logging

TOP_MARGIN = 2 * cm
BOTTOM_MARGIN = 2 * cm
LEFT_MARGIN = 2 * cm
RIGHT_MARGIN = 2 * cm

TITLE_COLOR = colors.HexColor("#2C3E50")
TEXT_COLOR = colors.HexColor("#34495E")
TABLE_HEADER_COLOR = colors.HexColor("#34495E")
GRID_COLOR = colors.black
ROW_COLORS = [colors.HexColor("#FFFFFF"), colors.HexColor("#F8F9FA")]

FONT_SIZE_TITLE = 20
FONT_SIZE_HEADER = 12
FONT_SIZE_NORMAL = 10

class ProductionOrderGenerator(BasePdfGenerator):
    def __init__(self, sale_id: int, data: dict, settings: dict):
        super().__init__(sale_id, data, settings, "Imalat_Emirleri", "IsEmri")

    def _draw(self):
        self._draw_header()
        self._draw_info_section()
        self._draw_products_table()

    def _draw_header(self):
        y_pos = self.height - TOP_MARGIN
        company_name = self.settings.get('company_name', 'Firma Adı')
        
        self.c.setFont(self.font_name_bold, FONT_SIZE_NORMAL)
        self.c.setFillColor(TEXT_COLOR)
        self.c.drawString(LEFT_MARGIN, y_pos, company_name)

        self.c.setFont(self.font_name_bold, FONT_SIZE_TITLE)
        self.c.setFillColor(TITLE_COLOR)
        self.c.drawCentredString(self.width / 2.0, y_pos - 0.5*cm, "İŞ EMRİ FORMU")
        
        line_y = y_pos - 1.2*cm
        self.c.setStrokeColorRGB(0.8, 0.8, 0.8)
        self.c.line(LEFT_MARGIN, line_y, self.width - RIGHT_MARGIN, line_y)

    def _draw_info_section(self):
        y_pos = self.height - TOP_MARGIN - 2*cm
        sale_info = self.data['sale_info']
        customer_name = sale_info.get('musteri_adi', 'Bilinmeyen Müşteri')

        self.c.setFont(self.font_name_bold, FONT_SIZE_HEADER)
        self.c.setFillColor(TEXT_COLOR)
        self.c.drawString(LEFT_MARGIN, y_pos, f"Müşteri: {customer_name}")
        self.c.drawRightString(self.width - RIGHT_MARGIN, y_pos, f"İŞ EMRİ NO: #{self.sale_id}")
        
        y_pos -= 0.5*cm
        formatted_date = datetime.strptime(sale_info['satis_tarihi'], '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y')
        self.c.setFont(self.font_name, FONT_SIZE_NORMAL)
        self.c.drawRightString(self.width - RIGHT_MARGIN, y_pos, f"Tarih: {formatted_date}")

    def _draw_products_table(self):
        table_data = [['SIRA', 'ÜRÜN ADI', 'MİKTAR', 'İMALAT NOTLARI']]
        for i, detail in enumerate(self.data['details'], 1):
            table_data.append([
                str(i),
                detail['urun_ad'],
                str(detail['miktar']),
                ''
            ])

        table_width = self.width - LEFT_MARGIN - RIGHT_MARGIN
        table = Table(table_data, colWidths=[table_width*0.1, table_width*0.5, table_width*0.15, table_width*0.25])
        
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), self.font_name_bold),
            ('FONTSIZE', (0, 0), (-1, -1), FONT_SIZE_NORMAL),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), ROW_COLORS),
            ('GRID', (0, 0), (-1, -1), 1, GRID_COLOR),
            ('FONTNAME', (0, 1), (-1, -1), self.font_name),
        ])
        table.setStyle(style)
        
        table.wrapOn(self.c, self.width, self.height)
        table_y_pos = self.height - TOP_MARGIN - 4*cm - table._height
        table.drawOn(self.c, LEFT_MARGIN, table_y_pos)