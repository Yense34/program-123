from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QFrame,
    QTreeView, QHeaderView, QStyleOptionButton, QStyle
)
from PySide6.QtCore import Signal, Qt, QSize, QEvent, QRect
from PySide6.QtGui import QIcon, QMouseEvent
import qtawesome as qta
from services.session_manager import session

class NavButton(QPushButton):
    def __init__(self, text, icon_name, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setIconSize(QSize(18, 18))
        self.setObjectName("NavButton")
        self.setIcon(qta.icon(icon_name))

class LeftNavBar(QWidget):
    page_requested = Signal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LeftNavBar")
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)
        self.layout.setContentsMargins(0, 15, 0, 15)
        self.layout.setSpacing(4)
        self.buttons = {}
        
        menu_items = [
            {"name": "dashboard", "text": "Ana Sayfa", "icon": "fa5s.home"},
            {"name": "sales", "text": "Yeni Satış", "icon": "fa5s.shopping-cart"},
            {"name": "products", "text": "Ürünler", "icon": "fa5s.box-open"},
            {"name": "customers", "text": "Müşteriler", "icon": "fa5s.users"},
            {"name": "separator"},
            {"name": "sale_history", "text": "Satış Geçmişi", "icon": "fa5s.history"},
            {"name": "reports", "text": "Raporlar", "icon": "fa5s.chart-pie"},
            {"name": "bulk_communication", "text": "Toplu İletişim", "icon": "fa5s.paper-plane"},
        ]
        
        for item in menu_items:
            if item.get("name") == "separator": 
                self.add_separator()
            else: 
                self._add_nav_button(item)
        
        self.layout.addStretch()
        self.add_separator()
        self._add_nav_button({"name": "settings", "text": "Ayarlar", "icon": "fa5s.cog"})

    def _add_nav_button(self, item_info):
        name = item_info["name"]
        button = NavButton(f"   {item_info['text']}", item_info['icon'])
        button.clicked.connect(lambda checked, n=name: self.page_requested.emit(n))
        self.buttons[name] = button
        self.layout.addWidget(button)

    def add_separator(self):
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setObjectName("NavSeparator")
        self.layout.addWidget(separator)
        
    def set_active_button(self, page_name):
        for name, button in self.buttons.items():
            button.setChecked(name == page_name)
    
    def update_visibility_for_session(self, current_session):
        if 'settings' in self.buttons: 
            self.buttons['settings'].setVisible(current_session.has_permission('settings:view'))
        if 'reports' in self.buttons: 
            self.buttons['reports'].setVisible(current_session.has_permission('reports:view'))

class PageHeader(QWidget):
    def __init__(self, title: str, icon_name: str = None, parent=None):
        super().__init__(parent)
        self.setObjectName("PageHeaderWidget")
        self.setFixedHeight(60)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(15, 0, 15, 0)
        self.layout.setSpacing(12)
        if icon_name:
            icon_label = QLabel()
            icon = qta.icon(f"fa5s.{icon_name}", color_off="#5E6C84")
            icon_label.setPixmap(icon.pixmap(QSize(24, 24)))
            self.layout.addWidget(icon_label)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("PageTitleLabel")
        self.layout.addWidget(self.title_label)
        self.layout.addStretch()
        
    def add_action_button(self, button: QPushButton): 
        self.layout.addWidget(button)
        
class PopupSearchWidget(QWidget):
    item_selected = Signal(object) 
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setFocusPolicy(Qt.NoFocus)
        self.setObjectName("PopupSearchWidget")
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(1, 1, 1, 1)
        self.main_layout.setSpacing(0)
        self.tree_view = QTreeView(self)
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setEditTriggers(QTreeView.NoEditTriggers)
        self.tree_view.setSelectionBehavior(QTreeView.SelectRows)
        self.tree_view.setFocusPolicy(Qt.ClickFocus)
        self.setMaximumHeight(250)
        self.main_layout.addWidget(self.tree_view)
        self.tree_view.hide()
        self.tree_view.clicked.connect(self._on_item_clicked)
        self.tree_view.activated.connect(self._on_item_clicked)
        if self.parent(): self.parent().installEventFilter(self) 
        
    def setModel(self, model): 
        self.tree_view.setModel(model)
        
    def _on_item_clicked(self, index):
        if index.isValid():
            item_data = index.data(Qt.UserRole)
            if isinstance(item_data, dict) and not item_data.get('is_group', False):
                self.item_selected.emit(item_data)
                self.hide_popup()
                
    def show_popup(self, relative_to_widget: QWidget):
        if self.tree_view.model() and self.tree_view.model().rowCount() > 0:
            global_pos = relative_to_widget.mapToGlobal(relative_to_widget.rect().bottomLeft())
            self.setFixedWidth(relative_to_widget.width())
            self.move(global_pos.x(), global_pos.y())
            self.tree_view.show()
            self.show()
        else: 
            self.hide_popup()
            
    def hide_popup(self):
        self.tree_view.hide()
        self.hide()
        
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            if not self.geometry().contains(event.globalPos()): 
                self.hide_popup()
        elif event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key_Escape: 
                self.hide_popup()
            elif event.key() == Qt.Key_Down:
                if self.isVisible() and self.tree_view.model() and self.tree_view.model().rowCount() > 0:
                    self.tree_view.setFocus()
                    current = self.tree_view.currentIndex()
                    if not current.isValid(): 
                        self.tree_view.setCurrentIndex(self.tree_view.model().index(0, 0))
                    return True
        return super().eventFilter(obj, event)
        
    def keyPressEvent(self, event):
        if event.key() in [Qt.Key_Return, Qt.Key_Enter]:
            if selected_indexes := self.tree_view.selectedIndexes(): 
                self._on_item_clicked(selected_indexes[0])
            self.hide_popup()
        elif event.key() == Qt.Key_Escape: 
            self.hide_popup()
        else: 
            super().keyPressEvent(event)

class CheckableHeaderView(QHeaderView):
    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent)
        self.setSectionsClickable(True)

    def paintSection(self, painter, rect, logicalIndex):
        painter.save()
        super().paintSection(painter, rect, logicalIndex)
        painter.restore()

        if logicalIndex == 0:
            option = QStyleOptionButton()
            option.rect = self.get_checkbox_rect(rect)
            check_state = self.model().headerData(logicalIndex, Qt.Horizontal, Qt.CheckStateRole)
            if check_state == Qt.Checked:
                option.state = QStyle.State_On
            else:
                option.state = QStyle.State_Off
            
            self.style().drawControl(QStyle.ControlElement.CE_CheckBox, option, painter)

    def mousePressEvent(self, event: QMouseEvent):
        if self.logicalIndexAt(event.pos()) == 0:
            if self.get_checkbox_rect(self.sectionViewportPosition(0)).contains(event.pos()):
                current_state = self.model().headerData(0, Qt.Horizontal, Qt.CheckStateRole)
                new_state = Qt.Checked if current_state == Qt.Unchecked else Qt.Unchecked
                self.model().setHeaderData(0, Qt.Horizontal, new_state, Qt.CheckStateRole)
                return
        super().mousePressEvent(event)

    def get_checkbox_rect(self, section_rect):
        checkbox_style = QStyleOptionButton()
        checkbox_rect = self.style().subElementRect(QStyle.SubElement.SE_CheckBoxIndicator, checkbox_style)
        
        checkbox_pos_x = section_rect.x() + 5
        checkbox_pos_y = section_rect.y() + (section_rect.height() - checkbox_rect.height()) // 2
        
        return QRect(checkbox_pos_x, checkbox_pos_y, checkbox_rect.width(), checkbox_rect.height())