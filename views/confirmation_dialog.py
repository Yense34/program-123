# dosya: views/confirmation_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, 
    QLabel, QWidget, QHBoxLayout
)
from utils.themed_widgets import CardWidget, DangerButton, NeutralButton

class ConfirmationDialog(QDialog):
    def __init__(self, parent, title: str, text: str, confirmation_text: str, button_text: str):
        super().__init__(parent)
        
        self.setWindowTitle("İşlem Onayı")
        self.setModal(True)
        self.confirmation_text = confirmation_text

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)

        card = CardWidget(title)
        card_layout = card.layout()

        self.main_text_label = QLabel(text)
        self.main_text_label.setWordWrap(True)
        self.main_text_label.setObjectName("ConfirmationTextLabel")

        self.instruction_label = QLabel(
            f"Lütfen devam etmek için aşağıdaki kutucuğa "
            f"büyük harflerle '<b>{self.confirmation_text}</b>' yazın."
        )
        self.instruction_label.setWordWrap(True)

        self.confirmation_input = QLineEdit()
        self.confirmation_input.setPlaceholderText(f"Buraya '{self.confirmation_text}' yazın...")

        card_layout.addWidget(self.main_text_label)
        card_layout.addSpacing(15)
        card_layout.addWidget(self.instruction_label)
        card_layout.addWidget(self.confirmation_input)
        
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 15, 0, 0)
        button_layout.addStretch()
        
        self.cancel_button = NeutralButton("İptal")
        self.confirm_button = DangerButton(button_text)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.confirm_button)
        
        self.confirm_button.setEnabled(False)
        
        main_layout.addWidget(card)
        main_layout.addWidget(button_container)

        self.confirmation_input.textChanged.connect(self._check_text)
        self.confirm_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def _check_text(self):
        entered_text = self.confirmation_input.text()
        is_match = (entered_text == self.confirmation_text)
        self.confirm_button.setEnabled(is_match)