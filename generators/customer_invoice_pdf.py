# dosya: generators/customer_invoice_pdf.py

import os
import logging
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from .base_pdf_generator import BasePdfGenerator

TOP_MARGIN = 2 * cm
BOTTOM_MARGIN = 2 * cm
LEFT_MARGIN = 2 * cm
RIGHT_MARGIN = 2 * cm

PRIMARY_COLOR = colors.HexColor("#34495E")
TABLE_HEADER_COLOR = colors.HexColor("#3498DB")
TEXT_COLOR = colors.HexColor("#2C3E50")
LIGHT_TEXT_COLOR = colors.HexColor("#7F8C8D")
GRID_COLOR = colors.black

FONT_SIZE_LARGE = 11
FONT_SIZE_NORMAL = 10
FONT_SIZE_SMALL = 9

class CustomerInvoiceGenerator(BasePdfGenerator):
    def __init__(self, sale_id: int, data: dict, settings: dict):
        super().__init__(sale_id, data, settings, "Siparis_Formlari", "Siparis")

    def _draw(self):
        self._draw_header()
        self._draw_info_section()
        table_y_pos = self._draw_products_table()
        self._draw_totals(table_y_pos)

    def _draw_header(self):
        y_pos = self.height - TOP_MARGIN
        
        if logo_path := self.settings.get('company_logo_path'):
            if os.path.exists(logo_path):
                try:
                    self.c.drawImage(logo_path, LEFT_MARGIN, y_pos - 1.5*cm, width=4*cm, preserveAspectRatio=True, anchor='n')
                except Exception as e:
                    logging.warning(f"Fatura logosu çizilemedi: {e}")

        self.c.setFont(self.font_name_bold, FONT_SIZE_LARGE)
        self.c.setFillColor(TEXT_COLOR)
        self.c.drawRightString(self.width - RIGHT_MARGIN, y_pos, self.settings.get('company_name', 'Firma Adı'))
        
        y_pos -= 0.5 * cm
        self.c.setFont(self.font_name, FONT_SIZE_SMALL)
        for key in ['company_phone', 'company_email', 'company_address']:
            if value := self.settings.get(key):
                self.c.drawRightString(self.width - RIGHT_MARGIN, y_pos, value)
                y_pos -= 0.5 * cm

        line_y = self.height - TOP_MARGIN - 2.2*cm
        self.c.setStrokeColorRGB(0.8, 0.8, 0.8)
        self.c.line(LEFT_MARGIN, line_y, self.width - RIGHT_MARGIN, line_y)

    def _draw_info_section(self):
        y_pos = self.height - TOP_MARGIN - 3*cm
        sale_info = self.data['sale_info']
        
        self.c.setFont(self.font_name_bold, FONT_SIZE_NORMAL)
        self.c.setFillColor(PRIMARY_COLOR)
        self.c.drawString(LEFT_MARGIN, y_pos, "MÜŞTERİ BİLGİLERİ")
        
        self.c.setFont(self.font_name, FONT_SIZE_NORMAL)
        self.c.setFillColor(TEXT_COLOR)
        self.c.drawString(LEFT_MARGIN, y_pos - 0.5*cm, sale_info.get('musteri_adi', 'Bilinmeyen Müşteri'))
        self.c.drawString(LEFT_MARGIN, y_pos - 1*cm, f"Telefon: {sale_info.get('telefon', 'N/A')}")
        
        self.c.setFont(self.font_name_bold, FONT_SIZE_NORMAL)
        self.c.setFillColor(PRIMARY_COLOR)
        self.c.drawRightString(self.width - RIGHT_MARGIN, y_pos, f"SİPARİŞ NO: #{self.sale_id}")
        
        self.c.setFont(self.font_name, FONT_SIZE_NORMAL)
        self.c.setFillColor(TEXT_COLOR)
        formatted_date = datetime.strptime(sale_info['satis_tarihi'], '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y')
        self.c.drawRightString(self.width - RIGHT_MARGIN, y_pos - 0.5*cm, f"TARİH: {formatted_date}")

    def _draw_products_table(self):
        table_data = [['ÜRÜN ADI', 'MİKTAR', 'BİRİM FİYAT', 'TOPLAM']]
        for detail in self.data['details']:
            total_price = detail['miktar'] * detail['birim_fiyat']
            table_data.append([
                detail['urun_ad'], str(detail['miktar']),
                f"{detail['birim_fiyat']:,.2f} TL", f"{total_price:,.2f} TL"
            ])

        table_width = self.width - LEFT_MARGIN - RIGHT_MARGIN
        table = Table(table_data, colWidths=[table_width*0.5, table_width*0.15, table_width*0.175, table_width*0.175])
        
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), self.font_name_bold),
            ('FONTNAME', (0, 1), (-1, -1), self.font_name),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, GRID_COLOR),
        ])
        table.setStyle(style)
        
        table.wrapOn(self.c, self.width, self.height)
        table_y_pos = self.height - TOP_MARGIN - 5*cm - table._height
        table.drawOn(self.c, LEFT_MARGIN, table_y_pos)
        return table_y_pos

    def _draw_totals(self, table_y_pos):
        sale_info = self.data['sale_info']
        total = sale_info['toplam_tutar']
        vat_rate_str = (self.settings.get('kdv_orani') or '20').replace(',', '.')
        vat_rate = float(vat_rate_str) / 100
        subtotal = total / (1 + vat_rate)
        vat = total - subtotal
        
        totals = [
            ("Ara Toplam:", f"{subtotal:,.2f} TL", FONT_SIZE_NORMAL, TEXT_COLOR, self.font_name),
            (f"KDV (%{float(vat_rate_str):.0f}):", f"{vat:,.2f} TL", FONT_SIZE_NORMAL, TEXT_COLOR, self.font_name),
            ("GENEL TOPLAM:", f"{total:,.2f} TL", FONT_SIZE_LARGE, PRIMARY_COLOR, self.font_name_bold),
            ("Ödenen Tutar:", f"{sale_info['odenen_tutar']:,.2f} TL", FONT_SIZE_NORMAL, TEXT_COLOR, self.font_name),
            ("Kalan Tutar:", f"{(total - sale_info['odenen_tutar']):,.2f} TL", FONT_SIZE_NORMAL, TEXT_COLOR, self.font_name_bold),
        ]
        
        y_pos = table_y_pos - 1.5*cm
        x_pos_label = self.width - RIGHT_MARGIN - 3.5*cm
        x_pos_value = self.width - RIGHT_MARGIN

        for label, value, font_size, color, font_name in totals:
            self.c.setFont(font_name, font_size)
            self.c.setFillColor(color)
            self.c.drawRightString(x_pos_label, y_pos, label)
            self.c.drawRightString(x_pos_value, y_pos, value)
            y_pos -= 0.7*cm