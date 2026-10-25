"""Complete FBX Rescaling and Unreal Engine Normalization Pipeline (Bake & Reset Architecture)."""
import os
import sys
from pathlib import Path
from typing import Callable, Optional, Dict, Any

project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    import fbx
except ImportError:
    fbx = None

from src.core.fbx_context import FBXSessionContext
from src.core.scale_calculator import calculate_normalization_factor, compute_world_visual_bounding_box
from src.core.geometry_scaler import bake_mesh_geometry_non_uniform
from src.core.skeleton_scaler import scale_skeleton_translations, reset_all_nodes_scaling
from src.core.bindpose_scaler import update_skinning_and_bind_pose
from src.core.anim_scaler import scale_scene_animations


def load_fbx_file(scene: "fbx.FbxScene", manager: "fbx.FbxManager", file_path: str) -> bool:
    """Loads an FBX file into the scene using FbxImporter."""
    importer = fbx.FbxImporter.Create(manager, "FileImporter")
    status = importer.Initialize(file_path, -1, manager.GetIOSettings())
    if not status:
        error_msg = importer.GetStatus().GetErrorString()
        importer.Destroy()
        raise RuntimeError(f"Failed to initialize FBX Importer: {error_msg}")

    status = importer.Import(scene)
    importer.Destroy()
    if not status:
        raise RuntimeError("Failed to import FBX file into scene.")
    return True


def save_fbx_file(scene: "fbx.FbxScene", manager: "fbx.FbxManager", output_path: str) -> bool:
    """
    Exports the modified FBX scene.
    Preserves relative material and UV textures links without embedding raw textures.
    """
    exporter = fbx.FbxExporter.Create(manager, "FileExporter")
    io_settings = manager.GetIOSettings()

    try:
        io_settings.SetBoolProp(fbx.EXP_FBX_MATERIAL, True)
        io_settings.SetBoolProp(fbx.EXP_FBX_TEXTURE, True)
        io_settings.SetBoolProp(fbx.EXP_FBX_EMBEDDED, False)
        io_settings.SetBoolProp(fbx.EXP_FBX_ANIMATION, True)
        io_settings.SetBoolProp(fbx.EXP_FBX_GLOBAL_SETTINGS, True)
    except Exception:
        pass

    file_format = manager.GetIOPluginRegistry().GetNativeWriterFormat()
    status = exporter.Initialize(output_path, file_format, io_settings)
    if not status:
        error_msg = exporter.GetStatus().GetErrorString()
        exporter.Destroy()
        raise RuntimeError(f"Failed to initialize FBX Exporter: {error_msg}")

    status = exporter.Export(scene)
    exporter.Destroy()
    if not status:
        raise RuntimeError("Failed to export modified FBX file.")
    return True


def convert_scene_metadata_to_ue(scene: "fbx.FbxScene", log_fn: Callable[[str, str], None]):
    """
    Step 5: Blocks automatic SDK geometry scaling while setting SystemUnit to Centimeter.
    Enforces Centimeters and Z-Up for Unreal Engine.
    """
    log_fn("INFO", "Setting scene unit metadata to Centimeters (FbxSystemUnit.cm)...")
    try:
        # Update metadata directly to cm so SDK knows scene is in cm
        scene.GetGlobalSettings().SetSystemUnit(fbx.FbxSystemUnit.cm)
        # Block SDK geometry re-scaling using ConversionOptions
        conv_opt = fbx.FbxSystemUnit.ConversionOptions()
        fbx.FbxSystemUnit.cm.ConvertScene(scene, conv_opt)
    except Exception as e:
        log_fn("WARNING", f"Notice during FbxSystemUnit conversion: {e}")

    log_fn("INFO", "Converting coordinate axis system to Unreal Engine standard (Z-Up)...")
    try:
        fbx.FbxAxisSystem.Max.ConvertScene(scene)
    except Exception:
        try:
            fbx.FbxAxisSystem.DirectX.ConvertScene(scene)
        except Exception as e:
            log_fn("WARNING", f"Notice during FbxAxisSystem conversion: {e}")


def process_fbx_file(
    input_path: str,
    auto_normalize: bool = True,
    manual_multiplier: float = 1.0,
    target_height_cm: float = 180.0,
    output_dir: Optional[str] = None,
    log_callback: Optional[Callable[[str, str], None]] = None
) -> Dict[str, Any]:
    """
    Executes the Non-Uniform 'Bake & Reset' pipeline for an FBX file.
    Output file is saved with '_UE_Scaled.fbx' suffix either in output_dir or input_path parent.
    """
    def _log(level: str, msg: str):
        if log_callback:
            log_callback(level, msg)

    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"File not found: {input_path}")

    if output_dir and Path(output_dir).is_dir():
        target_dir = Path(output_dir)
    else:
        target_dir = input_file.parent

    output_path = str(target_dir / f"{input_file.stem}_UE_Scaled{input_file.suffix}")

    _log("INFO", f"=== Processing: {input_file.name} ===")
    _log("INFO", "Initializing Autodesk FBX Manager...")

    with FBXSessionContext() as ctx:
        manager = ctx.manager
        scene = ctx.scene

        # Load FBX File
        _log("INFO", "Parsing FBX file hierarchy...")
        load_fbx_file(scene, manager, str(input_file))

        # 1. EVALUATE GLOBAL SCALE & BOUNDING BOX
        _log("INFO", "Step 1: Evaluating visual bounding box dimensions in world space...")
        norm_factor, visual_height, up_axis = calculate_normalization_factor(
            scene,
            auto_normalize=auto_normalize,
            manual_multiplier=manual_multiplier,
            target_height_cm=target_height_cm
        )

        if auto_normalize:
            _log("INFO", f"Visual viewport height: {visual_height:.2f} units (Up-Axis: {up_axis})")
            _log("INFO", f"Unreal target height: {target_height_cm:.1f} cm")
            _log("INFO", f"Uniform normalization factor: {norm_factor:.6f}")
        else:
            _log("INFO", f"Manual multiplier active: {norm_factor:.6f}")

        # 2. BAKE MATRICES (PER-AXIS NON-UNIFORM PRESERVATION)
        _log("INFO", "Step 2: Baking per-axis non-uniform scale (X, Y, Z) into geometry control points...")
        num_vertices = bake_mesh_geometry_non_uniform(scene, norm_factor)
        _log("INFO", f"Complete: {num_vertices} vertex control points & morph targets baked per-axis.")

        _log("INFO", "Baking bone spatial translation (FbxSkeleton LclTranslation)...")
        num_bones = scale_skeleton_translations(scene, norm_factor)
        _log("INFO", f"Complete: {num_bones} skeleton bones baked.")

        _log("INFO", "Extracting and baking translation animation curves...")
        curves_count, keys_count = scale_scene_animations(scene, norm_factor)
        _log("INFO", f"Complete: {curves_count} translation curves ({keys_count} keyframes) baked.")

        # 3. ABSOLUTE RESET OF ALL NODES (CRITICAL)
        _log("INFO", "Step 3 (CRITICAL): Resetting LclScaling & GeometricScaling across ALL scene nodes to (1.0, 1.0, 1.0)...")
        num_nodes_reset = reset_all_nodes_scaling(scene)
        _log("INFO", f"Complete: {num_nodes_reset} scene nodes frozen to scale 1.0.")

        # 4. RECALCULATE CLUSTERS & BIND POSES
        _log("INFO", "Step 4: Recalculating FbxCluster (TransformMatrix & TransformLinkMatrix) from new nodes...")
        clusters_count, poses_count = update_skinning_and_bind_pose(scene)
        _log("INFO", f"Complete: {clusters_count} skin clusters & {poses_count} pose nodes updated.")

        # 5. BLOCK AUTOMATIC SDK CONVERSION & ENFORCE UE METADATA
        _log("INFO", "Step 5: Blocking SDK auto-scaling & enforcing Unreal Engine metadata (cm, Z-Up)...")
        convert_scene_metadata_to_ue(scene, _log)

        # Export to New FBX File
        _log("INFO", f"Exporting baked asset to: {Path(output_path).name}...")
        save_fbx_file(scene, manager, output_path)
        _log("SUCCESS", f"Successfully exported: {output_path}")

    return {
        "input_path": input_path,
        "output_path": output_path,
        "norm_factor": norm_factor,
        "vertices_scaled": num_vertices,
        "bones_scaled": num_bones,
        "nodes_reset": num_nodes_reset,
        "clusters_scaled": clusters_count,
        "curves_scaled": curves_count,
        "keys_scaled": keys_count
    }
