# dosya: controllers/sale_controller.py

from PySide6.QtWidgets import QDialog, QHeaderView
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import QTimer, Qt, QEvent, QObject
import json
from collections import defaultdict

from database import database_manager as db
from models import price_calculator
from views.customer_dialog import CustomerDialog
from views.quantity_dialog import QuantityDialog
from views.table_models import GenericTableModel
from views.suspended_sales_dialog import SuspendedSalesDialog
from views.delegates import CartDeleteDelegate
from utils.signals import app_signals
from services.session_manager import session
from utils import ui_texts as texts
from utils import ui_helpers

class SaleController(QObject): 
    def __init__(self, view):
        super().__init__()
        
        self.view = view
        self.cart = [] 
        self.cart_quantities = defaultdict(int)
        self.settings = {}
        self.current_prices = {}
        self.editing_sale_id = None
        self.selected_product_from_popup = None
        
        self.product_search_timer = QTimer(self.view)
        self.product_list_model = QStandardItemModel(self.view)
        
        self._setup_ui()
        self._connect_signals()
        self.load_initial_data()
        
        self.view.product_search_input.installEventFilter(self)

    def eventFilter(self, watched, event):
        if watched == self.view.product_search_input and event.type() == QEvent.Type.MouseButtonPress:
            if not self.view.product_search_input.text().strip():
                self._search_products_and_show_popup()
        return super().eventFilter(watched, event)

    def _setup_ui(self):
        headers = ["Ürün Adı", "Miktar", "Birim Fiyat", "Toplam Fiyat", ""] 
        column_keys = ["ad", "miktar", "birim_fiyat", "toplam_fiyat", ""]
        self.cart_model = GenericTableModel(headers=headers, column_keys=column_keys)
        self.view.cart_table.setModel(self.cart_model)
        self.cart_delete_delegate = CartDeleteDelegate(self.view)
        self.view.cart_table.setItemDelegateForColumn(4, self.cart_delete_delegate)
        self.view.cart_table.setColumnWidth(4, 40)
        self.view.cart_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.view.cart_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.view.product_search_popup_widget.setModel(self.product_list_model)
        self.product_search_timer.setSingleShot(True)
        self.product_search_timer.setInterval(300) 

    def _connect_signals(self):
        self.view.product_search_input.textChanged.connect(self.product_search_timer.start)
        self.product_search_timer.timeout.connect(self._search_products_and_show_popup)
        self.view.product_search_popup_widget.item_selected.connect(self._on_product_selected_from_popup)
        
        # --- DÜZELTME: Sinyal bağlantısı eski butondan yeni QAction'a güncellendi ---
        self.view.show_search_popup_action.triggered.connect(self._show_product_search_popup)
        self.view.product_search_input.returnPressed.connect(self._show_product_search_popup)
        
        self.view.add_to_cart_button.clicked.connect(self._on_add_to_cart_clicked)
        self.view.btn_add_ozel.clicked.connect(self._add_to_cart_ozel)
        
        self.view.remove_from_cart_button.clicked.connect(self.remove_from_cart)
        self.view.clear_cart_button.clicked.connect(self.clear_cart)
        self.view.add_customer_button.clicked.connect(self.open_new_customer_dialog)
        self.view.deposit_input.textChanged.connect(self.update_totals)
        self.view.complete_sale_button.clicked.connect(self.complete_sale)
        self.view.pay_full_button.clicked.connect(self._pay_in_full)
        self.view.cart_table.doubleClicked.connect(self.open_quantity_dialog)
        self.cart_delete_delegate.delete_requested.connect(self._remove_cart_item_by_row)
        self.view.suspend_sale_button.clicked.connect(self.suspend_sale)
        self.view.view_suspended_sales_button.clicked.connect(self.open_suspended_sales_dialog)
        
        app_signals.customers_updated.connect(self.populate_customers)
        app_signals.products_updated.connect(self._search_products)

    def _on_add_to_cart_clicked(self):
        if not self.selected_product_from_popup:
            return ui_helpers.show_warning_message(self.view, texts.SALE_MSG_SELECT_PRODUCT)
        
        selected_price_type = self.view.price_type_combo.currentText()
        
        price_to_use = 0.0
        if selected_price_type == "Nakit Satış Fiyatı":
            price_to_use = self.current_prices.get('kdvli_fiyat', 0)
        elif selected_price_type == "Kredi Kartı Fiyatı":
            price_to_use = self.current_prices.get('kkli_fiyat', 0)
        elif selected_price_type == "Alış + Kâr Fiyatı":
            price_to_use = self.current_prices.get('karli_fiyat_kdv_haric', 0)
        
        if self._add_to_cart(price_to_use):
            self.view.show_button_feedback(self.view.add_to_cart_button)

    def load_initial_data(self):
        self.settings = db.get_all_settings()
        self.populate_customers()
        self._update_dynamic_prices(None)

    def populate_customers(self):
        self.view.customer_combo.blockSignals(True)
        current_customer_id = self.view.customer_combo.currentData()
        self.view.customer_combo.clear()
        self.view.customer_combo.addItem("Genel Müşteri", 1)
        for customer in db.search_customers(query=""):
            self.view.customer_combo.addItem(f"{customer['ad']} {customer['soyad']}", customer['id'])
        if (index := self.view.customer_combo.findData(current_customer_id)) >= 0:
            self.view.customer_combo.setCurrentIndex(index)
        self.view.customer_combo.blockSignals(False)
    
    def _search_products_and_show_popup(self):
        self._search_products()
        if self.view.product_search_input.hasFocus():
            self.view.product_search_popup_widget.show_popup(self.view.product_search_input)

    def _show_product_search_popup(self):
        self._search_products()
        self.view.product_search_popup_widget.show_popup(self.view.product_search_input)
       
    def _search_products(self):
        products_in_db = db.get_products(search_query=self.view.product_search_input.text().strip())
        self._build_product_list_model(products_in_db)
        
    def _build_product_list_model(self, products):
        self.product_list_model.clear()
        for product_data in products:
            item = QStandardItem(f"{product_data['ad']} (Stok: {product_data['stok_miktari']})")
            item.setData(dict(product_data), Qt.UserRole)
            is_selectable = product_data['stok_miktari'] > 0 or self.editing_sale_id is not None
            item.setEnabled(is_selectable)
            self.product_list_model.appendRow(item)
        if self.product_list_model.rowCount() == 0:
            self.view.product_search_popup_widget.hide_popup()
            self._update_dynamic_prices(None)

    def _on_product_selected_from_popup(self, product_data: dict):
        self.selected_product_from_popup = product_data
        self._update_dynamic_prices(product_data)
        self.view.product_search_input.setText(product_data.get('ad', ''))
        self.view.product_search_popup_widget.hide_popup()
        self.view.quantity_spinbox.setFocus()
        self.view.quantity_spinbox.selectAll()

    def open_new_customer_dialog(self):
        dialog = CustomerDialog(self.view, customer_groups=db.get_all_musteri_gruplari())
        if dialog.exec():
            data = dialog.get_data()
            if not data['ad'] or not data['soyad']:
                return ui_helpers.show_warning_message(dialog, texts.CUSTOMER_MSG_NAME_SURNAME_REQUIRED)
            new_id = db.add_customer(data)
            app_signals.customers_updated.emit()
            if new_id:
                self.view.customer_combo.setCurrentIndex(self.view.customer_combo.findData(new_id))

    def _update_dynamic_prices(self, product_data: dict | None):
        is_currency_defined = True
        if not product_data:
            self.current_prices = {}
        else:
            self.current_prices = price_calculator.calculate_prices(product_data, self.settings)
            currency = product_data.get('alis_para_birimi', 'TL')
            if (self.current_prices.get('kdvli_fiyat', 0) == 0 and currency != 'TL' and 
                float(self.settings.get(f"{currency.lower()}_tl_kuru", '0').replace(',', '.')) <= 0):
                is_currency_defined = False
        self.view.update_price_displays(self.current_prices, is_currency_defined)

    def _add_to_cart(self, sale_price: float) -> bool:
        product_data = self.selected_product_from_popup
        if not product_data: 
            ui_helpers.show_warning_message(self.view, texts.SALE_MSG_SELECT_PRODUCT)
            return False
        if sale_price <= 0: 
            ui_helpers.show_warning_message(self.view, texts.SALE_MSG_PRICE_CANNOT_BE_ZERO)
            return False

        quantity_to_add = self.view.quantity_spinbox.value()
        product_id = product_data['id']
        in_cart_quantity = self.cart_quantities[product_id]
        
        if not self.editing_sale_id and in_cart_quantity + quantity_to_add > product_data['stok_miktari']:
            ui_helpers.show_warning_message(self.view, texts.SALE_MSG_INSUFFICIENT_STOCK_DETAIL.format(stock_amount=product_data['stok_miktari']))
            return False

        if existing_item := next((item for item in self.cart if item['urun_id'] == product_id and item['birim_fiyat'] == sale_price), None):
            existing_item['miktar'] += quantity_to_add
        else:
            self.cart.append({"urun_id": product_id, "ad": product_data['ad'], "miktar": quantity_to_add, "birim_fiyat": sale_price})
        
        self.cart_quantities[product_id] += quantity_to_add
        self.refresh_cart_display()
        
        self.view.product_search_input.clear()
        self.view.product_search_input.setFocus()
        self.selected_product_from_popup = None
        self._update_dynamic_prices(None)
        self.view.quantity_spinbox.setValue(1)
        return True
    
    def _add_to_cart_ozel(self):
        try:
            ozel_fiyat = float(self.view.ozel_fiyat_input.text().replace(',', '.'))
            if self.view.kdv_ekle_check.isChecked():
                product_data = self.selected_product_from_popup
                if not product_data: return
                tax_rate_row = db.get_vergi_orani_by_id(product_data.get('vergi_id')) if product_data.get('vergi_id') else None
                vat_percent = tax_rate_row['oran'] if tax_rate_row else float(self.settings.get('kdv_orani', '20.0').replace(',', '.'))
                ozel_fiyat *= (1 + vat_percent / 100)
            self._add_to_cart(ozel_fiyat)
        except (ValueError, TypeError):
            ui_helpers.show_warning_message(self.view, texts.SALE_MSG_INVALID_PRICE_INPUT)

    def _remove_cart_item_by_row(self, row: int):
        if 0 <= row < len(self.cart):
            removed_item = self.cart.pop(row)
            self.cart_quantities[removed_item['urun_id']] -= removed_item['miktar']
            if self.cart_quantities[removed_item['urun_id']] <= 0:
                del self.cart_quantities[removed_item['urun_id']]
            self.refresh_cart_display()

    def open_quantity_dialog(self, index):
        if index.column() == 4: return
        cart_item = self.cart[index.row()]
        product = db.get_product_by_id(cart_item['urun_id'])
        if not product: return ui_helpers.show_critical_message(self.view, texts.SALE_MSG_PRODUCT_NOT_FOUND)
            
        available_stock = product['stok_miktari']
        if self.editing_sale_id:
            original_item = next((item for item in getattr(self, 'original_cart_for_edit', []) if item['urun_id'] == cart_item['urun_id']), None)
            if original_item:
                available_stock += original_item['miktar']
        
        dialog = QuantityDialog(cart_item['ad'], cart_item['miktar'], self.view)
        dialog.quantity_spinbox.setMaximum(available_stock)
        
        if dialog.exec():
            new_quantity = dialog.get_new_quantity()
            quantity_diff = new_quantity - cart_item['miktar']
            
            if new_quantity == 0: 
                self.cart.pop(index.row())
            else: 
                cart_item['miktar'] = new_quantity
            
            self.cart_quantities[cart_item['urun_id']] += quantity_diff
            if self.cart_quantities[cart_item['urun_id']] <= 0:
                del self.cart_quantities[cart_item['urun_id']]
            
            self.refresh_cart_display()

    def remove_from_cart(self):
        if not (selected_indexes := self.view.cart_table.selectionModel().selectedRows()):
            return ui_helpers.show_warning_message(self.view, texts.SALE_MSG_SELECT_ITEM_TO_REMOVE)
        for index in sorted(selected_indexes, key=lambda i: i.row(), reverse=True):
            self._remove_cart_item_by_row(index.row())
            
    def clear_cart(self):
        if not self.cart: return
        if not self.editing_sale_id and not ui_helpers.ask_confirmation(self.view, texts.SALE_MSG_CLEAR_CART_TITLE, texts.SALE_MSG_CLEAR_CART_TEXT):
            return
        self._reset_cart()
        self.refresh_cart_display()

    def _reset_cart(self):
        self.cart.clear(); self.cart_quantities.clear()

    def refresh_cart_display(self):
        self.cart_model.update_data([item | {"toplam_fiyat": item['miktar'] * item['birim_fiyat']} for item in self.cart])
        self.update_totals()

    def update_totals(self):
        total = sum(item['miktar'] * item['birim_fiyat'] for item in self.cart)
        try:
            deposit = float(self.view.deposit_input.text().replace(',', '.') or 0)
        except ValueError: deposit = 0
        self.view.total_label.setText(f"{total:,.2f} TL")
        self.view.balance_label.setText(f"{total - deposit:,.2f} TL")
        balance = total - deposit
        if balance < 0: self.view.balance_label.setStyleSheet("font-weight: bold; font-size: 18px; color: #2F9E44;")
        elif balance > 0: self.view.balance_label.setStyleSheet("font-weight: bold; font-size: 18px; color: #E03131;")
        else: self.view.balance_label.setStyleSheet("font-weight: bold; font-size: 18px; color: #2C3E50;")
    
    def _pay_in_full(self):
        total_text = self.view.total_label.text().replace(' TL', '').replace('.', '').replace(',', '.')
        self.view.deposit_input.setText(total_text)

    def complete_sale(self):
        if self.editing_sale_id and not session.has_permission('sales:edit'):
            return ui_helpers.show_warning_message(self.view, texts.MSG_UNAUTHORIZED_ACTION_DETAIL)
        if not self.cart: return ui_helpers.show_warning_message(self.view, texts.SALE_MSG_ADD_ITEM_FIRST)
        
        if self.editing_sale_id:
            success, msg = db.delete_sale_by_id(self.editing_sale_id)
            if not success:
                return ui_helpers.show_critical_message(self.view, f"Eski satış güncellenemedi: {msg}")
        
        sale_data = {'musteri_id': self.view.customer_combo.currentData(), 'toplam_tutar': sum(item['miktar'] * item['birim_fiyat'] for item in self.cart), 'odenen_tutar': float(self.view.deposit_input.text().replace(',', '.') or 0)}
        if satis_id := db.create_sale(sale_data, self.cart):
            message = texts.SALE_MSG_UPDATE_SUCCESS.format(old_sale_id=self.editing_sale_id, new_sale_id=satis_id) if self.editing_sale_id else texts.SALE_MSG_SAVE_SUCCESS.format(sale_id=satis_id)
            ui_helpers.show_info_message(self.view, message)
            app_signals.stock_updated.emit(); app_signals.sales_updated.emit(); app_signals.customers_updated.emit()
            self.reset_sale_form()
        else:
            ui_helpers.show_critical_message(self.view, texts.SALE_MSG_SAVE_ERROR)

    def load_sale_for_editing(self, sale_id):
        self.reset_sale_form()
        sale_data = db.get_sale_details_for_report(sale_id)
        if not sale_data: return ui_helpers.show_critical_message(self.view, texts.SALE_HISTORY_MSG_NOT_FOUND)
        self.editing_sale_id, self.original_cart_for_edit = sale_id, [dict(row) for row in sale_data['details']]
        sale_info = dict(sale_data['sale_info'])
        if (customer_index := self.view.customer_combo.findData(sale_info.get('musteri_id'))) != -1: self.view.customer_combo.setCurrentIndex(customer_index)
        self._reset_cart()
        for item in self.original_cart_for_edit:
            self.cart.append({"urun_id": item['urun_id'], "ad": item['urun_ad'], "miktar": item['miktar'], "birim_fiyat": item['birim_fiyat']})
            self.cart_quantities[item['urun_id']] += item['miktar']
        self.view.deposit_input.setText(str(sale_info.get('odenen_tutar', 0)))
        self.refresh_cart_display()
        self._search_products()
        self.view.update_ui_for_editing(True)

    def reset_sale_form(self):
        self._reset_cart(); self.refresh_cart_display()
        self.view.customer_combo.setCurrentIndex(0)
        self.view.deposit_input.setText("0")
        self.view.payment_method_combo.setCurrentIndex(0)
        self.editing_sale_id = None
        self.original_cart_for_edit = []
        self.view.update_ui_for_editing(False)
        self._search_products()
        self.view.product_search_input.clear()
        self.view.product_search_popup_widget.hide_popup()

    def suspend_sale(self):
        if not self.cart: return ui_helpers.show_warning_message(self.view, texts.SALE_MSG_SUSPEND_NO_ITEMS)
        note, ok = ui_helpers.get_text_input(self.view, texts.SALE_MSG_SUSPEND_TITLE, texts.SALE_MSG_SUSPEND_TEXT)
        if ok:
            db.add_suspended_sale(self.view.customer_combo.currentData(), json.dumps(self.cart), note)
            ui_helpers.show_info_message(self.view, texts.SALE_MSG_SUSPEND_SUCCESS)
            self.reset_sale_form()

    def open_suspended_sales_dialog(self):
        model = GenericTableModel(["Tarih", "Müşteri", "Not"], ["askiya_alinma_tarihi", "musteri_adi", "not_str"])
        dialog = SuspendedSalesDialog(model, self.view)
        dialog.sales_table.model().update_data(db.get_all_suspended_sales())
        result = dialog.exec()
        if result and (sale_id := dialog.get_selected_sale_id()):
            if result == QDialog.Accepted: self.resume_sale(sale_id)
            elif result == 2: self.delete_suspended_sale(sale_id)

    def resume_sale(self, sale_id):
        suspended_sale = db.get_suspended_sale_by_id(sale_id)
        if not suspended_sale: return ui_helpers.show_critical_message(self.view, texts.SALE_MSG_SUSPENDED_NOT_FOUND)
        self.reset_sale_form()
        if (customer_index := self.view.customer_combo.findData(suspended_sale['musteri_id'])) != -1: 
            self.view.customer_combo.setCurrentIndex(customer_index)
        self._reset_cart()
        self.cart = json.loads(suspended_sale['sepet_icerigi'])
        for item in self.cart: self.cart_quantities[item['urun_id']] += item['miktar']
        self.refresh_cart_display()
        db.delete_suspended_sale(sale_id)
        app_signals.status_message_updated.emit(texts.SALE_MSG_SUSPENDED_RESUMED.format(sale_id=sale_id), 4000)

    def delete_suspended_sale(self, sale_id):
        if ui_helpers.ask_confirmation(self.view, texts.SALE_MSG_DELETE_SUSPENDED_TITLE, texts.SALE_MSG_DELETE_SUSPENDED_TEXT.format(sale_id=sale_id)):
            db.delete_suspended_sale(sale_id)
            ui_helpers.show_info_message(self.view, texts.SALE_MSG_DELETE_SUSPENDED_SUCCESS)