# dosya: utils/themed_widgets.py

from PySide6.QtWidgets import (
    QPushButton, QWidget, QGroupBox, QVBoxLayout,
    QFrame, QHBoxLayout, QLabel
)
from PySide6.QtGui import QIcon, QEnterEvent, QCursor
from PySide6.QtCore import Qt, Signal, QSize
import qtawesome as qta

class PrimaryButton(QPushButton):
    def __init__(self, text: str, icon_name: str = None, parent: QWidget = None):
        super().__init__(text, parent)
        self.setObjectName("PrimaryButton")
        if icon_name:
            self.setIcon(qta.icon(icon_name, color="white"))

class SuccessButton(QPushButton):
    def __init__(self, text: str, icon_name: str = None, parent: QWidget = None):
        super().__init__(text, parent)
        self.setObjectName("SuccessButton")
        if icon_name:
            self.setIcon(qta.icon(icon_name, color="white"))

class DangerButton(QPushButton):
    def __init__(self, text: str, icon_name: str = None, parent: QWidget = None):
        super().__init__(text, parent)
        self.setObjectName("DangerButton")
        if icon_name:
            self.setIcon(qta.icon(icon_name, color="white"))

class NeutralButton(QPushButton):
    def __init__(self, text: str, icon_name: str = None, parent: QWidget = None):
        super().__init__(text, parent)
        self.setObjectName("NeutralButton")
        if icon_name:
            self.setIcon(qta.icon(icon_name))

class OutlineButton(QPushButton):
    def __init__(self, text: str, icon_name: str = None, parent: QWidget = None):
        super().__init__(text, parent)
        self.setObjectName("OutlineButton")
        if icon_name:
            self.setIcon(qta.icon(icon_name))

class CardWidget(QGroupBox):
    def __init__(self, title: str = "", parent: QWidget = None):
        super().__init__(title, parent)
        self._content_layout = QVBoxLayout(self)
        top_margin = 25 if title else 15
        self._content_layout.setContentsMargins(15, top_margin, 15, 15)
        self._content_layout.setSpacing(15)
    
    def layout(self) -> QVBoxLayout:
        return self._content_layout

class StatCard(QFrame):
    clicked = Signal()

    def __init__(self, title: str, icon_name: str, parent=None):
        super().__init__(parent)
        self.setObjectName("StatCardWidget")
        self.setProperty("icon_name", icon_name)
        
        card_layout = QHBoxLayout(self)
        card_layout.setSpacing(15)
        
        self.icon_label = QLabel()
        self.icon_label.setObjectName("IconBackground")
        self.icon_label.setFixedSize(48, 48)
        
        icon_widget = QLabel()
        icon = qta.icon(icon_name, color="#495057")
        icon_widget.setPixmap(icon.pixmap(22, 22))
        icon_widget.setAlignment(Qt.AlignCenter)
        
        icon_layout = QHBoxLayout(self.icon_label)
        icon_layout.setContentsMargins(0,0,0,0)
        icon_layout.addWidget(icon_widget)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)
        text_layout.setAlignment(Qt.AlignCenter)
        
        self.value_label = QLabel("N/A")
        self.value_label.setObjectName("ValueLabel")
        
        title_label = QLabel(title)
        title_label.setObjectName("TitleLabel")
        
        text_layout.addWidget(self.value_label)
        text_layout.addWidget(title_label)
        
        card_layout.addWidget(self.icon_label)
        card_layout.addLayout(text_layout, 1)

    def enterEvent(self, event: QEnterEvent):
        self.setCursor(QCursor(Qt.PointingHandCursor))
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.unsetCursor()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class HubCardWidget(QFrame):
    clicked = Signal()

    def __init__(self, icon_name: str, title: str, description: str, parent=None):
        super().__init__(parent)
        self.setObjectName("HubCardWidget")
        self.setCursor(Qt.PointingHandCursor)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setAlignment(Qt.AlignCenter)

        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(f"fa5s.{icon_name}", color="#0d6efd").pixmap(QSize(32, 32)))
        icon_label.setAlignment(Qt.AlignCenter)

        title_label = QLabel(title)
        title_label.setObjectName("HubCardTitle")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)

        description_label = QLabel(description)
        description_label.setObjectName("HubCardDescription")
        description_label.setAlignment(Qt.AlignCenter)
        description_label.setWordWrap(True)

        main_layout.addWidget(icon_label)
        main_layout.addWidget(title_label)
        main_layout.addWidget(description_label)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)