# dosya: controllers/report_controller.py

from PySide6.QtCore import QDate, Qt, QMargins
from PySide6.QtWidgets import QApplication, QFileDialog
import openpyxl
from datetime import datetime
from PySide6.QtGui import QPainter, QFont, QColor, QPen
from PySide6.QtCharts import QChart, QLineSeries, QPieSeries, QHorizontalBarSeries, QBarSet, QValueAxis, QBarCategoryAxis

from views.table_models import GenericTableModel
from database import database_manager as db
from generators.generic_report_pdf import GenericReportGenerator
from utils import ui_helpers

class ReportController:
    def __init__(self, view):
        self.view = view
        self.current_model = None 
        self.current_report_title = ""
        
        # --- DÜZELTME: Canlı ve standart renk paleti tanımlandı ---
        self.chart_colors = [
            "#007bff", "#17a2b8", "#28a745", "#ffc107", "#dc3545", "#6f42c1"
        ]
        
        self._connect_signals()
        self._set_default_dates()
        self._populate_filters()
        self.generate_sales_report()

    def _connect_signals(self):
        self.view.generate_sales_report_button.clicked.connect(self.generate_sales_report)
        self.view.generate_inventory_report_button.clicked.connect(self.generate_inventory_report)
        self.view.generate_product_report_button.clicked.connect(self.generate_product_report)
        self.view.generate_customer_report_button.clicked.connect(self.generate_customer_report)
        self.view.export_excel_button.clicked.connect(self.export_to_excel)
        self.view.export_pdf_button.clicked.connect(self.export_to_pdf)

    def _set_default_dates(self):
        today = QDate.currentDate()
        self.view.start_date_edit.setDate(QDate(today.year(), today.month(), 1))
        self.view.end_date_edit.setDate(today)

    def _populate_filters(self):
        self.view.customer_filter_combo.blockSignals(True)
        self.view.customer_filter_combo.clear()
        self.view.customer_filter_combo.addItem("Tüm Müşteriler", None)
        customers = db.search_customers(query="")
        for customer in customers:
            self.view.customer_filter_combo.addItem(f"{customer['ad']} {customer['soyad']}", customer['id'])
        self.view.customer_filter_combo.blockSignals(False)

        self.view.category_filter_combo.blockSignals(True)
        self.view.category_filter_combo.clear()
        self.view.category_filter_combo.addItem("Tüm Kategoriler", None)
        categories = db.get_all_kategoriler()
        for category in categories:
            self.view.category_filter_combo.addItem(category['ad'], category['id'])
        self.view.category_filter_combo.blockSignals(False)

    def _setup_report(self, title: str, headers: list, column_keys: list, enabled_filters: dict):
        self.view.show_loading(True)
        QApplication.processEvents()

        self.current_report_title = title
        self.view.customer_filter_combo.setEnabled(enabled_filters.get('customer', False))
        self.view.category_filter_combo.setEnabled(enabled_filters.get('category', False))

        self.current_model = GenericTableModel(headers=headers, column_keys=column_keys)
        self.view.report_table.setModel(self.current_model)
        self.view.totals_label.setVisible(False)
        self._clear_charts()

    def _get_common_filters(self):
        start_date = self.view.start_date_edit.date().toString("yyyy-MM-dd 00:00:00")
        end_date = self.view.end_date_edit.date().toString("yyyy-MM-dd 23:59:59")
        customer_id = self.view.customer_filter_combo.currentData()
        category_id = self.view.category_filter_combo.currentData()
        return start_date, end_date, customer_id, category_id

    def generate_sales_report(self):
        self._setup_report(
            title="Dönem Satış Raporu",
            headers=["Satış ID", "Tarih", "Müşteri Adı", "Toplam Tutar (TL)", "Toplam Maliyet (TL)", "Net Kâr (TL)"], 
            column_keys=["id", "satis_tarihi", "musteri_adi", "toplam_tutar", "toplam_maliyet", "kar"],
            enabled_filters={'customer': True, 'category': False}
        )
        
        start_date, end_date, customer_id, _ = self._get_common_filters()
        sales_data, totals = db.get_sales_with_profit_by_date_range(start_date, end_date, customer_id)
        daily_data = db.get_daily_sales_for_period(start_date, end_date, customer_id)
        
        self.current_model.update_data(sales_data)
        self.view.totals_label.setText(
            f"Dönem Özeti:   Toplam Satış: {totals.get('total_revenue', 0):,.2f} TL   |   "
            f"Toplam Maliyet: {totals.get('total_cost', 0):,.2f} TL   |   "
            f"Toplam Net Kâr: {totals.get('total_profit', 0):,.2f} TL"
        )
        self.view.totals_label.setVisible(True)
        self._draw_daily_sales_chart(daily_data)
        self.view.show_loading(False)
        self.view.set_export_buttons_enabled(len(sales_data) > 0)

    def generate_inventory_report(self):
        self._setup_report(
            title="Stok Durum Raporu",
            headers=["Stok Kodu", "Ürün Adı", "Kategori", "Mevcut Stok", "Alış Fiyatı (TL)", "Toplam Stok Değeri (TL)"], 
            column_keys=["stok_kodu", "ad", "kategori_ad", "stok_miktari", "alis_fiyati", "toplam_maliyet"],
            enabled_filters={'customer': False, 'category': True}
        )
        
        _, _, _, category_id = self._get_common_filters()
        report_data, total_value = db.get_inventory_report(category_id)
        category_value_data = db.get_inventory_value_by_category()
        
        self.current_model.update_data(report_data)
        self.view.totals_label.setText(f"Toplam Envanter Değeri: {total_value:,.2f} TL")
        self.view.totals_label.setVisible(True)
        self._draw_inventory_value_chart(category_value_data)
        self.view.show_loading(False)
        self.view.set_export_buttons_enabled(len(report_data) > 0)

    def generate_product_report(self):
        self._setup_report(
            title="Ürün Bazlı Satış Raporu",
            headers=["Stok Kodu", "Ürün Adı", "Satılan Adet", "Toplam Ciro (TL)", "Toplam Maliyet (TL)", "Toplam Net Kâr (TL)"],
            column_keys=["stok_kodu", "urun_adi", "toplam_satilan_adet", "toplam_ciro", "toplam_maliyet", "toplam_kar"],
            enabled_filters={'customer': False, 'category': True}
        )
        
        start_date, end_date, _, category_id = self._get_common_filters()
        report_data = db.get_product_sales_report(start_date, end_date, category_id)
        
        self.current_model.update_data(report_data)
        self._draw_top_products_charts(report_data)
        self.view.show_loading(False)
        self.view.set_export_buttons_enabled(len(report_data) > 0)

    def generate_customer_report(self):
        self._setup_report(
            title="Müşteri Bazlı Kârlılık Raporu",
            headers=["Müşteri Adı", "Toplam Ciro (TL)", "Toplam Maliyet (TL)", "Toplam Net Kâr (TL)"],
            column_keys=["musteri_adi", "toplam_ciro", "toplam_maliyet", "toplam_kar"],
            enabled_filters={'customer': False, 'category': False}
        )
        
        start_date, end_date, _, _ = self._get_common_filters()
        report_data = db.get_customer_sales_report(start_date, end_date)
        total_profit = sum(item['toplam_kar'] or 0 for item in report_data)

        self.current_model.update_data(report_data)
        self.view.totals_label.setText(f"Dönem Toplam Net Kârı: {total_profit:,.2f} TL")
        self.view.totals_label.setVisible(True)
        self._draw_top_customers_chart(report_data)
        self.view.show_loading(False)
        self.view.set_export_buttons_enabled(len(report_data) > 0)

    def export_to_excel(self):
        if not self.current_model or self.current_model.rowCount() == 0:
            return ui_helpers.show_warning_message(self.view, "Dışa aktarılacak veri bulunmuyor.")
        
        default_filename = f"{self.current_report_title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        save_path, _ = QFileDialog.getSaveFileName(self.view, "Excel Olarak Kaydet", default_filename, "Excel Dosyaları (*.xlsx)")
        if not save_path: return

        try:
            workbook = openpyxl.Workbook()
            sheet = workbook.active
            sheet.append(self.current_model.headers)
            for row_data in self.current_model.table_data:
                sheet.append([dict(row_data).get(key, "") for key in self.current_model.column_keys])
            workbook.save(save_path)
            ui_helpers.show_info_message(self.view, f"Rapor başarıyla şuraya kaydedildi:\n{save_path}")
        except Exception as e:
            ui_helpers.show_critical_message(self.view, f"Excel dosyası oluşturulurken bir hata oluştu:\n{e}")
            
    def export_to_pdf(self):
        if not self.current_model or self.current_model.rowCount() == 0:
            return ui_helpers.show_warning_message(self.view, "Dışa aktarılacak veri bulunmuyor.")
        
        data_for_pdf = [[str(dict(row).get(key, "")) for key in self.current_model.column_keys] for row in self.current_model.table_data]
        generator = GenericReportGenerator(
            report_title=self.current_report_title, headers=self.current_model.headers, data=data_for_pdf,
            file_prefix=self.current_report_title.replace(' ', '_'), 
            summary_line=self.view.totals_label.text() if self.view.totals_label.isVisible() else ""
        )
        success, message = generator.generate()
        if not success:
            ui_helpers.show_critical_message(self.view, message)

    def _clear_charts(self):
        self.view.chart_tab_widget.tabBar().setVisible(False)
        self.view.chart_view_1.setChart(QChart())
        self.view.chart_view_2.setChart(QChart())

    def _draw_daily_sales_chart(self, daily_data):
        self._clear_charts()
        if not daily_data: return
        
        series = QLineSeries()
        max_value = 0
        for row in daily_data:
            day = datetime.strptime(row['gun'], '%Y-%m-%d').day
            value = row['toplam_satis'] or 0
            series.append(day, value)
            if value > max_value: max_value = value
        
        chart = self._create_base_chart()
        series.setPen(QPen(QColor(self.chart_colors[0]), 2.5))
        chart.addSeries(series)
        
        axis_x = QValueAxis()
        axis_x.setLabelFormat("%d")
        axis_x.setTickCount(min(len(daily_data) + 1, 15))
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setLabelFormat("%.0f TL")
        axis_y.setRange(0, max_value * 1.15 if max_value > 0 else 100)
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        
        self.view.chart_tab_widget.setCurrentIndex(0)
        self.view.chart_view_1.setChart(chart)

    def _draw_top_products_charts(self, report_data):
        self._clear_charts()
        if not report_data: return
        
        self.view.chart_tab_widget.tabBar().setVisible(True)
        self.view.chart_tab_widget.setTabText(0, "Ciroya Göre Top 5 Ürün")
        self.view.chart_tab_widget.setTabText(1, "Kâra Göre Top 5 Ürün")

        top_revenue = sorted(report_data, key=lambda x: x['toplam_ciro'] or 0, reverse=True)[:5]
        ciro_chart = self._create_horizontal_bar_chart(top_revenue, 'urun_adi', 'toplam_ciro', self.chart_colors[0], "Ciro")
        self.view.chart_view_1.setChart(ciro_chart)

        top_profit = sorted(report_data, key=lambda x: x['toplam_kar'] or 0, reverse=True)[:5]
        kar_chart = self._create_horizontal_bar_chart(top_profit, 'urun_adi', 'toplam_kar', self.chart_colors[1], "Net Kâr")
        self.view.chart_view_2.setChart(kar_chart)
    
    def _draw_top_customers_chart(self, report_data):
        self._clear_charts()
        if not report_data: return
        top_customers = sorted(report_data, key=lambda x: x['toplam_kar'] or 0, reverse=True)[:5]
        chart = self._create_horizontal_bar_chart(top_customers, 'musteri_adi', 'toplam_kar', self.chart_colors[1], "Net Kâr")
        self.view.chart_view_1.setChart(chart)

    def _draw_inventory_value_chart(self, category_data):
        self._clear_charts()
        if not category_data: return
        
        series = QPieSeries()
        series.setHoleSize(0.40)
        series.setPieSize(0.8)
        
        total_value = sum(row['toplam_deger'] or 0 for row in category_data)
        if total_value > 0:
            for i, row in enumerate(category_data):
                slice_label = f"{row['kategori_adi'] or 'Diğer'}\n%{100 * (row['toplam_deger'] or 0) / total_value:.1f}"
                pie_slice = series.append(slice_label, row['toplam_deger'] or 0)
                pie_slice.setColor(QColor(self.chart_colors[i % len(self.chart_colors)]))
        
        series.setLabelsVisible(True)
        chart = self._create_base_chart()
        chart.legend().setAlignment(Qt.AlignRight)
        chart.addSeries(series)
        
        self.view.chart_tab_widget.setCurrentIndex(0)
        self.view.chart_view_1.setChart(chart)

    def _create_base_chart(self):
        chart = QChart()
        # --- DÜZELTME: Arka plan şeffaf yapıldı ve kenar boşlukları kaldırıldı ---
        chart.setBackgroundVisible(False)
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setMargins(QMargins(0, 0, 0, 0))
        chart.legend().setVisible(False)
        return chart
        
    def _create_horizontal_bar_chart(self, data, category_key, value_key, color, set_name):
        bar_set = QBarSet(set_name)
        bar_set.setColor(QColor(color))
        categories = []
        for row in reversed(data):
            bar_set.append(row[value_key] or 0)
            category_name = row[category_key] or ''
            categories.append(category_name[:20] + '...' if len(category_name) > 20 else category_name)
        
        series = QHorizontalBarSeries()
        series.append(bar_set)
        series.setLabelsVisible(True)
        series.setLabelsFormat("@value TL")

        chart = self._create_base_chart()
        chart.addSeries(series)
        
        axis_x = QValueAxis()
        axis_x.setLabelFormat("%.0f TL")
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QBarCategoryAxis()
        axis_y.append(categories)
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        
        return chart