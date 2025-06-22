# dosya: utils/shortcut_manager.py

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QWidget
from .shortcuts import SHORTCUTS

class ShortcutManager:
    _instance = None

    def __new__(cls, parent=None):
        if cls._instance is None:
            cls._instance = super(ShortcutManager, cls).__new__(cls)
            cls._instance.actions = {}
            cls._instance.parent = parent
            cls._instance._create_actions()
        return cls._instance

    def _create_actions(self):
        for name, props in SHORTCUTS.items():
            action = QAction(props.get("text", name), self.parent)
            action.setShortcut(QKeySequence(props["keys"]))
            action.setShortcutContext(Qt.WindowShortcut)
            self.actions[name] = action

    def get_action(self, name: str) -> QAction | None:
        return self.actions.get(name)

    def connect(self, name: str, slot):
        if action := self.get_action(name):
            action.triggered.connect(slot)
            return action
        return None

    def add_to_widget(self, name: str, widget: QWidget):
        if action := self.get_action(name):
            widget.addAction(action)

shortcut_manager = None

def initialize_shortcut_manager(parent=None):
    global shortcut_manager
    if shortcut_manager is None:
        shortcut_manager = ShortcutManager(parent)