# dosya: views/bulk_communication_view.py

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QHeaderView,
    QTabWidget, QTextEdit, QComboBox, QLabel, QLineEdit, QFormLayout
)
from PySide6.QtCore import Qt
import qtawesome as qta

from utils.custom_widgets import PageHeader
from utils.themed_widgets import CardWidget, SuccessButton, DangerButton, OutlineButton

class BulkCommunicationView(QWidget):
    def __init__(self):
        super().__init__()
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(25, 25, 25, 25)

        self.header = PageHeader("Toplu İletişim", icon_name="paper-plane")
        main_layout.addWidget(self.header)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        customer_group = CardWidget("1. Alıcıları Seç")
        customer_layout = customer_group.layout()
        
        selection_buttons_layout = QHBoxLayout()
        self.select_all_button = OutlineButton("Tümünü Seç")
        self.deselect_all_button = OutlineButton("Seçimleri Kaldır")
        selection_buttons_layout.addStretch()
        selection_buttons_layout.addWidget(self.select_all_button)
        selection_buttons_layout.addWidget(self.deselect_all_button)

        self.customer_list = QListWidget()
        self.customer_list.setAlternatingRowColors(True)

        customer_layout.addLayout(selection_buttons_layout)
        customer_layout.addWidget(self.customer_list)

        message_panel = QWidget()
        message_layout = QVBoxLayout(message_panel)
        message_layout.setContentsMargins(0,0,0,0)
        message_layout.setSpacing(15)

        template_group = CardWidget("2. Mesajı Yaz veya Şablondan Seç")
        template_layout = template_group.layout()

        template_selection_layout = QHBoxLayout()
        self.template_combo = QComboBox()
        self.delete_template_button = DangerButton("", icon_name='fa5s.trash-alt')
        self.delete_template_button.setToolTip("Seçili Şablonu Sil")

        template_selection_layout.addWidget(QLabel("Hazır Şablonlar:"), 0)
        template_selection_layout.addWidget(self.template_combo, 1)
        template_selection_layout.addWidget(self.delete_template_button, 0)

        self.message_tabs = QTabWidget()
        self.sms_tab = self._create_sms_tab()
        self.email_tab = self._create_email_tab()
        
        self.message_tabs.addTab(self.sms_tab, qta.icon('fa5s.comment-dots'), " SMS Gönder")
        self.message_tabs.addTab(self.email_tab, qta.icon('fa5s.envelope'), " E-posta Gönder")
        
        self.save_template_button = OutlineButton("Mesajı Şablon Olarak Kaydet", icon_name='fa5s.save')
        
        template_layout.addLayout(template_selection_layout)
        template_layout.addWidget(self.message_tabs)
        template_layout.addWidget(self.save_template_button, 0, Qt.AlignRight)
        
        self.send_button = SuccessButton("Seçili Alıcılara Gönder", icon_name='fa5s.paper-plane')
        self.send_button.setMinimumHeight(45)

        message_layout.addWidget(template_group)
        message_layout.addWidget(self.send_button)

        content_layout.addWidget(customer_group, 2)
        content_layout.addWidget(message_panel, 3)

        main_layout.addLayout(content_layout)

    def _create_sms_tab(self):
        tab = QWidget()
        tab.setObjectName("SMSTab")
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        layout.setContentsMargins(5, 15, 5, 5)

        form_layout = QFormLayout()
        self.sms_message_box = QTextEdit()
        self.sms_message_box.setMinimumHeight(150)
        form_layout.addRow("SMS Metni:", self.sms_message_box)
        layout.addLayout(form_layout)

        self.sms_char_count_label = QLabel("Karakter: 0 | SMS: 1")
        self.sms_char_count_label.setObjectName("SubtleInfoLabel")
        self.sms_char_count_label.setAlignment(Qt.AlignRight)
        
        layout.addWidget(self.sms_char_count_label)
        
        # --- DÜZELTİLEN BÖLÜM BURASI: Orijinal ve stabil çalışan yapıya geri dönüldü. ---
        single_send_group = CardWidget("Tekil Gönderim / Test")
        single_send_layout = QHBoxLayout()
        single_send_group.layout().addLayout(single_send_layout)
        
        self.single_number_input = QLineEdit()
        self.single_number_input.setPlaceholderText("05xxxxxxxxx formatında numara girin")
        self.send_single_sms_button = OutlineButton("Bu Numaraya Gönder")
        
        single_send_layout.addWidget(QLabel("Telefon:"))
        single_send_layout.addWidget(self.single_number_input, 1)
        single_send_layout.addWidget(self.send_single_sms_button)
        # --- DÜZELTME SONU ---

        layout.addWidget(single_send_group)
        
        return tab

    def _create_email_tab(self):
        tab = QWidget()
        tab.setObjectName("EmailTab")
        layout = QFormLayout(tab)
        layout.setContentsMargins(5, 15, 5, 5)
        layout.setSpacing(10)

        self.email_subject_input = QLineEdit()
        self.email_message_box = QTextEdit()
        self.email_message_box.setMinimumHeight(200)

        layout.addRow("E-posta Konusu:", self.email_subject_input)
        layout.addRow("E-posta İçeriği (HTML destekler):", self.email_message_box)
        
        return tab

    def set_sending_state(self, is_sending: bool):
        self.send_button.setEnabled(not is_sending)
        self.send_single_sms_button.setEnabled(not is_sending)
        
        if is_sending:
            self.send_button.setText("Gönderiliyor...")
            self.send_single_sms_button.setText("Gönderiliyor...")
        else:
            self.send_button.setText("Seçili Alıcılara Gönder")
            self.send_single_sms_button.setText("Bu Numaraya Gönder")