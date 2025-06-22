# dosya: views/settings_view.py

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QLineEdit,
    QLabel, QListWidgetItem, QFormLayout, QPushButton,
    QComboBox, QTextEdit, QTableView, QHeaderView,
    QStackedWidget, QCheckBox, QScrollArea, QTabWidget, QGridLayout
)
from PySide6.QtGui import QDoubleValidator, QIntValidator
from PySide6.QtCore import Qt, QSize
import qtawesome as qta

from utils import ui_texts as texts
from utils.themed_widgets import (
    CardWidget, PrimaryButton, DangerButton, OutlineButton, HubCardWidget, SuccessButton
)
from utils.custom_widgets import PageHeader

class ManagementWidget(QWidget):
    def __init__(self, title, placeholder_text, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        card = CardWidget(title)
        group_layout = card.layout() 
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(lambda: self.edit_button.click())
        group_layout.addWidget(self.list_widget)
        input_layout = QHBoxLayout()
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText(placeholder_text)
        self.add_button = PrimaryButton(texts.BTN_ADD)
        input_layout.addWidget(self.input_line, 1)
        input_layout.addWidget(self.add_button)
        group_layout.addLayout(input_layout)
        actions_layout = QHBoxLayout()
        self.edit_button = OutlineButton("Seçileni Düzenle")
        self.delete_button = DangerButton(texts.BTN_DELETE_SELECTED)
        actions_layout.addStretch()
        actions_layout.addWidget(self.edit_button)
        actions_layout.addWidget(self.delete_button)
        group_layout.addLayout(actions_layout)
        layout.addWidget(card)
        self.input_line.returnPressed.connect(self.add_button.click)

    def populate_list(self, items, key_for_text='ad'):
        self.list_widget.clear()
        for item in items:
            list_item = QListWidgetItem(item[key_for_text])
            list_item.setData(Qt.UserRole, item['id'])
            self.list_widget.addItem(list_item)

class CategoryProfitWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(350)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        card = CardWidget("Seçili Kategori Kâr Ayarları")
        group_layout = QFormLayout()
        card.layout().addLayout(group_layout)
        self.category_name_label = QLabel("<i>Lütfen bir kategori seçin</i>")
        self.profit_type_combo = QComboBox()
        self.profit_type_combo.addItems(["Yüzdesel Kâr (%)", "Sabit Tutar (TL)"])
        self.profit_value_input = QLineEdit()
        self.profit_value_input.setValidator(QDoubleValidator(0, 99999, 2))
        self.save_profit_button = PrimaryButton("Kâr Ayarını Kaydet")
        group_layout.addRow("<b>Kategori:</b>", self.category_name_label)
        group_layout.addRow("Kâr Tipi:", self.profit_type_combo)
        group_layout.addRow("Kâr Değeri:", self.profit_value_input)
        group_layout.addWidget(self.save_profit_button)
        layout.addWidget(card)
        self.setVisible(False)

class SettingsView(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        
        self._create_hub_page()
        self._create_detail_pages()

    def _create_hub_page(self):
        hub_page = QWidget()
        main_layout = QVBoxLayout(hub_page)
        main_layout.setContentsMargins(40, 25, 40, 25)
        main_layout.setSpacing(25)
        main_layout.setAlignment(Qt.AlignTop)

        self.header = PageHeader("Ayarlar", "cogs")
        main_layout.addWidget(self.header)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(30)
        
        self.card_user_company = HubCardWidget(
            "user-cog", "Firma ve Kullanıcılar", "Firma profili, kullanıcı hesapları, roller ve yetkiler."
        )
        self.card_product = HubCardWidget(
            "box-open", "Ürün Yönetimi", "Ürün kategorileri, varyant tipleri ve vergi oranları."
        )
        self.card_customer = HubCardWidget(
            "users", "Müşteri Yönetimi", "Müşteri grupları ve ilgili diğer ayarlar."
        )
        self.card_application = HubCardWidget(
            "cog", "Uygulama Ayarları", "Finansal, iletişim ve veritabanı yedekleme ayarları."
        )

        grid_layout.addWidget(self.card_user_company, 0, 0)
        grid_layout.addWidget(self.card_product, 0, 1)
        grid_layout.addWidget(self.card_customer, 1, 0)
        grid_layout.addWidget(self.card_application, 1, 1)
        
        main_layout.addLayout(grid_layout)
        main_layout.addStretch()
        
        self.stacked_widget.addWidget(hub_page)
    
    def _create_detail_pages(self):
        user_company_page = self._create_user_company_page()
        self.stacked_widget.addWidget(user_company_page)

        product_management_page = self._create_product_management_page()
        self.stacked_widget.addWidget(product_management_page)

        customer_management_page = self._create_customer_management_page()
        self.stacked_widget.addWidget(customer_management_page)

        application_settings_page = self._create_application_settings_page()
        self.stacked_widget.addWidget(application_settings_page)

    def _create_page_header_with_back_button(self, title: str, icon: str) -> tuple[QWidget, QPushButton]:
        header_container = QWidget()
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(0,0,0,0)
        
        back_button = PrimaryButton("", "fa5s.arrow-left")
        back_button.setFixedWidth(50)
        
        page_header = PageHeader(title, icon)
        header_layout.addWidget(back_button)
        header_layout.addWidget(page_header)
        
        return header_container, back_button

    def _create_user_company_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignTop)

        header_widget, self.back_to_hub_button = self._create_page_header_with_back_button("Firma ve Kullanıcı Ayarları", "user-cog")
        layout.addWidget(header_widget)

        self.user_company_tabs = QTabWidget()
        self.profile_content = self._create_profile_page_content()
        self.users_content = self._create_users_page_content()
        self.roles_content = self._create_roles_page_content()

        self.user_company_tabs.addTab(self.profile_content, qta.icon('fa5s.building'), "Firma Profili")
        self.user_company_tabs.addTab(self.users_content, qta.icon('fa5s.users-cog'), "Kullanıcı Yönetimi")
        self.user_company_tabs.addTab(self.roles_content, qta.icon('fa5s.user-shield'), "Roller ve Yetkiler")
        
        layout.addWidget(self.user_company_tabs, 1)
        return page
    
    def _create_product_management_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignTop)

        header_widget, self.back_to_hub_button_2 = self._create_page_header_with_back_button("Ürün Yönetimi", "box-open")
        layout.addWidget(header_widget)

        self.product_management_tabs = QTabWidget()
        kategori_yonetim_sayfasi = self._create_category_management_tab()
        self.varyant_tipi_widget = ManagementWidget("Varyant Tipleri", "Yeni varyant tipi (Eko, Lüx vb.)")
        self.vergi_page = self._create_tax_rate_management_page()
        
        self.product_management_tabs.addTab(kategori_yonetim_sayfasi, qta.icon('fa5s.sitemap'), "Ürün Kategorileri")
        self.product_management_tabs.addTab(self.varyant_tipi_widget, qta.icon('fa5s.tags'), "Varyant Tipleri")
        self.product_management_tabs.addTab(self.vergi_page, qta.icon('fa5s.percentage'), "Vergi Oranları")

        layout.addWidget(self.product_management_tabs, 1)
        return page

    def _create_customer_management_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignTop)

        header_widget, self.back_to_hub_button_3 = self._create_page_header_with_back_button("Müşteri Yönetimi", "users")
        layout.addWidget(header_widget)
        
        self.musteri_grup_widget = ManagementWidget("Müşteri Grupları", "Yeni grup adı (örn: Bayi, VIP)")
        layout.addWidget(self.musteri_grup_widget)
        
        return page
    
    def _create_application_settings_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignTop)

        header_widget, self.back_to_hub_button_4 = self._create_page_header_with_back_button("Uygulama Ayarları", "cog")
        layout.addWidget(header_widget)

        self.application_settings_tabs = QTabWidget()
        
        financial_tab = self._create_financial_settings_tab()
        communication_tab = self._create_communication_settings_tab()
        database_tab = self._create_database_settings_tab()

        self.application_settings_tabs.addTab(financial_tab, qta.icon('fa5s.lira-sign'), "Finansal")
        self.application_settings_tabs.addTab(communication_tab, qta.icon('fa5s.paper-plane'), "İletişim")
        self.application_settings_tabs.addTab(database_tab, qta.icon('fa5s.database'), "Veritabanı")

        self.save_app_settings_button = SuccessButton("Tüm Uygulama Ayarlarını Kaydet", "fa5s.save")

        layout.addWidget(self.application_settings_tabs)
        layout.addWidget(self.save_app_settings_button, 0, Qt.AlignRight)

        return page

    def _create_financial_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 20, 10, 10)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignTop)
        
        profit_card = CardWidget("Genel Fiyatlandırma Ayarları")
        profit_layout = QFormLayout()
        profit_card.layout().addLayout(profit_layout)

        self.kar_yontemi_combo = QComboBox()
        self.kar_yontemi_combo.addItems(["Yüzdesel Kâr (%)", "Sabit Tutar (TL)"])
        self.kar_degeri_input = QLineEdit()
        self.kar_degeri_input.setValidator(QDoubleValidator(0, 99999, 2))
        self.kdv_orani_input = QLineEdit()
        self.kdv_orani_input.setValidator(QDoubleValidator(0, 100, 2))
        self.kk_komisyonu_input = QLineEdit()
        self.kk_komisyonu_input.setValidator(QDoubleValidator(0, 100, 2))
        
        profit_layout.addRow("Varsayılan Kâr Yöntemi:", self.kar_yontemi_combo)
        profit_layout.addRow("Varsayılan Kâr Değeri:", self.kar_degeri_input)
        profit_layout.addRow("Genel KDV Oranı (%):", self.kdv_orani_input)
        profit_layout.addRow("Genel Kredi Kartı Komisyonu (%):", self.kk_komisyonu_input)
        
        currency_card = CardWidget("Döviz Kuru Bilgileri")
        currency_layout = QFormLayout()
        currency_card.layout().addLayout(currency_layout)

        self.usd_rate_label = QLabel("<i>Henüz güncellenmedi</i>")
        self.eur_rate_label = QLabel("<i>Henüz güncellenmedi</i>")
        self.rate_update_time_label = QLabel("<i>-</i>")
        self.manual_rate_update_button = OutlineButton("Kurları Şimdi Güncelle")
        currency_layout.addRow("<b>USD Kuru:</b>", self.usd_rate_label)
        currency_layout.addRow("<b>EUR Kuru:</b>", self.eur_rate_label)
        currency_layout.addRow("Son Güncelleme:", self.rate_update_time_label)
        currency_layout.addWidget(self.manual_rate_update_button)

        layout.addWidget(profit_card)
        layout.addWidget(currency_card)
        layout.addStretch()
        return tab

    def _create_communication_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 20, 10, 10)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignTop)

        sms_card = CardWidget("SMS Gönderim Ayarları (MutluCell)")
        sms_layout = QFormLayout()
        sms_card.layout().addLayout(sms_layout)

        self.sms_username_input = QLineEdit()
        self.sms_password_input = QLineEdit()
        self.sms_password_input.setEchoMode(QLineEdit.Password)
        self.sms_originator_input = QLineEdit()
        self.sms_originator_input.setPlaceholderText("Marka Adınız (örn: MyBusiness)")
        self.test_sms_button = OutlineButton("SMS Ayarlarını Test Et")
        sms_layout.addRow("Kullanıcı Adı:", self.sms_username_input)
        sms_layout.addRow("Şifre:", self.sms_password_input)
        sms_layout.addRow("Gönderici Başlığı:", self.sms_originator_input)
        sms_layout.addWidget(self.test_sms_button)

        email_card = CardWidget("E-Posta Gönderim Ayarları (SMTP)")
        email_layout = QFormLayout()
        email_card.layout().addLayout(email_layout)

        self.smtp_host_input = QLineEdit()
        self.smtp_port_input = QLineEdit()
        self.smtp_port_input.setValidator(QIntValidator(1, 65535))
        self.smtp_username_input = QLineEdit()
        self.smtp_password_input = QLineEdit()
        self.smtp_password_input.setEchoMode(QLineEdit.Password)
        self.test_email_button = OutlineButton("E-posta Ayarlarını Test Et")
        email_layout.addRow("SMTP Host:", self.smtp_host_input)
        email_layout.addRow("SMTP Port:", self.smtp_port_input)
        email_layout.addRow("SMTP Kullanıcı Adı:", self.smtp_username_input)
        email_layout.addRow("SMTP Şifre:", self.smtp_password_input)
        email_layout.addWidget(self.test_email_button)
        
        layout.addWidget(sms_card)
        layout.addWidget(email_card)
        layout.addStretch()
        return tab
        
    def _create_database_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 20, 10, 10)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignTop)

        backup_card = CardWidget("Veritabanı Yedekleme")
        backup_layout = backup_card.layout()
        backup_label = QLabel("Olası veri kayıplarına karşı programın veritabanını düzenli olarak yedeklemeniz önemlidir.")
        backup_label.setWordWrap(True)
        self.auto_backup_checkbox = QCheckBox("Programdan çıkarken veritabanını otomatik olarak yedekle")
        auto_backup_info = QLabel("<i>(Yedekler, programın ana klasöründeki 'backups' dizinine kaydedilir.)</i>")
        auto_backup_info.setObjectName("SubtleInfoLabel")
        self.backup_button = OutlineButton("Şimdi Manuel Yedekle", icon_name='fa5s.download')
        backup_layout.addWidget(backup_label)
        backup_layout.addSpacing(10)
        backup_layout.addWidget(self.auto_backup_checkbox)
        backup_layout.addWidget(auto_backup_info)
        backup_layout.addSpacing(15)
        backup_layout.addWidget(self.backup_button)
        
        restore_card = CardWidget("Yedekten Geri Yükleme")
        restore_layout = restore_card.layout()
        restore_warning_label = QLabel("<b>DİKKAT:</b> Bu işlem mevcut tüm verilerinizi, seçeceğiniz yedek dosyasıyla tamamen değiştirecektir. Bu işlem geri alınamaz. Geri yükleme sonrası program yeniden başlatılacaktır.")
        restore_warning_label.setObjectName("WarningTextLabel")
        restore_warning_label.setWordWrap(True)
        self.restore_button = DangerButton("Yedekten Geri Yükle", icon_name='fa5s.upload')
        restore_layout.addWidget(restore_warning_label)
        restore_layout.addSpacing(10)
        restore_layout.addWidget(self.restore_button)

        layout.addWidget(backup_card)
        layout.addWidget(restore_card)
        layout.addStretch()
        return tab

    def _create_category_management_tab(self):
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(10, 20, 10, 10)
        layout.setSpacing(20)
        self.kategori_widget = ManagementWidget("Ürün Kategorileri", "Yeni kategori adı...")
        self.kategori_kar_widget = CategoryProfitWidget()
        layout.addWidget(self.kategori_widget, 1)
        layout.addWidget(self.kategori_kar_widget, 1)
        return page

    def _create_tax_rate_management_page(self) -> QWidget:
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setSpacing(20)
        layout.setContentsMargins(10, 20, 10, 10)
        
        vergi_list_card = CardWidget("Tanımlı Vergi Oranları")
        self.vergi_table = QTableView()
        self.vergi_table.setSelectionBehavior(QTableView.SelectRows)
        self.vergi_table.setEditTriggers(QTableView.NoEditTriggers)
        vergi_list_card.layout().addWidget(self.vergi_table)

        vergi_actions_card = CardWidget("Yeni Vergi Ekle / Seçileni Sil")
        vergi_actions_card.setFixedWidth(300)
        vergi_actions_layout = QFormLayout()
        vergi_actions_card.layout().addLayout(vergi_actions_layout)

        self.vergi_ad_input = QLineEdit()
        self.vergi_ad_input.setPlaceholderText("Örn: Genel KDV")
        self.vergi_oran_input = QLineEdit()
        self.vergi_oran_input.setPlaceholderText("Örn: 20")
        self.vergi_oran_input.setValidator(QDoubleValidator(0, 100, 2))
        
        self.add_vergi_button = PrimaryButton("Yeni Vergi Ekle")
        self.delete_vergi_button = DangerButton("Seçili Vergiyi Sil")
        
        vergi_actions_layout.addRow("Vergi Adı:", self.vergi_ad_input)
        vergi_actions_layout.addRow("Oran (%):", self.vergi_oran_input)
        vergi_actions_layout.addWidget(self.add_vergi_button)
        vergi_actions_layout.addWidget(self.delete_vergi_button)
        
        layout.addWidget(vergi_list_card, 1)
        layout.addWidget(vergi_actions_card)
        return page

    def _create_profile_page_content(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 20, 10, 10)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignTop)
        
        profile_card = CardWidget("Firma ve Fatura Bilgileri")
        profile_layout = QHBoxLayout()
        profile_card.layout().addLayout(profile_layout)

        profile_form_widget = QWidget()
        profile_form = QFormLayout(profile_form_widget)
        profile_form.setSpacing(15)

        self.company_name_input = QLineEdit()
        self.company_address_input = QTextEdit()
        self.company_phone_input = QLineEdit()
        self.company_email_input = QLineEdit()
        self.company_website_input = QLineEdit()
        self.company_tax_office_input = QLineEdit()
        self.company_tax_id_input = QLineEdit()
        
        profile_form.addRow("Firma Unvanı:", self.company_name_input)
        profile_form.addRow("Adres:", self.company_address_input)
        profile_form.addRow("Telefon:", self.company_phone_input)
        profile_form.addRow("E-posta:", self.company_email_input)
        profile_form.addRow("Web Sitesi:", self.company_website_input)
        profile_form.addRow("Vergi Dairesi:", self.company_tax_office_input)
        profile_form.addRow("Vergi/TC Kimlik No:", self.company_tax_id_input)

        logo_card = CardWidget("Firma Logosu")
        logo_layout = logo_card.layout()
        logo_layout.setAlignment(Qt.AlignCenter)
        self.logo_preview_label = QLabel("Logo Yüklü Değil")
        self.logo_preview_label.setFixedSize(180, 180)
        self.logo_preview_label.setAlignment(Qt.AlignCenter)
        self.logo_preview_label.setObjectName("ImagePreview")
        self.logo_upload_button = OutlineButton("Logo Yükle/Değiştir")
        self.logo_remove_button = OutlineButton("Logoyu Kaldır")
        logo_layout.addWidget(self.logo_preview_label)
        logo_layout.addWidget(self.logo_upload_button)
        logo_layout.addWidget(self.logo_remove_button)

        profile_layout.addWidget(profile_form_widget, 2)
        profile_layout.addWidget(logo_card, 1)
        
        self.save_profile_button = PrimaryButton("Firma Bilgilerini Kaydet")
        layout.addWidget(profile_card)
        layout.addWidget(self.save_profile_button, 0, Qt.AlignRight)
        return page

    def _create_users_page_content(self) -> QWidget:
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(10, 20, 10, 10)
        layout.setSpacing(20)
        
        user_list_card = CardWidget(texts.SETTINGS_USERS_GROUP_TITLE)
        self.users_table = QTableView()
        self.users_table.setSelectionBehavior(QTableView.SelectRows)
        self.users_table.setEditTriggers(QTableView.NoEditTriggers)
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        user_list_card.layout().addWidget(self.users_table)

        user_actions_card = CardWidget(texts.SETTINGS_ACTIONS_GROUP_TITLE)
        user_actions_card.setFixedWidth(300)
        actions_layout = QVBoxLayout()
        user_actions_card.layout().addLayout(actions_layout)

        actions_layout.setAlignment(Qt.AlignTop)
        self.add_user_button = PrimaryButton(texts.SETTINGS_BTN_ADD_USER, "fa5s.user-plus")
        self.delete_user_button = DangerButton(texts.SETTINGS_BTN_DELETE_USER, "fa5s.user-minus")
        self.change_password_button = OutlineButton(texts.SETTINGS_BTN_CHANGE_PASS, "fa5s.key")
        actions_layout.addWidget(self.add_user_button)
        actions_layout.addWidget(self.delete_user_button)
        actions_layout.addWidget(self.change_password_button)
        
        layout.addWidget(user_list_card, 1)
        layout.addWidget(user_actions_card)
        return page

    def _create_roles_page_content(self) -> QWidget:
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(10, 20, 10, 10)
        layout.setSpacing(20)

        self.roles_widget = ManagementWidget("Roller", "Yeni rol adı...")
        self.permissions_card = CardWidget("Seçili Rolün Yetkileri")
        permissions_main_layout = self.permissions_card.layout()
        
        self.permissions_scroll_area = QScrollArea()
        self.permissions_scroll_area.setWidgetResizable(True)
        self.permissions_scroll_area.setObjectName("PermissionsScrollArea")
        
        self.permissions_container = QWidget()
        self.permissions_layout = QVBoxLayout(self.permissions_container)
        self.permissions_layout.setAlignment(Qt.AlignTop)
        
        self.permissions_scroll_area.setWidget(self.permissions_container)
        permissions_main_layout.addWidget(self.permissions_scroll_area)
        
        self.save_permissions_button = PrimaryButton("Yetkileri Kaydet")
        permissions_main_layout.addWidget(self.save_permissions_button, 0, Qt.AlignRight)
        
        layout.addWidget(self.roles_widget, 1)
        layout.addWidget(self.permissions_card, 2)
        return page