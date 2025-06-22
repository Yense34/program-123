# dosya: views/product_dialog.py

import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QWidget, QListWidget, QListWidgetItem, QLabel, 
    QComboBox, QHBoxLayout, QAbstractItemView, QTabWidget
)
from PySide6.QtGui import QDoubleValidator, QIntValidator, QPixmap
from PySide6.QtCore import Qt, Signal

from utils.themed_widgets import (
    CardWidget, SuccessButton, NeutralButton, DangerButton, OutlineButton, PrimaryButton
)

class VariantTypeSelectionDialog(QDialog):
    def __init__(self, variant_types, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Eklenecek Varyant Tiplerini Seçin")
        self.setMinimumSize(350, 400)
        
        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        
        if variant_types:
            for v_type in variant_types:
                item = QListWidgetItem(v_type['ad'])
                item.setData(Qt.UserRole, v_type)
                self.list_widget.addItem(item)
        
        button_layout = QHBoxLayout()
        self.cancel_button = NeutralButton("İptal")
        self.add_button = SuccessButton("Seçilenleri Ekle")
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.add_button)

        layout.addWidget(QLabel("Lütfen bu ürüne eklemek istediğiniz varyantları seçin:"))
        layout.addWidget(self.list_widget)
        layout.addLayout(button_layout)

        self.add_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
    
    def get_selected_variants(self):
        return [item.data(Qt.UserRole) for item in self.list_widget.selectedItems()]


class VariantDetailEditDialog(QDialog):
    def __init__(self, variant_data, parent=None):
        super().__init__(parent)
        variant_name = variant_data.get('variant_name') or variant_data.get('ad').split(' - ')[-1].strip()
        self.setWindowTitle(f"Varyant Detaylarını Düzenle: {variant_name}")
        self.setModal(True)
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        self.price_input = QLineEdit(str(variant_data.get('alis_fiyati', variant_data.get('price', 0))))
        self.price_input.setValidator(QDoubleValidator(0, 999999.99, 2))
        self.stock_input = QLineEdit(str(variant_data.get('stok_miktari', variant_data.get('stock', 0))))
        self.stock_input.setValidator(QIntValidator(0, 999999))
        self.barcode_input = QLineEdit(variant_data.get('barkod', ''))

        form_layout.addRow("Alış Fiyatı:", self.price_input)
        form_layout.addRow("Stok Miktarı:", self.stock_input)
        form_layout.addRow("Barkod:", self.barcode_input)
        
        button_layout = QHBoxLayout()
        self.cancel_button = NeutralButton("İptal")
        self.ok_button = SuccessButton("Güncelle")
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)

        layout.addLayout(form_layout)
        layout.addLayout(button_layout)
        
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def get_data(self):
        return {
            "alis_fiyati": float(self.price_input.text().replace(',', '.') or 0),
            "stok_miktari": int(self.stock_input.text() or 0),
            "barkod": self.barcode_input.text().strip()
        }

class SingleProductDialog(QDialog):
    archive_requested = Signal(int)
    
    def __init__(self, parent=None, product_data=None, categories=None, tax_rates=None):
        super().__init__(parent)
        self.is_edit_mode = product_data is not None
        self.product_id_for_action = product_data.get('id') if self.is_edit_mode else None
        self.secilen_resim_yolu = None
        
        self._setup_ui(categories, tax_rates)
        self._layout_widgets()
        self._connect_signals()

        if self.is_edit_mode:
            self.populate_edit_form(product_data)
        
        self._update_save_button_state()
        self.ad_input.setFocus()
        self.tab_widget.setTabEnabled(1, False) 

    def _setup_ui(self, categories, tax_rates):
        title = "Ürün Düzenle" if self.is_edit_mode else "Yeni Ürün Ekle"
        self.setWindowTitle(title)
        self.setMinimumWidth(850)
        self.setModal(True)

        self.tab_widget = QTabWidget()
        self.bilgiler_tab = QWidget()
        self.varyant_tab = QWidget()

        self.ad_input = QLineEdit()
        self.stok_kodu_input = QLineEdit()
        self.barkod_input = QLineEdit()
        self.kategori_combo = QComboBox()
        self.kategori_combo.addItem("Kategori Seçiniz...", None)
        if categories: [self.kategori_combo.addItem(cat['ad'], cat['id']) for cat in categories]
        self.vergi_combo = QComboBox()
        self.vergi_combo.addItem("Varsayılan Vergi", None)
        if tax_rates: [self.vergi_combo.addItem(f"{tax['ad']} (%{tax['oran']})", tax['id']) for tax in tax_rates]
        self.para_birimi_combo = QComboBox()
        self.para_birimi_combo.addItems(["TL", "USD", "EUR"])
        self.alis_fiyati_input = QLineEdit("0")
        self.alis_fiyati_input.setValidator(QDoubleValidator(0, 9999999.99, 2))
        self.stok_miktari_input = QLineEdit("0")
        self.stok_miktari_input.setValidator(QIntValidator(0, 999999))
        self.min_stok_input = QLineEdit("0")
        self.min_stok_input.setValidator(QIntValidator(0, 999999))

        self.image_label = QLabel("Resim Yüklü Değil")
        self.image_label.setFixedSize(180, 180)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setObjectName("ImagePreview")
        
        # --- DÜZELTME BURADA YAPILDI: Buton renkleri değiştirildi ---
        self.resim_sec_button = SuccessButton("Resim Yükle")
        self.resim_kaldir_button = DangerButton("Resmi Kaldır")

        self.variants_list = QListWidget()
        self.variants_list.setAlternatingRowColors(True)
        self.add_variant_button = SuccessButton("+ Yeni Varyant Ekle")
        self.delete_variant_button = DangerButton("- Seçili Varyantı Sil")
        # --- DÜZELTME SONU ---

        self.cancel_button = NeutralButton("İptal")
        self.save_button = SuccessButton("Kaydet")
        if self.is_edit_mode:
            self.archive_button = DangerButton("Bu Ürünü Arşivle")

    def _create_bilgiler_tab(self):
        layout = QVBoxLayout(self.bilgiler_tab)
        layout.setContentsMargins(0, 15, 0, 0)
        
        info_card = CardWidget("Genel Ürün Bilgileri")
        form_layout = QFormLayout()
        info_card.layout().addLayout(form_layout)

        form_layout.addRow("Ürün Adı (*):", self.ad_input)
        form_layout.addRow("Stok Kodu (SKU) (*):", self.stok_kodu_input)
        form_layout.addRow("Barkod:", self.barkod_input)
        form_layout.addRow("Kategori:", self.kategori_combo)
        form_layout.addRow("Vergi Oranı:", self.vergi_combo)
        form_layout.addRow("Alış Para Birimi:", self.para_birimi_combo)
        form_layout.addRow("Alış Fiyatı:", self.alis_fiyati_input)
        form_layout.addRow("Stok Miktarı:", self.stok_miktari_input)
        form_layout.addRow("Min. Stok Seviyesi:", self.min_stok_input)
        
        layout.addWidget(info_card)
        layout.addStretch()

    def _create_varyant_tab(self):
        layout = QVBoxLayout(self.varyant_tab)
        layout.setContentsMargins(0, 15, 0, 0)
        layout.setSpacing(10)
        
        layout.addWidget(QLabel("Detayları düzenlemek için bir varyanta çift tıklayın."))
        layout.addWidget(self.variants_list)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.add_variant_button)
        buttons_layout.addWidget(self.delete_variant_button)
        layout.addLayout(buttons_layout)

    def _layout_widgets(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        self._create_bilgiler_tab()
        self._create_varyant_tab()
        self.tab_widget.addTab(self.bilgiler_tab, "Ürün Bilgileri")
        self.tab_widget.addTab(self.varyant_tab, "Varyant Yönetimi")

        content_layout.addWidget(self.tab_widget, 2)

        right_panel_container = QWidget()
        right_panel_layout = QVBoxLayout(right_panel_container)
        right_panel_layout.setContentsMargins(0,0,0,0)

        gorsel_group = CardWidget("Görsel")
        gorsel_layout = gorsel_group.layout()
        
        gorsel_layout.addWidget(self.image_label, 0, Qt.AlignCenter)
        
        image_buttons_layout = QHBoxLayout()
        image_buttons_layout.addStretch()
        image_buttons_layout.addWidget(self.resim_sec_button)
        image_buttons_layout.addWidget(self.resim_kaldir_button)
        image_buttons_layout.addStretch()
        gorsel_layout.addLayout(image_buttons_layout)
        
        right_panel_layout.addStretch()
        right_panel_layout.addWidget(gorsel_group)
        right_panel_layout.addStretch()
        
        content_layout.addWidget(right_panel_container, 1)

        main_layout.addLayout(content_layout)

        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 15, 0, 0)
        if self.is_edit_mode:
            button_layout.addWidget(self.archive_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        main_layout.addWidget(button_container)

    def _connect_signals(self):
        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        if self.is_edit_mode:
            self.archive_button.clicked.connect(self.on_archive_requested)
        self.ad_input.textChanged.connect(self._update_save_button_state)
        self.stok_kodu_input.textChanged.connect(self._update_save_button_state)

    def _update_save_button_state(self):
        is_valid = bool(self.ad_input.text().strip() and self.stok_kodu_input.text().strip())
        self.save_button.setEnabled(is_valid)

    def on_archive_requested(self):
        if self.product_id_for_action:
            self.archive_requested.emit(self.product_id_for_action)
            self.reject()

    def populate_edit_form(self, data):
        self.ad_input.setText(data.get('ad', ''))
        self.stok_kodu_input.setText(data.get('stok_kodu', ''))
        self.barkod_input.setText(data.get('barkod', ''))
        self.alis_fiyati_input.setText(str(data.get('alis_fiyati', 0)))
        self.stok_miktari_input.setText(str(data.get('stok_miktari', 0)))
        self.min_stok_input.setText(str(data.get('min_stok_seviyesi', 0)))
        if (cat_index := self.kategori_combo.findData(data.get('kategori_id'))) >= 0:
            self.kategori_combo.setCurrentIndex(cat_index)
        if (tax_index := self.vergi_combo.findData(data.get('vergi_id'))) >= 0:
            self.vergi_combo.setCurrentIndex(tax_index)
        if (curr_index := self.para_birimi_combo.findText(data.get('alis_para_birimi', 'TL'))) >= 0:
            self.para_birimi_combo.setCurrentIndex(curr_index)
        self.secilen_resim_yolu = data.get('gorsel_yolu')
        self.update_image_preview()

    def update_image_preview(self):
        if self.secilen_resim_yolu and os.path.exists(self.secilen_resim_yolu):
            pixmap = QPixmap(self.secilen_resim_yolu)
            self.image_label.setPixmap(pixmap.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.image_label.setText("Resim Yüklü Değil")
            self.image_label.setPixmap(QPixmap())
    
    def show_variant_management(self, show):
        self.tab_widget.setTabEnabled(1, show)
        self.alis_fiyati_input.setEnabled(not show)
        self.stok_miktari_input.setEnabled(not show)
        self.stok_kodu_input.setReadOnly(show)

    def get_data(self):
        return {
            "ad": self.ad_input.text().strip(),
            "stok_kodu": self.stok_kodu_input.text().strip(),
            "barkod": self.barkod_input.text().strip(),
            "kategori_id": self.kategori_combo.currentData(),
            "vergi_id": self.vergi_combo.currentData(),
            "alis_para_birimi": self.para_birimi_combo.currentText(),
            "alis_fiyati": float(self.alis_fiyati_input.text().replace(',', '.') or 0),
            "stok_miktari": int(self.stok_miktari_input.text() or 0),
            "min_stok_seviyesi": int(self.min_stok_input.text() or 0),
            "ana_urun_kodu": None, 
            "gorsel_yolu": self.secilen_resim_yolu
        }