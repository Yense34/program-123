import os
import shutil
import uuid
from PySide6.QtWidgets import (
    QApplication, QDialog, QFileDialog, QListWidget, QListWidgetItem
)
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtCore import Qt

from database import database_manager as db
from views.delegates import GenericListDelegate
from views.product_dialog import SingleProductDialog, VariantTypeSelectionDialog, VariantDetailEditDialog
from views.stock_movement_dialog import StockMovementDialog
from utils.signals import app_signals
from services.session_manager import session
from utils import ui_texts as texts
from utils import ui_helpers

class ProductController:
    def __init__(self, view):
        self.view = view
        self.selected_product_id = None
        self.category_cache = {}
        
        self._setup_list()
        self._connect_signals()
        self.populate_filters()
        self.load_products()

    def _setup_list(self):
        self.delegate = GenericListDelegate()
        self.view.product_list.setItemDelegate(self.delegate)

    def _connect_signals(self):
        self.view.add_single_product_button.clicked.connect(self.open_add_product_dialog)
        self.view.search_input.textChanged.connect(self.load_products)
        self.view.category_filter_combo.currentIndexChanged.connect(self.load_products)
        self.view.stock_status_filter_combo.currentIndexChanged.connect(self.load_products)
        self.view.product_list.itemSelectionChanged.connect(self.on_product_selected)
        self.view.product_list.itemDoubleClicked.connect(self.handle_item_action)
        self.view.edit_product_button.clicked.connect(self._on_edit_button_clicked)
        self.view.archive_product_button.clicked.connect(self._on_archive_button_clicked)
        self.view.add_stock_movement_button.clicked.connect(self._open_stock_movement_dialog)
        self.delegate.edit_requested.connect(self._open_product_dialog)
        self.delegate.delete_requested.connect(self._archive_product)
        app_signals.products_updated.connect(self.on_data_updated)
        app_signals.stock_updated.connect(self.on_data_updated)

    def _load_category_cache(self):
        self.category_cache = {c['id']: c['ad'] for c in db.get_all_kategoriler()}

    def populate_filters(self):
        self.view.category_filter_combo.blockSignals(True)
        current_cat = self.view.category_filter_combo.currentData()
        self.view.category_filter_combo.clear()
        self.view.category_filter_combo.addItem("Kategoriler", None)
        
        self.category_cache = {cat['id']: cat['ad'] for cat in db.get_all_kategoriler()}
        for cat_id, cat_name in self.category_cache.items():
            self.view.category_filter_combo.addItem(cat_name, cat_id)
            
        if (index := self.view.category_filter_combo.findData(current_cat)) != -1:
            self.view.category_filter_combo.setCurrentIndex(index)
        self.view.category_filter_combo.blockSignals(False)

    def load_products(self):
        search_query = self.view.search_input.text()
        category_id = self.view.category_filter_combo.currentData()
        stock_status = self.view.stock_status_filter_combo.currentText()
        
        if stock_status == "Stok Durumu":
            stock_status = None
        if category_id is None and self.view.category_filter_combo.currentText() == "Kategoriler":
            pass

        products = db.get_products(search_query, category_id, stock_status)
        self._build_product_list(products)
        self.view.show_detail_panel(False)
    
    def _build_product_list(self, products):
        self.view.product_list.clear()
        for p_row in products:
            product = dict(p_row)
            item = QListWidgetItem()
            item_data = {
                "id": product['id'], "title": product.get("ad"),
                "subtitle": f"SKU: {product.get('stok_kodu')} | Kategori: {self.category_cache.get(product.get('kategori_id'), 'N/A')}",
                "stock": product.get('stok_miktari'), "actions": ['edit', 'delete']
            }
            item.setData(Qt.UserRole, item_data)
            self.view.product_list.addItem(item)
    
    def on_data_updated(self):
        self.populate_filters()
        self.load_products()

    def on_product_selected(self):
        selected_items = self.view.product_list.selectedItems()
        if not selected_items:
            self.selected_product_id = None; self.view.show_detail_panel(False)
            return
        self.selected_product_id = selected_items[0].data(Qt.UserRole)['id']
        self._refresh_detail_panel()
        
    def _refresh_detail_panel(self):
        if not self.selected_product_id: return self.view.show_detail_panel(False)
        product_row = db.get_product_by_id(self.selected_product_id)
        if not product_row: return self.view.show_detail_panel(False)
        product_data = dict(product_row)
        category_name = self.category_cache.get(product_data.get('kategori_id'), "Belirtilmemiş")
        self.view.update_details(product_data, category_name)
        self.view.show_detail_panel(True)

    def handle_item_action(self, item: QListWidgetItem):
        if product_data := item.data(Qt.UserRole): self._open_product_dialog(product_data.get('id'))

    def _on_edit_button_clicked(self):
        if self.selected_product_id: self._open_product_dialog(self.selected_product_id)

    def _on_archive_button_clicked(self):
        if self.selected_product_id: self._archive_product(self.selected_product_id)

    def _open_stock_movement_dialog(self):
        if not self.selected_product_id: return
        product_name = dict(db.get_product_by_id(self.selected_product_id))['ad']
        dialog = StockMovementDialog(product_name, self.view)
        if dialog.exec() == QDialog.Accepted:
            if data := dialog.get_data():
                db.add_stock_movement(self.selected_product_id, data['hareket_tipi'], data['miktar'], data['aciklama'])
                app_signals.products_updated.emit(); self._refresh_detail_panel()

    def open_add_product_dialog(self): self._open_product_dialog()

    def _open_product_dialog(self, product_id=None):
        product_data = dict(db.get_product_by_id(product_id)) if product_id else None
        dialog = SingleProductDialog(self.view, product_data, db.get_all_kategoriler(), db.get_all_vergi_oranlari())
        dialog.resim_sec_button.clicked.connect(lambda: self.select_product_image(dialog))
        dialog.resim_kaldir_button.clicked.connect(lambda: self.remove_product_image(dialog))
        is_main_product = product_data and not product_data.get('ana_urun_kodu')
        if product_id and is_main_product:
            dialog.show_variant_management(True)
            dialog.adjustSize()
            self._populate_variants_list(dialog.variants_list, product_data['stok_kodu'])
            dialog.add_variant_button.clicked.connect(lambda: self._handle_add_variant(dialog))
            dialog.delete_variant_button.clicked.connect(lambda: self._handle_delete_variant(dialog))
            dialog.variants_list.itemDoubleClicked.connect(self._handle_edit_variant_details)
        if dialog.exec() == QDialog.Accepted:
            self.save_product(dialog, editing_id=product_id, is_main_product_save=is_main_product)

    def save_product(self, dialog: SingleProductDialog, editing_id=None, is_main_product_save=False):
        main_product_data = dialog.get_data()
        if not main_product_data.get('ad') or not main_product_data.get('stok_kodu'):
            return ui_helpers.show_warning_message(dialog, "Ürün adı ve stok kodu zorunludur.")
        success = False
        if editing_id and is_main_product_save:
            variants_to_save = [dialog.variants_list.item(i).data(Qt.UserRole) for i in range(dialog.variants_list.count())]
            success = db.save_product_with_variants(editing_id, main_product_data, variants_to_save)
        else:
            success = db.add_product(main_product_data) if not editing_id else db.update_product(editing_id, main_product_data)
        if success:
            app_signals.products_updated.emit()
        else:
            ui_helpers.show_critical_message(dialog, "Ürün kaydedilirken bir hata oluştu.")
            
    def _populate_variants_list(self, list_widget: QListWidget, main_sku: str):
        list_widget.clear()
        variants = db.get_variants_by_main_code(main_sku)
        for variant in variants:
            item_text = f"{variant['ad'].split(' - ')[-1].strip()} (Fiyat: {variant['alis_fiyati']:.2f}, Stok: {variant['stok_miktari']})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, dict(variant))
            list_widget.addItem(item)
            
    def _handle_add_variant(self, product_dialog: SingleProductDialog):
        all_types = db.get_all_varyant_tipleri()
        selection_dialog = VariantTypeSelectionDialog(all_types, product_dialog)
        if selection_dialog.exec():
            selected_types = selection_dialog.get_selected_variants()
            for v_type in selected_types:
                exists = any( (product_dialog.variants_list.item(i).data(Qt.UserRole).get('variant_name') or product_dialog.variants_list.item(i).data(Qt.UserRole).get('ad', '').split(' - ')[-1].strip()) == v_type['ad'] for i in range(product_dialog.variants_list.count()) )
                if exists: continue
                item = QListWidgetItem(f"{v_type['ad']} (Detayları girmek için çift tıklayın)")
                item.setData(Qt.UserRole, {"variant_name": v_type['ad'], "varyant_tipi_id": v_type['id'], "alis_fiyati": 0, "stok_miktari": 0, "barkod": ""})
                product_dialog.variants_list.addItem(item)

    def _handle_delete_variant(self, product_dialog: SingleProductDialog):
        if selected_item := product_dialog.variants_list.currentItem():
            product_dialog.variants_list.takeItem(product_dialog.variants_list.currentRow())

    def _handle_edit_variant_details(self, item: QListWidgetItem):
        variant_data = item.data(Qt.UserRole)
        edit_dialog = VariantDetailEditDialog(variant_data.copy(), self.view)
        if edit_dialog.exec():
            new_details = edit_dialog.get_data()
            variant_data.update(new_details)
            item.setData(Qt.UserRole, variant_data)
            variant_name = variant_data.get('variant_name') or variant_data.get('ad', '').split(' - ')[-1].strip()
            item.setText(f"{variant_name} (Fiyat: {variant_data['alis_fiyati']:.2f}, Stok: {variant_data['stok_miktari']})")

    def _archive_product(self, product_id: int):
        product = dict(db.get_product_by_id(product_id))
        if ui_helpers.ask_confirmation(self.view, "Ürünü Arşivle", f"'{product['ad']}' ürününü ve ilişkili tüm varyantlarını arşivlemek istediğinizden emin misiniz?"):
            main_sku = product.get('ana_urun_kodu') or product.get('stok_kodu')
            db.archive_variant_group(main_sku)
            app_signals.products_updated.emit()

    def select_product_image(self, dialog_or_page):
        file_path, _ = QFileDialog.getOpenFileName(dialog_or_page, "Ürün Resmi Seç", "", "Resim Dosyaları (*.png *.jpg *.jpeg)")
        if not file_path: return
        target_folder = os.path.join("assets", "images", "products"); os.makedirs(target_folder, exist_ok=True)
        new_filename = f"{uuid.uuid4()}{os.path.splitext(file_path)[1]}"; new_path = os.path.join(target_folder, new_filename)
        try:
            shutil.copy(file_path, new_path)
            dialog_or_page.secilen_resim_yolu = new_path
            dialog_or_page.update_image_preview()
        except Exception as e:
            ui_helpers.show_critical_message(dialog_or_page, f"Logo kopyalanamadı: {e}")

    def remove_product_image(self, dialog_or_page):
        dialog_or_page.secilen_resim_yolu = None
        dialog_or_page.update_image_preview()