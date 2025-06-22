from PySide6.QtCore import QAbstractTableModel, Qt, Signal

class GenericTableModel(QAbstractTableModel):
    header_check_state_changed = Signal()

    def __init__(self, headers, column_keys, parent=None, checkable=False):
        super().__init__(parent)
        self.headers = headers
        self.column_keys = column_keys
        self.table_data = []
        self.is_checkable = checkable
        if self.is_checkable:
            self.checked_states = []
            self.header_checked_state = Qt.Unchecked

    def rowCount(self, parent=None):
        return len(self.table_data)

    def columnCount(self, parent=None):
        return len(self.headers)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section < len(self.headers):
                return self.headers[section]
        if self.is_checkable and section == 0 and role == Qt.CheckStateRole and orientation == Qt.Horizontal:
            return self.header_checked_state
        return None
    
    def setHeaderData(self, section, orientation, value, role=Qt.EditRole):
        if self.is_checkable and section == 0 and role == Qt.CheckStateRole and orientation == Qt.Horizontal:
            self.header_checked_state = Qt.CheckState(value)
            self.set_all_checked(value == Qt.Checked)
            self.headerDataChanged.emit(orientation, section, section)
            return True
        return super().setHeaderData(section, orientation, value, role)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.UserRole:
            return self.table_data[index.row()]
            
        if self.is_checkable and index.column() == 0 and role == Qt.CheckStateRole:
            return self.checked_states[index.row()]
        
        row_data = self.table_data[index.row()]
        col_offset = 1 if self.is_checkable else 0
        
        if role == Qt.EditRole:
            column_key = self.column_keys[index.column() - col_offset]
            return row_data.get(column_key, "")

        if role == Qt.DisplayRole:
            try:
                column_key = self.column_keys[index.column() - col_offset]
                value = row_data.get(column_key)
                
                if value is None: return ""
                if isinstance(value, float): return f"{value:,.2f}"
                if isinstance(value, str) and len(value) > 10 and ' ' in value:
                    try:
                        dt_obj = Qt.QDateTime.fromString(value, "yyyy-MM-dd HH:mm:ss")
                        if dt_obj.isValid(): return dt_obj.toString("dd.MM.yyyy HH:mm")
                    except Exception: pass
                
                return str(value)
            except (IndexError, KeyError):
                return None
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False
        
        if self.is_checkable and role == Qt.CheckStateRole and index.column() == 0:
            self.checked_states[index.row()] = Qt.CheckState(value)
            self.dataChanged.emit(index, index, [role])
            self.header_check_state_changed.emit()
            return True
        
        if role == Qt.EditRole:
            return True

        return False

    def flags(self, index):
        default_flags = super().flags(index)
        if self.is_checkable and index.column() == 0:
            return default_flags | Qt.ItemIsUserCheckable
        
        return default_flags

    def update_data(self, new_data):
        self.beginResetModel()
        if new_data and hasattr(new_data[0], 'keys'):
             self.table_data = [dict(row) for row in new_data]
        else:
             self.table_data = new_data
        
        if self.is_checkable:
            self.checked_states = [Qt.Unchecked] * len(self.table_data)
            self.header_checked_state = Qt.Unchecked
             
        self.endResetModel()
    
    def get_item_id(self, index):
        if not index.isValid() or index.row() >= len(self.table_data):
            return None
        return self.table_data[index.row()].get('id')

    def get_checked_items(self):
        if not self.is_checkable:
            return []
        return [self.table_data[i] for i, state in enumerate(self.checked_states) if state == Qt.Checked]

    def set_all_checked(self, checked: bool):
        if not self.is_checkable or not self.table_data:
            return
        
        new_state = Qt.Checked if checked else Qt.Unchecked
        self.checked_states = [new_state] * len(self.table_data)
        
        top_left_index = self.index(0, 0)
        bottom_right_index = self.index(self.rowCount() - 1, 0)
        self.dataChanged.emit(top_left_index, bottom_right_index, [Qt.CheckStateRole])
        self.header_check_state_changed.emit()