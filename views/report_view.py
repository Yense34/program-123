# dosya: views/report_view.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QDateEdit,
    QTableView, QHeaderView, QLabel, QStackedWidget, QComboBox,
    QFormLayout, QTabWidget, QSplitter
)
from PySide6.QtCore import Qt
from PySide6.QtCharts import QChartView
import qtawesome as qta

from utils.custom_widgets import PageHeader
from utils.themed_widgets import CardWidget, SuccessButton, DangerButton, OutlineButton

class ReportView(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(25, 25, 25, 25)

        self.header = PageHeader("Raporlar", icon_name="chart-pie")
        main_layout.addWidget(self.header)

        top_section_layout = QHBoxLayout()
        top_section_layout.setSpacing(20)
        
        filter_group = CardWidget("1. Filtreleme Seçenekleri")
        form_layout = QFormLayout()
        filter_group.layout().addLayout(form_layout)
        
        self.start_date_edit = QDateEdit()
        self.end_date_edit = QDateEdit()
        self.customer_filter_combo = QComboBox()
        self.category_filter_combo = QComboBox()
        
        form_layout.addRow("Başlangıç Tarihi:", self.start_date_edit)
        form_layout.addRow("Bitiş Tarihi:", self.end_date_edit)
        form_layout.addRow("Müşteri:", self.customer_filter_combo)
        form_layout.addRow("Ürün Kategorisi:", self.category_filter_combo)
        top_section_layout.addWidget(filter_group, 2)

        report_type_group = CardWidget("2. Rapor Türünü Seçin")
        report_type_layout = report_type_group.layout()
        self.generate_sales_report_button = OutlineButton("Dönem Satış Raporu")
        self.generate_product_report_button = OutlineButton("Ürün Bazlı Satış Raporu")
        self.generate_customer_report_button = OutlineButton("Müşteri Bazlı Satış Raporu")
        self.generate_inventory_report_button = OutlineButton("Stok Durum Raporu")
        report_type_layout.addWidget(self.generate_sales_report_button)
        report_type_layout.addWidget(self.generate_product_report_button)
        report_type_layout.addWidget(self.generate_customer_report_button)
        report_type_layout.addWidget(self.generate_inventory_report_button)
        top_section_layout.addWidget(report_type_group, 1)

        main_layout.addLayout(top_section_layout)

        results_group = CardWidget("3. Rapor Sonuçları")
        results_layout = results_group.layout()
        
        content_splitter = QSplitter(Qt.Horizontal)
        
        table_container_widget = QWidget()
        table_layout = QVBoxLayout(table_container_widget)
        table_layout.setContentsMargins(0,0,0,0)
        self.content_stack = QStackedWidget()
        self.report_table = QTableView()
        self.report_table.verticalHeader().setVisible(False)
        self.report_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        loading_widget = QWidget()
        loading_layout = QVBoxLayout(loading_widget)
        loading_layout.setAlignment(Qt.AlignCenter)
        loading_label = QLabel()
        spinner_icon = qta.icon('fa5s.spinner', color='#2980B9', animation=qta.Spin(loading_label))
        loading_label.setPixmap(spinner_icon.pixmap(64, 64))
        loading_layout.addWidget(loading_label)
        loading_layout.addWidget(QLabel("Rapor Oluşturuluyor..."))
        self.content_stack.addWidget(self.report_table)
        self.content_stack.addWidget(loading_widget)
        table_layout.addWidget(self.content_stack)

        self.chart_tab_widget = QTabWidget()
        self.chart_view_1 = QChartView()
        self.chart_view_2 = QChartView()
        self.chart_tab_widget.addTab(self.chart_view_1, "Grafik 1")
        self.chart_tab_widget.addTab(self.chart_view_2, "Grafik 2")
        
        content_splitter.addWidget(table_container_widget)
        content_splitter.addWidget(self.chart_tab_widget)
        content_splitter.setSizes([800, 450])
        results_layout.addWidget(content_splitter, 1)

        bottom_panel_layout = QHBoxLayout()
        self.totals_label = QLabel("")
        self.totals_label.setObjectName("SummaryLabel")
        
        self.export_excel_button = SuccessButton("Excel'e Aktar", icon_name='fa5s.file-excel')
        self.export_pdf_button = DangerButton("PDF Olarak Kaydet", icon_name='fa5s.file-pdf')
        
        bottom_panel_layout.addWidget(self.totals_label)
        bottom_panel_layout.addStretch()
        bottom_panel_layout.addWidget(self.export_excel_button)
        bottom_panel_layout.addWidget(self.export_pdf_button)
        results_layout.addLayout(bottom_panel_layout)
        
        main_layout.addWidget(results_group, 1)
    
    def show_loading(self, show: bool):
        self.content_stack.setCurrentIndex(1 if show else 0)
        if show:
            self.set_export_buttons_enabled(False)
            
    def set_export_buttons_enabled(self, is_enabled: bool):
        self.export_excel_button.setEnabled(is_enabled)
        self.export_pdf_button.setEnabled(is_enabled)