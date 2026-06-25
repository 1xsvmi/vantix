# ⬡ VANTIX – Cybersecurity Desktop Monitor

<p align="center">
  <img src="app/assets/logo.svg" width="120" alt="VANTIX Logo"/>
</p>

<p align="center">
  <b>Real-time process, network, storage & threat intelligence — all in one dark glassmorphism desktop app.</b><br/>
  <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python" alt="Python"/>
  <img src="https://img.shields.io/badge/PyQt6-6.7-green?logo=qt" alt="PyQt6"/>
  <img src="https://img.shields.io/badge/License-MIT-purple" alt="MIT"/>
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-cyan" alt="Cross-platform"/>
</p>

---

## Features

| Module | Description |
|--------|-------------|
| ⚡ **Overview Dashboard** | Real-time CPU, RAM, upload/download charts (1 s refresh) |
| ⚙ **Process Intelligence** | All running processes, risk scoring, kill process |
| 🌐 **Network IDS** | Active connections, suspicious port detection, bandwidth monitor |
| 💾 **Storage Intelligence** | Disk partitions, usage bars, read/write speed |
| 🎯 **Threat Intelligence** | FireHOL blocklist, custom IPs, export JSON/CSV |
| 🔗 **Risk Correlation Engine** | SQLite event log, 24h risk graph, overall risk score |

---

## Quick Start

### Run from source

**Linux / macOS:**
```bash
chmod +x run.sh && ./run.sh
```

**Windows:**
```cmd
run.bat
```

### Manual setup
```bash
python -m venv venv
# Linux/macOS
source venv/bin/activate
# Windows
venv\Scripts\activate

pip install -r requirements.txt
python app/main.py
```

---

## Building Standalone Binaries

**Windows `.exe`:**
```cmd
build_windows.bat
# Output: dist/Vantix.exe
```

**Linux binary:**
```bash
chmod +x build_linux.sh && ./build_linux.sh
# Output: dist/Vantix
```

---

## System Requirements

| Component | Minimum |
|-----------|---------|
| OS | Windows 10/11 · Ubuntu 20.04+ · Fedora 36+ |
| Python | 3.10+ (source only) |
| RAM | 256 MB |
| Disk | 200 MB |
| Network | Optional (for FireHOL updates) |

---

## Architecture

```
vantix/
├── app/
│   ├── main.py                    ← Entry point, MainWindow, TitleBar, Tray
│   ├── animated_stacked_widget.py ← Fade animation between tabs
│   ├── base_module.py             ← Abstract base for all modules
│   ├── modules/
│   │   ├── overview_dashboard.py
│   │   ├── process_intelligence.py
│   │   ├── network_ids.py
│   │   ├── storage_intelligence.py
│   │   ├── threat_intelligence.py
│   │   └── risk_correlation.py
│   ├── utils/
│   │   ├── system_monitor.py      ← psutil wrappers
│   │   └── threat_scanner.py      ← FireHOL + custom IP checking
│   └── assets/                    ← logo.svg, logo-text.svg, icon.ico
├── docs/index.html                ← GitHub Pages site
├── .github/workflows/build.yml   ← Auto-build on tag push
├── requirements.txt
├── build_windows.bat
├── build_linux.sh
└── run.sh / run.bat
```

---

## Data & Privacy

- All monitoring is **local only** — no data is sent externally.
- FireHOL blocklist is fetched from GitHub and cached at `~/.vantix/blocklist.json` for 24 hours.
- Risk events are logged to `~/.vantix/vantix.db` (SQLite).
- Application logs are written to `~/.vantix/vantix.log`.

---

## License

MIT © 2025 VANTIX Security
