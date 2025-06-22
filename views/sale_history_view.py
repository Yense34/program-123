# views/sale_history_view.py (Hata Düzeltmesi)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTableView, 
    QHeaderView, QLabel
)

from utils.custom_widgets import PageHeader
from utils.themed_widgets import CardWidget

class SaleHistoryView(QWidget):
    def __init__(self):
        super().__init__()
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(25, 25, 25, 25)

        self.header = PageHeader("Satış Geçmişi", icon_name="history")
        
        search_card = CardWidget("Filtrele ve Ara")
        # --- DEĞİŞİKLİK BURADA ---
        # Hatalı olan QHBoxLayout(search_card.layout()) çağrısı düzeltildi.
        # Önce CardWidget'ın kendi layout'u alınıyor.
        card_main_layout = search_card.layout()
        
        # Sonra yeni QHBoxLayout oluşturulup içine widget'lar ekleniyor.
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Satış ID veya Müşteri Adı ile ara...")
        
        search_layout.addWidget(QLabel("Arama:"))
        search_layout.addWidget(self.search_input)
        
        # En son olarak, hazırlanan bu yeni layout, CardWidget'ın ana layout'una ekleniyor.
        card_main_layout.addLayout(search_layout)
        # --- DEĞİŞİKLİK SONU ---

        self.history_table = QTableView()
        self.history_table.setSelectionBehavior(QTableView.SelectRows)
        self.history_table.setEditTriggers(QTableView.NoEditTriggers)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        info_label = QLabel("Detayları görmek için bir satış kaydına çift tıklayın.")
        info_label.setObjectName("SubtleInfoLabel")

        main_layout.addWidget(self.header)
        main_layout.addWidget(search_card)
        main_layout.addWidget(info_label)
        main_layout.addWidget(self.history_table, 1)