# dosya: controllers/sale_detail_controller.py

from database import database_manager as db
from generators.customer_invoice_pdf import CustomerInvoiceGenerator
from generators.production_order_pdf import ProductionOrderGenerator
from models import sms_service
from services.session_manager import session
from utils import ui_texts as texts
from utils import ui_helpers
from utils.signals import app_signals

class SaleDetailController:
    def __init__(self, dialog, sale_data: dict):
        self.dialog = dialog
        self.sale_data = sale_data
        self.sale_id = self.sale_data['sale_info']['id']
        self._connect_signals()

    def _connect_signals(self):
        self.dialog.invoice_pdf_button.clicked.connect(self.generate_customer_invoice)
        self.dialog.production_pdf_button.clicked.connect(self.generate_production_order)
        self.dialog.sms_button.clicked.connect(self.send_sale_confirmation_sms)
        self.dialog.delete_requested.connect(self.delete_sale)
        self.dialog.edit_requested.connect(self.edit_sale)

    def delete_sale(self):
        if not session.has_permission('sales:delete'):
            return ui_helpers.show_warning_message(self.dialog, texts.MSG_UNAUTHORIZED_ACTION, texts.MSG_UNAUTHORIZED_ACTION_DETAIL)
        
        is_confirmed = ui_helpers.ask_confirmation(
            parent=self.dialog,
            title=texts.SALE_HISTORY_MSG_DELETE_TITLE,
            text=texts.SALE_HISTORY_MSG_DELETE_TEXT.format(sale_id=self.sale_id),
            informative_text=texts.SALE_HISTORY_MSG_DELETE_INFO
        )

        if is_confirmed:
            success, message = db.delete_sale_by_id(self.sale_id)
            if success:
                ui_helpers.show_info_message(self.dialog, message, texts.TITLE_SUCCESS)
                app_signals.sales_updated.emit()
                app_signals.stock_updated.emit()
                app_signals.customers_updated.emit()
                self.dialog.accept()
            else:
                ui_helpers.show_critical_message(self.dialog, message, texts.TITLE_ERROR)

    def edit_sale(self):
        if not session.has_permission('sales:edit'):
            return ui_helpers.show_warning_message(self.dialog, texts.MSG_UNAUTHORIZED_ACTION, texts.MSG_UNAUTHORIZED_ACTION_DETAIL)

        app_signals.load_sale_for_editing_requested.emit(self.sale_id)
        self.dialog.accept()

    def generate_customer_invoice(self):
        company_settings = db.get_all_settings()
        generator = CustomerInvoiceGenerator(self.sale_id, self.sale_data, company_settings)
        success, message = generator.generate()
        if success:
            app_signals.status_message_updated.emit(message, 4000)
        else:
            ui_helpers.show_critical_message(self.dialog, message, texts.SALE_HISTORY_MSG_PDF_ERROR)
    
    def generate_production_order(self):
        company_settings = db.get_all_settings()
        generator = ProductionOrderGenerator(self.sale_id, self.sale_data, company_settings)
        success, message = generator.generate()
        if success:
            app_signals.status_message_updated.emit(message, 4000)
        else:
            ui_helpers.show_critical_message(self.dialog, message, texts.SALE_HISTORY_MSG_PDF_ERROR)

    def send_sale_confirmation_sms(self):
        if not session.has_permission('bulk_communication:send'):
             return ui_helpers.show_warning_message(self.dialog, texts.MSG_UNAUTHORIZED_ACTION, texts.MSG_UNAUTHORIZED_ACTION_DETAIL)

        customer_info = self.sale_data['sale_info']
        if not (phone_number := customer_info.get('telefon')):
            return ui_helpers.show_warning_message(self.dialog, texts.MSG_MISSING_INFO, texts.SALE_HISTORY_MSG_SMS_NO_PHONE)
        
        message = f"Sayin {customer_info['musteri_adi']}, {self.sale_id} numarali siparisiniz alinmistir. Bizi tercih ettiginiz icin tesekkurler."
        api_settings = db.get_all_settings()
        success, response_message = sms_service.send_bulk_sms(api_settings, [phone_number], message)
        
        if success:
            ui_helpers.show_info_message(self.dialog, response_message, texts.TITLE_SUCCESS)
        else:
            ui_helpers.show_critical_message(self.dialog, response_message, texts.SALE_HISTORY_MSG_SMS_ERROR)