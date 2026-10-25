"""Per-Axis Non-Uniform Vertex and Morph Target Geometry Baking."""
import sys
from pathlib import Path
from typing import Dict, Any

project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    import fbx
except ImportError:
    fbx = None

from src.core.scale_calculator import get_accumulated_node_scale


def bake_mesh_geometry_non_uniform(scene: "fbx.FbxScene", uniform_norm_factor: float) -> int:
    """
    Step 2: Bakes the full non-uniform local scale (Sx, Sy, Sz) and uniform normalization
    directly into each mesh's control points (vertices) and blend shapes.
    Preserves non-uniform shapes (such as elongated watermelons, flattened props, etc.).
    """
    total_vertices = 0
    mesh_count = scene.GetSrcObjectCount(fbx.FbxCriteria.ObjectType(fbx.FbxMesh.ClassId))

    for i in range(mesh_count):
        mesh = scene.GetSrcObject(fbx.FbxCriteria.ObjectType(fbx.FbxMesh.ClassId), i)
        if not mesh:
            continue

        node = mesh.GetNode()
        # Compute individual node non-uniform scale (incorporates GeometricScaling & parent scale)
        sx, sy, sz = get_accumulated_node_scale(node)

        # Combined per-axis bake factors
        fx = sx * uniform_norm_factor
        fy = sy * uniform_norm_factor
        fz = sz * uniform_norm_factor

        cp_count = mesh.GetControlPointsCount()
        for j in range(cp_count):
            cp = mesh.GetControlPointAt(j)
            scaled_cp = fbx.FbxVector4(
                cp[0] * fx,
                cp[1] * fy,
                cp[2] * fz,
                cp[3]
            )
            mesh.SetControlPointAt(scaled_cp, j)
            total_vertices += 1

        # Scale attached blend shapes / morph targets per-axis
        shape_count = mesh.GetShapeCount()
        for s in range(shape_count):
            shape = mesh.GetShape(s)
            if not shape:
                continue
            shape_cp_count = shape.GetControlPointsCount()
            for k in range(shape_cp_count):
                scp = shape.GetControlPointAt(k)
                scaled_scp = fbx.FbxVector4(
                    scp[0] * fx,
                    scp[1] * fy,
                    scp[2] * fz,
                    scp[3]
                )
                shape.SetControlPointAt(scaled_scp, k)

        # Re-generate normals to perfectly reflect the scaled geometry
        try:
            if hasattr(mesh, "GenerateNormals"):
                mesh.GenerateNormals(True, True, False)
        except Exception:
            pass

    return total_vertices
