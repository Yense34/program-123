# dosya: controllers/app_controller.py

from PySide6.QtCore import QThreadPool
from datetime import datetime
from typing import Dict, List, Optional

from views.main_window import MainWindow
from controllers.dashboard_controller import DashboardController
from controllers.customer_controller import CustomerController
from controllers.product_controller import ProductController
from controllers.sale_controller import SaleController
from controllers.sale_history_controller import SaleHistoryController
from controllers.report_controller import ReportController
from controllers.settings_controller import SettingsController
from controllers.bulk_communication_controller import BulkCommunicationController

from services.background_worker import BackgroundWorker
from services.session_manager import session
from models import currency_service
from database import database_manager as db
from utils.signals import app_signals

DASHBOARD = "dashboard"
SALES = "sales"
PRODUCTS = "products"
CUSTOMERS = "customers"
SALE_HISTORY = "sale_history"
REPORTS = "reports"
SETTINGS = "settings"
BULK_COMMUNICATION = "bulk_communication"

PAGE_PERMISSIONS: Dict[str, Optional[str]] = {
    DASHBOARD: None,
    SALES: None,
    PRODUCTS: None,
    CUSTOMERS: None,
    SALE_HISTORY: None,
    BULK_COMMUNICATION: None,
    REPORTS: 'reports:view',
    SETTINGS: 'settings:view',
}

class AppController:
    def __init__(self, main_view: MainWindow):
        self.view = main_view
        self.page_controllers: Dict[str, object] = {}
        self.thread_pool = QThreadPool()
        self.active_workers: List[BackgroundWorker] = []
        
        self._create_page_controllers()
        self._connect_signals()
        self._setup_ui_for_role()

        self.view.page_changed.emit(DASHBOARD)
        self._trigger_startup_update()

    def _create_page_controllers(self):
        self.page_controllers = {
            DASHBOARD: DashboardController(self.view.pages[DASHBOARD]),
            SALES: SaleController(self.view.pages[SALES]),
            PRODUCTS: ProductController(self.view.pages[PRODUCTS]),
            CUSTOMERS: CustomerController(self.view.pages[CUSTOMERS]),
            SALE_HISTORY: SaleHistoryController(self.view.pages[SALE_HISTORY]),
            REPORTS: ReportController(self.view.pages[REPORTS]),
            SETTINGS: SettingsController(self.view.pages[SETTINGS]),
            BULK_COMMUNICATION: BulkCommunicationController(self.view.pages[BULK_COMMUNICATION]),
        }

    def _connect_signals(self):
        self.view.page_changed.connect(self.switch_page)
        app_signals.show_sale_detail_requested.connect(self.show_sale_detail)
        app_signals.load_sale_for_editing_requested.connect(self._load_sale_for_editing)
        app_signals.page_change_requested.connect(self.switch_page)

    def _setup_ui_for_role(self):
        self.view.update_ui_for_role(session)

    def switch_page(self, page_name: str):
        required_permission = PAGE_PERMISSIONS.get(page_name)
        
        if required_permission and not session.has_permission(required_permission):
            self._update_status_bar(f"Bu sayfayı görüntüleme yetkiniz yok: {page_name}", 3000)
            return
            
        if page_name in self.view.pages:
            self.view.switch_to_page(page_name)
    
    def show_sale_detail(self, sale_id: int):
        if sale_history_controller := self.page_controllers.get(SALE_HISTORY):
            sale_history_controller.open_sale_detail_by_id(sale_id)

    def _load_sale_for_editing(self, sale_id: int):
        self.switch_page(SALES)
        
        if sale_controller := self.page_controllers.get(SALES):
            sale_controller.load_sale_for_editing(sale_id)

    def _trigger_startup_update(self):
        self._update_status_bar("Arka planda kurlar güncelleniyor...", 2000)
        
        worker = BackgroundWorker(currency_service.get_all_rates)
        worker.signals.result.connect(self._on_currency_update_finished)
        worker.signals.error.connect(self._on_currency_update_error)
        worker.signals.finished.connect(lambda: self._remove_worker(worker))
        
        self.active_workers.append(worker)
        self.thread_pool.start(worker)

    def _on_currency_update_finished(self, rates: Optional[Dict[str, float]]):
        if rates:
            now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
            db.save_setting('usd_tl_kuru', rates.get('USD', '0'))
            db.save_setting('eur_tl_kuru', rates.get('EUR', '0'))
            db.save_setting('kur_guncelleme_tarihi', f"{now_str} (Otomatik)")
            self._update_status_bar("Döviz kurları başarıyla güncellendi.", 4000)
        else:
            self._update_status_bar("Kurlar güncellenemedi. Ağ bağlantınızı kontrol edin.", 4000)

    def _on_currency_update_error(self, error_info: tuple):
        print(f"Kur güncelleme hatası: {error_info[1]}")
        self._update_status_bar("Kur güncelleme hatası! Detaylar için logları kontrol edin.", 5000)

    def _remove_worker(self, worker_to_remove: BackgroundWorker):
        if worker_to_remove in self.active_workers:
            self.active_workers.remove(worker_to_remove)

    def _update_status_bar(self, message: str, timeout: int):
        app_signals.status_message_updated.emit(message, timeout)