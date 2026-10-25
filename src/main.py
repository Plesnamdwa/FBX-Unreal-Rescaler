"""Entry point for the FBX Unreal Rescaler application."""
import sys
import os
from pathlib import Path

# Add project root to sys.path so local imports and local fbx bindings resolve cleanly
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from src.ui.main_window import MainWindow


def main():
    # Set Windows AppUserModelID so the taskbar displays the custom icon properly
    if sys.platform == "win32":
        try:
            import ctypes
            app_id = "unrealtools.fbx_rescaler.v1"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except Exception:
            pass

    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("FBX Unreal Rescaler")
    app.setApplicationDisplayName("FBX Unreal Rescaler")
    app.setOrganizationName("UnrealTools")

    # Set Application Icon
    icon_path = Path(project_root) / "assets" / "icon.ico"
    if not icon_path.exists():
        icon_path = Path(project_root) / "assets" / "icon.png"

    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow()
    if icon_path.exists():
        window.setWindowIcon(QIcon(str(icon_path)))

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
