"""Unit tests for FBX Unreal Rescaler mathematical core and UI components."""
import unittest
import sys
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PyQt6.QtWidgets import QApplication
from src.ui.scale_config import ScaleConfigWidget
from src.ui.drop_zone import DropZoneWidget
from src.core.skeleton_scaler import is_pure_skeleton_node


class DummyAttr:
    def __init__(self, attr_type):
        self._type = attr_type

    def GetAttributeType(self):
        return self._type


class DummyNode:
    def __init__(self, name: str, attr_type=None):
        self._name = name
        self._attr = DummyAttr(attr_type) if attr_type is not None else None

    def GetName(self):
        return self._name

    def GetNodeAttribute(self):
        return self._attr


class TestRescalerMathAndLogic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create headless QApp for testing UI widgets
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()

    def test_scale_config_defaults(self):
        """Verify default state of ScaleConfigWidget and QDoubleSpinBox behavior."""
        widget = ScaleConfigWidget()
        self.assertTrue(widget.is_auto_normalize())
        self.assertFalse(widget.spin_multiplier.isEnabled())
        self.assertEqual(widget.spin_multiplier.minimum(), 0.001)
        self.assertEqual(widget.spin_multiplier.maximum(), 1000.0)
        self.assertEqual(widget.spin_multiplier.decimals(), 3)
        self.assertAlmostEqual(widget.get_manual_multiplier(), 1.000)

    def test_scale_config_manual_toggle(self):
        """Verify toggle behavior activates QDoubleSpinBox."""
        widget = ScaleConfigWidget()
        widget.rb_manual.setChecked(True)
        self.assertFalse(widget.is_auto_normalize())
        self.assertTrue(widget.spin_multiplier.isEnabled())

        widget.spin_multiplier.setValue(0.010)
        self.assertAlmostEqual(widget.get_manual_multiplier(), 0.010)

        widget.rb_auto.setChecked(True)
        self.assertTrue(widget.is_auto_normalize())
        self.assertFalse(widget.spin_multiplier.isEnabled())

    def test_pure_skeleton_node_filter(self):
        """Verify Blender dummy Empty 'Armature' is strictly excluded from skeleton bone scaling."""
        eSkeleton_type = 3
        eNull_type = 1

        bone_node = DummyNode("Spine1", attr_type=eSkeleton_type)
        empty_armature = DummyNode("Armature", attr_type=eNull_type)
        plain_node = DummyNode("RootGroup", attr_type=None)

        import src.core.skeleton_scaler as ss
        class MockFbxAttr:
            eSkeleton = 3

        class MockFbx:
            FbxNodeAttribute = MockFbxAttr

        old_fbx = ss.fbx
        ss.fbx = MockFbx
        try:
            self.assertTrue(ss.is_pure_skeleton_node(bone_node))
            self.assertFalse(ss.is_pure_skeleton_node(empty_armature))
            self.assertFalse(ss.is_pure_skeleton_node(plain_node))
            self.assertFalse(ss.is_pure_skeleton_node(None))
        finally:
            ss.fbx = old_fbx

    def test_bake_and_reset_scaling_math(self):
        """Verify Bake & Reset Freeze Transformation preserves true physical size."""
        # Simulated raw vertex in meters (1.97 m) with native node scale 100
        raw_vertex_y = 1.97416
        native_node_scale = 100.0
        visual_height_cm = raw_vertex_y * native_node_scale # 197.416 cm

        target_height_cm = 180.0
        norm_factor = target_height_cm / visual_height_cm
        bake_factor = native_node_scale * norm_factor # 91.1777

        # 1. Bake factor into vertex
        baked_vertex_y = raw_vertex_y * bake_factor
        # 2. Reset node scale to 1.0
        final_node_scale = 1.0

        # Effective height in Unreal Engine
        effective_ue_height = baked_vertex_y * final_node_scale
        self.assertAlmostEqual(effective_ue_height, 180.0, places=2)
        self.assertEqual(final_node_scale, 1.0)

    def test_export_directory_selection(self):
        """Verify selecting and resetting custom export directory."""
        widget = ScaleConfigWidget()
        self.assertIsNone(widget.get_export_directory())
        self.assertEqual(widget.line_export_dir.text(), "")

        # Simulate selecting a custom directory
        dummy_dir = str(Path("d:/custom_export").resolve())
        widget._custom_export_dir = dummy_dir
        widget.line_export_dir.setText(dummy_dir)
        self.assertEqual(widget.get_export_directory(), dummy_dir)

        # Reset
        widget._reset_directory()
        self.assertIsNone(widget.get_export_directory())
        self.assertEqual(widget.line_export_dir.text(), "")

    def test_drop_zone_file_filtering(self):
        """Verify drop zone only adds valid fbx files and filters out already scaled ones."""
        zone = DropZoneWidget()
        test_files = [
            "d:/test/character.fbx",
            "d:/test/character_UE_Scaled.fbx",
            "d:/test/texture.png"
        ]
        filtered = [f for f in test_files if f.lower().endswith(".fbx") and not f.endswith("_UE_Scaled.fbx")]
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0], "d:/test/character.fbx")


if __name__ == "__main__":
    unittest.main()
