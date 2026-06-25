"""Storage Intelligence Module."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QTableWidget, QTableWidgetItem, QProgressBar,
                              QHeaderView, QFrame, QAbstractItemView)
from PyQt6.QtCore    import QTimer, Qt
from PyQt6.QtGui     import QColor
from app.utils.system_monitor import get_disks
import psutil

COLS = ["Device","Mount","FS","Total GB","Used GB","Free GB","Usage %"]

STYLE = """
QWidget{background:#0a0a10;color:#e0e0f0;}
QTableWidget{background:#13131f;gridline-color:#1e1e30;border:1px solid #1e1e30;border-radius:6px;}
QTableWidget::item{padding:4px 8px;}
QHeaderView::section{background:#0d0d1a;color:#7a7a9a;font-weight:600;font-size:11px;
                     border:none;padding:6px 8px;}
"""

class StorageBar(QProgressBar):
    def __init__(self, pct, parent=None):
        super().__init__(parent)
        self.setRange(0, 100)
        self.setValue(int(pct))
        self.setTextVisible(True)
        self.setFormat(f"{pct:.1f}%")
        if pct >= 90:
            color = "#FF3232"
        elif pct >= 70:
            color = "#FFB300"
        else:
            color = "#00FF88"
        self.setStyleSheet(f"""
            QProgressBar{{background:#0d0d1a;border:1px solid #1e1e30;border-radius:4px;
                          height:18px;color:#ffffff;font-size:11px;font-weight:600;}}
            QProgressBar::chunk{{background:{color};border-radius:3px;}}
        """)

class StorageIntelligence(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(STYLE)
        lay = QVBoxLayout(self); lay.setContentsMargins(20,20,20,20); lay.setSpacing(12)

        hdr = QHBoxLayout()
        t = QLabel("STORAGE INTELLIGENCE")
        t.setStyleSheet("color:#00F5FF;font-size:18px;font-weight:700;letter-spacing:2px;")
        hdr.addWidget(t); hdr.addStretch()
        lay.addLayout(hdr)

        # Summary row
        self._sum_row = QHBoxLayout(); self._sum_row.setSpacing(12)
        self._total_card = self._stat_card("TOTAL STORAGE","0 GB")
        self._used_card  = self._stat_card("USED",         "0 GB")
        self._free_card  = self._stat_card("FREE",         "0 GB")
        self._rd_card    = self._stat_card("DISK READ",    "0 MB/s")
        self._wr_card    = self._stat_card("DISK WRITE",   "0 MB/s")
        for w in [self._total_card,self._used_card,self._free_card,self._rd_card,self._wr_card]:
            self._sum_row.addWidget(w)
        lay.addLayout(self._sum_row)

        self._table = QTableWidget(0, len(COLS))
        self._table.setHorizontalHeaderLabels(COLS)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        lay.addWidget(self._table)

        self._prev_io = None
        self._timer = QTimer(self); self._timer.timeout.connect(self._refresh)
        self._timer.start(5000); self._refresh()

    def _stat_card(self, label, val):
        f = QFrame(); f.setStyleSheet("background:#13131f;border:1px solid #1e1e30;border-radius:8px;")
        v = QVBoxLayout(f); v.setContentsMargins(14,10,14,10)
        l1 = QLabel(label); l1.setStyleSheet("color:#7a7a9a;font-size:11px;font-weight:600;")
        l2 = QLabel(val);   l2.setStyleSheet("color:#ffffff;font-size:16px;font-weight:700;")
        l2.setObjectName("val")
        v.addWidget(l1); v.addWidget(l2)
        return f

    def _refresh(self):
        disks = get_disks()
        total = sum(d["total_gb"] for d in disks)
        used  = sum(d["used_gb"]  for d in disks)
        free  = sum(d["free_gb"]  for d in disks)
        self._total_card.findChild(QLabel,"val").setText(f"{total:.1f} GB")
        self._used_card.findChild(QLabel,"val").setText(f"{used:.1f} GB")
        self._free_card.findChild(QLabel,"val").setText(f"{free:.1f} GB")

        # Disk I/O speed
        try:
            io = psutil.disk_io_counters()
            if self._prev_io and io:
                rd = (io.read_bytes  - self._prev_io.read_bytes)  / 5 / 1e6
                wr = (io.write_bytes - self._prev_io.write_bytes) / 5 / 1e6
                self._rd_card.findChild(QLabel,"val").setText(f"{rd:.2f} MB/s")
                self._wr_card.findChild(QLabel,"val").setText(f"{wr:.2f} MB/s")
            self._prev_io = io
        except Exception:
            pass

        self._table.setRowCount(0)
        for d in disks:
            r = self._table.rowCount(); self._table.insertRow(r)
            vals = [d["device"],d["mount"],d["fstype"],
                    f"{d['total_gb']:.1f}",f"{d['used_gb']:.1f}",
                    f"{d['free_gb']:.1f}", ""]
            for c,v in enumerate(vals):
                if c == 6:
                    bar = StorageBar(d["percent"])
                    self._table.setCellWidget(r, c, bar)
                else:
                    item = QTableWidgetItem(v)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignLeft)
                    self._table.setItem(r, c, item)
        self._table.setRowHeight(r, 28) if disks else None
