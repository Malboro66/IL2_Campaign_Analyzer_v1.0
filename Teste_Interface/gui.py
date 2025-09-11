from pathlib import Path

# try to import a Qt QApplication from commonly used bindings (use dynamic import to avoid static analysis errors)
import importlib

QAPP_CANDIDATES = ("PySide6.QtWidgets", "PyQt5.QtWidgets", "PyQt6.QtWidgets")
QApplication = None
for _mod in QAPP_CANDIDATES:
    try:
        module = importlib.import_module(_mod)
        QApplication = getattr(module, "QApplication", None)
        if QApplication is not None:
            break
    except Exception:
        QApplication = None

# dentro de main(), antes de app.setStyleSheet(...)
assets_dir = Path(__file__).parent / 'assets'
texture_path = assets_dir.joinpath('paper_texture_2048.png').as_posix()

# create or reuse the QApplication instance so `app` is defined
if 'QApplication' in globals() and QApplication is not None:
    app = QApplication.instance() or QApplication([])
else:
    app = None

app.setStyleSheet(f"""
QWidget {{
    background-color: #E8E0CF;
    background-image: url("file://{texture_path}");
    background-repeat: repeat;
    font-family: "Source Sans 3", Arial, sans-serif;
    color: #231F20;
    font-size: 12px;
}}
QGroupBox {{
    font-weight: bold;
    border: 2px solid rgba(176,139,79,0.35);
    border-radius: 8px;
    padding: 10px;
    background-color: rgba(215,201,176,0.6);
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px 0 5px;
    font-family: "Roboto Slab", Georgia, serif;
    font-size: 16px;
}}
QPushButton {{
    background-color: #7A4B2E;
    color: #FFFFFF;
    border-radius: 6px;
    padding: 8px 12px;
    border: 2px solid #B08B4F;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: #8b5632;
    border: 2px solid #c3a66d;
}}
QPushButton:disabled {{
    background-color: #cccccc;
    color: #666666;
    border: 2px solid #bdbdbd;
}}
QTableWidget {{
    background-color: rgba(255,255,255,0.75);
    gridline-color: rgba(0,0,0,0.06);
    alternate-background-color: rgba(0,0,0,0.02);
    font-family: "Source Sans 3", Arial, sans-serif;
}}
QHeaderView::section {{
    background-color: rgba(176,139,79,0.08);
    padding: 6px;
    border: none;
    font-family: "Roboto Slab", Georgia, serif;
    font-weight: 600;
}}
QLabel#photo_label, QLabel#rank_image_label, QLabel#hat_image_label, QLabel#uniform_image_label, QLabel#weapon_image_label {{
    border: 2px solid #7A4B2E;
    background-color: rgba(255,255,255,0.85);
    border-radius: 4px;
}}
QProgressBar {{
    border: 1px solid #B08B4F;
    border-radius: 6px;
    background: rgba(0,0,0,0.03);
    height: 14px;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #B08B4F, stop:1 #7A4B2E);
    border-radius: 6px;
}}
QTextEdit, QLineEdit {{
    background-color: rgba(255,255,255,0.9);
    border: 1px solid rgba(0,0,0,0.06);
}}
QToolTip {{
    background-color: #231F20;
    color: #E8E0CF;
    border: 1px solid #7A4B2E;
}}
""")
