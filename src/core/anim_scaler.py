"""Scaling of Animation Translation Curves and Locking Scaling Curves."""
import sys
from pathlib import Path
from typing import List, Tuple

project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    import fbx
except ImportError:
    fbx = None

from src.core.scale_calculator import get_accumulated_node_scale


def scale_anim_curve(curve: "fbx.FbxAnimCurve", scale_factor: float) -> int:
    """Scales all keyframe values in an animation curve by scale_factor."""
    if not curve:
        return 0

    key_count = curve.KeyGetCount()
    if key_count == 0:
        return 0

    curve.KeyModifyBegin()
    for k in range(key_count):
        val = curve.KeyGetValue(k)
        curve.KeySetValue(k, val * scale_factor)
    curve.KeyModifyEnd()

    return key_count


def reset_scaling_anim_curve(curve: "fbx.FbxAnimCurve") -> int:
    """Forces all keyframes on a scaling curve to 1.0."""
    if not curve:
        return 0

    key_count = curve.KeyGetCount()
    if key_count == 0:
        return 0

    curve.KeyModifyBegin()
    for k in range(key_count):
        curve.KeySetValue(k, 1.0)
    curve.KeyModifyEnd()

    return key_count


def scale_scene_animations(scene: "fbx.FbxScene", uniform_norm_factor: float) -> Tuple[int, int]:
    """
    Step 2 & 3: Multiplies translation keyframes per-axis by their accumulated scale
    and uniform normalization factor, and resets scaling curves to 1.0.
    Returns (num_translation_curves_scaled, num_keyframes_scaled).
    """
    total_trans_curves = 0
    total_keys = 0

    root_node = scene.GetRootNode()
    if not root_node:
        return 0, 0

    all_nodes: List["fbx.FbxNode"] = []
    def _collect(n: "fbx.FbxNode"):
        if not n:
            return
        all_nodes.append(n)
        for i in range(n.GetChildCount()):
            _collect(n.GetChild(i))
    _collect(root_node)

    stack_count = scene.GetSrcObjectCount(fbx.FbxCriteria.ObjectType(fbx.FbxAnimStack.ClassId))
    for s in range(stack_count):
        stack = scene.GetSrcObject(fbx.FbxCriteria.ObjectType(fbx.FbxAnimStack.ClassId), s)
        if not stack:
            continue

        layer_count = stack.GetMemberCount(fbx.FbxCriteria.ObjectType(fbx.FbxAnimLayer.ClassId))
        for l in range(layer_count):
            layer = stack.GetMember(fbx.FbxCriteria.ObjectType(fbx.FbxAnimLayer.ClassId), l)
            if not layer:
                continue

            for node in all_nodes:
                psx, psy, psz = get_accumulated_node_scale(node.GetParent())
                factors = {
                    "X": psx * uniform_norm_factor,
                    "Y": psy * uniform_norm_factor,
                    "Z": psz * uniform_norm_factor
                }

                # 1. Scale Translation curves
                for channel in ["X", "Y", "Z"]:
                    curve = node.LclTranslation.GetCurve(layer, channel)
                    if curve and curve.KeyGetCount() > 0:
                        total_keys += scale_anim_curve(curve, factors[channel])
                        total_trans_curves += 1

                # 2. Reset Scaling curves to 1.0
                for channel in ["X", "Y", "Z"]:
                    scale_curve = node.LclScaling.GetCurve(layer, channel)
                    if scale_curve and scale_curve.KeyGetCount() > 0:
                        reset_scaling_anim_curve(scale_curve)

    return total_trans_curves, total_keys
