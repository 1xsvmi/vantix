"""Animated stacked widget with cross-fade transition."""
from PyQt6.QtWidgets import QStackedWidget
from PyQt6.QtCore    import QPropertyAnimation, QEasingCurve, pyqtProperty, QByteArray
from PyQt6.QtGui     import QPainter, QColor

class AnimatedStackedWidget(QStackedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._opacity = 1.0
        self._anim    = QPropertyAnimation(self, QByteArray(b"opacity"))
        self._anim.setDuration(250)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

    def setCurrentIndex(self, idx: int):
        if idx == self.currentIndex():
            return
        self._anim.stop()
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.finished.connect(lambda: self._switch(idx))
        self._anim.start()

    def _switch(self, idx: int):
        try: self._anim.finished.disconnect()
        except TypeError: pass
        super().setCurrentIndex(idx)
        self._anim2 = QPropertyAnimation(self, QByteArray(b"opacity"))
        self._anim2.setDuration(250)
        self._anim2.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._anim2.setStartValue(0.0)
        self._anim2.setEndValue(1.0)
        self._anim2.start()

    @pyqtProperty(float)
    def opacity(self):
        return self._opacity

    @opacity.setter
    def opacity(self, value: float):
        self._opacity = value
        self.setWindowOpacity(value) if self.isWindow() else self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setOpacity(self._opacity)
        super().paintEvent(event)
        painter.end()
