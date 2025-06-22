# dosya: controllers/bulk_communication_controller.py

import math
from PySide6.QtWidgets import QListWidgetItem
from PySide6.QtCore import QThreadPool, Qt
from typing import List

from database import database_manager as db
from models import sms_service, email_service
from services.background_worker import BackgroundWorker
from utils.signals import app_signals
from utils import ui_texts as texts
from services.session_manager import session
from utils import ui_helpers
from views.delegates import CommunicationListDelegate

class BulkCommunicationController:
    def __init__(self, view):
        self.view = view
        self.thread_pool = QThreadPool()
        self.active_workers: List[BackgroundWorker] = []
        self._setup_customer_list()
        self._connect_signals()
        self.load_initial_data()
        
        has_permission = session.has_permission('bulk_communication:send')
        self.view.send_button.setEnabled(has_permission)
        self.view.send_single_sms_button.setEnabled(has_permission)

    def _setup_customer_list(self):
        delegate = CommunicationListDelegate(self.view.customer_list)
        self.view.customer_list.setItemDelegate(delegate)

    def _connect_signals(self):
        self.view.select_all_button.clicked.connect(self.select_all_customers)
        self.view.deselect_all_button.clicked.connect(self.deselect_all_customers)
        self.view.message_tabs.currentChanged.connect(self.load_templates)
        self.view.template_combo.currentIndexChanged.connect(self.on_template_selected)
        self.view.save_template_button.clicked.connect(self.save_new_template)
        self.view.delete_template_button.clicked.connect(self.delete_selected_template)
        self.view.sms_message_box.textChanged.connect(self.update_sms_char_count)
        self.view.send_button.clicked.connect(self.start_bulk_sending_process)
        self.view.send_single_sms_button.clicked.connect(self.send_single_test_sms)

    def load_initial_data(self):
        self.load_customers()
        self.load_templates()

    def load_customers(self):
        self.view.customer_list.clear()
        customers = db.search_customers(query="")
        for customer in customers:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, dict(customer))
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.view.customer_list.addItem(item)
    
    def select_all_customers(self):
        for i in range(self.view.customer_list.count()):
            self.view.customer_list.item(i).setCheckState(Qt.Checked)

    def deselect_all_customers(self):
        for i in range(self.view.customer_list.count()):
            self.view.customer_list.item(i).setCheckState(Qt.Unchecked)

    def get_checked_items(self):
        checked_customers = []
        for i in range(self.view.customer_list.count()):
            item = self.view.customer_list.item(i)
            if item.checkState() == Qt.Checked:
                checked_customers.append(item.data(Qt.UserRole))
        return checked_customers

    def load_templates(self):
        self.view.template_combo.blockSignals(True)
        self.view.template_combo.clear()
        template_type = 'SMS' if 'SMS' in self.view.message_tabs.currentWidget().objectName() else 'E-posta'
        templates = db.get_message_templates(template_type)
        self.view.template_combo.addItem("Şablon Seçiniz...", None)
        for template in templates:
            self.view.template_combo.addItem(template['ad'], template)
        self.view.template_combo.blockSignals(False)

    def on_template_selected(self, index):
        if not (template_data := self.view.template_combo.currentData()): return
        
        if 'SMS' in self.view.message_tabs.currentWidget().objectName():
            self.view.sms_message_box.setPlainText(template_data['icerik'])
        else:
            self.view.email_message_box.setHtml(template_data['icerik'])
    
    def save_new_template(self):
        is_sms = 'SMS' in self.view.message_tabs.currentWidget().objectName()
        template_type = 'SMS' if is_sms else 'E-posta'
        content = self.view.sms_message_box.toPlainText() if is_sms else self.view.email_message_box.toHtml()

        if not content.strip():
            return ui_helpers.show_warning_message(self.view, texts.BULK_EMPTY_CONTENT_TEXT, texts.BULK_EMPTY_CONTENT_TITLE)
        
        template_name, ok = ui_helpers.get_text_input(self.view, texts.BULK_SAVE_TEMPLATE_TITLE, texts.BULK_SAVE_TEMPLATE_TEXT)
        if ok and template_name:
            success, message = db.add_message_template(template_name, content, template_type)
            if success:
                ui_helpers.show_info_message(self.view, message)
                self.load_templates()
            else:
                ui_helpers.show_critical_message(self.view, message)

    def delete_selected_template(self):
        if not (template_data := self.view.template_combo.currentData()):
            return ui_helpers.show_warning_message(self.view, texts.BULK_NO_TEMPLATE_SELECTED_TEXT, texts.BULK_NO_TEMPLATE_SELECTED_TITLE)
        
        if ui_helpers.ask_confirmation(self.view, texts.BULK_CONFIRM_DELETE_TEMPLATE_TITLE, texts.BULK_CONFIRM_DELETE_TEMPLATE_TEXT.format(template_name=template_data['ad'])):
            db.delete_message_template(template_data['id'])
            self.load_templates()

    def update_sms_char_count(self):
        char_count = len(self.view.sms_message_box.toPlainText())
        sms_count = math.ceil(char_count / 160) if char_count > 0 else 1
        self.view.sms_char_count_label.setText(f"Karakter: {char_count} | SMS: {sms_count}")

    def send_single_test_sms(self):
        if not session.has_permission('bulk_communication:send'):
            return ui_helpers.show_warning_message(self.view, texts.MSG_UNAUTHORIZED_ACTION_DETAIL, texts.MSG_UNAUTHORIZED_ACTION)

        phone_number = self.view.single_number_input.text().strip()
        message = self.view.sms_message_box.toPlainText().strip()
        
        if not phone_number: return ui_helpers.show_warning_message(self.view, texts.BULK_MISSING_PHONE_TEXT, texts.BULK_MISSING_PHONE_TITLE)
        if not message: return ui_helpers.show_warning_message(self.view, texts.BULK_EMPTY_CONTENT_TEXT, texts.BULK_EMPTY_CONTENT_TITLE)
            
        self._execute_sending_job(sms_service.send_bulk_sms, [phone_number], message)

    def start_bulk_sending_process(self):
        if not session.has_permission('bulk_communication:send'):
            return ui_helpers.show_warning_message(self.view, texts.MSG_UNAUTHORIZED_ACTION_DETAIL, texts.MSG_UNAUTHORIZED_ACTION)

        if not (selected_customers := self.get_checked_items()):
            return ui_helpers.show_warning_message(self.view, texts.BULK_NO_RECIPIENT_TEXT, texts.BULK_NO_RECIPIENT_TITLE)
        
        if 'SMS' in self.view.message_tabs.currentWidget().objectName():
            self._prepare_and_send_sms(selected_customers)
        else:
            self._prepare_and_send_email(selected_customers)

    def _prepare_and_send_sms(self, customers: List[dict]):
        message = self.view.sms_message_box.toPlainText().strip()
        if not message:
            return ui_helpers.show_warning_message(self.view, texts.BULK_EMPTY_CONTENT_TEXT, texts.BULK_EMPTY_CONTENT_TITLE)

        recipients = [c['telefon'] for c in customers if c.get('telefon')]
        if not recipients:
            return ui_helpers.show_warning_message(self.view, texts.BULK_NO_VALID_RECIPIENT_TEXT, texts.BULK_NO_VALID_RECIPIENT_TITLE)
            
        self._execute_sending_job(sms_service.send_bulk_sms, recipients, message)

    def _prepare_and_send_email(self, customers: List[dict]):
        subject = self.view.email_subject_input.text().strip()
        message = self.view.email_message_box.toHtml()
        
        if not subject: return ui_helpers.show_warning_message(self.view, texts.BULK_EMAIL_NO_SUBJECT_TEXT, texts.BULK_EMAIL_NO_SUBJECT_TITLE)
        if not message.strip(): return ui_helpers.show_warning_message(self.view, texts.BULK_EMPTY_CONTENT_TEXT, texts.BULK_EMPTY_CONTENT_TITLE)

        recipients = [c['eposta'] for c in customers if c.get('eposta')]
        if not recipients:
            return ui_helpers.show_warning_message(self.view, texts.BULK_NO_VALID_RECIPIENT_TEXT, texts.BULK_NO_VALID_RECIPIENT_TITLE)
            
        send_function = lambda settings, rec, msg: email_service.send_bulk_email(settings, rec, subject, msg)
        self._execute_sending_job(send_function, recipients, message)

    def _execute_sending_job(self, send_function, recipients, message):
        settings = db.get_all_settings()
        self.view.set_sending_state(True)
        
        worker = BackgroundWorker(send_function, settings, recipients, message)
        worker.signals.result.connect(self.on_sending_finished, Qt.QueuedConnection)
        worker.signals.error.connect(self.on_sending_error, Qt.QueuedConnection)
        worker.signals.finished.connect(lambda: self.active_workers.remove(worker))

        self.active_workers.append(worker)
        self.thread_pool.start(worker)

    def on_sending_finished(self, result: tuple):
        self.view.set_sending_state(False)
        success, message = result
        if success:
            ui_helpers.show_info_message(self.view, message, texts.BULK_SEND_SUCCESS_TITLE)
        else:
            ui_helpers.show_critical_message(self.view, message, texts.BULK_SEND_ERROR_TITLE)

    def on_sending_error(self, error_info: tuple):
        self.view.set_sending_state(False)
        error_message = texts.BULK_SEND_CRITICAL_ERROR_TEXT.format(error=error_info[1])
        ui_helpers.show_critical_message(self.view, error_message, texts.BULK_SEND_CRITICAL_ERROR_TITLE)