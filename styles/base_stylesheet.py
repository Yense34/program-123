# dosya: styles/base_stylesheet.py

BASE_STYLESHEET = """
/* =========================================================================
   GENEL VE PENCERE
   ========================================================================= */
QWidget {
    font-family: "Segoe UI", "Verdana", Arial, sans-serif;
    color: #495057;
    font-size: 14px;
}
QMainWindow, QDialog { 
    background-color: #F4F6F8;
}
QWidget#ContentFrame {
    background-color: #FFFFFF;
}
QStackedWidget > QWidget {
    background-color: transparent;
}
QStatusBar {
    background-color: #FFFFFF; 
    border-top: 1px solid #E9ECEF;
    color: #495057; 
    font-weight: 500; 
    padding: 6px;
}
QSplitter::handle {
    background-color: #F4F6F8;
}
QSplitter::handle:horizontal {
    width: 1px;
}

/* =========================================================================
   SOL NAVİGASYON MENÜSÜ
   ========================================================================= */
QWidget#LeftNavBar {
    background-color: #F4F6F8;
    border-right: 1px solid #DEE2E6;
}
QPushButton#NavButton {
    background-color: transparent;
    border: none;
    text-align: left;
    padding: 12px 20px;
    margin: 4px 10px;
    border-radius: 8px;
    font-weight: 600;
    color: #495057;
}
QPushButton#NavButton:hover {
    background-color: #E9ECEF;
}
QPushButton#NavButton:checked {
    background-color: #0d6efd;
    color: white;
}
QFrame#NavSeparator {
    background-color: #DEE2E6;
    height: 1px;
    border: none;
    margin: 8px 15px;
}

/* =========================================================================
   ANA SAYFA İSTATİSTİK KARTLARI
   ========================================================================= */
QFrame#StatCardWidget {
    background-color: #FFFFFF;
    border-radius: 12px;
    border: 1px solid #E9ECEF;
    padding: 20px;
}
QFrame#StatCardWidget QLabel {
    background-color: transparent;
}
QLabel#IconBackground {
    border-radius: 25px; /* Yüksekliğin/Genişliğin yarısı */
}
QFrame#StatCardWidget[icon_name="fa5s.users"] QLabel#IconBackground { background-color: #E6F2FF; }
QFrame#StatCardWidget[icon_name="fa5s.box-open"] QLabel#IconBackground { background-color: #FFF4E6; }
QFrame#StatCardWidget[icon_name="fa5s.chart-line"] QLabel#IconBackground { background-color: #E6F8F0; }
QFrame#StatCardWidget[icon_name="fa5s.sms"] QLabel#IconBackground { background-color: #F3E8FD; }

QFrame#StatCardWidget[icon_name="fa5s.users"] .QLabel { color: #007BFF; }
QFrame#StatCardWidget[icon_name="fa5s.box-open"] .QLabel { color: #FF9500; }
QFrame#StatCardWidget[icon_name="fa5s.chart-line"] .QLabel { color: #28A745; }
QFrame#StatCardWidget[icon_name="fa5s.sms"] .QLabel { color: #6F42C1; }

QLabel#ValueLabel {
    font-size: 24px;
    font-weight: 600;
    color: #212529;
}
QLabel#TitleLabel {
    font-size: 11px;
    font-weight: 600;
    color: #6C757D;
    text-transform: uppercase;
}

/* =========================================================================
   GENEL KARTLAR, BUTONLAR VE FORMLAR
   ========================================================================= */
QGroupBox {
    border: 1px solid #E9ECEF; 
    border-radius: 12px;
    margin-top: 15px; 
    background-color: #FFFFFF;
}
QGroupBox::title {
    subcontrol-origin: margin; 
    subcontrol-position: top left;
    padding: 4px 12px; 
    margin-left: 15px; 
    font-size: 12px;
    font-weight: 600; 
    color: #495057; 
    background-color: #F8F9FA;
    border: 1px solid #E9ECEF;
    border-bottom: none;
    border-radius: 8px;
}
QLineEdit, QSpinBox, QDateEdit, QTextEdit, QComboBox {
    background-color: #FFFFFF; 
    border: 1px solid #CED4DA;
    border-radius: 8px; 
    padding: 8px 12px; 
    min-height: 22px; 
}
QLineEdit:focus, QSpinBox:focus, QDateEdit:focus, QTextEdit:focus, QComboBox:focus {
    border-color: #0d6efd;
}
QPushButton {
    min-height: 40px;
    padding: 0 16px;
    border-radius: 8px;
    font-weight: 500;
}
QPushButton#PrimaryButton {
    background-color: #0d6efd;
    color: white;
    border: none;
}
QPushButton#PrimaryButton:hover {
    background-color: #0b5ed7;
}
QPushButton#SuccessButton {
    background-color: #28a745;
    color: white;
    border: none;
}
QPushButton#SuccessButton:hover {
    background-color: #218838;
}
QPushButton#DangerButton {
    background-color: #dc3545;
    color: white;
    border: none;
}
QPushButton#DangerButton:hover {
    background-color: #bb2d3b;
}
QPushButton#NeutralButton {
    background-color: #6c757d;
    color: white;
    border: none;
}
QPushButton#NeutralButton:hover {
    background-color: #5a6268;
}
QPushButton#OutlineButton {
    background-color: #FFFFFF;
    color: #495057;
    border: 1px solid #CED4DA;
}
QPushButton#OutlineButton:hover {
    background-color: #F8F9FA;
}
QPushButton:disabled { 
    background-color: #E9ECEF; 
    color: #ADB5BD; 
    border: 1px solid #E9ECEF;
}
QFrame#HubCardWidget {
    background-color: #FFFFFF;
    border: 1px solid #E9ECEF;
    border-radius: 12px;
    padding: 25px;
    min-height: 150px;
}
QFrame#HubCardWidget:hover {
    border-color: #0d6efd;
    background-color: #F8F9FA;
}
QLabel#HubCardTitle {
    font-size: 16px;
    font-weight: 600;
    color: #343a40;
}
QLabel#HubCardDescription {
    color: #6c757d;
}

/* =========================================================================
   TABLOLAR, LİSTELER VE SEKMELER
   ========================================================================= */
QTableView, QListWidget#ModernList, QListWidget {
    background-color: #FFFFFF; 
    border: 1px solid #DEE2E6;
    border-radius: 8px; 
    gridline-color: #E9ECEF;
    selection-background-color: #E6F2FF;
    selection-color: #0056b3;
}
QHeaderView::section {
    background-color: #F8F9FA; 
    border: none;
    border-bottom: 1px solid #DEE2E6; 
    padding: 10px;
    font-weight: 600; 
    font-size: 12px;
    color: #495057;
}
QTabWidget::pane {
    border: none;
    background-color: transparent; 
}
QTabBar::tab {
    background-color: transparent; 
    color: #6C757D; 
    border: none;
    border-bottom: 3px solid transparent;
    padding: 10px 15px; 
    font-weight: 600;
    margin-right: 5px;
}
QTabBar::tab:hover {
    color: #212529;
}
QTabBar::tab:selected {
    color: #0d6efd;
    border-bottom: 3px solid #0d6efd;
}

/* =========================================================================
   ÖZEL DURUM ETİKETLERİ
   ========================================================================= */
QLabel#ErrorLabel {
    color: #dc3545;
    font-weight: 600;
}
QLabel#SubtleInfoLabel, QLabel#WarningTextLabel {
    color: #6C757D;
    font-size: 12px;
    font-style: italic;
}
QLabel#BalanceLabel {
    font-size: 22px;
    font-weight: 700;
}
QLabel#BalanceLabel[balanceState="negative"] {
    color: #dc3545;
}
QLabel#BalanceLabel[balanceState="positive"] {
    color: #28a745;
}
QLabel#BalanceLabel[balanceState="neutral"] {
    color: #495057;
}
QLabel#ImagePreview {
    background-color: #F8F9FA;
    border: 2px dashed #DEE2E6;
    border-radius: 8px;
}
"""