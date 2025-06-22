# dosya: controllers/sale_history_controller.py

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QListWidgetItem

from database import database_manager as db
from views.table_models import GenericTableModel
from views.sale_detail_dialog import SaleDetailDialog
from utils.signals import app_signals
from utils import ui_helpers
from controllers.sale_detail_controller import SaleDetailController
from views.delegates import SaleDetailDelegate

class SaleHistoryController:
    def __init__(self, view):
        self.view = view
        
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(350) 
        
        self._setup_table()
        self._connect_signals()
        self.load_history()

    def _setup_table(self):
        headers = ["Satış ID", "Tarih", "Müşteri Adı", "Toplam Tutar (TL)"]
        column_keys = ["id", "satis_tarihi", "musteri_adi", "toplam_tutar"]
        self.table_model = GenericTableModel(headers=headers, column_keys=column_keys)
        self.view.history_table.setModel(self.table_model)

    def _connect_signals(self):
        self.view.search_input.textChanged.connect(self.search_timer.start)
        self.search_timer.timeout.connect(self.load_history)
        self.view.history_table.doubleClicked.connect(self.open_sale_detail)
        app_signals.sales_updated.connect(self.load_history)

    def load_history(self):
        query = self.view.search_input.text()
        sales_data = db.search_sales_history(query) if query else db.get_all_sales_history()
        self.table_model.update_data(sales_data)

    def open_sale_detail(self, index):
        sale_id = self.table_model.get_item_id(index)
        if sale_id:
            self.open_sale_detail_by_id(sale_id)

    def open_sale_detail_by_id(self, sale_id: int):
        if not sale_id: 
            return

        report_data_raw = db.get_sale_details_for_report(sale_id)
        if not report_data_raw:
            return ui_helpers.show_critical_message(self.view, "Satış detayları bulunamadı.")

        report_data = {
            "sale_info": dict(report_data_raw["sale_info"]),
            "details": [dict(row) for row in report_data_raw["details"]]
        }

        dialog = SaleDetailDialog(report_data, self.view)
        
        delegate = SaleDetailDelegate(dialog.products_list)
        dialog.products_list.setItemDelegate(delegate)

        for product in report_data['details']:
            item = QListWidgetItem(dialog.products_list)
            
            item_data = product.copy()
            item_data['toplam'] = product['miktar'] * product['birim_fiyat']
            item.setData(Qt.UserRole, item_data)
        
        _ = SaleDetailController(dialog, report_data)
        
        dialog.exec()