# dosya: views/stock_movement_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QLabel, QHBoxLayout, QWidget, QSpinBox
)
from PySide6.QtCore import Qt

from utils.themed_widgets import CardWidget, SuccessButton, NeutralButton
from utils import ui_helpers

class StockMovementDialog(QDialog):
    def __init__(self, product_name, parent=None):
        super().__init__(parent)
        self.product_name = product_name
        
        self.setWindowTitle("Stok Hareketi Ekle")
        self.setModal(True)

        self._setup_ui()
        self._layout_widgets()
        self._connect_signals()
        
        self.quantity_input.setFocus()
        self.quantity_input.selectAll()

    def _setup_ui(self):
        self.product_label = QLabel(f"<b>{self.product_name}</b>")
        self.product_label.setObjectName("DialogHeaderLabel")
        self.product_label.setAlignment(Qt.AlignCenter)
        
        self.movement_type_combo = QComboBox()
        self.movement_type_combo.addItems(["Stok Girişi (Alım/İade)", "Stok Düşüşü (Fire/Kayıp)"])

        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, 99999)
        self.quantity_input.setValue(1)
        self.quantity_input.setAlignment(Qt.AlignCenter)

        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Örn: Yeni Sevkiyat, Sayım Farkı...")

        self.cancel_button = NeutralButton("İptal")
        self.save_button = SuccessButton("İşlemi Kaydet")
        
    def _layout_widgets(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        main_layout.addWidget(self.product_label)
        
        card = CardWidget()
        form_layout = QFormLayout()
        card.layout().addLayout(form_layout)
        
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignLeft)

        form_layout.addRow("İşlem Tipi:", self.movement_type_combo)
        form_layout.addRow("Miktar:", self.quantity_input)
        form_layout.addRow("Açıklama (*):", self.description_input)

        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 15, 0, 0)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)

        main_layout.addWidget(card)
        main_layout.addStretch()
        main_layout.addWidget(button_container)

    def _connect_signals(self):
        self.save_button.clicked.connect(self.on_save)
        self.cancel_button.clicked.connect(self.reject)

    def on_save(self):
        if not self.description_input.text().strip():
            ui_helpers.show_warning_message(self, "Açıklama alanı boş bırakılamaz.")
            return
        self.accept()

    def get_data(self):
        miktar = self.quantity_input.value()
        if miktar <= 0: return None
            
        hareket_tipi_text = self.movement_type_combo.currentText()
        hareket_tipi = "Giriş" if "Giriş" in hareket_tipi_text else "Düşüş"
        
        return {
            "miktar": miktar if hareket_tipi == "Giriş" else -miktar,
            "hareket_tipi": hareket_tipi,
            "aciklama": self.description_input.text().strip()
        }