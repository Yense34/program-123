# dosya: views/quantity_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel,
    QSpinBox, QWidget, QHBoxLayout
)
from PySide6.QtCore import Qt
from utils import ui_texts as texts
from utils.themed_widgets import CardWidget, SuccessButton, NeutralButton

class QuantityDialog(QDialog):
    def __init__(self, product_name: str, current_quantity: int, parent=None):
        super().__init__(parent)
        self.product_name = product_name
        self.current_quantity = current_quantity
        
        self._setup_ui()
        self._layout_widgets()
        self._connect_signals()

        self.quantity_spinbox.setFocus()
        self.quantity_spinbox.selectAll()

    def _setup_ui(self):
        self.setWindowTitle("Miktarı Güncelle")
        self.setModal(True)

        self.quantity_spinbox = QSpinBox()
        self.quantity_spinbox.setRange(0, 9999)
        self.quantity_spinbox.setValue(self.current_quantity)
        self.quantity_spinbox.setSuffix(" adet")
        self.quantity_spinbox.setAlignment(Qt.AlignCenter)
        font = self.quantity_spinbox.font()
        font.setPointSize(14)
        self.quantity_spinbox.setFont(font)
        
        self.info_label = QLabel("<i>Not: Miktarı 0 yaparsanız ürün sepetten kaldırılır.</i>")
        self.info_label.setObjectName("SubtleInfoLabel")

        self.save_button = SuccessButton(texts.BTN_SAVE)
        self.cancel_button = NeutralButton(texts.BTN_CANCEL)
    
    def _layout_widgets(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        card = CardWidget(self.product_name)
        form_layout = QFormLayout()
        card.layout().addLayout(form_layout)
        form_layout.addRow("Yeni Miktar:", self.quantity_spinbox)
        
        main_layout.addWidget(card)
        main_layout.addWidget(self.info_label, 0, Qt.AlignCenter)

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

    def get_new_quantity(self) -> int:
        return self.quantity_spinbox.value()