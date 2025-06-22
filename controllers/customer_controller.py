# dosya: controllers/customer_controller.py

from PySide6.QtWidgets import QHeaderView
from PySide6.QtCore import QTimer
from PySide6.QtGui import QShortcut, QKeySequence

from database import database_manager as db
from views.table_models import GenericTableModel
from views.customer_dialog import CustomerDialog
from views.payment_dialog import PaymentDialog
from views.transaction_history_dialog import TransactionHistoryDialog
from views.delegates import ActionDelegate
from utils.signals import app_signals
from utils import ui_texts as texts
from services.session_manager import session
from utils import ui_helpers

class CustomerController:
    def __init__(self, view):
        self.view = view
        self.selected_customer_id = None
        
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(350) 
        
        self._setup_table_model()
        self._connect_signals()
        self._setup_shortcuts()
        self._populate_filters()
        self.load_customers()

    def _setup_table_model(self):
        headers = ["Ad", "Soyad", "Telefon", "E-posta", "İşlemler"]
        column_keys = ["ad", "soyad", "telefon", "eposta", ""]
        self.table_model = GenericTableModel(headers=headers, column_keys=column_keys)
        self.view.customer_table.setModel(self.table_model)
        
        self.action_delegate = ActionDelegate(self.view)
        self.view.customer_table.setItemDelegateForColumn(4, self.action_delegate)
        self.view.customer_table.setMouseTracking(True)
        self.view.customer_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.view.customer_table.setColumnWidth(4, 80)

    def _connect_signals(self):
        self.view.add_customer_button.clicked.connect(self.open_add_dialog)
        self.view.search_input.textChanged.connect(self.search_timer.start)
        self.view.group_filter_combo.currentIndexChanged.connect(self.load_customers)
        self.search_timer.timeout.connect(self.load_customers)
        
        self.view.customer_table.selectionModel().selectionChanged.connect(self.on_customer_selected)
        
        self.action_delegate.edit_requested.connect(self.handle_edit_request)
        self.action_delegate.delete_requested.connect(self.handle_delete_request)
        
        self.view.add_payment_button.clicked.connect(self.open_add_payment_dialog)
        self.view.view_transactions_button.clicked.connect(self.open_transaction_history_dialog)
        
        app_signals.customers_updated.connect(self.on_data_updated)
        app_signals.sales_updated.connect(self.on_data_updated)

    def _setup_shortcuts(self):
        add_shortcut = QShortcut(QKeySequence("Ctrl+N"), self.view)
        add_shortcut.activated.connect(self.view.add_customer_button.click)

    def handle_edit_request(self, row):
        customer_id = self.table_model.get_item_id(self.table_model.index(row, 0))
        self.open_edit_dialog(customer_id)

    def handle_delete_request(self, row):
        customer_id = self.table_model.get_item_id(self.table_model.index(row, 0))
        self.archive_customer(customer_id)

    def _populate_filters(self):
        current_selection = self.view.group_filter_combo.currentData()
        self.view.group_filter_combo.blockSignals(True)
        self.view.group_filter_combo.clear()
        self.view.group_filter_combo.addItem("Tüm Gruplar", 0)
        
        groups = db.get_all_musteri_gruplari()
        for group in groups:
            self.view.group_filter_combo.addItem(group['ad'], group['id'])
        
        if (index := self.view.group_filter_combo.findData(current_selection)) > 0:
            self.view.group_filter_combo.setCurrentIndex(index)
            
        self.view.group_filter_combo.blockSignals(False)

    def on_data_updated(self):
        current_id = self.selected_customer_id
        self._populate_filters()
        self.load_customers()
        if current_id:
            for row in range(self.table_model.rowCount()):
                item_id = self.table_model.get_item_id(self.table_model.index(row, 0))
                if item_id == current_id:
                    self.view.customer_table.selectRow(row)
                    break
        else:
            self.view.show_detail_panel(False)

    def load_customers(self):
        query = self.view.search_input.text()
        grup_id = self.view.group_filter_combo.currentData()
        customers = db.search_customers(query, group_id=grup_id)
        self.table_model.update_data(customers)
        self.view.show_detail_panel(False)
        self.selected_customer_id = None
        self.view.add_customer_button.setVisible(session.has_permission('customers:create'))

    def on_customer_selected(self, selected, deselected):
        indexes = selected.indexes()
        if not indexes:
            self.selected_customer_id = None
            self.view.show_detail_panel(False)
            return

        self.selected_customer_id = self.table_model.get_item_id(indexes[0])
        self._refresh_detail_panel()

    def _refresh_detail_panel(self):
        if not self.selected_customer_id:
            self.view.show_detail_panel(False)
            return
        
        customer_row = db.get_customer_by_id(self.selected_customer_id)
        if not customer_row: 
            self.view.show_detail_panel(False)
            return
            
        balance_info = db.get_customer_balance(self.selected_customer_id)
        self.view.update_details(dict(customer_row), balance_info)
        self.view.show_detail_panel(True)
            
    def _validate_customer_data(self, data, dialog):
        if not data['ad'] or not data['soyad']:
            ui_helpers.show_warning_message(dialog, texts.CUSTOMER_MSG_NAME_SURNAME_REQUIRED)
            return False
        return True

    def open_add_dialog(self):
        if not session.has_permission('customers:create'): return
        customer_groups = db.get_all_musteri_gruplari()
        dialog = CustomerDialog(self.view, customer_groups=customer_groups)
        if dialog.exec():
            data = dialog.get_data()
            if not self._validate_customer_data(data, dialog): return
            customer_name = f"{data['ad']} {data['soyad']}"
            db.add_customer(data)
            app_signals.customers_updated.emit()
            app_signals.status_message_updated.emit(texts.CUSTOMER_MSG_ADD_SUCCESS.format(customer_name=customer_name), 3000)

    def open_edit_dialog(self, customer_id):
        if not customer_id: return
        if not session.has_permission('customers:edit'): return
        customer_row = db.get_customer_by_id(customer_id)
        if not customer_row:
            ui_helpers.show_critical_message(self.view, texts.CUSTOMER_MSG_NOT_FOUND)
            return
        customer_groups = db.get_all_musteri_gruplari()
        customer_data = dict(customer_row)
        dialog = CustomerDialog(self.view, customer_data=customer_data, customer_groups=customer_groups)
        if dialog.exec():
            new_data = dialog.get_data()
            if not self._validate_customer_data(new_data, dialog): return
            db.update_customer(customer_id, new_data)
            app_signals.customers_updated.emit()
            app_signals.status_message_updated.emit(texts.CUSTOMER_MSG_UPDATE_SUCCESS, 3000)

    def open_add_payment_dialog(self):
        if not self.selected_customer_id: return
        dialog = PaymentDialog(self.view)
        if dialog.exec():
            data = dialog.get_data()
            if data['tutar'] > 0:
                db.add_payment(self.selected_customer_id, data['tutar'], data['aciklama'])
                app_signals.customers_updated.emit()
                app_signals.status_message_updated.emit(texts.CUSTOMER_MSG_PAYMENT_SUCCESS, 3000)

    def archive_customer(self, customer_id):
        if not customer_id: return
        if not session.has_permission('customers:delete'): return
        customer = db.get_customer_by_id(customer_id)
        customer_name = f"{customer['ad']} {customer['soyad']}"
        confirmed = ui_helpers.ask_confirmation(
            parent=self.view,
            title=texts.CUSTOMER_ARCHIVE_TITLE,
            text=texts.CUSTOMER_ARCHIVE_TEXT.format(customer_name=customer_name),
            informative_text=texts.CUSTOMER_ARCHIVE_INFO
        )
        if confirmed:
            db.archive_customer(customer_id)
            app_signals.customers_updated.emit()
            app_signals.status_message_updated.emit(texts.CUSTOMER_MSG_ARCHIVE_SUCCESS.format(customer_name=customer_name), 3000)

    def open_transaction_history_dialog(self):
        if not self.selected_customer_id: return
        customer = db.get_customer_by_id(self.selected_customer_id)
        customer_name = f"{customer['ad']} {customer['soyad']}"
        dialog = TransactionHistoryDialog(customer_name, self.view)
        headers = ["Tarih", "İşlem Tipi", "Açıklama", "Borç", "Alacak"]
        column_keys = ["tarih", "islem_tipi", "aciklama", "borc", "alacak"]
        history_model = GenericTableModel(headers, column_keys)
        dialog.history_table.setModel(history_model)
        transactions = db.get_customer_transaction_history(self.selected_customer_id)
        history_model.update_data(transactions)
        
        total_debit = sum(t.get('borc', 0) for t in transactions)
        total_credit = sum(t.get('alacak', 0) for t in transactions)
        balance = total_debit - total_credit
        dialog.total_debit_label.setText(f"Toplam Borç: {total_debit:,.2f} TL")
        dialog.total_credit_label.setText(f"Toplam Alacak: {total_credit:,.2f} TL")
        dialog.balance_label.setText(f"Bakiye: {balance:,.2f} TL")
        dialog.exec()