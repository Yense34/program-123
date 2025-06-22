# dosya: utils/signals.py

from PySide6.QtCore import QObject, Signal

class AppSignals(QObject):
    stock_updated = Signal()
    customers_updated = Signal()
    products_updated = Signal()
    sales_updated = Signal()
    
    status_message_updated = Signal(str, int)
    show_sale_detail_requested = Signal(int)
    load_sale_for_editing_requested = Signal(int)
    page_change_requested = Signal(str)

    app_closed = Signal()

app_signals = AppSignals()