# dosya: views/product_view.py

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget,
    QComboBox, QLabel, QStackedWidget, QFormLayout, QSplitter
)
from PySide6.QtGui import QPixmap, QAction
from PySide6.QtCore import Qt
import qtawesome as qta

from utils.themed_widgets import CardWidget, PrimaryButton, DangerButton, OutlineButton
from utils.custom_widgets import PageHeader
from services.session_manager import session

class ProductView(QWidget):
    def __init__(self):
        super().__init__()
        
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        splitter = QSplitter(Qt.Horizontal)

        left_panel = self._create_left_panel()
        right_panel = self._create_right_panel()

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([800, 400])

        main_layout.addWidget(splitter)

    def _create_left_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        self.header = PageHeader("Ürünler", icon_name="box-open")
        
        control_bar = QWidget()
        control_bar_layout = QHBoxLayout(control_bar)
        control_bar_layout.setContentsMargins(0, 0, 0, 0)
        control_bar_layout.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ürünlerde Ara...")
        search_icon_action = QAction(self)
        search_icon_action.setIcon(qta.icon('fa5s.search', color='gray'))
        self.search_input.addAction(search_icon_action, QLineEdit.LeadingPosition)
        
        self.category_filter_combo = QComboBox()
        self.stock_status_filter_combo = QComboBox()
        self.stock_status_filter_combo.addItems(["Stok Durumu", "Stokta Olanlar", "Tükenenler", "Kritik Seviyedekiler"])
        
        self.add_single_product_button = PrimaryButton("Yeni Ürün Ekle", icon_name="fa5s.plus")

        control_bar_layout.addWidget(self.search_input, 2)
        control_bar_layout.addWidget(self.category_filter_combo, 1)
        control_bar_layout.addWidget(self.stock_status_filter_combo, 1)
        control_bar_layout.addStretch()
        control_bar_layout.addWidget(self.add_single_product_button)
        
        self.content_stack = QStackedWidget()
        self.product_list = QListWidget()
        self.product_list.setObjectName("ModernList")
        
        loading_widget = QWidget()
        loading_layout = QVBoxLayout(loading_widget)
        loading_layout.setAlignment(Qt.AlignCenter)
        loading_label = QLabel("Yükleniyor...")
        loading_layout.addWidget(loading_label)
        
        self.content_stack.addWidget(self.product_list)
        self.content_stack.addWidget(loading_widget)

        layout.addWidget(self.header)
        layout.addWidget(control_bar)
        layout.addWidget(self.content_stack, 1)
        
        return panel

    def _create_right_panel(self) -> QWidget:
        panel = QWidget()
        panel.setContentsMargins(0, 25, 25, 25)
        main_layout = QVBoxLayout(panel)
        main_layout.setContentsMargins(0,0,0,0)
        
        card = CardWidget("Ürün Detayı")
        card.setMinimumWidth(350)
        layout = card.layout()
        
        self.detail_stack = QStackedWidget()
        self.detail_info_label = QLabel("Detayları görmek için soldaki listeden bir ürün seçin.")
        self.detail_info_label.setAlignment(Qt.AlignCenter)
        self.detail_info_label.setWordWrap(True)
        self.detail_info_label.setObjectName("InfoLabel")
        
        self.detail_widget = QWidget()
        detail_layout = QVBoxLayout(self.detail_widget)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(15)
        
        self.detail_image_label = QLabel()
        self.detail_image_label.setFixedSize(200, 200)
        self.detail_image_label.setAlignment(Qt.AlignCenter)
        self.detail_image_label.setObjectName("ProductDetailImage")
        detail_layout.addWidget(self.detail_image_label, 0, Qt.AlignCenter)
        
        self.detail_name_label = QLabel("Ürün Adı Buraya Gelecek")
        self.detail_name_label.setObjectName("ProductDetailName")
        self.detail_name_label.setAlignment(Qt.AlignCenter)
        self.detail_name_label.setWordWrap(True)
        detail_layout.addWidget(self.detail_name_label)
        
        info_form_group = CardWidget("Temel Bilgiler")
        info_form_layout = QFormLayout()
        info_form_group.layout().addLayout(info_form_layout)
        self.detail_sku_label = QLabel()
        self.detail_barcode_label = QLabel()
        self.detail_category_label = QLabel()
        self.detail_purchase_price_label = QLabel()
        info_form_layout.addRow("<b>Stok Kodu:</b>", self.detail_sku_label)
        info_form_layout.addRow("<b>Barkod:</b>", self.detail_barcode_label)
        info_form_layout.addRow("<b>Kategori:</b>", self.detail_category_label)
        info_form_layout.addRow("<b>Alış Fiyatı:</b>", self.detail_purchase_price_label)
        detail_layout.addWidget(info_form_group)
        
        stock_group = CardWidget("Stok Bilgileri")
        stock_layout = QFormLayout()
        stock_group.layout().addLayout(stock_layout)
        self.detail_stock_label = QLabel()
        self.add_stock_movement_button = PrimaryButton("Stok Hareketi Ekle", icon_name='fa5s.plus-circle')
        stock_layout.addRow("<b>Mevcut Stok:</b>", self.detail_stock_label)
        stock_layout.addWidget(self.add_stock_movement_button)
        detail_layout.addWidget(stock_group)
        
        detail_layout.addStretch()
        
        action_button_layout = QHBoxLayout()
        self.edit_product_button = OutlineButton("Düzenle", icon_name='fa5s.edit')
        self.archive_product_button = DangerButton("Arşivle", icon_name='fa5s.archive')
        action_button_layout.addWidget(self.edit_product_button)
        action_button_layout.addWidget(self.archive_product_button)
        detail_layout.addLayout(action_button_layout)
        
        self.detail_stack.addWidget(self.detail_info_label)
        self.detail_stack.addWidget(self.detail_widget)
        layout.addWidget(self.detail_stack)
        main_layout.addWidget(card)
        return panel

    def show_loading(self, show: bool):
        self.content_stack.setCurrentIndex(1 if show else 0)
        
    def show_detail_panel(self, show: bool):
        self.detail_stack.setCurrentIndex(1 if show else 0)
        
    def update_details(self, product_data, category_name):
        self.detail_name_label.setText(product_data.get('ad', 'N/A'))
        self.detail_sku_label.setText(f"<b>{product_data.get('stok_kodu', 'N/A')}</b>")
        self.detail_barcode_label.setText(f"<b>{product_data.get('barkod', 'N/A')}</b>")
        self.detail_category_label.setText(f"<b>{category_name}</b>")
        price_str = f"<b>{product_data.get('alis_fiyati', 0):,.2f} {product_data.get('alis_para_birimi', 'TL')}</b>"
        self.detail_purchase_price_label.setText(price_str)
        self.detail_stock_label.setText(f"<b>{product_data.get('stok_miktari', 0)}</b>")
        image_path = product_data.get('gorsel_yolu')
        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            self.detail_image_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.detail_image_label.setPixmap(QPixmap())
            self.detail_image_label.setText("Görsel Yok")
            
        self.edit_product_button.setVisible(session.has_permission('products:edit'))
        self.archive_product_button.setVisible(session.has_permission('products:delete'))
        self.add_stock_movement_button.setEnabled(session.has_permission('products:edit'))