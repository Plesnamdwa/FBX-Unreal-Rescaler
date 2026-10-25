"""Calculation of Visual Bounding Box, Axis-aware Height, and Normalization Factors."""
from typing import Tuple
import math
import sys
from pathlib import Path

project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    import fbx
except ImportError:
    fbx = None


def get_accumulated_node_scale(node: "fbx.FbxNode") -> Tuple[float, float, float]:
    """
    Computes total non-uniform scale (Sx, Sy, Sz) accumulated from the node up to RootNode.
    Also incorporates GeometricScaling if present.
    """
    if not node:
        return (1.0, 1.0, 1.0)

    sx, sy, sz = 1.0, 1.0, 1.0
    curr = node
    # Traverse upwards until RootNode (RootNode parent is None)
    while curr and curr.GetParent():
        sc = curr.LclScaling.Get()
        sx *= float(sc[0])
        sy *= float(sc[1])
        sz *= float(sc[2])

        if hasattr(curr, "GetGeometricScaling"):
            try:
                gs = curr.GetGeometricScaling(fbx.FbxNode.EPivotSet.eSourcePivot)
                sx *= float(gs[0])
                sy *= float(gs[1])
                sz *= float(gs[2])
            except Exception:
                pass
        curr = curr.GetParent()

    return (sx, sy, sz)


def compute_world_visual_bounding_box(scene: "fbx.FbxScene") -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
    """
    Computes visual bounding box in world space using EvaluateGlobalTransform().
    Accurately accounts for non-uniform scaling and rotation of nodes in the viewport.
    """
    min_x, min_y, min_z = float("inf"), float("inf"), float("inf")
    max_x, max_y, max_z = float("-inf"), float("-inf"), float("-inf")
    found_points = False

    mesh_count = scene.GetSrcObjectCount(fbx.FbxCriteria.ObjectType(fbx.FbxMesh.ClassId))
    for i in range(mesh_count):
        mesh = scene.GetSrcObject(fbx.FbxCriteria.ObjectType(fbx.FbxMesh.ClassId), i)
        if not mesh:
            continue
        node = mesh.GetNode()
        gt = node.EvaluateGlobalTransform() if node else fbx.FbxAMatrix()

        cp_count = mesh.GetControlPointsCount()
        for j in range(cp_count):
            cp = mesh.GetControlPointAt(j)
            pw = gt.MultT(cp)
            x, y, z = pw[0], pw[1], pw[2]
            if x < min_x: min_x = x
            if x > max_x: max_x = x
            if y < min_y: min_y = y
            if y > max_y: max_y = y
            if z < min_z: min_z = z
            if z > max_z: max_z = z
            found_points = True

    if not found_points:
        return (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)

    return (min_x, min_y, min_z), (max_x, max_y, max_z)


def get_scene_up_axis(scene: "fbx.FbxScene") -> str:
    """Detects whether the FBX scene coordinate system uses Y-Up or Z-Up."""
    try:
        axis_system = scene.GetGlobalSettings().GetAxisSystem()
        up_vector, up_sign = axis_system.GetUpVector()
        eY = getattr(getattr(fbx.FbxAxisSystem, "EUpVector", None), "eYAxis", None)
        eZ = getattr(getattr(fbx.FbxAxisSystem, "EUpVector", None), "eZAxis", None)
        if eY is not None and up_vector == eY:
            return "Y"
        elif eZ is not None and up_vector == eZ:
            return "Z"
    except Exception:
        pass
    return "Z"


def calculate_normalization_factor(
    scene: "fbx.FbxScene",
    auto_normalize: bool = True,
    manual_multiplier: float = 1.0,
    target_height_cm: float = 180.0
) -> Tuple[float, float, str]:
    """
    Calculates uniform normalization factor F_norm applied to the entire scene.
    Returns (uniform_norm_factor, visual_height, up_axis).
    """
    if not auto_normalize:
        return float(manual_multiplier), 0.0, "Manual"

    bbox_min, bbox_max = compute_world_visual_bounding_box(scene)
    up_axis = get_scene_up_axis(scene)

    if up_axis == "Y":
        visual_height = bbox_max[1] - bbox_min[1]
    else:
        visual_height = bbox_max[2] - bbox_min[2]

    if visual_height <= 0.0001 or math.isinf(visual_height) or math.isnan(visual_height):
        alt_height = max(bbox_max[1] - bbox_min[1], bbox_max[2] - bbox_min[2])
        if alt_height > 0.0001:
            visual_height = alt_height
        else:
            return float(manual_multiplier), 0.0, up_axis

    norm_factor = target_height_cm / visual_height
    return norm_factor, visual_height, up_axis
