# dosya: views/dashboard_view.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QListWidget
)
from PySide6.QtCharts import QChartView
from PySide6.QtGui import QPainter

from utils.custom_widgets import PageHeader
from utils.themed_widgets import StatCard, CardWidget, OutlineButton

class DashboardView(QWidget):
    def __init__(self):
        super().__init__()
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(25, 25, 25, 25)

        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.header = PageHeader("Ana Sayfa", icon_name="home")
        self.refresh_button = OutlineButton("", icon_name='fa5s.sync-alt')
        self.refresh_button.setToolTip("Verileri Yenile ve SMS Kredisini Sorgula")

        header_layout.addWidget(self.header, 1)
        header_layout.addWidget(self.refresh_button)
        main_layout.addWidget(header_widget)

        top_cards_layout = QHBoxLayout()
        top_cards_layout.setSpacing(20)

        self.customer_card = StatCard("TOPLAM MÜŞTERİ", "fa5s.users")
        self.product_card = StatCard("TOPLAM ÜRÜN", "fa5s.box-open")
        self.sales_card = StatCard("BU AYKİ SATIŞ", "fa5s.chart-line")
        self.credit_card = StatCard("SMS KREDİSİ", "fa5s.sms")

        top_cards_layout.addWidget(self.customer_card)
        top_cards_layout.addWidget(self.product_card)
        top_cards_layout.addWidget(self.sales_card)
        top_cards_layout.addWidget(self.credit_card)
        main_layout.addLayout(top_cards_layout)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        chart_card = CardWidget("Analiz Grafikleri")
        chart_layout = chart_card.layout()
        self.chart_tabs = QTabWidget()
        self.monthly_sales_chart_view = QChartView()
        self.monthly_sales_chart_view.setRenderHint(QPainter.Antialiasing)
        self.category_sales_chart_view = QChartView()
        self.category_sales_chart_view.setRenderHint(QPainter.Antialiasing)
        self.chart_tabs.addTab(self.monthly_sales_chart_view, "Aylık Satış Performansı")
        self.chart_tabs.addTab(self.category_sales_chart_view, "Kategori Satış Dağılımı")
        chart_layout.addWidget(self.chart_tabs)
        
        right_panel_widget = QWidget()
        right_layout = QVBoxLayout(right_panel_widget)
        right_layout.setContentsMargins(0,0,0,0)
        right_layout.setSpacing(20)

        recent_sales_card = CardWidget("Son Satışlar")
        self.recent_sales_list = QListWidget()
        
        low_stock_card = CardWidget("Stok Seviyesi Kritik Ürünler")
        self.low_stock_list = QListWidget()
        
        recent_sales_card.layout().addWidget(self.recent_sales_list)
        low_stock_card.layout().addWidget(self.low_stock_list)

        right_layout.addWidget(recent_sales_card)
        right_layout.addWidget(low_stock_card)
        
        content_layout.addWidget(chart_card, 2)
        content_layout.addWidget(right_panel_widget, 1)

        main_layout.addLayout(content_layout, 1)

    def update_stats(self, stats: dict):
        self.customer_card.value_label.setText(str(stats.get("total_customers", 0)))
        self.product_card.value_label.setText(str(stats.get("total_products", 0)))
        self.sales_card.value_label.setText(str(stats.get("total_sales_this_month", 0)))
        self.credit_card.value_label.setText(str(stats.get("sms_credit", "N/A")))