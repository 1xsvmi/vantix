"""Base module class for all VANTIX panels."""
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore    import QTimer

class BaseModule(QWidget):
    REFRESH_MS = 2000

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 16, 16, 16)
        self._layout.setSpacing(12)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        raise NotImplementedError

    def _refresh(self):
        raise NotImplementedError

    def start(self):
        self._timer.start(self.REFRESH_MS)

    def stop(self):
        self._timer.stop()
