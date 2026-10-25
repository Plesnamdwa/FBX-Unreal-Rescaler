"""Skeleton Bone Translation Scaling and Absolute Scene Scale Reset."""
import sys
from pathlib import Path
from typing import List

project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    import fbx
except ImportError:
    fbx = None

from src.core.scale_calculator import get_accumulated_node_scale


def is_pure_skeleton_node(node: "fbx.FbxNode") -> bool:
    """
    Checks if node has a pure FbxSkeleton attribute.
    Excludes dummy empty nodes (such as Blender's 'Armature' Empty).
    """
    if not node:
        return False
    attr = node.GetNodeAttribute()
    if not attr:
        return False
    try:
        attr_type = attr.GetAttributeType()
        expected = getattr(getattr(fbx.FbxNodeAttribute, "EType", None), "eSkeleton", None)
        if expected is None:
            expected = getattr(fbx.FbxNodeAttribute, "eSkeleton", None)
        return attr_type == expected
    except Exception:
        return False


def collect_skeleton_nodes(root_node: "fbx.FbxNode") -> List["fbx.FbxNode"]:
    """Recursively collects all nodes in the hierarchy that are pure skeleton bones."""
    skeleton_nodes: List["fbx.FbxNode"] = []

    def _traverse(node: "fbx.FbxNode"):
        if not node:
            return
        if is_pure_skeleton_node(node):
            skeleton_nodes.append(node)
        for i in range(node.GetChildCount()):
            _traverse(node.GetChild(i))

    _traverse(root_node)
    return skeleton_nodes


def scale_skeleton_translations(scene: "fbx.FbxScene", uniform_norm_factor: float) -> int:
    """
    Step 2: Multiplies local translation of all pure skeleton nodes by their accumulated
    parent scale and uniform normalization factor.
    """
    root_node = scene.GetRootNode()
    if not root_node:
        return 0

    bone_nodes = collect_skeleton_nodes(root_node)
    for bone in bone_nodes:
        # Scale of parent hierarchy
        psx, psy, psz = get_accumulated_node_scale(bone.GetParent())

        t = bone.LclTranslation.Get()
        scaled_t = fbx.FbxDouble3(
            t[0] * psx * uniform_norm_factor,
            t[1] * psy * uniform_norm_factor,
            t[2] * psz * uniform_norm_factor
        )
        bone.LclTranslation.Set(scaled_t)

    return len(bone_nodes)


def reset_all_nodes_scaling(scene: "fbx.FbxScene") -> int:
    """
    Step 3 (CRITICAL): Recursively traverses EVERY node in the scene
    (Root, Empty, Armature, Mesh, Joint, Bone) and forces its LclScaling to (1.0, 1.0, 1.0).
    Also resets GeometricScaling to (1.0, 1.0, 1.0).
    Completes the 'Freeze Transformation / Apply Scale' operation.
    """
    root_node = scene.GetRootNode()
    if not root_node:
        return 0

    reset_count = 0

    def _reset_recursive(node: "fbx.FbxNode"):
        nonlocal reset_count
        if not node:
            return

        # 1. Force LclScaling to absolute (1.0, 1.0, 1.0)
        unit_scale = fbx.FbxDouble3(1.0, 1.0, 1.0)
        node.LclScaling.Set(unit_scale)

        # 2. Reset GeometricScaling if present
        if hasattr(node, "SetGeometricScaling"):
            try:
                node.SetGeometricScaling(fbx.FbxNode.EPivotSet.eSourcePivot, unit_scale)
            except Exception:
                pass

        reset_count += 1

        for i in range(node.GetChildCount()):
            _reset_recursive(node.GetChild(i))

    _reset_recursive(root_node)
    return reset_count
