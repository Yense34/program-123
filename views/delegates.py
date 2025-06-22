# dosya: views/delegates.py

import os
from PySide6.QtGui import (
    QPainter, QIntValidator, QIcon, QCursor, QPalette, QFont, QPixmap, QColor, QFontMetrics
)
from PySide6.QtWidgets import (
    QStyledItemDelegate, QStyle, QLineEdit, QStyleOptionViewItem, QStyleOptionButton
)
from PySide6.QtCore import Qt, Signal, QRect, QEvent, QSize, QModelIndex
import qtawesome as qta

class SaleDetailDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        self.initStyleOption(option, index)
        
        style = option.widget.style()
        style.drawPrimitive(QStyle.PrimitiveElement.PE_PanelItemViewItem, option, painter, option.widget)
        
        product_data = index.data(Qt.UserRole)
        product_name = product_data.get("urun_ad", "")
        quantity = product_data.get("miktar", 0)
        unit_price = product_data.get("birim_fiyat", 0.0)
        total_price = product_data.get("toplam", 0.0)
        
        content_rect = option.rect.adjusted(10, 10, -10, -10)
        
        text_color = option.palette.color(QPalette.ColorRole.Text)
        details_color = option.palette.color(QPalette.ColorRole.PlaceholderText)
        total_color = option.palette.color(QPalette.ColorRole.Highlight)
        
        font_product_name = QFont(option.font)
        font_product_name.setBold(True)
        font_product_name.setPointSize(option.font.pointSize() + 1)
        
        font_details = QFont(option.font)
        
        font_total = QFont(option.font)
        font_total.setBold(True)
        
        painter.setFont(font_product_name)
        painter.setPen(text_color)
        product_name_rect = QRect(content_rect.x(), content_rect.y(), content_rect.width() - 100, 20)
        painter.drawText(product_name_rect, Qt.AlignLeft | Qt.AlignTop, product_name)
        
        painter.setFont(font_details)
        painter.setPen(details_color)
        details_text = f"Miktar: {quantity}  x  {unit_price:,.2f} TL"
        details_rect = QRect(content_rect.x(), content_rect.y() + 25, content_rect.width(), 15)
        painter.drawText(details_rect, Qt.AlignLeft | Qt.AlignVCenter, details_text)
        
        painter.setFont(font_total)
        painter.setPen(total_color)
        total_text = f"{total_price:,.2f} TL"
        total_rect = QRect(content_rect.x(), content_rect.y(), content_rect.width(), 20)
        painter.drawText(total_rect, Qt.AlignRight | Qt.AlignTop, total_text)
        
        painter.restore()

    def sizeHint(self, option, index):
        return QSize(200, 65)

class DashboardListDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        painter.save()
        self.initStyleOption(option, index)
        style = option.widget.style()
        style.drawPrimitive(QStyle.PrimitiveElement.PE_PanelItemViewItem, option, painter, option.widget)

        main_text = index.data(Qt.UserRole).get("main_text", "")
        sub_text = index.data(Qt.UserRole).get("sub_text", "")
        is_critical = index.data(Qt.UserRole).get("is_critical", False)
        
        main_color = option.palette.color(QPalette.ColorRole.Text)
        sub_color = option.palette.color(QPalette.ColorRole.PlaceholderText)
        danger_color = QColor("#dc3545")

        font_main = QFont(option.font)
        font_main.setBold(True)
        font_sub = QFont(option.font)

        painter.setFont(font_main)
        painter.setPen(main_color)
        main_rect = option.rect.adjusted(10, 5, -10, -5)
        painter.drawText(main_rect, Qt.AlignLeft | Qt.AlignVCenter, main_text)
        
        painter.setFont(font_sub)
        painter.setPen(danger_color if is_critical else sub_color)
        sub_rect = option.rect.adjusted(10, 5, -10, -5)
        painter.drawText(sub_rect, Qt.AlignRight | Qt.AlignVCenter, sub_text)
        painter.restore()

    def sizeHint(self, option, index):
        return QSize(200, 40)

class ActionDelegate(QStyledItemDelegate):
    edit_requested = Signal(int)
    delete_requested = Signal(int)
    
    ICON_SIZE = 18
    ICON_PADDING = 8
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hover_row = -1
        self.danger_color = QColor("#dc3545")

    def paint(self, painter, option, index):
        painter.save()
        self.initStyleOption(option, index)
        style = option.widget.style()
        style.drawPrimitive(QStyle.PrimitiveElement.PE_PanelItemViewItem, option, painter, option.widget)

        y_center = option.rect.y() + (option.rect.height() - self.ICON_SIZE) // 2
        total_width = (self.ICON_SIZE * 2) + self.ICON_PADDING
        x_start = option.rect.right() - total_width - self.ICON_PADDING
        
        edit_rect = QRect(x_start, y_center, self.ICON_SIZE, self.ICON_SIZE)
        delete_rect = QRect(x_start + self.ICON_SIZE + self.ICON_PADDING, y_center, self.ICON_SIZE, self.ICON_SIZE)
        
        mouse_pos = option.widget.mapFromGlobal(QCursor.pos())
        
        is_hovering_edit = edit_rect.contains(mouse_pos) and self.hover_row == index.row()
        is_hovering_delete = delete_rect.contains(mouse_pos) and self.hover_row == index.row()

        edit_color = option.palette.color(QPalette.ColorRole.Highlight) if is_hovering_edit else option.palette.color(QPalette.ColorRole.PlaceholderText)
        delete_color = self.danger_color if is_hovering_delete else option.palette.color(QPalette.ColorRole.PlaceholderText)

        qta.icon('fa5s.pencil-alt', color=edit_color).paint(painter, edit_rect)
        qta.icon('fa5s.trash-alt', color=delete_color).paint(painter, delete_rect)

        painter.restore()

    def editorEvent(self, event, model, option, index):
        if event.type() in [QEvent.Type.MouseMove, QEvent.Type.Enter]:
            new_hover_row = index.row() if option.rect.contains(event.pos()) else -1
            if self.hover_row != new_hover_row:
                self.hover_row = new_hover_row
                option.widget.viewport().update()
            return True
        if event.type() == QEvent.Type.Leave:
            if self.hover_row != -1:
                self.hover_row = -1
                option.widget.viewport().update()
            return True
        if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.LeftButton:
            y_center = option.rect.y() + (option.rect.height() - self.ICON_SIZE) // 2
            total_width = (self.ICON_SIZE * 2) + self.ICON_PADDING
            x_start = option.rect.right() - total_width - self.ICON_PADDING
            edit_rect = QRect(x_start, y_center, self.ICON_SIZE, self.ICON_SIZE)
            delete_rect = QRect(x_start + self.ICON_SIZE + self.ICON_PADDING, y_center, self.ICON_SIZE, self.ICON_SIZE)
            if edit_rect.contains(event.pos()):
                self.edit_requested.emit(index.row())
                return True
            if delete_rect.contains(event.pos()):
                self.delete_requested.emit(index.row())
                return True
        return super().editorEvent(event, model, option, index)

    def sizeHint(self, option, index):
        return QSize((self.ICON_SIZE * 2) + (self.ICON_PADDING * 3), 40)

class CartDeleteDelegate(QStyledItemDelegate):
    delete_requested = Signal(int)
    ICON_SIZE = 18
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hover_row = -1
        self.danger_color = QColor("#dc3545")

    def paint(self, painter, option, index):
        self.initStyleOption(option, index)
        style = option.widget.style()
        style.drawPrimitive(QStyle.PrimitiveElement.PE_PanelItemViewItem, option, painter, option.widget)
        
        x_center = option.rect.x() + (option.rect.width() - self.ICON_SIZE) / 2
        y_center = option.rect.y() + (option.rect.height() - self.ICON_SIZE) / 2
        icon_rect = QRect(int(x_center), int(y_center), self.ICON_SIZE, self.ICON_SIZE)
        
        color = self.danger_color if self.hover_row == index.row() else option.palette.color(QPalette.ColorRole.PlaceholderText)
        qta.icon('fa5s.times-circle', color=color).paint(painter, icon_rect)

    def editorEvent(self, event, model, option, index):
        if event.type() in [QEvent.Type.MouseMove, QEvent.Type.Enter]:
            is_hovering = option.rect.contains(event.pos())
            if (self.hover_row == index.row()) != is_hovering:
                self.hover_row = index.row() if is_hovering else -1
                option.widget.viewport().update()
            return True
        if event.type() == QEvent.Type.Leave:
            if self.hover_row != -1:
                self.hover_row = -1
                option.widget.viewport().update()
            return True
        if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.LeftButton:
            if option.rect.contains(event.pos()):
                self.delete_requested.emit(index.row())
                return True
        return super().editorEvent(event, model, option, index)

    def sizeHint(self, option, index):
        return QSize(40, 40)

class GenericListDelegate(QStyledItemDelegate):
    edit_requested = Signal(int)
    delete_requested = Signal(int)
    ICON_SIZE = 16
    ICON_PADDING = 10
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.thumbnail_size = 50
        self.padding = 10
        self.action_rects = {}
        self.danger_color = QColor("#dc3545")

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        self.initStyleOption(option, index)
        
        style = option.widget.style()
        style.drawPrimitive(QStyle.PrimitiveElement.PE_PanelItemViewItem, option, painter, option.widget)
        
        item_data = index.data(Qt.UserRole)
        if not isinstance(item_data, dict):
            painter.restore()
            return
            
        content_rect = option.rect.adjusted(self.padding, self.padding, -self.padding, -self.padding)
        
        title_color = option.palette.color(QPalette.ColorRole.Text)
        subtitle_color = option.palette.color(QPalette.ColorRole.PlaceholderText)
        icon_color = option.palette.color(QPalette.ColorRole.PlaceholderText)
        icon_hover_color_edit = option.palette.color(QPalette.ColorRole.Highlight)
        
        thumb_rect = QRect(content_rect.x(), content_rect.y(), self.thumbnail_size, self.thumbnail_size)
        pixmap = self._get_pixmap(item_data, icon_color)
        if pixmap:
            painter.drawPixmap(thumb_rect.x(), thumb_rect.y() + (content_rect.height() - self.thumbnail_size) // 2, pixmap)
        
        text_x = thumb_rect.right() + self.padding
        actions = item_data.get('actions', [])
        actions_width = self.padding + (len(actions) * (self.ICON_SIZE + self.ICON_PADDING))
        text_area_width = content_rect.width() - text_x - actions_width
        
        font_title = QFont(option.font)
        font_title.setBold(True)
        font_subtitle = QFont(option.font)
        
        title = item_data.get("title", "")
        painter.setFont(font_title)
        painter.setPen(title_color)
        title_rect = QRect(text_x, content_rect.y(), text_area_width, content_rect.height() // 2)
        painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignBottom, title)
        
        subtitle = item_data.get("subtitle", "")
        painter.setFont(font_subtitle)
        painter.setPen(subtitle_color)
        subtitle_rect = QRect(text_x, title_rect.bottom() + 2, text_area_width, content_rect.height() // 2)
        painter.drawText(subtitle_rect, Qt.AlignLeft | Qt.AlignTop, subtitle)

        current_x = option.rect.right() - self.padding
        self.action_rects[index.row()] = {}
        mouse_pos = option.widget.mapFromGlobal(QCursor.pos())
        
        for action in reversed(actions):
            current_x -= self.ICON_SIZE
            action_rect = QRect(current_x, option.rect.center().y() - self.ICON_SIZE // 2, self.ICON_SIZE, self.ICON_SIZE)
            self.action_rects[index.row()][action] = action_rect
            
            is_hovering = action_rect.contains(mouse_pos)
            color = icon_color
            if is_hovering:
                color = icon_hover_color_edit if action == 'edit' else self.danger_color
            
            icon_name = 'fa5s.pencil-alt' if action == 'edit' else 'fa5s.trash-alt'
            qta.icon(icon_name, color=color).paint(painter, action_rect)
            current_x -= self.ICON_PADDING

        painter.restore()
        
    def _get_pixmap(self, item_data, color):
        if (thumb_path := item_data.get("thumbnail_path")) and os.path.exists(thumb_path):
            return QPixmap(thumb_path).scaled(self.thumbnail_size, self.thumbnail_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        elif thumb_icon := item_data.get("thumbnail_icon"):
            return qta.icon(thumb_icon, color=color).pixmap(QSize(self.thumbnail_size, self.thumbnail_size))
        return None

    def sizeHint(self, option, index):
        return QSize(200, self.thumbnail_size + self.padding * 2)

    def editorEvent(self, event, model, option, index):
        if event.type() in [QEvent.Type.MouseMove, QEvent.Type.Enter, QEvent.Type.Leave]:
            option.widget.viewport().update()
        
        if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.LeftButton:
            if index.row() in self.action_rects:
                for action, rect in self.action_rects[index.row()].items():
                    if rect.contains(event.pos()):
                        item_id = index.data(Qt.UserRole).get("id")
                        if action == 'edit': self.edit_requested.emit(item_id)
                        elif action == 'delete': self.delete_requested.emit(item_id)
                        return True
        return super().editorEvent(event, model, option, index)

class CustomerListDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        self.initStyleOption(option, index)
        
        style = option.widget.style()
        
        item_data = index.data(Qt.UserRole)
        if not item_data:
            style.drawControl(QStyle.ControlElement.CE_ItemViewItem, option, painter)
            painter.restore()
            return
        
        option.text = ""
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, option, painter)
        
        check_option = QStyleOptionButton()
        check_option.rect = style.subElementRect(QStyle.SubElement.SE_ItemViewItemCheckIndicator, option, option.widget)
        check_option.state = QStyle.State_Enabled
        if option.checkState == Qt.Checked:
            check_option.state |= QStyle.State_On
        else:
            check_option.state |= QStyle.State_Off
        style.drawControl(QStyle.ControlElement.CE_CheckBox, check_option, painter)
        
        full_name = f"{item_data.get('ad', '')} {item_data.get('soyad', '')}"
        phone = item_data.get('telefon', '')
        
        name_color = option.palette.color(QPalette.ColorRole.Text)
        contact_color = option.palette.color(QPalette.ColorRole.PlaceholderText)
        
        text_rect = option.rect.adjusted(check_option.rect.width() + 15, 0, -10, 0)
        
        font_name = QFont(option.font)
        font_name.setBold(True)
        font_contact = QFont(option.font)
        font_contact.setPointSize(option.font.pointSize() - 1)
        
        fm = QFontMetrics(font_contact)
        phone_width = fm.horizontalAdvance(phone) if phone else 0
        icon_size = 14
        icon_padding = 5
        text_padding = 10
        
        phone_part_width = 0
        if phone:
            phone_part_width = icon_size + icon_padding + phone_width + text_padding

        painter.setFont(font_name)
        painter.setPen(name_color)
        available_width_for_name = text_rect.width() - phone_part_width
        elided_name = QFontMetrics(font_name).elidedText(full_name, Qt.ElideRight, available_width_for_name)
        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, elided_name)
        
        if phone:
            painter.setFont(font_contact)
            painter.setPen(contact_color)
            
            phone_text_x = text_rect.right() - phone_width
            phone_icon_x = phone_text_x - icon_padding - icon_size
            
            phone_text_rect = QRect(phone_text_x, text_rect.y(), phone_width, text_rect.height())
            painter.drawText(phone_text_rect, Qt.AlignLeft | Qt.AlignVCenter, phone)
            
            phone_icon_rect = QRect(phone_icon_x, text_rect.center().y() - icon_size // 2, icon_size, icon_size)
            qta.icon('fa5s.phone-alt', color=contact_color).paint(painter, phone_icon_rect)

        painter.restore()

    def sizeHint(self, option, index):
        return QSize(200, 50)

class CommunicationListDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        painter.save()
        self.initStyleOption(option, index)
        
        style = option.widget.style()
        
        item_data = index.data(Qt.UserRole)
        if not item_data:
            style.drawControl(QStyle.ControlElement.CE_ItemViewItem, option, painter)
            painter.restore()
            return
        
        option.text = ""
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, option, painter)
        
        check_option = QStyleOptionButton()
        check_option.rect = style.subElementRect(QStyle.SubElement.SE_ItemViewItemCheckIndicator, option, option.widget)
        check_option.state = QStyle.State_Enabled
        if option.checkState == Qt.Checked:
            check_option.state |= QStyle.State_On
        else:
            check_option.state |= QStyle.State_Off
        style.drawControl(QStyle.ControlElement.CE_CheckBox, check_option, painter)
        
        full_name = f"{item_data.get('ad', '')} {item_data.get('soyad', '')}"
        name_color = option.palette.color(QPalette.ColorRole.Text)
        
        text_rect = option.rect.adjusted(check_option.rect.width() + 15, 0, -10, 0)
        
        font_name = QFont(option.font)
        font_name.setBold(True)
        
        painter.setFont(font_name)
        painter.setPen(name_color)
        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, full_name)

        painter.restore()

    def sizeHint(self, option, index):
        return QSize(200, 40)