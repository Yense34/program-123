# dosya: views/sale_detail_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QFormLayout, QFrame, QListWidget, QWidget
)
from PySide6.QtCore import Qt, Signal
import qtawesome as qta

from utils.themed_widgets import (
    PrimaryButton, DangerButton, NeutralButton, SuccessButton, OutlineButton
)

class SaleDetailDialog(QDialog):
    delete_requested = Signal(int)
    edit_requested = Signal(int)

    def __init__(self, sale_data, parent=None):
        super().__init__(parent)
        
        sale_info = sale_data['sale_info']
        self.sale_id = sale_info['id']
        
        self.setWindowTitle(f"Satış Detayı: #{self.sale_id} - {sale_info['musteri_adi']}")
        self.setMinimumSize(800, 600)
        self.setModal(True)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        info_frame = QFrame()
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(0,0,0,0)
        
        customer_info_layout = QVBoxLayout()
        customer_name_label = QLabel(sale_info['musteri_adi'])
        sale_id_label = QLabel(f"Satış No: #{self.sale_id} | Telefon: {sale_info.get('telefon', 'N/A')}")
        
        customer_name_label.setObjectName("SaleDetailCustomerName")
        sale_id_label.setObjectName("SaleDetailInfo")

        customer_info_layout.addWidget(customer_name_label)
        customer_info_layout.addWidget(sale_id_label)

        price_info_layout = QFormLayout()
        price_info_layout.setContentsMargins(0,5,0,0)
        total_amount_label = QLabel(f"<b>{sale_info['toplam_tutar']:,.2f} TL</b>")
        total_amount_label.setObjectName("SaleDetailTotalLabel")
        price_info_layout.addRow("<b>Satış Tarihi:</b>", QLabel(sale_info['satis_tarihi']))
        price_info_layout.addRow("<b>Toplam Tutar:</b>", total_amount_label)

        info_layout.addLayout(customer_info_layout, 1)
        info_layout.addLayout(price_info_layout)
        main_layout.addWidget(info_frame)
        
        products_header_label = QLabel("Satılan Ürünler")
        products_header_label.setObjectName("SubheaderLabel")
        
        self.products_list = QListWidget()
        self.products_list.setFocusPolicy(Qt.NoFocus)
        
        main_layout.addWidget(products_header_label)
        main_layout.addWidget(self.products_list, 1)

        actions_container = QWidget()
        actions_layout = QHBoxLayout(actions_container)
        actions_layout.setContentsMargins(0,0,0,0)
        
        self.edit_sale_button = OutlineButton("Düzenle", icon_name='fa5s.edit')
        self.delete_sale_button = DangerButton("Sil", icon_name='fa5s.trash-alt')
        self.invoice_pdf_button = PrimaryButton("Sipariş Formu (PDF)", icon_name='fa5s.file-pdf')
        self.production_pdf_button = NeutralButton("İmalat Formu (PDF)", icon_name='fa5s.industry')
        self.sms_button = SuccessButton("Onay SMS'i Gönder", icon_name='fa5s.comment-dots')
        self.close_button = NeutralButton("Kapat")
        
        actions_layout.addWidget(self.edit_sale_button)
        actions_layout.addWidget(self.delete_sale_button)
        actions_layout.addStretch()
        actions_layout.addWidget(self.invoice_pdf_button)
        actions_layout.addWidget(self.production_pdf_button)
        actions_layout.addWidget(self.sms_button)
        actions_layout.addStretch()
        actions_layout.addWidget(self.close_button)
        main_layout.addWidget(actions_container)

        self.close_button.clicked.connect(self.accept)
        
        self.delete_sale_button.clicked.connect(self._on_delete_requested)
        self.edit_sale_button.clicked.connect(self._on_edit_requested)

    def _on_delete_requested(self):
        self.delete_requested.emit(self.sale_id)

    def _on_edit_requested(self):
        self.edit_requested.emit(self.sale_id)
    
    def set_delete_button_visibility(self, is_visible):
        self.delete_sale_button.setVisible(is_visible)

    def set_edit_button_visibility(self, is_visible):
        self.edit_sale_button.setVisible(is_visible)