"""Main Application Window for FBX Unreal Rescaler."""
import os
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QProgressBar, QLabel, QMessageBox, QHBoxLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from src.ui.drop_zone import DropZoneWidget
from src.ui.scale_config import ScaleConfigWidget
from src.ui.console_view import ConsoleViewWidget
from src.ui.worker_thread import BatchWorkerThread


class MainWindow(QMainWindow):
    """
    Main Window integrating Drag-and-Drop, Scale Configuration,
    Live Console, and the background Batch Rescaling Worker.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FBX Unreal Rescaler - Matrix Baking Tool")
        self.resize(740, 700)
        self.setMinimumSize(620, 560)

        # Set logo icon
        icon_path = Path(__file__).resolve().parent.parent.parent / "assets" / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.worker_thread: BatchWorkerThread = None
        self._init_ui()
        self._apply_dark_theme()

        self._check_fbx_sdk_available()

    def _init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(14)

        # 1. Header Section
        header_layout = QHBoxLayout()
        lbl_app_title = QLabel("FBX Unreal Rescaler")
        lbl_app_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #4fc3f7;")
        lbl_version = QLabel("v1.0.0 (Unreal Engine Scale Baker)")
        lbl_version.setStyleSheet("font-size: 11px; color: #888888; padding-top: 5px;")
        header_layout.addWidget(lbl_app_title)
        header_layout.addWidget(lbl_version)
        header_layout.addStretch()

        # 2. Drop Zone
        self.drop_zone = DropZoneWidget()
        self.drop_zone.files_changed.connect(self._on_files_changed)

        # 3. Scale Configuration
        self.scale_config = ScaleConfigWidget()
        self.scale_config.process_requested.connect(self._start_processing)

        # 4. Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet(
            "QProgressBar { background-color: #222222; border: 1px solid #444444; border-radius: 4px; "
            "text-align: center; color: #ffffff; font-weight: bold; height: 18px; }"
            "QProgressBar::chunk { background-color: #0288d1; border-radius: 3px; }"
        )

        # 5. Live Console View
        self.console_view = ConsoleViewWidget()

        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.drop_zone)
        main_layout.addWidget(self.scale_config)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.console_view)

    def _apply_dark_theme(self):
        self.setStyleSheet(
            "QMainWindow { background-color: #1e1e1e; }"
            "QWidget { color: #e0e0e0; font-family: 'Segoe UI', Arial, sans-serif; }"
            "QGroupBox { font-weight: bold; border: 1px solid #3c3c3c; border-radius: 6px; "
            "margin-top: 6px; padding-top: 10px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; color: #90caf9; }"
            "QRadioButton { spacing: 8px; }"
            "QRadioButton::indicator { width: 14px; height: 14px; }"
        )

    def _check_fbx_sdk_available(self):
        try:
            import fbx
            self.console_view.log("SUCCESS", "Autodesk FBX Python SDK loaded successfully.")
        except ImportError:
            self.console_view.log(
                "WARNING",
                "Autodesk FBX Python SDK ('fbx.pyd') was not found in project root or site-packages. "
                "Place 'fbx.pyd' and 'FbxCommon.py' in the project folder to process files."
            )

    def _on_files_changed(self, files):
        has_files = len(files) > 0
        self.scale_config.set_process_enabled(has_files)
        if has_files:
            self.console_view.log("INFO", f"{len(files)} FBX file(s) queued for processing.")

    def _start_processing(self):
        files = self.drop_zone.get_files()
        if not files:
            QMessageBox.warning(self, "Warning", "Please select at least one FBX file.")
            return

        auto_mode = self.scale_config.is_auto_normalize()
        multiplier = self.scale_config.get_manual_multiplier()
        export_dir = self.scale_config.get_export_directory()

        self.scale_config.set_process_enabled(False)
        self.scale_config.btn_select_dir.setEnabled(False)
        self.scale_config.btn_reset_dir.setEnabled(False)
        self.drop_zone.btn_browse.setEnabled(False)
        self.drop_zone.btn_clear.setEnabled(False)
        self.progress_bar.setValue(0)

        self.worker_thread = BatchWorkerThread(
            files=files,
            auto_normalize=auto_mode,
            manual_multiplier=multiplier,
            target_height_cm=180.0,
            output_dir=export_dir
        )
        self.worker_thread.log_message.connect(self.console_view.log)
        self.worker_thread.progress_updated.connect(self._on_worker_progress)
        self.worker_thread.batch_finished.connect(self._on_batch_finished)
        self.worker_thread.start()

    def _on_worker_progress(self, current, total, filename):
        percent = int((current / total) * 100)
        self.progress_bar.setValue(percent)

    def _on_batch_finished(self, total, success_count):
        self.progress_bar.setValue(100)
        self.scale_config.set_process_enabled(True)
        self.scale_config.btn_select_dir.setEnabled(True)
        self.scale_config.btn_reset_dir.setEnabled(True)
        self.drop_zone.btn_browse.setEnabled(True)
        self.drop_zone.btn_clear.setEnabled(True)

        if success_count == total:
            self.console_view.log("SUCCESS", f"All {total} file(s) processed and exported successfully (_UE_Scaled.fbx)!")
            QMessageBox.information(
                self,
                "Batch Completed",
                f"Batch processing completed successfully!\n{success_count} of {total} file(s) normalized for Unreal Engine."
            )
        else:
            self.console_view.log("WARNING", f"Completed with warnings: {success_count} of {total} file(s) succeeded.")
            QMessageBox.warning(
                self,
                "Completed with Warnings",
                f"{success_count} of {total} file(s) were successfully processed. Check live console for error details."
            )
