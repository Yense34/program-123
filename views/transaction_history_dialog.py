# dosya: views/transaction_history_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableView, 
    QHeaderView, QLabel, QWidget
)
from PySide6.QtCore import Qt
from utils.themed_widgets import CardWidget, NeutralButton

class TransactionHistoryDialog(QDialog):
    def __init__(self, customer_name, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle(f"Hesap Ekstresi: {customer_name}")
        self.resize(900, 600)
        self.setModal(True)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        self.history_table = QTableView()
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setEditTriggers(QTableView.NoEditTriggers)
        self.history_table.setSelectionBehavior(QTableView.SelectRows)
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setSortingEnabled(True)
        self.history_table.verticalHeader().setVisible(False)
        main_layout.addWidget(self.history_table, 1)

        summary_card = CardWidget("Dönem Özeti")
        summary_layout = QHBoxLayout()
        summary_card.layout().addLayout(summary_layout)
        
        self.total_debit_label = QLabel("Toplam Borç: 0,00 TL")
        self.total_credit_label = QLabel("Toplam Alacak: 0,00 TL")
        self.balance_label = QLabel("Bakiye: 0,00 TL")

        summary_layout.addWidget(self.total_debit_label, 1, Qt.AlignLeft)
        summary_layout.addWidget(self.total_credit_label, 1, Qt.AlignCenter)
        summary_layout.addWidget(self.balance_label, 1, Qt.AlignRight)
        
        main_layout.addWidget(summary_card)

        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0,0,0,0)
        button_layout.addStretch()
        self.close_button = NeutralButton("Kapat")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        
        main_layout.addWidget(button_container)