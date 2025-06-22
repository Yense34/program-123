# dosya: controllers/dashboard_controller.py

import logging
from PySide6.QtCore import QThreadPool, Qt, QMargins
from PySide6.QtGui import QPainter, QFont, QColor, QPen
from PySide6.QtCharts import QChart, QLineSeries, QPieSeries, QValueAxis, QPieSlice
from PySide6.QtWidgets import QDialog, QListWidgetItem

from datetime import datetime
from database import database_manager as db
from models import sms_service
from services.background_worker import BackgroundWorker
from utils.signals import app_signals
from views.delegates import DashboardListDelegate
from views.stock_movement_dialog import StockMovementDialog
from utils import ui_texts as texts
from utils import ui_helpers

PAGE_CUSTOMERS = "customers"
PAGE_PRODUCTS = "products"
PAGE_SALE_HISTORY = "sale_history"
PAGE_BULK_COMMUNICATION = "bulk_communication"

class DashboardController:
    def __init__(self, view):
        self.view = view
        self.thread_pool = QThreadPool()
        self.active_workers = []
        
        # --- DÜZELTME: Canlı renk paleti tanımlandı ---
        self.chart_colors = [
            "#007bff", "#17a2b8", "#28a745", "#ffc107", "#dc3545", "#6f42c1"
        ]

        self._setup_lists()
        self._connect_signals()
        self.refresh_stats()

    def _setup_lists(self):
        self.delegate = DashboardListDelegate(self.view)
        self.view.low_stock_list.setItemDelegate(self.delegate)
        self.view.recent_sales_list.setItemDelegate(self.delegate)

    def _connect_signals(self):
        self.view.refresh_button.clicked.connect(self.refresh_and_check_credit)
        app_signals.customers_updated.connect(self.refresh_stats)
        app_signals.products_updated.connect(self.refresh_stats)
        app_signals.sales_updated.connect(self.refresh_stats)
        app_signals.stock_updated.connect(self.refresh_stats)
        
        self.view.recent_sales_list.itemDoubleClicked.connect(self.open_sale_detail_from_dashboard)
        self.view.low_stock_list.itemDoubleClicked.connect(self.open_stock_correction_dialog)
        
        self.view.customer_card.clicked.connect(self.go_to_customers)
        self.view.product_card.clicked.connect(self.go_to_products)
        self.view.sales_card.clicked.connect(self.go_to_sales_history)
        self.view.credit_card.clicked.connect(self.go_to_bulk_communication)

    def go_to_customers(self): app_signals.page_change_requested.emit(PAGE_CUSTOMERS)
    def go_to_products(self): app_signals.page_change_requested.emit(PAGE_PRODUCTS)
    def go_to_sales_history(self): app_signals.page_change_requested.emit(PAGE_SALE_HISTORY)
    def go_to_bulk_communication(self): app_signals.page_change_requested.emit(PAGE_BULK_COMMUNICATION)
    
    def refresh_and_check_credit(self):
        self.refresh_stats(check_live_credit=True)

    def refresh_stats(self, check_live_credit: bool = False):
        try:
            stats = db.get_dashboard_stats()
            today = datetime.now()
            start_date = today.strftime('%Y-%m-01 00:00:00')
            end_date = today.strftime('%Y-%m-%d 23:59:59')
            sales_this_month, _ = db.get_sales_by_date_range(start_date, end_date)
            stats['total_sales_this_month'] = len(sales_this_month)
            stats['sms_credit'] = db.get_setting('sms_credit', 'Bilinmiyor')
            self.view.update_stats(stats)
            
            self.view.low_stock_list.clear()
            low_stock_data = db.get_low_stock_products()[:5]
            self.view.low_stock_list.setVisible(bool(low_stock_data))
            for product in low_stock_data:
                item = QListWidgetItem()
                item_data = { "main_text": product['ad'], "sub_text": str(product['stok_miktari']), "is_critical": True, "db_id": product['id'], "product_name": product['ad'] }
                item.setData(Qt.UserRole, item_data)
                self.view.low_stock_list.addItem(item)

            self.view.recent_sales_list.clear()
            recent_sales_data = db.get_recent_sales()
            self.view.recent_sales_list.setVisible(bool(recent_sales_data))
            for sale in recent_sales_data:
                item = QListWidgetItem()
                item_data = { "main_text": sale['musteri_adi'], "sub_text": f"{sale['toplam_tutar']:,.2f} TL", "is_critical": False, "db_id": sale['id'] }
                item.setData(Qt.UserRole, item_data)
                self.view.recent_sales_list.addItem(item)
            
            self._draw_monthly_sales_chart(db.get_sales_by_day_for_month())
            self._draw_category_distribution_chart(db.get_sales_by_category())

            if check_live_credit: self._check_live_credit()
        
        except Exception as e:
            logging.error(f"Dashboard istatistikleri yüklenirken hata oluştu: {e}", exc_info=True)
            ui_helpers.show_critical_message(self.view, f"Dashboard verileri yüklenemedi.\n\nHata: {e}")

    def _create_base_chart(self):
        chart = QChart()
        # --- DÜZELTME: Arka plan şeffaf yapıldı ve kenar boşlukları kaldırıldı ---
        chart.setBackgroundVisible(False)
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setMargins(QMargins(0, 0, 0, 0))
        chart.legend().setVisible(True)
        return chart

    def _draw_monthly_sales_chart(self, monthly_data):
        chart = self._create_base_chart()
        chart.legend().hide()
        
        series = QLineSeries()
        max_value = 0
        if monthly_data:
            for row in monthly_data:
                day = datetime.strptime(row['gun'], '%Y-%m-%d').day
                value = row['toplam_satis'] or 0
                series.append(day, value)
                max_value = max(max_value, value)
        
        pen = QPen(QColor(self.chart_colors[0]), 2.5) # Kalınlık 2.5 olarak ayarlandı
        series.setPen(pen)
        chart.addSeries(series)

        axis_pen = QPen(QColor("#E5E7EB"))
        
        axis_x = QValueAxis()
        axis_x.setLabelFormat("%d")
        axis_x.setTickCount(min(len(monthly_data) + 1, 15))
        axis_x.setLinePen(axis_pen)
        axis_x.setGridLineVisible(False)
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setLabelFormat("%.0f TL")
        axis_y.setRange(0, max_value * 1.15 if max_value > 0 else 100)
        axis_y.setLinePen(axis_pen)
        axis_y.setGridLinePen(axis_pen)
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        
        self.view.monthly_sales_chart_view.setChart(chart)

    def _draw_category_distribution_chart(self, category_data):
        chart = self._create_base_chart()
        chart.legend().setAlignment(Qt.AlignBottom)

        if not category_data:
            self.view.category_sales_chart_view.setChart(chart)
            return

        series = QPieSeries()
        series.setHoleSize(0.40)
        series.setLabelsVisible(False)
        
        category_data_dicts = [dict(row) for row in category_data]
        sorted_data = sorted(category_data_dicts, key=lambda x: x.get('toplam_ciro', 0), reverse=True)
        
        display_data = sorted_data[:5]
        if len(sorted_data) > 5:
            other_total = sum(item.get('toplam_ciro', 0) for item in sorted_data[5:])
            if other_total > 0:
                display_data.append({'kategori_adi': 'Diğer', 'toplam_ciro': other_total})

        total_revenue = sum(item.get('toplam_ciro', 0) for item in display_data)
        
        if total_revenue > 0:
            for i, item in enumerate(display_data):
                value = item.get('toplam_ciro', 0)
                percentage = (value / total_revenue) * 100
                label = f"{item.get('kategori_adi', 'Bilinmiyor')} ({percentage:.1f}%)"
                
                pie_slice = series.append(label, value)
                pie_slice.setColor(QColor(self.chart_colors[i % len(self.chart_colors)]))
                pie_slice.setBorderColor(QColor("#FFFFFF"))
                pie_slice.setBorderWidth(2)
        
        chart.addSeries(series)
        self.view.category_sales_chart_view.setChart(chart)
        
    def _check_live_credit(self):
        app_signals.status_message_updated.emit("SMS kredisi sorgulanıyor...", 2000)
        api_settings = db.get_all_settings()
        
        if not api_settings.get('sms_username'):
            app_signals.status_message_updated.emit("SMS ayarları eksik, kredi sorgulanamadı.", 4000)
            return

        worker = BackgroundWorker(sms_service.get_credit_info, api_settings)
        worker.signals.result.connect(self._on_credit_check_finished)
        worker.signals.finished.connect(lambda: self.active_workers.remove(worker))
        self.active_workers.append(worker)
        self.thread_pool.start(worker)

    def _on_credit_check_finished(self, credit: str):
        if credit is not None:
            db.save_setting('sms_credit', credit)
            self.view.credit_card.value_label.setText(str(credit))
            app_signals.status_message_updated.emit("SMS kredisi başarıyla güncellendi.", 4000)
        else:
            app_signals.status_message_updated.emit("SMS kredisi sorgulanamadı.", 4000)

    def open_sale_detail_from_dashboard(self, item: QListWidgetItem):
        if sale_id := item.data(Qt.UserRole).get("db_id"):
            app_signals.show_sale_detail_requested.emit(sale_id)

    def open_stock_correction_dialog(self, item: QListWidgetItem):
        item_data = item.data(Qt.UserRole)
        product_id = item_data.get("db_id")
        product_name = item_data.get("product_name")
        if not product_id: return

        dialog = StockMovementDialog(product_name, self.view)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if not data or data.get('miktar') == 0:
                return
            
            if db.add_stock_movement(product_id, data['hareket_tipi'], data['miktar'], data['aciklama']):
                app_signals.status_message_updated.emit(texts.PRODUCT_MSG_STOCK_MOVEMENT_SUCCESS.format(product_name=product_name), 4000)
                app_signals.stock_updated.emit()
            else:
                ui_helpers.show_critical_message(self.view, texts.PRODUCT_MSG_STOCK_MOVEMENT_DB_ERROR)