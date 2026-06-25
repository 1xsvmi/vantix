"""Overview Dashboard – CPU, RAM, Network."""
import collections
from PyQt6.QtWidgets  import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QFrame, QSizePolicy, QGridLayout)
from PyQt6.QtCore     import QTimer, Qt
from PyQt6.QtGui      import QPainter, QColor, QPen, QBrush, QLinearGradient, QFont
from app.utils.system_monitor import get_cpu_percent, get_ram, get_net_speed
import psutil

CYAN   = QColor("#00F5FF")
PURPLE = QColor("#7B2FFF")
GREEN  = QColor("#00FF88")
WARN   = QColor("#FFB300")
DANGER = QColor("#FF3232")
BG     = QColor("#0d0d18")
CARD   = QColor("#13131f")
BORDER = QColor("#1e1e30")

class SparkChart(QWidget):
    def __init__(self, color: QColor, max_val=100, parent=None):
        super().__init__(parent)
        self._color  = color
        self._max    = max_val
        self._data   = collections.deque([0.0]*60, maxlen=60)
        self.setMinimumHeight(80)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def push(self, val: float):
        self._data.append(float(val))
        self.update()

    def paintEvent(self, e):
        p    = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, CARD)
        if len(self._data) < 2:
            return
        pts = list(self._data)
        n   = len(pts)
        step = w / (n - 1)

        # gradient fill
        poly_x = [i * step for i in range(n)]
        poly_y = [h - (v / self._max) * (h - 4) for v in pts]
        grad = QLinearGradient(0, 0, 0, h)
        c1 = QColor(self._color); c1.setAlpha(80)
        c2 = QColor(self._color); c2.setAlpha(0)
        grad.setColorAt(0, c1); grad.setColorAt(1, c2)
        from PyQt6.QtGui import QPolygonF
        from PyQt6.QtCore import QPointF
        poly = QPolygonF([QPointF(poly_x[i], poly_y[i]) for i in range(n)])
        poly.append(QPointF(poly_x[-1], h))
        poly.append(QPointF(0, h))
        p.setBrush(QBrush(grad)); p.setPen(Qt.PenStyle.NoPen)
        p.drawPolygon(poly)

        # line
        pen = QPen(self._color, 2)
        p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
        from PyQt6.QtGui import QPainterPath
        path = QPainterPath()
        path.moveTo(poly_x[0], poly_y[0])
        for i in range(1, n):
            path.lineTo(poly_x[i], poly_y[i])
        p.drawPath(path)
        p.end()

class StatCard(QFrame):
    def __init__(self, title: str, color: QColor, max_val=100, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            StatCard {{
                background: #13131f;
                border: 1px solid #1e1e30;
                border-radius: 10px;
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(6)

        hdr = QHBoxLayout()
        self._title_lbl = QLabel(title)
        self._title_lbl.setStyleSheet("color: #7a7a9a; font-size: 12px; font-weight: 600;")
        self._val_lbl   = QLabel("0%")
        self._val_lbl.setStyleSheet(f"color: {color.name()}; font-size: 22px; font-weight: 700;")
        hdr.addWidget(self._title_lbl)
        hdr.addStretch()
        hdr.addWidget(self._val_lbl)
        lay.addLayout(hdr)

        self._chart = SparkChart(color, max_val)
        lay.addWidget(self._chart)

    def update_val(self, val, label: str):
        self._val_lbl.setText(label)
        self._chart.push(val)

class OverviewDashboard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: #0a0a10;")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(16)

        title = QLabel("OVERVIEW DASHBOARD")
        title.setStyleSheet("color: #00F5FF; font-size: 18px; font-weight: 700; letter-spacing: 2px;")
        lay.addWidget(title)

        grid = QGridLayout(); grid.setSpacing(16)
        self._cpu_card  = StatCard("CPU USAGE", CYAN)
        self._ram_card  = StatCard("RAM USAGE", PURPLE)
        self._up_card   = StatCard("UPLOAD",    GREEN, max_val=10000)
        self._dn_card   = StatCard("DOWNLOAD",  WARN,  max_val=10000)
        grid.addWidget(self._cpu_card, 0, 0)
        grid.addWidget(self._ram_card, 0, 1)
        grid.addWidget(self._up_card,  1, 0)
        grid.addWidget(self._dn_card,  1, 1)
        lay.addLayout(grid)

        # Bottom stats bar
        stats = QHBoxLayout()
        self._proc_lbl = self._make_stat("PROCESSES", "0")
        self._disk_lbl = self._make_stat("DISK READ",  "0 KB/s")
        self._conn_lbl = self._make_stat("CONNECTIONS","0")
        for w in [self._proc_lbl, self._disk_lbl, self._conn_lbl]:
            stats.addWidget(w)
        lay.addLayout(stats)
        lay.addStretch()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(1000)
        self._refresh()

    def _make_stat(self, label, val):
        f = QFrame(); f.setStyleSheet("background:#13131f;border:1px solid #1e1e30;border-radius:8px;")
        v = QVBoxLayout(f); v.setContentsMargins(16, 12, 16, 12)
        l1 = QLabel(label); l1.setStyleSheet("color:#7a7a9a;font-size:11px;font-weight:600;")
        l2 = QLabel(val);   l2.setStyleSheet("color:#ffffff;font-size:18px;font-weight:700;")
        l2.setObjectName("val")
        v.addWidget(l1); v.addWidget(l2)
        return f

    def _refresh(self):
        cpu = get_cpu_percent()
        ram = get_ram()
        net = get_net_speed()
        self._cpu_card.update_val(cpu, f"{cpu:.1f}%")
        self._ram_card.update_val(ram["percent"], f"{ram['percent']:.1f}%")
        self._up_card.update_val(net["upload_kbs"], f"{net['upload_kbs']:.1f} KB/s")
        self._dn_card.update_val(net["download_kbs"], f"{net['download_kbs']:.1f} KB/s")
        try:
            pcount = len(list(psutil.process_iter()))
            self._proc_lbl.findChild(QLabel, "val").setText(str(pcount))
            conns = len(psutil.net_connections())
            self._conn_lbl.findChild(QLabel, "val").setText(str(conns))
            dk = psutil.disk_io_counters()
            self._disk_lbl.findChild(QLabel, "val").setText(f"{dk.read_bytes//1024} KB/s" if dk else "N/A")
        except Exception:
            pass
