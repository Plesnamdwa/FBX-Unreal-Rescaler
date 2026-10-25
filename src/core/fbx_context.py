"""RAII Memory Management for Autodesk FBX SDK."""
from typing import Optional
import sys
from pathlib import Path

# Ensure local project root is on sys.path for fbx.pyd or FbxCommon.py
project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    import fbx
except ImportError:
    fbx = None


class FBXSessionContext:
    """Context manager to ensure explicit C++ FbxManager destruction."""

    def __init__(self):
        if fbx is None:
            raise ImportError(
                "Autodesk FBX Python SDK ('fbx') was not found.\n"
                "Ensure 'fbx.pyd' and its dependency files are placed in the "
                "project root directory or in Python site-packages."
            )
        self.manager: Optional[fbx.FbxManager] = None
        self.io_settings: Optional[fbx.FbxIOSettings] = None
        self.scene: Optional[fbx.FbxScene] = None

    def __enter__(self):
        self.manager = fbx.FbxManager.Create()
        if not self.manager:
            raise RuntimeError("Failed to create C++ FbxManager instance.")

        self.io_settings = fbx.FbxIOSettings.Create(self.manager, fbx.IOSROOT)
        self.manager.SetIOSettings(self.io_settings)
        self.scene = fbx.FbxScene.Create(self.manager, "RescalerScene")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.manager:
            # Explicit destruction to prevent C++ wrapper memory leaks
            self.manager.Destroy()
            self.manager = None
            self.io_settings = None
            self.scene = None
        return False
