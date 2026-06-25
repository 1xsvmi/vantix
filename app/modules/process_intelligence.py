"""Process Intelligence Module."""
import psutil, logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QTableWidget, QTableWidgetItem, QLineEdit,
                              QPushButton, QHeaderView, QMessageBox, QAbstractItemView)
from PyQt6.QtCore    import QTimer, Qt
from PyQt6.QtGui     import QColor, QBrush
from app.utils.system_monitor import get_processes

log = logging.getLogger(__name__)

RISK_COLOR = {"SAFE": "#00FF88", "SUSPICIOUS": "#FFB300", "DANGEROUS": "#FF3232"}
COLS = ["PID","Name","CPU %","Memory MB","User","Risk"]

STYLE = """
QWidget { background: #0a0a10; color: #e0e0f0; }
QTableWidget { background: #13131f; gridline-color: #1e1e30; border: 1px solid #1e1e30;
               border-radius: 6px; selection-background-color: #1c1c32; }
QTableWidget::item { padding: 4px 8px; }
QHeaderView::section { background: #0d0d1a; color: #7a7a9a; font-weight: 600;
                       font-size: 11px; border: none; padding: 6px 8px; }
QLineEdit { background: #13131f; border: 1px solid #1e1e30; border-radius: 6px;
            color: #e0e0f0; padding: 6px 10px; font-size: 13px; }
QLineEdit:focus { border-color: #00F5FF; }
QPushButton { background: #1c1c32; border: 1px solid #2a2a45; border-radius: 6px;
              color: #00F5FF; font-weight: 600; padding: 6px 14px; }
QPushButton:hover { background: #00F5FF20; }
"""

class ProcessIntelligence(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(STYLE)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20,20,20,20); lay.setSpacing(12)

        hdr = QHBoxLayout()
        t = QLabel("PROCESS INTELLIGENCE")
        t.setStyleSheet("color:#00F5FF;font-size:18px;font-weight:700;letter-spacing:2px;")
        hdr.addWidget(t); hdr.addStretch()
        self._cnt_lbl = QLabel("Processes: 0")
        self._cnt_lbl.setStyleSheet("color:#7a7a9a;font-size:13px;")
        hdr.addWidget(self._cnt_lbl)
        lay.addLayout(hdr)

        bar = QHBoxLayout()
        self._search = QLineEdit(); self._search.setPlaceholderText("🔍  Search processes...")
        self._search.textChanged.connect(self._filter)
        self._kill_btn = QPushButton("⚠ Kill Selected")
        self._kill_btn.clicked.connect(self._kill_process)
        bar.addWidget(self._search); bar.addWidget(self._kill_btn)
        lay.addLayout(bar)

        self._table = QTableWidget(0, len(COLS))
        self._table.setHorizontalHeaderLabels(COLS)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.doubleClicked.connect(self._kill_process)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet(self._table.styleSheet() +
            "QTableWidget { alternate-background-color: #0f0f1e; }")
        lay.addWidget(self._table)

        self._all_procs = []
        self._timer = QTimer(self); self._timer.timeout.connect(self._refresh)
        self._timer.start(2000); self._refresh()

    def _refresh(self):
        self._all_procs = get_processes()
        self._cnt_lbl.setText(f"Processes: {len(self._all_procs)}")
        self._populate(self._all_procs)

    def _filter(self, txt):
        t = txt.lower()
        filtered = [p for p in self._all_procs if t in p["name"].lower() or t in str(p["pid"])]
        self._populate(filtered)

    def _populate(self, procs):
        self._table.setRowCount(0)
        for p in procs:
            r = self._table.rowCount(); self._table.insertRow(r)
            vals = [str(p["pid"]), p["name"], f"{p['cpu']:.1f}", f"{p['mem']:.1f}",
                    p["user"], p["risk"]]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                if c == 5:
                    item.setForeground(QBrush(QColor(RISK_COLOR.get(v,"#ffffff"))))
                self._table.setItem(r, c, item)

    def _kill_process(self):
        row = self._table.currentRow()
        if row < 0:
            QMessageBox.information(self,"VANTIX","Select a process first."); return
        pid_item = self._table.item(row, 0)
        name_item = self._table.item(row, 1)
        if not pid_item: return
        pid  = int(pid_item.text())
        name = name_item.text() if name_item else str(pid)
        reply = QMessageBox.question(self,"Confirm Kill",
            f"Terminate process '{name}' (PID {pid})?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                psutil.Process(pid).terminate()
                QMessageBox.information(self,"VANTIX",f"Process {name} terminated.")
                self._refresh()
            except psutil.NoSuchProcess:
                QMessageBox.warning(self,"VANTIX","Process no longer exists.")
            except psutil.AccessDenied:
                QMessageBox.critical(self,"VANTIX","Access denied – run as administrator.")
            except Exception as e:
                QMessageBox.critical(self,"VANTIX",f"Error: {e}")
