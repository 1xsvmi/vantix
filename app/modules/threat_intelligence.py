"""Threat Intelligence Module."""
import json, csv, io, logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QTableWidget, QTableWidgetItem, QPushButton,
                              QLineEdit, QHeaderView, QFileDialog, QFrame,
                              QMessageBox, QAbstractItemView, QTextEdit)
from PyQt6.QtCore    import QTimer, Qt, QThread, pyqtSignal
from PyQt6.QtGui     import QColor, QBrush
from app.utils.system_monitor import get_connections
from app.utils.threat_scanner import (fetch_blocklist, check_connections,
                                       add_custom_ip, remove_custom_ip,
                                       get_custom_ips, blocklist_size)

log = logging.getLogger(__name__)

COLS = ["Remote IP","Status","Process","Threat","Blocklisted"]

STYLE = """
QWidget{background:#0a0a10;color:#e0e0f0;}
QTableWidget{background:#13131f;gridline-color:#1e1e30;border:1px solid #1e1e30;border-radius:6px;}
QTableWidget::item{padding:4px 8px;}
QHeaderView::section{background:#0d0d1a;color:#7a7a9a;font-weight:600;font-size:11px;border:none;padding:6px 8px;}
QLineEdit{background:#13131f;border:1px solid #1e1e30;border-radius:6px;color:#e0e0f0;padding:6px 10px;}
QLineEdit:focus{border-color:#00F5FF;}
QPushButton{background:#1c1c32;border:1px solid #2a2a45;border-radius:6px;color:#00F5FF;
            font-weight:600;padding:6px 14px;}
QPushButton:hover{background:#00F5FF20;}
"""

class FetchThread(QThread):
    done = pyqtSignal(int)
    def run(self):
        n = fetch_blocklist()
        self.done.emit(n)

class ThreatIntelligence(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(STYLE)
        lay = QVBoxLayout(self); lay.setContentsMargins(20,20,20,20); lay.setSpacing(12)

        hdr = QHBoxLayout()
        t = QLabel("THREAT INTELLIGENCE")
        t.setStyleSheet("color:#00F5FF;font-size:18px;font-weight:700;letter-spacing:2px;")
        hdr.addWidget(t); hdr.addStretch()
        self._score_lbl = QLabel("Threat Score: 0 / 100")
        self._score_lbl.setStyleSheet("color:#00FF88;font-size:14px;font-weight:700;")
        hdr.addWidget(self._score_lbl)
        lay.addLayout(hdr)

        # Summary cards
        sc = QHBoxLayout(); sc.setSpacing(12)
        self._bl_size_card = self._stat_card("BLOCKLIST SIZE","0 IPs")
        self._threat_card  = self._stat_card("THREATS DETECTED","0")
        self._custom_card  = self._stat_card("CUSTOM IPs","0")
        for w in [self._bl_size_card, self._threat_card, self._custom_card]:
            sc.addWidget(w)
        lay.addLayout(sc)

        # Fetch button
        fb = QHBoxLayout()
        self._fetch_btn = QPushButton("⬇ Update FireHOL Blocklist")
        self._fetch_btn.clicked.connect(self._do_fetch)
        self._status_lbl = QLabel("Status: Ready")
        self._status_lbl.setStyleSheet("color:#7a7a9a;font-size:12px;")
        fb.addWidget(self._fetch_btn); fb.addWidget(self._status_lbl); fb.addStretch()
        lay.addLayout(fb)

        # Connection threat table
        lay.addWidget(QLabel("🔍 Active Connection Threats"))
        self._table = QTableWidget(0, len(COLS))
        self._table.setHorizontalHeaderLabels(COLS)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        lay.addWidget(self._table)

        # Custom IP management
        lay.addWidget(QLabel("Custom Blocklist Management"))
        cip = QHBoxLayout()
        self._ip_input = QLineEdit(); self._ip_input.setPlaceholderText("Enter IP to block...")
        self._add_btn  = QPushButton("+ Add")
        self._rem_btn  = QPushButton("- Remove")
        self._add_btn.clicked.connect(self._add_ip)
        self._rem_btn.clicked.connect(self._rem_ip)
        cip.addWidget(self._ip_input); cip.addWidget(self._add_btn); cip.addWidget(self._rem_btn)
        lay.addLayout(cip)

        # Export buttons
        exp = QHBoxLayout()
        self._exp_json = QPushButton("📥 Export JSON")
        self._exp_csv  = QPushButton("📥 Export CSV")
        self._exp_json.clicked.connect(lambda: self._export("json"))
        self._exp_csv.clicked.connect( lambda: self._export("csv"))
        exp.addWidget(self._exp_json); exp.addWidget(self._exp_csv); exp.addStretch()
        lay.addLayout(exp)

        self._results = []
        self._timer = QTimer(self); self._timer.timeout.connect(self._refresh)
        self._timer.start(10000)
        self._do_fetch()

    def _stat_card(self, label, val):
        f = QFrame(); f.setStyleSheet("background:#13131f;border:1px solid #1e1e30;border-radius:8px;")
        v = QVBoxLayout(f); v.setContentsMargins(14,10,14,10)
        l1 = QLabel(label); l1.setStyleSheet("color:#7a7a9a;font-size:11px;font-weight:600;")
        l2 = QLabel(val);   l2.setStyleSheet("color:#ffffff;font-size:16px;font-weight:700;")
        l2.setObjectName("val"); v.addWidget(l1); v.addWidget(l2)
        return f

    def _do_fetch(self):
        self._status_lbl.setText("Status: Fetching blocklist...")
        self._fetch_btn.setEnabled(False)
        self._thread = FetchThread()
        self._thread.done.connect(self._fetch_done)
        self._thread.start()

    def _fetch_done(self, n):
        self._status_lbl.setText(f"Status: Loaded {n:,} IPs")
        self._fetch_btn.setEnabled(True)
        self._bl_size_card.findChild(QLabel,"val").setText(f"{blocklist_size():,}")
        self._refresh()

    def _refresh(self):
        conns = get_connections()
        self._results = check_connections(conns)
        threats = [r for r in self._results if r["threat"]=="DANGEROUS"]
        score = min(100, len(threats)*20)
        self._threat_card.findChild(QLabel,"val").setText(str(len(threats)))
        self._custom_card.findChild(QLabel,"val").setText(str(len(get_custom_ips())))
        color = "#00FF88" if score<30 else "#FFB300" if score<70 else "#FF3232"
        self._score_lbl.setText(f"Threat Score: {score} / 100")
        self._score_lbl.setStyleSheet(f"color:{color};font-size:14px;font-weight:700;")

        self._table.setRowCount(0)
        for r in self._results:
            row = self._table.rowCount(); self._table.insertRow(row)
            vals = [r["raddr"], r["status"], r["pname"],
                    r["threat"], "YES" if r["blocklisted"] else "NO"]
            for c,v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignLeft)
                if c==3:
                    item.setForeground(QBrush(QColor("#FF3232" if v=="DANGEROUS" else "#00FF88")))
                if c==4 and v=="YES":
                    item.setForeground(QBrush(QColor("#FF3232")))
                self._table.setItem(row,c,item)

    def _add_ip(self):
        ip = self._ip_input.text().strip()
        if ip: add_custom_ip(ip); self._ip_input.clear(); self._refresh()

    def _rem_ip(self):
        ip = self._ip_input.text().strip()
        if ip: remove_custom_ip(ip); self._ip_input.clear(); self._refresh()

    def _export(self, fmt):
        path, _ = QFileDialog.getSaveFileName(self,"Export Threat Report",
                    f"vantix_threats.{fmt}", f"{fmt.upper()} Files (*.{fmt})")
        if not path: return
        try:
            if fmt=="json":
                with open(path,"w") as f: json.dump(self._results, f, indent=2)
            else:
                with open(path,"w",newline="") as f:
                    w = csv.DictWriter(f, fieldnames=self._results[0].keys() if self._results else [])
                    w.writeheader(); w.writerows(self._results)
            QMessageBox.information(self,"VANTIX",f"Exported to {path}")
        except Exception as e:
            QMessageBox.critical(self,"VANTIX",f"Export error: {e}")
