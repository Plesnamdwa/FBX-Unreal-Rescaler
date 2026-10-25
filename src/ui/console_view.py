"""Live Console and Logging Widget."""
import datetime
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit, QLabel, QHBoxLayout, QPushButton
from PyQt6.QtGui import QTextCursor


class ConsoleViewWidget(QWidget):
    """Console log viewer with rich formatting and color-coded status messages."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        header_layout = QHBoxLayout()
        lbl_console = QLabel("💻 Live Processing Log")
        lbl_console.setStyleSheet("font-size: 12px; font-weight: bold; color: #d0d0d0;")

        btn_clear_log = QPushButton("Clear Log")
        btn_clear_log.setStyleSheet(
            "background-color: transparent; color: #888; font-size: 10px; border: none; padding: 2px 6px;"
        )
        btn_clear_log.clicked.connect(self.clear_log)

        header_layout.addWidget(lbl_console)
        header_layout.addStretch()
        header_layout.addWidget(btn_clear_log)

        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet(
            "QPlainTextEdit {"
            "background-color: #151515;"
            "color: #cfcfcf;"
            "font-family: 'Consolas', 'Courier New', monospace;"
            "font-size: 11px;"
            "border: 1px solid #2e2e2e;"
            "border-radius: 6px;"
            "padding: 8px;"
            "}"
        )

        layout.addLayout(header_layout)
        layout.addWidget(self.text_edit)

    def log(self, level: str, message: str):
        """Appends a color-coded log message to the console view."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        color_map = {
            "INFO": "#64b5f6",     # Light Blue / Cyan
            "SUCCESS": "#81c784",  # Green
            "WARNING": "#ffb74d",  # Orange / Yellow
            "ERROR": "#e57373"     # Red
        }
        color = color_map.get(level.upper(), "#ffffff")

        html_entry = (
            f"<span style='color: #666666;'>[{timestamp}]</span> "
            f"<span style='color: {color}; font-weight: bold;'>[{level.upper()}]</span> "
            f"<span style='color: #e0e0e0;'>{message}</span><br>"
        )

        self.text_edit.appendHtml(html_entry)
        self.text_edit.moveCursor(QTextCursor.MoveOperation.End)

    def clear_log(self):
        self.text_edit.clear()
