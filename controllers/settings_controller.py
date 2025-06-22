# dosya: controllers/settings_controller.py

import os
import shutil
import logging
from datetime import datetime
from PySide6.QtWidgets import QFileDialog, QInputDialog, QLineEdit, QCheckBox, QApplication
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QThreadPool

from services.background_worker import BackgroundWorker
from database import database_manager as db
from models import currency_service, sms_service, email_service
from utils.signals import app_signals
from services.session_manager import session
from utils import ui_texts as texts
from views.user_dialog import UserDialog
from views.table_models import GenericTableModel
from utils import ui_helpers
from views.confirmation_dialog import ConfirmationDialog

class SettingsController:
    def __init__(self, view):
        self.view = view
        self.company_logo_path = None
        self.selected_category_id = None
        self.selected_role_id = None
        self.thread_pool = QThreadPool()
        self.active_workers = []
        self.permission_checkboxes = [] 
        
        self._setup_tables()
        self._connect_signals()
        self._apply_permissions()

    def _setup_tables(self):
        self.user_table_model = GenericTableModel(
            headers=["Kullanıcı Adı", "Atanmış Rol"], 
            column_keys=["kullanici_adi", "rol_adi"]
        )
        self.view.users_table.setModel(self.user_table_model)

        self.vergi_table_model = GenericTableModel(
            headers=["Vergi Adı", "Oran (%)"], 
            column_keys=["ad", "oran"]
        )
        self.view.vergi_table.setModel(self.vergi_table_model)

    def _connect_signals(self):
        # Navigasyon sinyalleri
        self.view.card_user_company.clicked.connect(self.on_user_company_card_clicked)
        self.view.card_product.clicked.connect(self.on_product_card_clicked)
        self.view.card_customer.clicked.connect(self.on_customer_card_clicked)
        self.view.card_application.clicked.connect(self.on_application_card_clicked)
        
        self.view.back_to_hub_button.clicked.connect(self.on_back_to_hub_clicked)
        self.view.back_to_hub_button_2.clicked.connect(self.on_back_to_hub_clicked)
        self.view.back_to_hub_button_3.clicked.connect(self.on_back_to_hub_clicked)
        self.view.back_to_hub_button_4.clicked.connect(self.on_back_to_hub_clicked)
        
        # Sekme değişim sinyalleri
        self.view.user_company_tabs.currentChanged.connect(self.on_user_company_tab_changed)
        self.view.product_management_tabs.currentChanged.connect(self.on_product_tab_changed)
        self.view.application_settings_tabs.currentChanged.connect(self.on_application_tab_changed)

        # Firma Profili Sinyalleri
        self.view.save_profile_button.clicked.connect(self.save_company_profile)
        self.view.logo_upload_button.clicked.connect(self.select_company_logo)
        self.view.logo_remove_button.clicked.connect(self.remove_company_logo)
        
        # Kullanıcı Yönetimi Sinyalleri
        self.view.add_user_button.clicked.connect(self.open_add_user_dialog)
        self.view.delete_user_button.clicked.connect(self.delete_selected_user)
        self.view.change_password_button.clicked.connect(self.change_selected_user_password)
        
        # Roller ve Yetkiler Sinyalleri
        self.view.roles_widget.list_widget.currentItemChanged.connect(self._on_role_selected)
        self.view.roles_widget.add_button.clicked.connect(self.add_rol)
        self.view.roles_widget.delete_button.clicked.connect(self.delete_rol)
        self.view.save_permissions_button.clicked.connect(self.save_permissions_for_role)
        
        # Ürün Yönetimi Sinyalleri
        self.view.kategori_widget.add_button.clicked.connect(self.add_kategori)
        self.view.kategori_widget.delete_button.clicked.connect(self.delete_kategori)
        self.view.kategori_widget.edit_button.clicked.connect(self.edit_kategori)
        self.view.kategori_widget.list_widget.currentItemChanged.connect(self._on_category_selected)
        self.view.kategori_kar_widget.save_profit_button.clicked.connect(self._save_category_profit)
        self.view.varyant_tipi_widget.add_button.clicked.connect(self.add_varyant_tipi)
        self.view.varyant_tipi_widget.delete_button.clicked.connect(self.delete_varyant_tipi)
        self.view.varyant_tipi_widget.edit_button.clicked.connect(self.edit_varyant_tipi)
        self.view.add_vergi_button.clicked.connect(self.add_vergi_orani)
        self.view.delete_vergi_button.clicked.connect(self.delete_vergi_orani)
        
        # Müşteri Yönetimi Sinyalleri
        self.view.musteri_grup_widget.add_button.clicked.connect(self.add_musteri_grup)
        self.view.musteri_grup_widget.delete_button.clicked.connect(self.delete_musteri_grup)
        self.view.musteri_grup_widget.edit_button.clicked.connect(self.edit_musteri_grup)
        
        # Uygulama Ayarları Sinyalleri
        self.view.save_app_settings_button.clicked.connect(self.save_application_settings)
        self.view.manual_rate_update_button.clicked.connect(self.trigger_live_rate_update)
        self.view.test_sms_button.clicked.connect(self._test_sms_settings)
        self.view.test_email_button.clicked.connect(self._test_email_settings)
        self.view.backup_button.clicked.connect(self._backup_database)
        self.view.restore_button.clicked.connect(self._restore_database)
        self.view.auto_backup_checkbox.stateChanged.connect(self._save_auto_backup_setting)
    
    def on_user_company_card_clicked(self):
        settings = db.get_all_settings()
        self.load_company_profile(settings)
        self.view.stacked_widget.setCurrentIndex(1)
        self._apply_permissions()
        
    def on_product_card_clicked(self):
        self.load_product_management_data()
        self.view.stacked_widget.setCurrentIndex(2)

    def on_customer_card_clicked(self):
        self.load_customer_management_data()
        self.view.stacked_widget.setCurrentIndex(3)

    def on_application_card_clicked(self):
        self.load_application_settings_data()
        self.view.stacked_widget.setCurrentIndex(4)

    def on_back_to_hub_clicked(self):
        self.view.stacked_widget.setCurrentIndex(0)
    
    def on_user_company_tab_changed(self, index):
        tab_text = self.view.user_company_tabs.tabText(index)
        if "Kullanıcı" in tab_text: self.load_users_list()
        elif "Roller" in tab_text: self.load_roles_and_permissions_tab()
            
    def on_product_tab_changed(self, index):
        self.load_product_management_data()
    
    def on_application_tab_changed(self, index):
        self.load_application_settings_data()

    def load_product_management_data(self):
        current_tab_text = self.view.product_management_tabs.tabText(self.view.product_management_tabs.currentIndex())
        if "Kategoriler" in current_tab_text:
            self.view.kategori_widget.populate_list(db.get_all_kategoriler())
            self.view.kategori_kar_widget.setVisible(False)
        elif "Varyant" in current_tab_text:
            self.view.varyant_tipi_widget.populate_list(db.get_all_varyant_tipleri())
        elif "Vergi" in current_tab_text:
            self.vergi_table_model.update_data(db.get_all_vergi_oranlari())

    def load_customer_management_data(self):
        self.view.musteri_grup_widget.populate_list(db.get_all_musteri_gruplari())

    def load_application_settings_data(self):
        settings = db.get_all_settings()
        self.load_financial_settings(settings)
        self.load_communication_settings(settings)
        self.load_backup_settings()

    def _apply_permissions(self):
        can_manage_users = session.has_permission('settings:user_management')
        try:
            profile_tab_index = self.view.user_company_tabs.indexOf(self.view.profile_content)
            users_tab_index = self.view.user_company_tabs.indexOf(self.view.users_content)
            roles_tab_index = self.view.user_company_tabs.indexOf(self.view.roles_content)
            if users_tab_index != -1: self.view.user_company_tabs.setTabVisible(users_tab_index, can_manage_users)
            if roles_tab_index != -1: self.view.user_company_tabs.setTabVisible(roles_tab_index, can_manage_users)
            self.view.add_user_button.setEnabled(can_manage_users)
            self.view.delete_user_button.setEnabled(can_manage_users)
            self.view.change_password_button.setEnabled(can_manage_users)
            self.view.roles_widget.setEnabled(can_manage_users)
            self.view.permissions_card.setEnabled(can_manage_users)
        except AttributeError: pass
    
    def _clear_permissions_layout(self):
        self.permission_checkboxes.clear()
        while self.view.permissions_layout.count():
            child = self.view.permissions_layout.takeAt(0)
            if child and child.widget(): child.widget().deleteLater()

    def _populate_permissions(self, all_permissions, role_permissions, is_enabled):
        self._clear_permissions_layout()
        role_permission_ids = {p['id'] for p in role_permissions}
        for perm in all_permissions:
            checkbox = QCheckBox(perm['aciklama'])
            checkbox.setProperty("permission_id", perm['id'])
            checkbox.setChecked(perm['id'] in role_permission_ids)
            checkbox.setEnabled(is_enabled)
            self.view.permissions_layout.addWidget(checkbox)
            self.permission_checkboxes.append(checkbox)
        self.view.save_permissions_button.setEnabled(is_enabled)

    def _on_role_selected(self, current, previous):
        if not current:
            self.selected_role_id = None
            self._clear_permissions_layout()
            self.view.permissions_card.setEnabled(False)
            self.view.roles_widget.delete_button.setEnabled(False)
            return
        self.selected_role_id = current.data(Qt.UserRole)
        is_protected = current.text().lower() == 'yönetici'
        self.view.permissions_card.setEnabled(True)
        self._populate_permissions(db.get_all_yetkiler(), db.get_yetkiler_for_rol(self.selected_role_id), not is_protected)
        self.view.roles_widget.delete_button.setEnabled(not is_protected)
        self.view.permissions_card.setToolTip("Yönetici rolünün tüm yetkileri vardır ve değiştirilemez." if is_protected else "")

    def save_permissions_for_role(self):
        if not self.selected_role_id: return
        selected_ids = [cb.property("permission_id") for cb in self.permission_checkboxes if cb.isChecked()]
        db.update_yetkiler_for_rol(self.selected_role_id, selected_ids)
        ui_helpers.show_info_message(self.view, texts.SETTINGS_MSG_PERMISSIONS_UPDATE_SUCCESS)
    
    def _on_category_selected(self, current, previous):
        if not current:
            self.view.kategori_kar_widget.setVisible(False)
            self.selected_category_id = None
            return
        self.selected_category_id = current.data(Qt.UserRole)
        details = db.get_category_details(self.selected_category_id)
        if details:
            self.view.kategori_kar_widget.category_name_label.setText(f"<b>{details['ad']}</b>")
            self.view.kategori_kar_widget.profit_type_combo.setCurrentText(details['kar_tipi'] or db.get_setting('kar_yontemi', 'Yüzdesel Kâr (%)'))
            self.view.kategori_kar_widget.profit_value_input.setText(str(details['kar_degeri'] if details['kar_degeri'] is not None else db.get_setting('kar_degeri', '50')))
            self.view.kategori_kar_widget.setVisible(True)
            
    def load_company_profile(self, settings):
        self.view.company_name_input.setText(settings.get('company_name', ''))
        self.view.company_address_input.setPlainText(settings.get('company_address', ''))
        self.view.company_phone_input.setText(settings.get('company_phone', ''))
        self.view.company_email_input.setText(settings.get('company_email', ''))
        self.view.company_website_input.setText(settings.get('company_website', ''))
        self.view.company_tax_office_input.setText(settings.get('company_tax_office', ''))
        self.view.company_tax_id_input.setText(settings.get('company_tax_id', ''))
        self.company_logo_path = settings.get('company_logo_path')
        self.update_logo_preview()
        
    def save_company_profile(self):
        settings_to_save = {'company_name': self.view.company_name_input.text(),'company_address': self.view.company_address_input.toPlainText(),'company_phone': self.view.company_phone_input.text(),'company_email': self.view.company_email_input.text(),'company_website': self.view.company_website_input.text(),'company_tax_office': self.view.company_tax_office_input.text(),'company_tax_id': self.view.company_tax_id_input.text(),'company_logo_path': self.company_logo_path or ""}
        for key, value in settings_to_save.items(): db.save_setting(key, value)
        ui_helpers.show_info_message(self.view, texts.SETTINGS_MSG_PROFILE_SAVE_SUCCESS)
        
    def select_company_logo(self):
        file_path, _ = QFileDialog.getOpenFileName(self.view, "Logo Seç", "", "Resim Dosyaları (*.png *.jpg)")
        if not file_path: return
        target_folder = os.path.join("assets", "images", "company"); os.makedirs(target_folder, exist_ok=True)
        new_path = os.path.join(target_folder, f"logo{os.path.splitext(file_path)[1]}")
        try:
            shutil.copy(file_path, new_path)
            self.company_logo_path = new_path
            self.update_logo_preview()
        except Exception as e: ui_helpers.show_critical_message(self.view, texts.SETTINGS_MSG_LOGO_COPY_ERROR.format(error=e))
        
    def remove_company_logo(self):
        self.company_logo_path = None
        self.update_logo_preview()
        ui_helpers.show_info_message(self.view, texts.SETTINGS_MSG_LOGO_REMOVE_SUCCESS)
        
    def update_logo_preview(self):
        if self.company_logo_path and os.path.exists(self.company_logo_path):
            self.view.logo_preview_label.setPixmap(QPixmap(self.company_logo_path).scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.view.logo_preview_label.setText("Logo Yüklü Değil")
            self.view.logo_preview_label.setPixmap(QPixmap())
            
    def _add_management_item(self, widget, db_add_function, post_add_signal=None):
        item_name = widget.input_line.text().strip()
        if item_name:
            db_add_function(item_name)
            widget.input_line.clear()
            if widget in [self.view.kategori_widget, self.view.varyant_tipi_widget]: self.load_product_management_data()
            elif widget == self.view.musteri_grup_widget: self.load_customer_management_data()
            if post_add_signal: post_add_signal.emit()
            
    def _edit_management_item(self, widget, db_update_function, title, post_edit_signal=None):
        selected_item = widget.list_widget.currentItem()
        if not selected_item: return ui_helpers.show_warning_message(self.view, texts.MSG_SELECT_TO_EDIT)
        old_name, item_id = selected_item.text(), selected_item.data(Qt.UserRole)
        new_name, ok = QInputDialog.getText(self.view, title, "Yeni ad:", QLineEdit.Normal, old_name)
        if ok and new_name and new_name.strip() != old_name:
            db_update_function(item_id, new_name.strip())
            if widget in [self.view.kategori_widget, self.view.varyant_tipi_widget]: self.load_product_management_data()
            elif widget == self.view.musteri_grup_widget: self.load_customer_management_data()
            if post_edit_signal: post_edit_signal.emit()
            
    def _delete_management_item(self, widget, db_delete_function, in_use_check_function=None, error_text=None, post_delete_signal=None):
        selected = widget.list_widget.currentItem()
        if not selected: return ui_helpers.show_warning_message(self.view, "Lütfen silmek için bir öğe seçin.")
        item_id, item_name = selected.data(Qt.UserRole), selected.text()
        if in_use_check_function and in_use_check_function(item_id): return ui_helpers.show_warning_message(self.view, error_text.format(name=item_name))
        if ui_helpers.ask_confirmation(self.view, texts.TITLE_CONFIRM_DELETE, f"'{item_name}' öğesini silmek istediğinizden emin misiniz?"):
            success, message = db_delete_function(item_id)
            if success:
                if widget in [self.view.kategori_widget, self.view.varyant_tipi_widget]: self.load_product_management_data()
                elif widget == self.view.musteri_grup_widget: self.load_customer_management_data()
                if post_delete_signal: post_delete_signal.emit()
            else: ui_helpers.show_warning_message(self.view, message)

    def add_kategori(self): self._add_management_item(self.view.kategori_widget, db.add_kategori, app_signals.products_updated)
    def edit_kategori(self): self._edit_management_item(self.view.kategori_widget, db.update_kategori, "Kategori Düzenle", app_signals.products_updated)
    def delete_kategori(self): self._delete_management_item(self.view.kategori_widget, db.delete_kategori, db.check_kategori_in_use, texts.SETTINGS_MSG_CATEGORY_DELETE_ERROR, app_signals.products_updated)
    def add_varyant_tipi(self): self._add_management_item(self.view.varyant_tipi_widget, db.add_varyant_tipi)
    def edit_varyant_tipi(self): self._edit_management_item(self.view.varyant_tipi_widget, db.update_varyant_tipi, "Varyant Tipi Düzenle")
    def delete_varyant_tipi(self): self._delete_management_item(self.view.varyant_tipi_widget, db.delete_varyant_tipi, db.check_varyant_tipi_in_use, texts.SETTINGS_MSG_VARIANT_TYPE_DELETE_ERROR)
    def add_musteri_grup(self): self._add_management_item(self.view.musteri_grup_widget, db.add_musteri_grup, app_signals.customers_updated)
    def edit_musteri_grup(self): self._edit_management_item(self.view.musteri_grup_widget, db.update_musteri_grup, "Müşteri Grubu Düzenle", app_signals.customers_updated)
    def delete_musteri_grup(self): self._delete_management_item(self.view.musteri_grup_widget, db.delete_musteri_grup, db.check_musteri_grup_in_use, "Bu grup bir veya daha fazla müşteriye atanmış olduğu için silinemez.", app_signals.customers_updated)
    
    def _save_category_profit(self):
        if not self.selected_category_id: return
        try:
            profit_value = float(self.view.kategori_kar_widget.profit_value_input.text().replace(',', '.'))
            profit_type = self.view.kategori_kar_widget.profit_type_combo.currentText()
            db.update_category_profit(self.selected_category_id, profit_type, profit_value)
            app_signals.status_message_updated.emit(texts.SETTINGS_MSG_CATEGORY_PROFIT_SAVE_SUCCESS, 3000)
        except (ValueError, TypeError): ui_helpers.show_warning_message(self.view, texts.SETTINGS_MSG_INVALID_PROFIT_VALUE, texts.MSG_INVALID_INPUT)
        
    def add_vergi_orani(self):
        ad = self.view.vergi_ad_input.text().strip()
        oran_str = self.view.vergi_oran_input.text().strip().replace(',', '.')
        if not ad or not oran_str: return ui_helpers.show_warning_message(self.view, "Lütfen Vergi Adı ve Oranı alanlarını doldurun.", texts.MSG_MISSING_INFO)
        try:
            oran = float(oran_str)
            success, message = db.add_vergi_orani(ad, oran)
            if success:
                ui_helpers.show_info_message(self.view, message); self.load_product_management_data(); self.view.vergi_ad_input.clear(); self.view.vergi_oran_input.clear()
            else: ui_helpers.show_critical_message(self.view, message)
        except ValueError: ui_helpers.show_warning_message(self.view, "Lütfen Oran alanına geçerli bir sayı girin.", texts.MSG_INVALID_INPUT)
        
    def delete_vergi_orani(self):
        selected_indexes = self.view.vergi_table.selectionModel().selectedRows()
        if not selected_indexes: return ui_helpers.show_warning_message(self.view, "Lütfen silmek için tablodan bir vergi oranı seçin.")
        vergi_id = self.vergi_table_model.get_item_id(selected_indexes[0])
        vergi_adi = self.vergi_table_model.data(selected_indexes[0], Qt.DisplayRole)
        if ui_helpers.ask_confirmation(self.view, "Vergi Oranını Sil", f"'{vergi_adi}' adlı vergi oranını silmek istediğinizden emin misiniz?", "Bu vergi oranı herhangi bir üründe kullanılıyorsa silinemez."):
            success, message = db.delete_vergi_orani(vergi_id)
            if success: ui_helpers.show_info_message(self.view, message); self.load_product_management_data()
            else: ui_helpers.show_critical_message(self.view, message)
            
    def load_users_list(self): self.user_table_model.update_data(db.get_all_users())
    
    def open_add_user_dialog(self):
        roles = db.get_all_roller()
        if not roles: return ui_helpers.show_warning_message(self.view, texts.SETTINGS_MSG_NO_ROLE_DEFINED)
        dialog = UserDialog(self.view, roles=roles)
        if dialog.exec():
            data = dialog.get_data()
            if data == "short": return ui_helpers.show_warning_message(dialog, texts.SETTINGS_MSG_USERNAME_PASSWORD_SHORT, texts.MSG_INVALID_INPUT)
            if data == "mismatch": return ui_helpers.show_warning_message(dialog, texts.SETTINGS_MSG_PASSWORDS_DONT_MATCH, texts.MSG_INVALID_INPUT)
            if data:
                success, message = db.add_user(data['username'], data['password'], data['role_id'])
                if success: ui_helpers.show_info_message(dialog, message); self.load_users_list()
                else: ui_helpers.show_critical_message(dialog, message)
                
    def delete_selected_user(self):
        selected_indexes = self.view.users_table.selectionModel().selectedRows()
        if not selected_indexes: return ui_helpers.show_warning_message(self.view, texts.MSG_SELECT_TO_DELETE)
        user_id = self.user_table_model.get_item_id(selected_indexes[0])
        if user_id == session.get_user_data().get('id'): return ui_helpers.show_warning_message(self.view, texts.SETTINGS_MSG_CANNOT_DELETE_SELF, texts.MSG_ACTION_PREVENTED)
        user_row = db.get_user_by_id(user_id)
        if user_row and db.is_last_admin_role(user_row['rol_id']): return ui_helpers.show_warning_message(self.view, texts.SETTINGS_MSG_CANNOT_DELETE_LAST_ADMIN, texts.MSG_ACTION_PREVENTED)
        username = self.user_table_model.table_data[selected_indexes[0].row()]['kullanici_adi']
        if ui_helpers.ask_confirmation(self.view, texts.TITLE_CONFIRM_DELETE, texts.USER_DELETE_TEXT.format(username=username)):
            db.delete_user(user_id)
            ui_helpers.show_info_message(self.view, texts.SETTINGS_MSG_DELETE_USER_SUCCESS.format(username=username)); self.load_users_list()
            
    def change_selected_user_password(self):
        selected_indexes = self.view.users_table.selectionModel().selectedRows()
        if not selected_indexes: return ui_helpers.show_warning_message(self.view, "Lütfen şifresini değiştirmek için bir kullanıcı seçin.")
        user_id = self.user_table_model.get_item_id(selected_indexes[0])
        username = self.user_table_model.table_data[selected_indexes[0].row()]['kullanici_adi']
        new_password, ok = QInputDialog.getText(self.view, texts.SETTINGS_MSG_CHANGE_PASSWORD_TITLE, texts.SETTINGS_MSG_CHANGE_PASSWORD_TEXT.format(username=username), QLineEdit.Password)
        if ok and new_password:
            if len(new_password) < 4: return ui_helpers.show_warning_message(self.view, texts.SETTINGS_MSG_PASSWORD_TOO_SHORT, texts.MSG_INVALID_INPUT)
            db.update_user_password(user_id, new_password)
            ui_helpers.show_info_message(self.view, texts.SETTINGS_MSG_PASSWORD_UPDATE_SUCCESS.format(username=username))
            
    def load_roles_and_permissions_tab(self):
        self.view.roles_widget.populate_list(db.get_all_roller())
        self.selected_role_id = None
        self._clear_permissions_layout()
        self.view.permissions_card.setEnabled(False)
        self.view.roles_widget.delete_button.setEnabled(False)
        
    def add_rol(self):
        role_name, ok = QInputDialog.getText(self.view, texts.SETTINGS_MSG_ADD_ROLE_TITLE, texts.SETTINGS_MSG_ADD_ROLE_TEXT)
        if ok and role_name:
            success, message = db.add_rol(role_name)
            if success: self.load_roles_and_permissions_tab()
            else: ui_helpers.show_critical_message(self.view, message)
            
    def delete_rol(self):
        if not self.selected_role_id: return ui_helpers.show_warning_message(self.view, "Lütfen silmek için bir rol seçin.")
        rol_adi = self.view.roles_widget.list_widget.currentItem().text()
        if rol_adi.lower() in ['yönetici', 'standart kullanıcı']: return ui_helpers.show_warning_message(self.view, texts.SETTINGS_MSG_CANNOT_DELETE_DEFAULT_ROLE, texts.MSG_ACTION_PREVENTED)
        if ui_helpers.ask_confirmation(self.view, "Rolü Sil", texts.SETTINGS_MSG_CONFIRM_DELETE_ROLE_TEXT.format(role_name=rol_adi)):
            db.delete_rol(self.selected_role_id)
            self.load_roles_and_permissions_tab()
            
    def save_application_settings(self):
        self.save_financial_settings()
        self.save_communication_settings()
        self._save_auto_backup_setting()
        ui_helpers.show_info_message(self.view, "Tüm uygulama ayarları başarıyla kaydedildi.")

    def load_financial_settings(self, settings):
        self.view.kar_yontemi_combo.setCurrentText(settings.get('kar_yontemi', 'Yüzdesel Kâr (%)'))
        self.view.kar_degeri_input.setText(settings.get('kar_degeri', '50'))
        self.view.kdv_orani_input.setText(settings.get('kdv_orani', '20'))
        self.view.kk_komisyonu_input.setText(settings.get('kk_komisyonu', '2.5'))
        usd_rate = settings.get('usd_tl_kuru', '0')
        eur_rate = settings.get('eur_tl_kuru', '0')
        update_time = settings.get('kur_guncelleme_tarihi', 'Bilinmiyor')
        self.view.usd_rate_label.setText(f"<b>{float(usd_rate.replace(',', '.')):.4f} TL</b>" if float(usd_rate.replace(',', '.')) > 0 else "Alınamadı")
        self.view.eur_rate_label.setText(f"<b>{float(eur_rate.replace(',', '.')):.4f} TL</b>" if float(eur_rate.replace(',', '.')) > 0 else "Alınamadı")
        self.view.rate_update_time_label.setText(f"<i>{update_time}</i>")
        
    def save_financial_settings(self):
        db.save_setting('kar_yontemi', self.view.kar_yontemi_combo.currentText())
        db.save_setting('kar_degeri', self.view.kar_degeri_input.text())
        db.save_setting('kdv_orani', self.view.kdv_orani_input.text())
        db.save_setting('kk_komisyonu', self.view.kk_komisyonu_input.text())
        
    def trigger_live_rate_update(self):
        self.view.manual_rate_update_button.setText("Güncelleniyor...")
        self.view.manual_rate_update_button.setEnabled(False)
        app_signals.status_message_updated.emit("TCMB'den kurlar çekiliyor...", 0)
        worker = BackgroundWorker(currency_service.get_all_rates)
        worker.signals.result.connect(self._on_live_rate_update_finished)
        worker.signals.error.connect(self._on_live_rate_update_error)
        worker.signals.finished.connect(lambda: (self.view.manual_rate_update_button.setText("Kurları Şimdi Güncelle"), self.view.manual_rate_update_button.setEnabled(True), self.active_workers.remove(worker)))
        self.active_workers.append(worker)
        self.thread_pool.start(worker)
        
    def _on_live_rate_update_finished(self, rates):
        if rates:
            now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
            db.save_setting('usd_tl_kuru', rates.get('USD', '0')); db.save_setting('eur_tl_kuru', rates.get('EUR', '0')); db.save_setting('kur_guncelleme_tarihi', f"{now_str} (Manuel)")
            app_signals.status_message_updated.emit("Döviz kurları başarıyla güncellendi.", 4000)
            self.load_financial_settings(db.get_all_settings())
        else:
            ui_helpers.show_warning_message(self.view, texts.SETTINGS_MSG_RATES_UPDATE_ERROR)
            app_signals.status_message_updated.emit("Kurlar güncellenemedi.", 4000)
            
    def _on_live_rate_update_error(self, error_tuple):
        ui_helpers.show_critical_message(self.view, texts.SETTINGS_MSG_RATES_UNEXPECTED_ERROR.format(error=error_tuple[1]))
        app_signals.status_message_updated.emit("Kur güncelleme hatası!", 5000)
        
    def load_communication_settings(self, settings):
        self.view.sms_username_input.setText(settings.get('sms_username', ''))
        self.view.sms_password_input.setText(settings.get('sms_password', ''))
        self.view.sms_originator_input.setText(settings.get('sms_originator', ''))
        self.view.smtp_host_input.setText(settings.get('smtp_host', ''))
        self.view.smtp_port_input.setText(settings.get('smtp_port', '587'))
        self.view.smtp_username_input.setText(settings.get('smtp_username', ''))
        self.view.smtp_password_input.setText(settings.get('smtp_password', ''))
        
    def save_communication_settings(self):
        db.save_setting('sms_username', self.view.sms_username_input.text()); db.save_setting('sms_password', self.view.sms_password_input.text()); db.save_setting('sms_originator', self.view.sms_originator_input.text())
        db.save_setting('smtp_host', self.view.smtp_host_input.text()); db.save_setting('smtp_port', self.view.smtp_port_input.text()); db.save_setting('smtp_username', self.view.smtp_username_input.text()); db.save_setting('smtp_password', self.view.smtp_password_input.text())
        
    def _test_sms_settings(self):
        settings = {'sms_username': self.view.sms_username_input.text(),'sms_password': self.view.sms_password_input.text(),'sms_originator': self.view.sms_originator_input.text()}
        if not all(settings.values()): return ui_helpers.show_warning_message(self.view, texts.SETTINGS_MSG_INPUT_REQUIRED, texts.MSG_MISSING_INFO)
        phone_number, ok = QInputDialog.getText(self.view, texts.SETTINGS_MSG_TEST_SMS_PROMPT_TITLE, texts.SETTINGS_MSG_TEST_SMS_PROMPT_TEXT)
        if ok and phone_number:
            worker = BackgroundWorker(sms_service.send_bulk_sms, settings, [phone_number], "Bu bir test mesajıdır.")
            worker.signals.result.connect(self._on_test_finished)
            worker.signals.error.connect(self._on_test_error)
            self.thread_pool.start(worker)
            app_signals.status_message_updated.emit("Test SMS'i gönderiliyor...", 0)
            
    def _test_email_settings(self):
        settings = {'smtp_host': self.view.smtp_host_input.text(),'smtp_port': self.view.smtp_port_input.text(),'smtp_username': self.view.smtp_username_input.text(),'smtp_password': self.view.smtp_password_input.text()}
        if not all(settings.values()): return ui_helpers.show_warning_message(self.view, texts.SETTINGS_MSG_INPUT_REQUIRED, texts.MSG_MISSING_INFO)
        email, ok = QInputDialog.getText(self.view, texts.SETTINGS_MSG_TEST_EMAIL_PROMPT_TITLE, texts.SETTINGS_MSG_TEST_EMAIL_PROMPT_TEXT)
        if ok and email:
            worker = BackgroundWorker(email_service.send_bulk_email, settings, [email], "Test E-postası", "Bu bir test e-postasıdır.")
            worker.signals.result.connect(self._on_test_finished)
            worker.signals.error.connect(self._on_test_error)
            self.thread_pool.start(worker)
            app_signals.status_message_updated.emit("Test E-postası gönderiliyor...", 0)
            
    def _on_test_finished(self, result):
        success, message = result
        if success: ui_helpers.show_info_message(self.view, message, texts.SETTINGS_MSG_TEST_SUCCESS)
        else: ui_helpers.show_warning_message(self.view, message, texts.SETTINGS_MSG_TEST_FAIL)
        app_signals.status_message_updated.emit(texts.SETTINGS_MSG_TEST_COMPLETE, 3000)
        
    def _on_test_error(self, error_tuple):
        ui_helpers.show_critical_message(self.view, texts.SETTINGS_MSG_TEST_UNEXPECTED_ERROR.format(error=error_tuple[1]))
        app_signals.status_message_updated.emit("Test hatası!", 4000)
        
    def load_backup_settings(self):
        self.view.auto_backup_checkbox.setChecked(db.get_setting('auto_backup_on_exit', 'False') == 'True')
        
    def _save_auto_backup_setting(self):
        is_checked = self.view.auto_backup_checkbox.isChecked()
        db.save_setting('auto_backup_on_exit', str(is_checked))
        
    def _backup_database(self):
        default_filename = os.path.join(os.path.expanduser("~"), f"ticari_program_yedek_{datetime.now().strftime('%Y-%m-%d')}.db")
        save_path, _ = QFileDialog.getSaveFileName(self.view, "Veritabanı Yedeğini Kaydet", default_filename, "SQLite Veritabanı (*.db)")
        if save_path:
            try:
                shutil.copy(db.DATABASE_PATH, save_path)
                ui_helpers.show_info_message(self.view, texts.SETTINGS_MSG_BACKUP_SUCCESS.format(path=save_path))
            except Exception as e:
                logging.error(f"Manuel yedekleme hatası: {e}", exc_info=True)
                ui_helpers.show_critical_message(self.view, texts.SETTINGS_MSG_BACKUP_ERROR.format(error=e))
                
    def _restore_database(self):
        dialog = ConfirmationDialog(self.view, texts.SETTINGS_MSG_RESTORE_CONFIRM_TITLE, texts.SETTINGS_MSG_RESTORE_CONFIRM_TEXT + "\n\n" + texts.SETTINGS_MSG_RESTORE_CONFIRM_INFO, "GERİ YÜKLE", texts.SETTINGS_MSG_RESTORE_CONFIRM_BTN)
        if dialog.exec():
            open_path, _ = QFileDialog.getOpenFileName(self.view, texts.SETTINGS_MSG_RESTORE_SELECT_FILE, os.path.expanduser("~"), "SQLite Veritabanı (*.db)")
            if open_path:
                try:
                    shutil.copy(open_path, db.DATABASE_PATH)
                    ui_helpers.show_info_message(self.view, texts.SETTINGS_MSG_RESTORE_SUCCESS)
                    QApplication.instance().quit()
                except Exception as e:
                    logging.error(f"Geri yükleme hatası: {e}", exc_info=True)
                    ui_helpers.show_critical_message(self.view, texts.SETTINGS_MSG_RESTORE_ERROR.format(error=e))