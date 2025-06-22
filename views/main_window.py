# dosya: views/main_window.py

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QStackedWidget, QStatusBar
)
from PySide6.QtCore import Signal, Qt

from utils.custom_widgets import LeftNavBar
from utils.signals import app_signals

class MainWindow(QMainWindow):
    page_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modern Ticari Program")
        self.resize(1366, 768)
        self.setMinimumSize(1100, 700)
        
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.nav_bar = LeftNavBar()
        self.nav_bar.page_requested.connect(self.page_changed.emit)
        self.main_layout.addWidget(self.nav_bar)

        self.content_frame = QWidget()
        self.content_frame.setObjectName("ContentFrame")
        content_layout = QHBoxLayout(self.content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.stacked_widget = QStackedWidget()
        content_layout.addWidget(self.stacked_widget)

        self.main_layout.addWidget(self.content_frame, 1)

        self._create_pages()

        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        app_signals.status_message_updated.connect(self.show_status_message)

        self.page_changed.connect(self.switch_to_page)

    def _create_pages(self):
        from views.dashboard_view import DashboardView
        from views.customer_view import CustomerView
        from views.product_view import ProductView
        from views.sale_view import SaleView
        from views.sale_history_view import SaleHistoryView
        from views.report_view import ReportView
        from views.settings_view import SettingsView
        from views.bulk_communication_view import BulkCommunicationView

        self.pages = {
            "dashboard": DashboardView(),
            "sales": SaleView(),
            "products": ProductView(),
            "customers": CustomerView(),
            "sale_history": SaleHistoryView(),
            "reports": ReportView(),
            "settings": SettingsView(),
            "bulk_communication": BulkCommunicationView(),
        }
        for page in self.pages.values():
            self.stacked_widget.addWidget(page)

    def switch_to_page(self, page_name: str):
        if page_name in self.pages:
            self.stacked_widget.setCurrentWidget(self.pages[page_name])
            self.nav_bar.set_active_button(page_name)

    def show_status_message(self, message: str, timeout: int = 4000):
        self.status_bar.showMessage(message, timeout)

    def update_ui_for_role(self, session_manager):
        self.nav_bar.update_visibility_for_session(session_manager)

    def closeEvent(self, event):
        app_signals.app_closed.emit()
        super().closeEvent(event)