# dosya: views/sale_view.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QComboBox,
    QTableView, QHeaderView, QLineEdit, QLabel, QSpinBox, QCheckBox,
    QTabWidget, QAbstractItemView, QToolButton, QGridLayout, QPushButton
)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QDoubleValidator, QIcon, QAction

from utils.custom_widgets import PopupSearchWidget
from utils.themed_widgets import (
    CardWidget, OutlineButton, DangerButton,
    SuccessButton, NeutralButton, PrimaryButton
)
import qtawesome as qta

class SaleView(QWidget):
    def __init__(self):
        super().__init__()
        self.feedback_timers = {}
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.addWidget(self._create_left_panel(), 2)
        main_layout.addWidget(self._create_right_panel(), 1)

    def _create_left_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)

        customer_card = CardWidget("1. Müşteri Seçimi")
        customer_layout = customer_card.layout()
        h_customer = QHBoxLayout()
        self.customer_combo = QComboBox()
        self.view_suspended_sales_button = OutlineButton("Bekleyen Satışlar")
        self.add_customer_button = PrimaryButton("Yeni Müşteri")
        h_customer.addWidget(self.customer_combo, 1)
        h_customer.addWidget(self.view_suspended_sales_button)
        h_customer.addWidget(self.add_customer_button)
        customer_layout.addLayout(h_customer)

        product_card = CardWidget("2. Ürün Arama")
        product_layout = product_card.layout()
        self.product_search_input = QLineEdit()
        self.product_search_input.setObjectName("SearchLineEdit")
        self.product_search_input.setPlaceholderText("Ürün adı, kodu veya barkod ile ara...")
        
        # --- DÜZELTME: Ayrı buton yerine QAction kullanıldı ---
        search_icon_action = QAction(self)
        search_icon_action.setIcon(qta.icon('fa5s.search', color='gray'))
        
        self.show_search_popup_action = QAction(self)
        self.show_search_popup_action.setIcon(qta.icon('fa5s.chevron-down', color='gray'))
        self.show_search_popup_action.setToolTip("Tüm ürünleri listele")

        self.product_search_input.addAction(search_icon_action, QLineEdit.LeadingPosition)
        self.product_search_input.addAction(self.show_search_popup_action, QLineEdit.TrailingPosition)
        # --- DÜZELTME SONU ---
        
        self.product_search_popup_widget = PopupSearchWidget(self)
        
        self.currency_warning_label = QLabel("DİKKAT: Kur ayarı eksik, fiyatlar hatalı olabilir!")
        self.currency_warning_label.setObjectName("ErrorLabel")
        self.currency_warning_label.setVisible(False)

        product_layout.addWidget(self.product_search_input)
        product_layout.addWidget(self.currency_warning_label)

        cart_card = CardWidget("Satış Sepeti")
        cart_layout = cart_card.layout()
        self.cart_table = QTableView()
        self.cart_table.setObjectName("CartTable")
        self.cart_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.cart_table.setFocusPolicy(Qt.NoFocus)
        header = self.cart_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        cart_buttons = QHBoxLayout()
        self.remove_from_cart_button = OutlineButton("Seçili Ürünü Çıkar")
        self.clear_cart_button = DangerButton("Sepeti Temizle")
        cart_buttons.addStretch()
        cart_buttons.addWidget(self.remove_from_cart_button)
        cart_buttons.addWidget(self.clear_cart_button)
        cart_layout.addWidget(self.cart_table)
        cart_layout.addLayout(cart_buttons)
        
        layout.addWidget(customer_card)
        layout.addWidget(product_card)
        layout.addWidget(cart_card, 1)
        return panel

    def _create_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)
        
        price_card = CardWidget("3. Fiyat ve Sepete Ekleme")
        tabs = QTabWidget()
        tabs.addTab(self._create_main_add_to_cart_tab(), "Fiyatlar")
        tabs.addTab(self._create_custom_price_tab(), "Özel Fiyat")
        price_card.layout().addWidget(tabs)
        
        layout.addWidget(price_card)
        layout.addWidget(self._create_summary_widget())
        layout.addLayout(self._create_final_buttons())
        layout.addStretch()
        return panel

    def _create_main_add_to_cart_tab(self) -> QWidget:
        widget = QWidget()
        main_tab_layout = QVBoxLayout(widget)
        main_tab_layout.setContentsMargins(10, 15, 10, 15)
        main_tab_layout.setSpacing(15)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        
        h_qty_layout = QHBoxLayout()
        h_qty_layout.setSpacing(2)
        self.quantity_spinbox = QSpinBox()
        self.quantity_spinbox.setRange(1, 9999)
        self.quantity_spinbox.setAlignment(Qt.AlignCenter)
        self.quantity_spinbox.setButtonSymbols(QSpinBox.NoButtons)
        
        self.decrease_quantity_btn = QPushButton(qta.icon('fa5s.minus'), "")
        self.increase_quantity_btn = QPushButton(qta.icon('fa5s.plus'), "")
        
        self.decrease_quantity_btn.setFixedSize(40,40)
        self.increase_quantity_btn.setFixedSize(40,40)
        
        h_qty_layout.addWidget(self.decrease_quantity_btn)
        h_qty_layout.addWidget(self.quantity_spinbox, 1)
        h_qty_layout.addWidget(self.increase_quantity_btn)
        
        self.decrease_quantity_btn.clicked.connect(lambda: self.quantity_spinbox.setValue(max(1, self.quantity_spinbox.value() - 1)))
        self.increase_quantity_btn.clicked.connect(lambda: self.quantity_spinbox.setValue(self.quantity_spinbox.value() + 1))

        self.fiyat_karli_label = QLabel("0.00 TL")
        self.fiyat_nakit_label = QLabel("0.00 TL")
        self.fiyat_kk_label = QLabel("0.00 TL")

        for label in [self.fiyat_karli_label, self.fiyat_nakit_label, self.fiyat_kk_label]:
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            label.setObjectName("PriceLabel")

        self.price_type_combo = QComboBox()
        self.price_type_combo.addItems(["Nakit Satış Fiyatı", "Kredi Kartı Fiyatı", "Alış + Kâr Fiyatı"])
        
        self.add_to_cart_button = SuccessButton("Sepete Ekle", icon_name="fa5s.cart-plus")
        self.add_to_cart_button.setMinimumHeight(40)

        form_layout.addRow("Miktar:", h_qty_layout)
        form_layout.addRow("Alış + Kâr Fiyatı:", self.fiyat_karli_label)
        form_layout.addRow("Nakit Satış Fiyatı:", self.fiyat_nakit_label)
        form_layout.addRow("K. Kartı Satış Fiyatı:", self.fiyat_kk_label)
        form_layout.addRow("<b>Kullanılacak Fiyat:</b>", self.price_type_combo)

        main_tab_layout.addLayout(form_layout)
        main_tab_layout.addWidget(self.add_to_cart_button)

        return widget

    def _create_custom_price_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        form_layout = QFormLayout()
        self.ozel_fiyat_input = QLineEdit("0")
        self.ozel_fiyat_input.setValidator(QDoubleValidator(0, 9999999.99, 2))
        self.kdv_ekle_check = QCheckBox("Fiyata KDV Dahil")
        self.kdv_ekle_check.setChecked(True)
        form_layout.addRow("Özel Fiyat (TL):", self.ozel_fiyat_input)
        form_layout.addRow("", self.kdv_ekle_check)
        layout.addLayout(form_layout)
        self.btn_add_ozel = PrimaryButton("Özel Fiyatı Ekle", icon_name="fa5s.cart-plus")
        layout.addWidget(self.btn_add_ozel, 0, Qt.AlignRight)
        return widget

    def _create_summary_widget(self) -> QWidget:
        widget = CardWidget("4. Ödeme")
        form = QFormLayout()
        widget.layout().addLayout(form)
        self.total_label = QLabel("0.00 TL")
        self.total_label.setObjectName("SaleTotalLabel")
        self.total_label.setAlignment(Qt.AlignRight)
        form.addRow("Sepet Toplamı:", self.total_label)
        h_payment = QHBoxLayout()
        self.deposit_input = QLineEdit("0")
        self.deposit_input.setValidator(QDoubleValidator(0, 9999999.99, 2))
        self.pay_full_button = OutlineButton("Tamamını Öde")
        h_payment.addWidget(self.deposit_input, 1)
        h_payment.addWidget(self.pay_full_button)
        form.addRow("Alınan Ödeme:", h_payment)
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItems(["Nakit", "Kredi Kartı", "Havale/EFT", "Diğer"])
        form.addRow("Ödeme Yöntemi:", self.payment_method_combo)
        self.balance_label = QLabel("0.00 TL")
        self.balance_label.setObjectName("BalanceLabel")
        self.balance_label.setAlignment(Qt.AlignRight)
        form.addRow("Kalan Tutar:", self.balance_label)
        return widget

    def _create_final_buttons(self):
        layout = QHBoxLayout()
        self.suspend_sale_button = NeutralButton("Sepeti Askıya Al")
        self.complete_sale_button = SuccessButton("Satışı Tamamla")
        self.suspend_sale_button.setMinimumHeight(45)
        self.complete_sale_button.setMinimumHeight(45)
        layout.addStretch()
        layout.addWidget(self.suspend_sale_button)
        layout.addWidget(self.complete_sale_button)
        return layout

    def update_price_displays(self, prices: dict, is_currency_ok: bool):
        karli_fiyat = prices.get('karli_fiyat_kdv_haric', 0)
        kdvli_fiyat = prices.get('kdvli_fiyat', 0)
        kkli_fiyat = prices.get('kkli_fiyat', 0)
        self.fiyat_karli_label.setText(f"<b>{karli_fiyat:,.2f} TL</b>")
        self.fiyat_nakit_label.setText(f"<b>{kdvli_fiyat:,.2f} TL</b>")
        self.fiyat_kk_label.setText(f"<b>{kkli_fiyat:,.2f} TL</b>")
        self.currency_warning_label.setVisible(not is_currency_ok)

    def show_button_feedback(self, button):
        if not isinstance(button, SuccessButton): return
        original_text = button.text()
        if button in self.feedback_timers and self.feedback_timers[button].isActive():
            self.feedback_timers[button].stop()
        button.setText("✓ Eklendi")
        button.setEnabled(False)
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self._reset_button_style(button, original_text))
        timer.start(1200)
        self.feedback_timers[button] = timer

    def _reset_button_style(self, button, original_text: str):
        button.setText(original_text)
        button.setEnabled(True)

    def update_ui_for_editing(self, is_editing: bool):
        if is_editing:
            self.complete_sale_button.setText("Satışı Güncelle")
            self.complete_sale_button.setIcon(qta.icon("fa5s.check", color="white"))
        else:
            self.complete_sale_button.setText("Satışı Tamamla")
            self.complete_sale_button.setIcon(QIcon())