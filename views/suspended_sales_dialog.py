# dosya: views/suspended_sales_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableView, 
    QHeaderView, QAbstractItemView, QWidget
)
from PySide6.QtCore import Qt
from utils.themed_widgets import SuccessButton, DangerButton, NeutralButton

class SuspendedSalesDialog(QDialog):
    def __init__(self, model, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Askıdaki Satışlar")
        self.resize(700, 500)
        self.setModal(True)
        self.selected_sale_id = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        self.sales_table = QTableView()
        self.sales_table.setModel(model)
        self.sales_table.setAlternatingRowColors(True)
        self.sales_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.sales_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.sales_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.sales_table.verticalHeader().setVisible(False)
        
        main_layout.addWidget(self.sales_table, 1)

        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        self.resume_button = SuccessButton("Bu Satışa Devam Et")
        self.delete_button = DangerButton("Askıdaki Kaydı Sil")
        self.close_button = NeutralButton("Kapat")
        
        button_layout.addStretch()
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.resume_button)
        button_layout.addStretch()
        button_layout.addWidget(self.close_button, 0, Qt.AlignRight)
        
        main_layout.addWidget(button_container)

        self.resume_button.clicked.connect(self.accept)
        self.delete_button.clicked.connect(self.on_delete_clicked)
        self.close_button.clicked.connect(self.reject)

        self.sales_table.selectionModel().selectionChanged.connect(self.on_selection_changed)
        
        self.resume_button.setEnabled(False)
        self.delete_button.setEnabled(False)

    def on_selection_changed(self, selected, deselected):
        indexes = selected.indexes()
        is_item_selected = bool(indexes)
        self.resume_button.setEnabled(is_item_selected)
        self.delete_button.setEnabled(is_item_selected)

        if is_item_selected:
            self.selected_sale_id = self.sales_table.model().get_item_id(indexes[0])
        else:
            self.selected_sale_id = None

    def on_delete_clicked(self):
        self.done(2) 

    def get_selected_sale_id(self):
        return self.selected_sale_id