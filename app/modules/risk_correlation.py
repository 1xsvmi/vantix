"""Risk Correlation Engine – SQLite logging + historical graph."""
import os, sqlite3, json, time, logging, collections
from datetime  import datetime, timedelta
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QFrame, QTableWidget, QTableWidgetItem,
                              QHeaderView, QAbstractItemView)
from PyQt6.QtCore    import QTimer, Qt
from PyQt6.QtGui     import QPainter, QColor, QPen, QBrush, QLinearGradient
from PyQt6.QtCore    import QPointF
from PyQt6.QtGui     import QPolygonF, QPainterPath
from app.utils.system_monitor import get_processes, get_connections, get_disks

log = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.expanduser("~"), ".vantix", "vantix.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def _db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS events
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         ts TEXT, level TEXT, module TEXT, detail TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS risk_log
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         ts TEXT, risk TEXT, score INTEGER)""")
    con.commit()
    return con

class RiskGraph(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(120)
        self._data = []  # list of (ts, score)

    def set_data(self, data):
        self._data = data; self.update()

    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(0,0,w,h,QColor("#13131f"))
        if len(self._data) < 2: return
        scores = [d[1] for d in self._data]
        n = len(scores); step = w/(n-1)
        pts_x = [i*step for i in range(n)]
        pts_y = [h-(s/100)*(h-4) for s in scores]
        # fill
        poly = QPolygonF([QPointF(pts_x[i],pts_y[i]) for i in range(n)])
        poly.append(QPointF(pts_x[-1],h)); poly.append(QPointF(0,h))
        grad = QLinearGradient(0,0,0,h)
        c1=QColor("#7B2FFF"); c1.setAlpha(80)
        c2=QColor("#7B2FFF"); c2.setAlpha(0)
        grad.setColorAt(0,c1); grad.setColorAt(1,c2)
        p.setBrush(QBrush(grad)); p.setPen(Qt.PenStyle.NoPen)
        p.drawPolygon(poly)
        # line
        path = QPainterPath()
        path.moveTo(pts_x[0],pts_y[0])
        for i in range(1,n): path.lineTo(pts_x[i],pts_y[i])
        p.setPen(QPen(QColor("#7B2FFF"),2)); p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)
        p.end()

class RiskCorrelation(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background:#0a0a10;color:#e0e0f0;")
        lay = QVBoxLayout(self); lay.setContentsMargins(20,20,20,20); lay.setSpacing(12)

        hdr = QHBoxLayout()
        t = QLabel("RISK CORRELATION ENGINE")
        t.setStyleSheet("color:#00F5FF;font-size:18px;font-weight:700;letter-spacing:2px;")
        hdr.addWidget(t); hdr.addStretch()
        self._risk_lbl = QLabel("Overall: SAFE")
        self._risk_lbl.setStyleSheet("color:#00FF88;font-size:16px;font-weight:700;")
        hdr.addWidget(self._risk_lbl)
        lay.addLayout(hdr)

        # Module status row
        ms = QHBoxLayout(); ms.setSpacing(12)
        self._cards = {}
        for mod in ["Process","Network","Storage","Threats"]:
            f = QFrame(); f.setStyleSheet("background:#13131f;border:1px solid #1e1e30;border-radius:8px;")
            v = QVBoxLayout(f); v.setContentsMargins(14,10,14,10)
            l1=QLabel(mod.upper()); l1.setStyleSheet("color:#7a7a9a;font-size:11px;font-weight:600;")
            l2=QLabel("SAFE"); l2.setStyleSheet("color:#00FF88;font-size:16px;font-weight:700;")
            l2.setObjectName("val"); v.addWidget(l1); v.addWidget(l2)
            self._cards[mod] = f
            ms.addWidget(f)
        lay.addLayout(ms)

        # Graph
        lay.addWidget(QLabel("Risk History (last 24h)"))
        self._graph = RiskGraph(); self._graph.setStyleSheet("border:1px solid #1e1e30;border-radius:6px;")
        lay.addWidget(self._graph)

        # Events table
        lay.addWidget(QLabel("Recent Security Events"))
        self._table = QTableWidget(0,4)
        self._table.setHorizontalHeaderLabels(["Time","Level","Module","Detail"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setStyleSheet("""
            QTableWidget{background:#13131f;gridline-color:#1e1e30;border:1px solid #1e1e30;border-radius:6px;}
            QHeaderView::section{background:#0d0d1a;color:#7a7a9a;font-weight:600;font-size:11px;border:none;padding:6px;}
        """)
        lay.addWidget(self._table)

        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh)
        self._refresh_timer.start(5000)
        self._save_timer = QTimer(self)
        self._save_timer.timeout.connect(self._save_state)
        self._save_timer.start(300000)  # 5 min
        self._refresh()

    def _assess(self):
        events = []
        status = {}
        # Processes
        procs = get_processes()
        dangerous_p = [p for p in procs if p["risk"]=="DANGEROUS"]
        suspicious_p = [p for p in procs if p["risk"]=="SUSPICIOUS"]
        if dangerous_p:
            status["Process"] = "DANGEROUS"
            for p in dangerous_p:
                events.append(("DANGEROUS","Process",f"Dangerous process: {p['name']} PID={p['pid']}"))
        elif len(suspicious_p) > 3:
            status["Process"] = "SUSPICIOUS"
        else:
            status["Process"] = "SAFE"

        # Network
        conns = get_connections()
        dangerous_c = [c for c in conns if c["risk"]=="DANGEROUS"]
        if dangerous_c:
            status["Network"] = "DANGEROUS"
            for c in dangerous_c:
                events.append(("DANGEROUS","Network",f"Suspicious port {c['raddr']}"))
        else:
            status["Network"] = "SAFE"

        # Storage
        disks = get_disks()
        critical_d = [d for d in disks if d["percent"]>=95]
        if critical_d:
            status["Storage"] = "SUSPICIOUS"
            events.append(("SUSPICIOUS","Storage",f"Disk {critical_d[0]['device']} at {critical_d[0]['percent']:.1f}%"))
        else:
            status["Storage"] = "SAFE"

        status["Threats"] = "SAFE"

        # Overall
        vals = list(status.values())
        if "DANGEROUS" in vals or vals.count("SUSPICIOUS") >= 3:
            overall = "DANGEROUS"
        elif "SUSPICIOUS" in vals:
            overall = "SUSPICIOUS"
        else:
            overall = "SAFE"

        return status, overall, events

    def _refresh(self):
        status, overall, events = self._assess()
        COLORS = {"SAFE":"#00FF88","SUSPICIOUS":"#FFB300","DANGEROUS":"#FF3232"}
        for mod, lvl in status.items():
            lbl = self._cards[mod].findChild(QLabel,"val")
            if lbl:
                lbl.setText(lvl); lbl.setStyleSheet(f"color:{COLORS[lvl]};font-size:16px;font-weight:700;")

        self._risk_lbl.setText(f"Overall: {overall}")
        self._risk_lbl.setStyleSheet(f"color:{COLORS[overall]};font-size:16px;font-weight:700;")

        # log events
        con = _db()
        ts = datetime.now().strftime("%H:%M:%S")
        score = {"SAFE":0,"SUSPICIOUS":40,"DANGEROUS":90}[overall]
        con.execute("INSERT INTO risk_log(ts,risk,score) VALUES(?,?,?)",
                    (datetime.now().isoformat(), overall, score))
        for lvl,mod,detail in events:
            con.execute("INSERT INTO events(ts,level,module,detail) VALUES(?,?,?,?)",
                        (datetime.now().isoformat(),lvl,mod,detail))
        con.commit()

        # load graph data
        cutoff = (datetime.now()-timedelta(hours=24)).isoformat()
        rows = con.execute("SELECT ts,score FROM risk_log WHERE ts>? ORDER BY ts",
                           (cutoff,)).fetchall()
        self._graph.set_data(rows)

        # load events table
        ev_rows = con.execute(
            "SELECT ts,level,module,detail FROM events ORDER BY id DESC LIMIT 50"
        ).fetchall()
        self._table.setRowCount(0)
        for er in ev_rows:
            r = self._table.rowCount(); self._table.insertRow(r)
            for c,v in enumerate(er):
                item = QTableWidgetItem(str(v))
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignLeft)
                if c==1:
                    item.setForeground(QBrush(QColor(COLORS.get(str(v),"#ffffff"))))
                self._table.setItem(r,c,item)
        con.close()

    def _save_state(self):
        log.info("Auto-saved risk state")
