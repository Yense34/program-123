# dosya: views/customer_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, 
    QTextEdit, QComboBox, QWidget, QTabWidget
)
import re

from utils import ui_texts as texts
from utils.location_data import LOCATIONS, CITIES
from utils.themed_widgets import CardWidget, SuccessButton, NeutralButton

class CustomerDialog(QDialog):
    def __init__(self, parent=None, customer_data=None, customer_groups=None):
        super().__init__(parent)
        self.is_edit_mode = customer_data is not None
        
        self._setup_ui(customer_groups)
        self._layout_widgets()
        self._connect_signals()

        if self.is_edit_mode:
            self._populate_edit_form(customer_data)

        self._update_save_button_state()
        self.ad_input.setFocus()

    def _setup_ui(self, customer_groups):
        title = texts.CUSTOMER_DIALOG_TITLE_EDIT if self.is_edit_mode else texts.CUSTOMER_DIALOG_TITLE_ADD
        self.setWindowTitle(title)
        self.setMinimumWidth(550)
        self.setModal(True)

        self.ad_input = QLineEdit()
        self.soyad_input = QLineEdit()
        
        # --- DÜZELTME: Maske '0' karakterini sabit metin yapacak şekilde güncellendi ---
        self.telefon_input = QLineEdit()
        self.telefon_input.setInputMask("\\0(999) 999 99 99")
        self.ikinci_telefon_input = QLineEdit()
        self.ikinci_telefon_input.setInputMask("\\0(999) 999 99 99")
        # --- DÜZELTME SONU ---
        
        self.eposta_input = QLineEdit()
        
        self.grup_combo = QComboBox()
        self.grup_combo.addItem("Grupsuz", None)
        if customer_groups:
            for group in customer_groups:
                self.grup_combo.addItem(group['ad'], group['id'])

        self.tc_no_input = QLineEdit()
        self.tc_no_input.setInputMask("99999999999")
        self.vergi_no_input = QLineEdit()

        self.il_combo = QComboBox()
        self.il_combo.setEditable(True)
        self.il_combo.addItems(CITIES)
        
        self.ilce_combo = QComboBox()
        self.ilce_combo.setEditable(True)
        
        self.mahalle_input = QLineEdit()
        self.acik_adres_input = QTextEdit()
        self.acik_adres_input.setPlaceholderText("Sokak, bina no, daire no vb.")
        self.acik_adres_input.setMaximumHeight(80)
        self.notlar_input = QTextEdit()
        self.notlar_input.setMaximumHeight(80)

        self.save_button = SuccessButton(texts.BTN_SAVE)
        self.cancel_button = NeutralButton(texts.BTN_CANCEL)

    def _layout_widgets(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        tab_widget = QTabWidget()

        temel_bilgiler_tab = QWidget()
        temel_bilgiler_layout = QVBoxLayout(temel_bilgiler_tab)
        temel_bilgiler_layout.setContentsMargins(0, 10, 0, 0)
        
        info_card = CardWidget()
        form_layout = QFormLayout()
        info_card.layout().addLayout(form_layout)
        form_layout.addRow("Ad (*):", self.ad_input)
        form_layout.addRow("Soyad (*):", self.soyad_input)
        form_layout.addRow("Müşteri Grubu:", self.grup_combo)
        form_layout.addRow("Cep Telefonu (GSM):", self.telefon_input)
        form_layout.addRow("Sabit/İkinci Telefon:", self.ikinci_telefon_input)
        form_layout.addRow("E-posta:", self.eposta_input)
        form_layout.addRow("TC Kimlik No:", self.tc_no_input)
        form_layout.addRow("Vergi No:", self.vergi_no_input)
        temel_bilgiler_layout.addWidget(info_card)
        
        adres_bilgileri_tab = QWidget()
        adres_bilgileri_layout = QVBoxLayout(adres_bilgileri_tab)
        adres_bilgileri_layout.setContentsMargins(0, 10, 0, 0)
        
        address_card = CardWidget()
        address_layout = QFormLayout()
        address_card.layout().addLayout(address_layout)
        address_layout.addRow("İl:", self.il_combo)
        address_layout.addRow("İlçe:", self.ilce_combo)
        address_layout.addRow("Mahalle:", self.mahalle_input)
        address_layout.addRow("Açık Adres:", self.acik_adres_input)
        adres_bilgileri_layout.addWidget(address_card)
        adres_bilgileri_layout.addStretch()

        notlar_tab = QWidget()
        notlar_layout = QVBoxLayout(notlar_tab)
        notlar_layout.setContentsMargins(0, 10, 0, 0)
        
        notes_card = CardWidget("Müşteri Hakkında Notlar")
        notes_card.layout().addWidget(self.notlar_input)
        notlar_layout.addWidget(notes_card)

        tab_widget.addTab(temel_bilgiler_tab, "Temel ve İletişim Bilgileri")
        tab_widget.addTab(adres_bilgileri_tab, "Adres Bilgileri")
        tab_widget.addTab(notlar_tab, "Müşteri Notları")

        main_layout.addWidget(tab_widget)

        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 10, 0, 0)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        
        main_layout.addWidget(button_container)

    def _connect_signals(self):
        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
        self.il_combo.currentIndexChanged.connect(self._on_city_selected)
        
        self.ad_input.textChanged.connect(self._update_save_button_state)
        self.soyad_input.textChanged.connect(self._update_save_button_state)

    def _update_save_button_state(self):
        is_valid = bool(self.ad_input.text().strip() and self.soyad_input.text().strip())
        self.save_button.setEnabled(is_valid)

    def _on_city_selected(self, index):
        selected_city = self.il_combo.currentText()
        self.ilce_combo.clear()
        if selected_city in LOCATIONS:
            self.ilce_combo.addItems(LOCATIONS[selected_city])

    def _populate_edit_form(self, data):
        self.ad_input.setText(data.get('ad', ''))
        self.soyad_input.setText(data.get('soyad', ''))
        
        self.telefon_input.setText(data.get('telefon', ''))
        self.ikinci_telefon_input.setText(data.get('ikinci_telefon', ''))
        
        self.eposta_input.setText(data.get('eposta', ''))
        self.tc_no_input.setText(data.get('tc_no', ''))
        self.vergi_no_input.setText(data.get('vergi_no', ''))
        self.notlar_input.setPlainText(data.get('notlar', ''))
        
        if (grup_id := data.get('grup_id')) is not None:
            if (index := self.grup_combo.findData(grup_id)) >= 0:
                self.grup_combo.setCurrentIndex(index)
        
        if saved_city := data.get('il', ''):
            if (city_index := self.il_combo.findText(saved_city)) > -1:
                self.il_combo.setCurrentIndex(city_index)
                self.ilce_combo.blockSignals(True)
                self._on_city_selected(city_index)
                if saved_district := data.get('ilce', ''):
                    if (district_index := self.ilce_combo.findText(saved_district)) > -1:
                        self.ilce_combo.setCurrentIndex(district_index)
                self.ilce_combo.blockSignals(False)

        self.mahalle_input.setText(data.get('mahalle', ''))
        self.acik_adres_input.setPlainText(data.get('acik_adres', ''))

    def get_data(self):
        phone_number = re.sub(r'\D', '', self.telefon_input.text())
        second_phone_number = re.sub(r'\D', '', self.ikinci_telefon_input.text())

        return {
            "ad": self.ad_input.text().strip(),
            "soyad": self.soyad_input.text().strip(),
            "telefon": phone_number,
            "ikinci_telefon": second_phone_number,
            "eposta": self.eposta_input.text().strip(),
            "tc_no": self.tc_no_input.text().strip(),
            "vergi_no": self.vergi_no_input.text().strip(),
            "il": self.il_combo.currentText(),
            "ilce": self.ilce_combo.currentText(),
            "mahalle": self.mahalle_input.text().strip(),
            "acik_adres": self.acik_adres_input.toPlainText().strip(),
            "notlar": self.notlar_input.toPlainText().strip(),
            "grup_id": self.grup_combo.currentData() 
        }