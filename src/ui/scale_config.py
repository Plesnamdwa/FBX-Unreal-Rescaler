"""Scale Configuration Widget with Dynamic Mode Selection and Export Location."""
from typing import Optional
from pathlib import Path
from PyQt6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QRadioButton, QDoubleSpinBox, QLabel,
    QPushButton, QLineEdit, QFileDialog
)
from PyQt6.QtCore import pyqtSignal, Qt


class ScaleConfigWidget(QGroupBox):
    """
    Control panel for selecting Auto-Normalize (180 cm) or Manual Multiplier,
    as well as specifying the custom export output directory.
    """
    process_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Scale & Export Settings", parent)
        self._custom_export_dir: Optional[str] = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Mode 1: Auto-Normalize
        self.rb_auto = QRadioButton("Auto-Normalize (Target 180 cm Unreal Engine Standard)")
        self.rb_auto.setChecked(True)
        self.rb_auto.setStyleSheet("font-size: 12px; font-weight: bold; color: #ffffff;")
        self.rb_auto.toggled.connect(self._on_mode_changed)

        lbl_auto_desc = QLabel(
            "Analyzes the mesh bounding box, calculates scale factor against 180 cm Unreal standard, "
            "and bakes the transform directly into vertices, bone translations, and bind poses."
        )
        lbl_auto_desc.setWordWrap(True)
        lbl_auto_desc.setStyleSheet("font-size: 10px; color: #a0a0a0; margin-left: 20px;")

        # Mode 2: Manual Multiplier
        manual_layout = QHBoxLayout()
        self.rb_manual = QRadioButton("Manual Multiplier:")
        self.rb_manual.setStyleSheet("font-size: 12px; font-weight: bold; color: #ffffff;")

        self.spin_multiplier = QDoubleSpinBox()
        self.spin_multiplier.setRange(0.001, 1000.0)
        self.spin_multiplier.setDecimals(3)
        self.spin_multiplier.setValue(1.000)
        self.spin_multiplier.setSingleStep(0.1)
        self.spin_multiplier.setEnabled(False)
        self.spin_multiplier.setStyleSheet(
            "QDoubleSpinBox { background-color: #2b2b2b; color: #ffffff; padding: 4px 8px; "
            "border: 1px solid #4f4f4f; border-radius: 4px; font-size: 12px; font-weight: bold; }"
            "QDoubleSpinBox:disabled { background-color: #1c1c1c; color: #666666; border: 1px solid #333333; }"
        )

        manual_layout.addWidget(self.rb_manual)
        manual_layout.addWidget(self.spin_multiplier)
        manual_layout.addStretch()

        lbl_manual_desc = QLabel(
            "Freezes and applies a custom multiplier ratio (e.g. 0.010, 1.000, or 100.000) directly to geometry."
        )
        lbl_manual_desc.setWordWrap(True)
        lbl_manual_desc.setStyleSheet("font-size: 10px; color: #a0a0a0; margin-left: 20px;")

        # --- Export Location Section (Right before Process Button) ---
        export_box = QVBoxLayout()
        export_box.setSpacing(6)

        lbl_export_title = QLabel("📂 Export Destination Directory:")
        lbl_export_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #90caf9;")

        export_row = QHBoxLayout()
        self.line_export_dir = QLineEdit()
        self.line_export_dir.setReadOnly(True)
        self.line_export_dir.setPlaceholderText("Default: Save in the same folder as the original file")
        self.line_export_dir.setStyleSheet(
            "QLineEdit { background-color: #242424; color: #e0e0e0; border: 1px solid #444444; "
            "border-radius: 4px; padding: 6px 10px; font-size: 11px; }"
        )

        self.btn_select_dir = QPushButton("Browse Folder...")
        self.btn_select_dir.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_select_dir.setStyleSheet(
            "QPushButton { background-color: #37474f; color: #ffffff; font-weight: bold; "
            "padding: 6px 14px; border-radius: 4px; border: 1px solid #546e7a; }"
            "QPushButton:hover { background-color: #455a64; }"
        )
        self.btn_select_dir.clicked.connect(self._choose_directory)

        self.btn_reset_dir = QPushButton("Reset")
        self.btn_reset_dir.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reset_dir.setToolTip("Revert export destination to original file's directory")
        self.btn_reset_dir.setStyleSheet(
            "QPushButton { background-color: #2b2b2b; color: #aaaaaa; padding: 6px 10px; "
            "border-radius: 4px; border: 1px solid #3c3c3c; }"
            "QPushButton:hover { background-color: #383838; color: #ffffff; }"
        )
        self.btn_reset_dir.clicked.connect(self._reset_directory)

        export_row.addWidget(self.line_export_dir)
        export_row.addWidget(self.btn_select_dir)
        export_row.addWidget(self.btn_reset_dir)

        export_box.addWidget(lbl_export_title)
        export_box.addLayout(export_row)

        # Start Process Button
        self.btn_process = QPushButton("🚀 Process & Export FBX")
        self.btn_process.setEnabled(False)
        self.btn_process.setStyleSheet(
            "QPushButton { background-color: #2e7d32; color: white; font-size: 13px; "
            "font-weight: bold; padding: 10px; border-radius: 6px; }"
            "QPushButton:hover { background-color: #388e3c; }"
            "QPushButton:disabled { background-color: #333333; color: #777777; }"
        )
        self.btn_process.clicked.connect(self.process_requested.emit)

        layout.addWidget(self.rb_auto)
        layout.addWidget(lbl_auto_desc)
        layout.addLayout(manual_layout)
        layout.addWidget(lbl_manual_desc)
        layout.addLayout(export_box)
        layout.addWidget(self.btn_process)

    def _on_mode_changed(self, auto_checked: bool):
        self.spin_multiplier.setEnabled(not auto_checked)

    def _choose_directory(self):
        chosen_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory for Exported FBX",
            self._custom_export_dir or ""
        )
        if chosen_dir:
            self._custom_export_dir = str(Path(chosen_dir).resolve())
            self.line_export_dir.setText(self._custom_export_dir)

    def _reset_directory(self):
        self._custom_export_dir = None
        self.line_export_dir.clear()

    def get_export_directory(self) -> Optional[str]:
        """Returns custom output directory if selected, or None for original file directory."""
        return self._custom_export_dir

    def is_auto_normalize(self) -> bool:
        return self.rb_auto.isChecked()

    def get_manual_multiplier(self) -> float:
        return float(self.spin_multiplier.value())

    def set_process_enabled(self, enabled: bool):
        self.btn_process.setEnabled(enabled)
