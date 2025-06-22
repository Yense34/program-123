# dosya: views/customer_view.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTableView,
    QHeaderView, QLabel, QFormLayout, QComboBox, QStackedWidget, QSplitter
)
from PySide6.QtCore import Qt
import qtawesome as qta

from utils.themed_widgets import CardWidget, PrimaryButton, SuccessButton
from utils.custom_widgets import PageHeader
from services.session_manager import session

class CustomerView(QWidget):
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

        self.header = PageHeader("Müşteriler", icon_name="users")

        action_bar = QWidget()
        action_bar_layout = QHBoxLayout(action_bar)
        action_bar_layout.setContentsMargins(0, 0, 0, 0)
        action_bar_layout.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Müşteri adı, soyadı, telefon...")
        
        self.group_filter_combo = QComboBox()
        
        self.add_customer_button = PrimaryButton("Yeni Müşteri Ekle", icon_name="fa5s.user-plus")

        action_bar_layout.addWidget(self.search_input, 1)
        action_bar_layout.addWidget(self.group_filter_combo, 0)
        action_bar_layout.addStretch()
        action_bar_layout.addWidget(self.add_customer_button, 0)
        
        self.customer_table = QTableView()
        self.customer_table.setSelectionBehavior(QTableView.SelectRows)
        self.customer_table.setEditTriggers(QTableView.NoEditTriggers)
        self.customer_table.setAlternatingRowColors(True)
        self.customer_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.customer_table.verticalHeader().setVisible(False)

        layout.addWidget(self.header)
        layout.addWidget(action_bar)
        layout.addWidget(self.customer_table, 1)
        
        return panel

    def _create_right_panel(self) -> QWidget:
        panel = QWidget()
        panel.setContentsMargins(0, 25, 25, 25)
        
        main_layout = QVBoxLayout(panel)
        main_layout.setContentsMargins(0,0,0,0)
        
        card = CardWidget("Müşteri Detayları")
        card.setMinimumWidth(350)
        layout = card.layout()
        
        self.detail_stack = QStackedWidget()
        
        self.detail_info_label = QLabel("Detayları görmek için soldaki listeden bir müşteri seçin.")
        self.detail_info_label.setAlignment(Qt.AlignCenter)
        self.detail_info_label.setWordWrap(True)
        self.detail_info_label.setObjectName("InfoLabel")

        self.detail_widget = QWidget()
        detail_layout = QVBoxLayout(self.detail_widget)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(15)
        
        self.detail_name_label = QLabel()
        self.detail_name_label.setObjectName("CustomerDetailName")
        self.detail_name_label.setAlignment(Qt.AlignCenter)
        self.detail_name_label.setWordWrap(True)
        detail_layout.addWidget(self.detail_name_label)
        
        info_card = CardWidget("Temel Bilgiler")
        info_layout = QFormLayout()
        info_card.layout().addLayout(info_layout)
        
        self.detail_phone_label = QLabel()
        self.detail_email_label = QLabel()
        self.detail_address_label = QLabel()
        self.detail_address_label.setWordWrap(True)
        
        info_layout.addRow(self._create_detail_row("phone-alt", "Telefon:"), self.detail_phone_label)
        info_layout.addRow(self._create_detail_row("envelope", "E-posta:"), self.detail_email_label)
        info_layout.addRow(self._create_detail_row("map-marker-alt", "Adres:"), self.detail_address_label)
        detail_layout.addWidget(info_card)

        balance_card = CardWidget("Güncel Bakiye")
        balance_layout = QHBoxLayout()
        balance_card.layout().addLayout(balance_layout)
        
        self.detail_balance_label = QLabel()
        self.detail_balance_label.setObjectName("BalanceLabel")
        balance_layout.addStretch()
        balance_layout.addWidget(self.detail_balance_label)
        balance_layout.addStretch()
        detail_layout.addWidget(balance_card)
        
        self.view_transactions_button = PrimaryButton("Hesap Ekstresini Görüntüle", icon_name='fa5s.list-alt')
        self.add_payment_button = SuccessButton("Ödeme Ekle/Al", icon_name='fa5s.money-bill-wave')
        detail_layout.addWidget(self.view_transactions_button)
        detail_layout.addWidget(self.add_payment_button)
        
        detail_layout.addStretch()
        
        self.detail_stack.addWidget(self.detail_info_label)
        self.detail_stack.addWidget(self.detail_widget)
        
        layout.addWidget(self.detail_stack)
        main_layout.addWidget(card)
        
        return panel

    def show_detail_panel(self, show: bool):
        self.detail_stack.setCurrentIndex(1 if show else 0)

    def _create_detail_row(self, icon_name: str, text: str) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        icon_label = QLabel()
        icon = qta.icon(f"fa5s.{icon_name}", color_off='#4A5568')
        icon_label.setPixmap(icon.pixmap(16, 16))
        
        text_label = QLabel(f"<b>{text}</b>")
        
        layout.addWidget(icon_label)
        layout.addWidget(text_label)
        # layout.addStretch() # Bu satır hizalamayı bozuyordu, kaldırıldı.
        
        return widget

    def update_details(self, customer_data, balance_data):
        if not customer_data:
            self.show_detail_panel(False)
            return

        self.detail_name_label.setText(f"{customer_data.get('ad')} {customer_data.get('soyad')}")
        self.detail_phone_label.setText(customer_data.get('telefon') or '<i>Belirtilmemiş</i>')
        self.detail_email_label.setText(customer_data.get('eposta') or '<i>Belirtilmemiş</i>')
        
        address_parts = [
            customer_data.get('acik_adres'), customer_data.get('mahalle'),
            customer_data.get('ilce'), customer_data.get('il')
        ]
        full_address = ", ".join(filter(None, address_parts))
        self.detail_address_label.setText(full_address or "<i>Adres belirtilmemiş</i>")

        balance = balance_data.get('balance', 0)
        self.detail_balance_label.setText(f"{balance:,.2f} TL")

        state = "neutral"
        if balance < 0:
            state = "positive"
        elif balance > 0:
            state = "negative"
        
        self.detail_balance_label.setProperty("balanceState", state)
        self.detail_balance_label.style().unpolish(self.detail_balance_label)
        self.detail_balance_label.style().polish(self.detail_balance_label)
        
        can_edit = session.has_permission('customers:edit')
        self.add_payment_button.setEnabled(can_edit)