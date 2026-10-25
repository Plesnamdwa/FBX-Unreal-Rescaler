"""Drag-and-Drop Zone Widget for FBX files."""
import os
from pathlib import Path
from typing import List, Set
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QFileDialog, QPushButton, QHBoxLayout, QListWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent


class DropZoneWidget(QFrame):
    """
    Interactive area allowing users to drag and drop FBX files or folders.
    Emits files_changed signal when the file list updates.
    """
    files_changed = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._files: List[str] = []

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setObjectName("DropZone")

        self._init_ui()
        self._set_idle_style()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Header label
        self.lbl_title = QLabel("📁 Drag & Drop FBX Files Here")
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #e0e0e0;")

        self.lbl_subtitle = QLabel("Supports multiple files or folders containing .fbx files")
        self.lbl_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_subtitle.setStyleSheet("font-size: 11px; color: #9e9e9e;")

        # List widget showing queued files
        self.file_list_widget = QListWidget()
        self.file_list_widget.setFixedHeight(95)
        self.file_list_widget.setStyleSheet(
            "background-color: #1a1a1a; color: #dcdcdc; border: 1px solid #333; "
            "border-radius: 4px; padding: 4px; font-size: 11px;"
        )
        self.file_list_widget.hide()

        # Action buttons
        btn_layout = QHBoxLayout()
        self.btn_browse = QPushButton("Browse Files...")
        self.btn_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_browse.setStyleSheet(
            "background-color: #2b5b84; color: white; padding: 5px 14px; "
            "border-radius: 4px; font-weight: bold;"
        )
        self.btn_browse.clicked.connect(self._browse_files)

        self.btn_clear = QPushButton("Clear List")
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.setStyleSheet(
            "background-color: #3f3f3f; color: #ccc; padding: 5px 12px; "
            "border-radius: 4px;"
        )
        self.btn_clear.clicked.connect(self.clear_files)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_browse)
        btn_layout.addWidget(self.btn_clear)
        btn_layout.addStretch()

        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_subtitle)
        layout.addWidget(self.file_list_widget)
        layout.addLayout(btn_layout)

    def _set_idle_style(self):
        self.setStyleSheet(
            "#DropZone {"
            "border: 2px dashed #4a4a4a;"
            "border-radius: 8px;"
            "background-color: #242424;"
            "}"
        )

    def _set_hover_style(self):
        self.setStyleSheet(
            "#DropZone {"
            "border: 2px dashed #3a86ff;"
            "border-radius: 8px;"
            "background-color: #2a2d36;"
            "}"
        )

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._set_hover_style()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self._set_idle_style()

    def dropEvent(self, event: QDropEvent):
        self._set_idle_style()
        urls = event.mimeData().urls()
        raw_paths = [url.toLocalFile() for url in urls if url.isLocalFile()]
        self._add_paths(raw_paths)
        event.acceptProposedAction()

    def _browse_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select FBX Files",
            "",
            "FBX Files (*.fbx)"
        )
        if paths:
            self._add_paths(paths)

    def _add_paths(self, raw_paths: List[str]):
        collected: Set[str] = set(self._files)
        for p in raw_paths:
            path_obj = Path(p)
            if path_obj.is_file() and path_obj.suffix.lower() == ".fbx":
                collected.add(str(path_obj.resolve()))
            elif path_obj.is_dir():
                for fbx_file in path_obj.glob("**/*.fbx"):
                    if not fbx_file.name.endswith("_UE_Scaled.fbx"):
                        collected.add(str(fbx_file.resolve()))

        self._files = sorted(list(collected))
        self._update_display()
        self.files_changed.emit(self._files)

    def _update_display(self):
        self.file_list_widget.clear()
        if self._files:
            self.file_list_widget.show()
            self.lbl_title.setText(f"📁 {len(self._files)} FBX File(s) Selected")
            for f in self._files:
                self.file_list_widget.addItem(Path(f).name)
        else:
            self.file_list_widget.hide()
            self.lbl_title.setText("📁 Drag & Drop FBX Files Here")

    def get_files(self) -> List[str]:
        return list(self._files)

    def clear_files(self):
        self._files.clear()
        self._update_display()
        self.files_changed.emit(self._files)
