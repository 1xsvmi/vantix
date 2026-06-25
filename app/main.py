#!/usr/bin/env python3
"""VANTIX – Main Entry Point."""
import sys, os, logging

# Set up logging
log_path = os.path.join(os.path.expanduser("~"), ".vantix", "vantix.log")
os.makedirs(os.path.dirname(log_path), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
    handlers=[
        logging.FileHandler(log_path),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger("vantix")

from PyQt6.QtWidgets  import (QApplication, QMainWindow, QWidget,
                               QHBoxLayout, QVBoxLayout, QPushButton,
                               QLabel, QSystemTrayIcon, QMenu,
                               QFrame, QSizePolicy, QGraphicsOpacityEffect)
from PyQt6.QtCore     import Qt, QTimer, QPoint, QPropertyAnimation, QByteArray
from PyQt6.QtGui      import (QIcon, QPixmap, QFont, QColor, QPalette,
                               QAction, QPainter)
from PyQt6.QtSvg      import QSvgRenderer

from app.modules.overview_dashboard   import OverviewDashboard
from app.modules.process_intelligence import ProcessIntelligence
from app.modules.network_ids          import NetworkIDS
from app.modules.storage_intelligence import StorageIntelligence
from app.modules.threat_intelligence  import ThreatIntelligence
from app.modules.risk_correlation     import RiskCorrelation
from app.animated_stacked_widget      import AnimatedStackedWidget

ASSETS = os.path.join(os.path.dirname(__file__), "assets")

NAV_TABS = [
    ("⚡ Overview",      OverviewDashboard),
    ("⚙ Processes",      ProcessIntelligence),
    ("🌐 Network IDS",   NetworkIDS),
    ("💾 Storage",        StorageIntelligence),
    ("🎯 Threats",        ThreatIntelligence),
    ("🔗 Risk Engine",    RiskCorrelation),
]

QSS = """
QMainWindow, QWidget#central {
    background: #0a0a10;
}
QScrollBar:vertical {
    background: #13131f; width: 6px; border-radius: 3px;
}
QScrollBar::handle:vertical {
    background: #2a2a45; border-radius: 3px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QToolTip { background: #13131f; color: #e0e0f0; border: 1px solid #2a2a45;
           border-radius: 4px; padding: 4px 8px; font-size: 12px; }
"""

NAV_BTN_STYLE = """
QPushButton {{
    background: transparent;
    border: none;
    border-radius: 8px;
    color: #7a7a9a;
    font-size: 13px;
    font-weight: 600;
    padding: 10px 16px;
    text-align: left;
}}
QPushButton:hover {{
    background: #1a1a28;
    color: #e0e0f0;
}}
"""
NAV_BTN_ACTIVE = """
QPushButton {{
    background: linear-gradient(90deg, #00F5FF20, #7B2FFF20);
    border: none;
    border-left: 2px solid #00F5FF;
    border-radius: 0 8px 8px 0;
    color: #00F5FF;
    font-size: 13px;
    font-weight: 700;
    padding: 10px 16px;
    text-align: left;
}}
"""


class ToastNotification(QFrame):
    def __init__(self, message: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background: #1a0a0a;
                border: 1px solid #FF3232;
                border-radius: 8px;
                padding: 2px;
            }
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        lbl = QLabel(f"⚠ {message}")
        lbl.setStyleSheet("color: #FF3232; font-size: 13px; font-weight: 600;")
        lay.addWidget(lbl)
        self.setFixedWidth(360)

        self._effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._effect)
        self._anim_in  = QPropertyAnimation(self._effect, QByteArray(b"opacity"))
        self._anim_out = QPropertyAnimation(self._effect, QByteArray(b"opacity"))
        self._anim_in.setDuration(300); self._anim_in.setStartValue(0); self._anim_in.setEndValue(1)
        self._anim_out.setDuration(500); self._anim_out.setStartValue(1); self._anim_out.setEndValue(0)
        self._anim_out.finished.connect(self.deleteLater)
        self._anim_in.start()
        QTimer.singleShot(4000, self._anim_out.start)


class TitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(48)
        self.setStyleSheet("background: #0d0d1a; border-bottom: 1px solid #1e1e30;")
        lay = QHBoxLayout(self); lay.setContentsMargins(16, 0, 8, 0)

        # Logo
        svg_path = os.path.join(ASSETS, "logo-text.svg")
        if os.path.exists(svg_path):
            rnd = QSvgRenderer(svg_path)
            pix = QPixmap(180, 44)
            pix.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pix)
            rnd.render(painter); painter.end()
            logo = QLabel(); logo.setPixmap(pix)
        else:
            logo = QLabel("⬡ VANTIX")
            logo.setStyleSheet("color:#00F5FF;font-size:18px;font-weight:800;letter-spacing:3px;")
        lay.addWidget(logo)

        lay.addStretch()

        # Window buttons
        for sym, tip, slot in [
            ("−", "Minimize", parent.showMinimized if parent else None),
            ("□", "Maximize", self._toggle_max),
            ("✕", "Close",    QApplication.quit),
        ]:
            btn = QPushButton(sym); btn.setFixedSize(36, 36)
            btn.setToolTip(tip)
            btn.setStyleSheet(f"""
                QPushButton {{ background:transparent; color:#7a7a9a;
                               border:none; border-radius:4px; font-size:14px; }}
                QPushButton:hover {{ background: {'#FF3232' if sym=='✕' else '#1e1e30'};
                                     color: #ffffff; }}
            """)
            if slot: btn.clicked.connect(slot)
            lay.addWidget(btn)
        self._win = parent
        self._drag_pos = None

    def _toggle_max(self):
        if self._win:
            if self._win.isMaximized(): self._win.showNormal()
            else: self._win.showMaximized()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - (self._win.frameGeometry().topLeft() if self._win else QPoint())

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.MouseButton.LeftButton and self._drag_pos and self._win:
            self._win.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None


class Sidebar(QWidget):
    def __init__(self, on_tab, parent=None):
        super().__init__(parent)
        self.setFixedWidth(200)
        self.setStyleSheet("background: #0d0d1a; border-right: 1px solid #1e1e30;")
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 16, 0, 16); lay.setSpacing(4)
        self._btns = []
        for i, (label, _) in enumerate(NAV_TABS):
            btn = QPushButton(label)
            btn.setStyleSheet(NAV_BTN_STYLE)
            btn.clicked.connect(lambda _, idx=i: on_tab(idx))
            self._btns.append(btn); lay.addWidget(btn)
        lay.addStretch()

        ver = QLabel("v1.0.0"); ver.setStyleSheet("color:#2a2a45;font-size:11px;padding:8px 16px;")
        lay.addWidget(ver)

    def set_active(self, idx):
        for i, btn in enumerate(self._btns):
            btn.setStyleSheet(NAV_BTN_ACTIVE if i==idx else NAV_BTN_STYLE)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        self.setWindowTitle("VANTIX")
        ico_path = os.path.join(ASSETS, "icon.ico")
        if os.path.exists(ico_path):
            self.setWindowIcon(QIcon(ico_path))

        central = QWidget(); central.setObjectName("central")
        self.setCentralWidget(central)
        root = QVBoxLayout(central); root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        self._title_bar = TitleBar(self)
        root.addWidget(self._title_bar)

        body = QHBoxLayout(); body.setContentsMargins(0,0,0,0); body.setSpacing(0)
        self._sidebar = Sidebar(self._switch_tab)
        body.addWidget(self._sidebar)

        self._stack = AnimatedStackedWidget()
        self._modules = []
        for _, ModClass in NAV_TABS:
            m = ModClass()
            self._modules.append(m)
            self._stack.addWidget(m)
        body.addWidget(self._stack)
        root.addLayout(body)

        self._setup_tray()
        self._switch_tab(0)

        # danger alert timer
        self._alert_timer = QTimer(self)
        self._alert_timer.timeout.connect(self._check_alerts)
        self._alert_timer.start(15000)

    def _switch_tab(self, idx):
        self._stack.setCurrentIndex(idx)
        self._sidebar.set_active(idx)

    def _setup_tray(self):
        self._tray = QSystemTrayIcon(self)
        ico_path = os.path.join(ASSETS, "icon.ico")
        if os.path.exists(ico_path):
            self._tray.setIcon(QIcon(ico_path))
        else:
            pix = QPixmap(32,32); pix.fill(QColor("#00F5FF"))
            self._tray.setIcon(QIcon(pix))
        self._tray.setToolTip("VANTIX – Cybersecurity Monitor")
        menu = QMenu()
        menu.addAction(QAction("Open VANTIX", self, triggered=self.show))
        menu.addSeparator()
        for i,(label,_) in enumerate(NAV_TABS):
            menu.addAction(QAction(label, self, triggered=lambda _,idx=i: (self.show(), self._switch_tab(idx))))
        menu.addSeparator()
        menu.addAction(QAction("Quit", self, triggered=QApplication.quit))
        self._tray.setContextMenu(menu)
        self._tray.show()
        self._tray.activated.connect(lambda r: self.show() if r==QSystemTrayIcon.ActivationReason.Trigger else None)

    def _check_alerts(self):
        from app.utils.system_monitor import get_processes
        procs = get_processes()
        dangerous = [p for p in procs if p["risk"]=="DANGEROUS"]
        if dangerous:
            msg = f"Dangerous process: {dangerous[0]['name']} (PID {dangerous[0]['pid']})"
            self._toast(msg)
            self._tray.showMessage("VANTIX ALERT", msg, QSystemTrayIcon.MessageIcon.Critical, 5000)

    def _toast(self, msg):
        toast = ToastNotification(msg, self.centralWidget())
        x = self.width() - toast.width() - 20
        y = self.height() - 80
        toast.move(x, y); toast.show()

    def closeEvent(self, e):
        e.ignore(); self.hide()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)
    app.setApplicationName("VANTIX")
    app.setOrganizationName("VANTIX Security")

    # Custom font via system fallback (Space Grotesk / Inter not always available)
    font = QFont("Segoe UI" if sys.platform=="win32" else "Ubuntu", 10)
    app.setFont(font)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
