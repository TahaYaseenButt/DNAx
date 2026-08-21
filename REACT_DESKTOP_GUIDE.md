# DNAx Laboratory Suite — React + Python Desktop Architecture

This document describes the modern **React Frontend + Python Backend Desktop Architecture** for DNAx Lab, designed to be packaged into a standalone Windows `.exe` that runs on any fresh PC without Python or Node.js pre-installed.

---

## 🏗️ Architecture Overview

```
DNAx/
├── ui/                              # React Frontend (Vite + Tailwind CSS + Lucide Icons)
│   ├── src/
│   │   ├── api.js                   # Universal JS-to-Python Bridge (window.pywebview.api)
│   │   ├── components/              # Reusable UI (Sidebar, TopNavBar, MetricCard, SequenceViewer)
│   │   ├── pages/                   # All 6 Pipeline Steps + Matrix DB + Protocol SOPs
│   │   ├── App.jsx                  # Main application router and state management
│   │   └── index.css                # Custom glassmorphic styling and scrollbars
│   └── dist/                        # Compiled production static bundle (HTML, JS, CSS)
│
├── src/
│   ├── main_webview.py              # Native Windows Desktop launcher (PyWebView + Edge WebView2)
│   ├── api_bridge.py                # Python Controller exposing calculations & DB to React
│   ├── utils/                       # SQLite DB, Needleman-Wunsch & Vectorized 4-mer similarity engine
│   └── tools/                       # DNA Generator, Primer Designer, qPCR Probe Designer
│
├── DNAx_Webview.spec                # PyInstaller packaging configuration
└── build_desktop.bat                # 1-Click build script to create dist/DNAx_Lab_Pro.exe
```

---

## 🚀 How to Run in Development

### Option A: Launch the Desktop App directly with Python
```bash
# Ensure UI is built:
cd ui
npm run build
cd ..

# Launch the desktop app:
python src/main_webview.py
```

### Option B: Live-Reload Frontend in Web Browser
```bash
cd ui
npm run dev
# Open http://localhost:3000 in your browser
```

---

## 📦 How to Build the Standalone Windows `.exe`

Run the included automated build script:
```cmd
build_desktop.bat
```
Or run manually from the command line:
```cmd
cd ui
call npm.cmd run build
cd ..
python -m PyInstaller --noconfirm DNAx_Webview.spec
```

The resulting standalone file will be generated at:
```
DNAx/dist/DNAx_Lab_Pro.exe
```
This `.exe` is **100% self-contained**: it includes the embedded Python runtime, SQLite database engine, NumPy, and the compiled React user interface. It can be copied to any fresh Windows PC and executed immediately with zero configuration.
