"""Recalculation of FbxCluster and Scene Bind Poses from Evaluated Transforms."""
import sys
from pathlib import Path
from typing import Tuple

project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    import fbx
except ImportError:
    fbx = None


def recalculate_cluster_matrices(scene: "fbx.FbxScene") -> int:
    """
    Step 5 (CRITICAL): Recalculates TransformMatrix and TransformLinkMatrix for all FbxClusters
    directly from the evaluated world transforms after Vertex baking and Node Scale reset.
    This guarantees accurate Inverse Bind Matrices without distortion or explosion.
    """
    total_clusters = 0
    mesh_count = scene.GetSrcObjectCount(fbx.FbxCriteria.ObjectType(fbx.FbxMesh.ClassId))

    skin_type = getattr(getattr(fbx.FbxDeformer, "EDeformerType", None), "eSkin", None)
    if skin_type is None:
        skin_type = getattr(fbx.FbxDeformer, "eSkin", None)

    for m in range(mesh_count):
        mesh = scene.GetSrcObject(fbx.FbxCriteria.ObjectType(fbx.FbxMesh.ClassId), m)
        if not mesh:
            continue

        mesh_node = mesh.GetNode()
        # Mesh global transform at bind time (with newly frozen scale 1.0)
        mesh_gt = mesh_node.EvaluateGlobalTransform() if mesh_node else fbx.FbxAMatrix()

        deformer_count = mesh.GetDeformerCount(skin_type) if skin_type is not None else mesh.GetDeformerCount()
        for d in range(deformer_count):
            skin = mesh.GetDeformer(d, skin_type) if skin_type is not None else mesh.GetDeformer(d)
            if not skin:
                continue

            cluster_count = skin.GetClusterCount()
            for c in range(cluster_count):
                cluster = skin.GetCluster(c)
                if not cluster:
                    continue

                link_node = cluster.GetLink()
                if not link_node:
                    continue

                # Bone global transform at bind time (with newly baked translation and scale 1.0)
                link_gt = link_node.EvaluateGlobalTransform()

                # 1. Update Mesh Node Bind Matrix
                cluster.SetTransformMatrix(mesh_gt)

                # 2. Update Bone Node Bind Link Matrix
                cluster.SetTransformLinkMatrix(link_gt)

                # 3. Associate Model Matrix if present
                assoc_node = cluster.GetAssociateModel()
                if assoc_node:
                    cluster.SetTransformAssociateModelMatrix(assoc_node.EvaluateGlobalTransform())

                total_clusters += 1

    return total_clusters


def recalculate_scene_bind_poses(scene: "fbx.FbxScene") -> int:
    """
    Rebuilds scene FbxPose bind poses using the freshly evaluated global transforms.
    """
    updated_poses = 0
    pose_count = scene.GetPoseCount()

    for i in range(pose_count):
        pose = scene.GetPose(i)
        if not pose or not pose.IsBindPose():
            continue

        # Collect current nodes in the pose
        pose_items = []
        for j in range(pose.GetCount()):
            node = pose.GetNode(j)
            if node:
                is_local = pose.IsLocalMatrix(j)
                new_matrix = fbx.FbxMatrix(node.EvaluateGlobalTransform())
                pose_items.append((node, new_matrix, is_local))

        # Re-add with updated matrices
        while pose.GetCount() > 0:
            pose.Remove(0)

        for node, new_mat, is_local in pose_items:
            pose.Add(node, new_mat, is_local)

        updated_poses += 1

    return updated_poses


def update_skinning_and_bind_pose(scene: "fbx.FbxScene") -> Tuple[int, int]:
    """
    Master function to recalculate both skin cluster matrices and scene bind poses.
    Returns (clusters_count, poses_count).
    """
    clusters_count = recalculate_cluster_matrices(scene)
    poses_count = recalculate_scene_bind_poses(scene)
    return clusters_count, poses_count
