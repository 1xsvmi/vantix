"""Network IDS Module."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QTableWidget, QTableWidgetItem, QComboBox,
                              QHeaderView, QFrame, QAbstractItemView)
from PyQt6.QtCore    import QTimer, Qt
from PyQt6.QtGui     import QColor, QBrush
from app.utils.system_monitor import get_connections, get_net_speed

RISK_COLOR = {"SAFE":"#00FF88","SUSPICIOUS":"#FFB300","DANGEROUS":"#FF3232"}
COLS = ["Local Addr","Remote Addr","Status","PID","Process","Risk"]

STYLE = """
QWidget { background:#0a0a10; color:#e0e0f0; }
QTableWidget { background:#13131f; gridline-color:#1e1e30; border:1px solid #1e1e30; border-radius:6px; }
QTableWidget::item { padding:4px 8px; }
QHeaderView::section { background:#0d0d1a; color:#7a7a9a; font-weight:600; font-size:11px;
                       border:none; padding:6px 8px; }
QComboBox { background:#13131f; border:1px solid #1e1e30; border-radius:6px; color:#e0e0f0;
            padding:6px 10px; }
QComboBox::drop-down { border:none; }
"""

class NetworkIDS(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(STYLE)
        lay = QVBoxLayout(self); lay.setContentsMargins(20,20,20,20); lay.setSpacing(12)

        hdr = QHBoxLayout()
        t = QLabel("NETWORK IDS")
        t.setStyleSheet("color:#00F5FF;font-size:18px;font-weight:700;letter-spacing:2px;")
        hdr.addWidget(t); hdr.addStretch()
        self._status_lbl = QLabel("Connections: 0")
        self._status_lbl.setStyleSheet("color:#7a7a9a;font-size:13px;")
        hdr.addWidget(self._status_lbl)
        lay.addLayout(hdr)

        # Bandwidth cards
        bw = QHBoxLayout(); bw.setSpacing(12)
        self._up_lbl = self._bw_card("UPLOAD", "#00FF88")
        self._dn_lbl = self._bw_card("DOWNLOAD","#FFB300")
        bw.addWidget(self._up_lbl[0]); bw.addWidget(self._dn_lbl[0])
        lay.addLayout(bw)

        # Filter
        fil = QHBoxLayout()
        fil.addWidget(QLabel("Filter:"))
        self._combo = QComboBox()
        self._combo.addItems(["All","ESTABLISHED","LISTEN","TIME_WAIT","CLOSE_WAIT"])
        self._combo.currentTextChanged.connect(self._apply_filter)
        fil.addWidget(self._combo); fil.addStretch()
        lay.addLayout(fil)

        self._table = QTableWidget(0, len(COLS))
        self._table.setHorizontalHeaderLabels(COLS)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.verticalHeader().setVisible(False)
        lay.addWidget(self._table)

        self._raw = []
        self._timer = QTimer(self); self._timer.timeout.connect(self._refresh)
        self._timer.start(3000); self._refresh()

    def _bw_card(self, label, color):
        f = QFrame(); f.setStyleSheet(f"background:#13131f;border:1px solid #1e1e30;border-radius:8px;")
        v = QVBoxLayout(f); v.setContentsMargins(14,10,14,10)
        l1 = QLabel(label); l1.setStyleSheet("color:#7a7a9a;font-size:11px;font-weight:600;")
        l2 = QLabel("0 KB/s"); l2.setStyleSheet(f"color:{color};font-size:20px;font-weight:700;")
        v.addWidget(l1); v.addWidget(l2)
        return f, l2

    def _refresh(self):
        self._raw = get_connections()
        self._status_lbl.setText(f"Connections: {len(self._raw)}")
        net = get_net_speed()
        self._up_lbl[1].setText(f"{net['upload_kbs']:.1f} KB/s")
        self._dn_lbl[1].setText(f"{net['download_kbs']:.1f} KB/s")
        self._apply_filter(self._combo.currentText())

    def _apply_filter(self, flt):
        data = self._raw if flt == "All" else [c for c in self._raw if c["status"] == flt]
        self._table.setRowCount(0)
        for c in data:
            r = self._table.rowCount(); self._table.insertRow(r)
            vals = [c["laddr"],c["raddr"],c["status"],str(c["pid"]),c["pname"],c["risk"]]
            for col, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignLeft)
                if col == 5:
                    item.setForeground(QBrush(QColor(RISK_COLOR.get(v,"#ffffff"))))
                self._table.setItem(r, col, item)
