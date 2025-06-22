# dosya: views/payment_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QHBoxLayout, QWidget
)
from PySide6.QtGui import QDoubleValidator
from utils import ui_texts as texts
from utils.themed_widgets import SuccessButton, NeutralButton

class PaymentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._setup_ui()
        self._layout_widgets()
        self._connect_signals()
        
        self._update_save_button_state()
        self.amount_input.setFocus()

    def _setup_ui(self):
        self.setWindowTitle(texts.PAYMENT_DIALOG_TITLE)
        self.setModal(True)

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText(texts.PAYMENT_DIALOG_AMOUNT_PLACEHOLDER)
        self.amount_input.setValidator(QDoubleValidator(0, 9999999.99, 2))
        
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText(texts.PAYMENT_DIALOG_DESC_PLACEHOLDER)
        
        self.save_button = SuccessButton(texts.PAYMENT_DIALOG_SAVE_BTN)
        self.cancel_button = NeutralButton(texts.BTN_CANCEL)

    def _layout_widgets(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        form_layout.addRow(texts.PAYMENT_DIALOG_AMOUNT_LABEL, self.amount_input)
        form_layout.addRow(texts.PAYMENT_DIALOG_DESC_LABEL, self.description_input)
        
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 15, 0, 0)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        
        main_layout.addLayout(form_layout)
        main_layout.addWidget(button_container)

    def _connect_signals(self):
        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.amount_input.textChanged.connect(self._update_save_button_state)

    def _update_save_button_state(self):
        try:
            amount = float(self.amount_input.text().replace(',', '.'))
            is_valid = amount > 0
        except ValueError:
            is_valid = False
        
        self.save_button.setEnabled(is_valid)

    def get_data(self) -> dict:
        try:
            tutar = float(self.amount_input.text().replace(',', '.'))
        except ValueError:
            tutar = 0.0
            
        return {
            "tutar": tutar,
            "aciklama": self.description_input.text().strip()
        }