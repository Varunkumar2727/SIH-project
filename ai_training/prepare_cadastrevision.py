"""
Data Preparation & Patching Adapter for CadastreVision Benchmark Subset.

Performs:
1. Retrieval/Extraction of designated CadastreVision benchmark tiles.
2. Conversion of parcel polygons/lines to raster boundary ground truth masks.
3. 512x512 patch generation with overlap to prevent edge boundary clipping.
4. Scene metadata tagging to guarantee spatial data leakage prevention.
"""

import os
import json
import argparse
from typing import List, Dict, Any, Tuple
import numpy as np
from PIL import Image
import cv2
from rasterio.features import rasterize
from rasterio.transform import Affine
from shapely.geometry import shape
from shapely.ops import transform as shapely_transform
from shapely.validation import make_valid
from pyproj import CRS, Transformer

try:
    from shapely.geometry import Polygon, LineString, MultiPolygon
    from shapely import wkt
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False


def rasterize_boundary_geometries(
    geometries: List[Any],
    width: int,
    height: int,
    image_transform: Affine,
    image_crs: Any,
    geometry_crs: Any,
    boundary_width_px: int = 3
) -> np.ndarray:
    """Rasterize authorized vector boundaries into a binary image-aligned mask."""
    if boundary_width_px < 1:
        raise ValueError("boundary_width_px must be at least 1")
    if width < 1 or height < 1:
        raise ValueError("Raster dimensions must be positive")
    if image_transform is None:
        raise ValueError("image_transform is required for GIS geometry rasterization")
    if image_crs is None or geometry_crs is None:
        if image_crs != geometry_crs:
            raise ValueError("Both image_crs and geometry_crs are required when CRS values differ")

    source_crs = CRS.from_user_input(geometry_crs) if geometry_crs is not None else None
    target_crs = CRS.from_user_input(image_crs) if image_crs is not None else None
    coordinate_transform = None
    if source_crs != target_crs:
        coordinate_transform = Transformer.from_crs(source_crs, target_crs, always_xy=True).transform

    boundary_shapes = []
    for geometry in geometries:
        geom = shape(geometry) if isinstance(geometry, dict) else geometry
        if geom is None or geom.is_empty:
            continue
        if not geom.is_valid:
            geom = make_valid(geom)
        if geom.is_empty:
            continue
        if coordinate_transform is not None:
            geom = shapely_transform(coordinate_transform, geom)
        boundary = geom.boundary
        if not boundary.is_empty:
            boundary_shapes.append((boundary, 1))

    if not boundary_shapes:
        raise ValueError("No valid boundary geometries were supplied")

    mask = rasterize(
        boundary_shapes,
        out_shape=(height, width),
        transform=image_transform,
        fill=0,
        dtype="uint8",
        all_touched=True
    )
    if boundary_width_px > 1:
        kernel_size = boundary_width_px if boundary_width_px % 2 == 1 else boundary_width_px + 1
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        mask = cv2.dilate(mask, kernel)
    return (mask > 0).astype(np.uint8) * 255


def validate_image_mask_alignment(image_shape: Tuple[int, int], mask: np.ndarray) -> None:
    """Reject masks whose raster grid does not match the source image grid."""
    if mask.ndim != 2 or tuple(mask.shape) != tuple(image_shape):
        raise ValueError(
            f"Image/mask alignment mismatch: image={tuple(image_shape)}, mask={tuple(mask.shape)}"
        )
    unique_values = set(np.unique(mask).tolist())
    if not unique_values.issubset({0, 1, 255}):
        raise ValueError(f"Mask contains non-binary values: {sorted(unique_values)}")


def load_boundary_geometries(annotation_path: str) -> Tuple[List[Any], Any]:
    """Load GeoJSON or GeoPackage boundaries and return geometries plus their CRS."""
    extension = os.path.splitext(annotation_path)[1].lower()
    if extension in {".geojson", ".json"}:
        with open(annotation_path, "r", encoding="utf-8") as annotation_file:
            document = json.load(annotation_file)
        if document.get("type") == "FeatureCollection":
            features = document.get("features", [])
            geometries = [shape(feature["geometry"]) for feature in features if feature.get("geometry")]
        elif document.get("type") == "Feature":
            geometries = [shape(document["geometry"])]
        else:
            geometries = [shape(document)]
        return geometries, document.get("crs", {}).get("properties", {}).get("name")
    if extension == ".gpkg":
        try:
            import geopandas as gpd
        except ImportError as exc:
            raise RuntimeError("geopandas is required to read GeoPackage annotations") from exc
        frame = gpd.read_file(annotation_path)
        return list(frame.geometry.dropna()), frame.crs
    raise ValueError(f"Unsupported boundary annotation format: {annotation_path}")


def create_boundary_mask_from_polygons(
    polygons: List[Any],
    width: int,
    height: int,
    boundary_width_px: int = 3
) -> np.ndarray:
    """
    Renders polygon borders into a binary raster boundary mask.
    """
    mask = np.zeros((height, width), dtype=np.uint8)

    for poly in polygons:
        if hasattr(poly, "exterior") and poly.exterior is not None:
            coords = np.array(poly.exterior.coords, dtype=np.int32)
            cv2.polylines(mask, [coords], isClosed=True, color=255, thickness=boundary_width_px)
            for interior in poly.interiors:
                int_coords = np.array(interior.coords, dtype=np.int32)
                cv2.polylines(mask, [int_coords], isClosed=True, color=255, thickness=boundary_width_px)
        elif isinstance(poly, list):
            coords = np.array(poly, dtype=np.int32)
            cv2.polylines(mask, [coords], isClosed=True, color=255, thickness=boundary_width_px)

    return mask


def extract_patches(
    image_np: np.ndarray,
    mask_np: np.ndarray,
    patch_size: int = 512,
    overlap_ratio: float = 0.15,
    min_boundary_pixels: int = 20
) -> List[Dict[str, Any]]:
    """
    Extracts sliding window patches of (patch_size x patch_size) from high-res image and mask.
    """
    if image_np.ndim != 3 or image_np.shape[2] != 3:
        raise ValueError("Images must have shape (height, width, 3)")
    if mask_np.ndim != 2 or mask_np.shape != image_np.shape[:2]:
        raise ValueError("Image and mask must have matching spatial dimensions")
    h, w = image_np.shape[:2]
    step = int(patch_size * (1.0 - overlap_ratio))
    if step < 1:
        step = patch_size

    patches = []
    patch_idx = 0

    y_coords = list(range(0, max(1, h - patch_size + step), step))
    x_coords = list(range(0, max(1, w - patch_size + step), step))

    for y in y_coords:
        for x in x_coords:
            y1 = min(y, max(0, h - patch_size))
            x1 = min(x, max(0, w - patch_size))
            y2 = min(y1 + patch_size, h)
            x2 = min(x1 + patch_size, w)

            img_crop = image_np[y1:y2, x1:x2]
            mask_crop = mask_np[y1:y2, x1:x2]

            # Pad if needed on edges
            if img_crop.shape[0] != patch_size or img_crop.shape[1] != patch_size:
                pad_img = np.zeros((patch_size, patch_size, 3), dtype=image_np.dtype)
                pad_mask = np.zeros((patch_size, patch_size), dtype=mask_np.dtype)
                pad_img[:img_crop.shape[0], :img_crop.shape[1]] = img_crop
                pad_mask[:mask_crop.shape[0], :mask_crop.shape[1]] = mask_crop
                img_crop = pad_img
                mask_crop = pad_mask

            boundary_px_count = int(np.sum(mask_crop > 127))

            patches.append({
                "patch_id": f"p_{patch_idx:04d}",
                "bbox": [x1, y1, x2, y2],
                "boundary_pixels": boundary_px_count,
                "image": img_crop,
                "mask": mask_crop
            })
            patch_idx += 1

    return patches


def prepare_cadastrevision_subset(
    raw_dir: str,
    output_dir: str,
    patch_size: int = 512,
    overlap: float = 0.15,
    allow_synthetic_fixture: bool = False
) -> Dict[str, Any]:
    """
    Prepares and packages a small reproducible CadastreVision prototype subset.
    """
    img_out_dir = os.path.join(output_dir, "images")
    mask_out_dir = os.path.join(output_dir, "masks")
    os.makedirs(img_out_dir, exist_ok=True)
    os.makedirs(mask_out_dir, exist_ok=True)

    manifest_samples = []

    # Synthetic fixtures are only available through an explicit test-only opt-in.
    raw_images = [
        f for f in os.listdir(raw_dir)
        if f.lower().endswith((".png", ".jpg", ".tif", ".tiff"))
        and not f.lower().endswith("_mask.png")
    ] if os.path.exists(raw_dir) else []

    if not raw_images:
        if not allow_synthetic_fixture:
            raise FileNotFoundError(
                "REAL CADASTREVISION DATA NOT FOUND: expected labelled imagery and masks in "
                f"'{raw_dir}'. Obtain an authorised subset before preparing training data."
            )
        print(f"[TEST ONLY] No raw imagery found in {raw_dir}. Generating an explicitly synthetic fixture...")
        # Create 2 distinct scenes for reproducible demonstration and tests
        for scene_idx, scene_name in enumerate(["scene_north_sector", "scene_south_sector"]):
            h, w = 1024, 1024
            synth_img = np.full((h, w, 3), 120 + scene_idx * 20, dtype=np.uint8)
            
            # Synthetic parcel boundaries
            polys = [
                [[100, 100], [450, 100], [450, 450], [100, 450]],
                [[450, 100], [900, 100], [900, 450], [450, 450]],
                [[100, 450], [450, 450], [450, 900], [100, 900]],
                [[450, 450], [900, 450], [900, 900], [450, 900]]
            ]
            synth_mask = create_boundary_mask_from_polygons(polys, w, h, boundary_width_px=3)

            # Draw grid lines on image for realistic appearance
            cv2.polylines(synth_img, [np.array(p, dtype=np.int32) for p in polys], True, (40, 40, 40), 3)

            patches = extract_patches(synth_img, synth_mask, patch_size=patch_size, overlap_ratio=overlap)
            for p in patches:
                img_name = f"{scene_name}_{p['patch_id']}.png"
                mask_name = f"{scene_name}_{p['patch_id']}_mask.png"
                img_path = os.path.join(img_out_dir, img_name)
                mask_path = os.path.join(mask_out_dir, mask_name)

                Image.fromarray(p["image"]).save(img_path)
                Image.fromarray(p["mask"]).save(mask_path)

                manifest_samples.append({
                    "sample_id": f"{scene_name}_{p['patch_id']}",
                    "scene_id": scene_name,
                    "image_path": img_path,
                    "mask_path": mask_path,
                    "width": patch_size,
                    "height": patch_size,
                    "boundary_pixels": p["boundary_pixels"]
                })
    else:
        # Process actual downloaded imagery
        for img_name in raw_images:
            base_name = os.path.splitext(img_name)[0]
            scene_id = base_name.split("_")[0] if "_" in base_name else base_name
            img_path = os.path.join(raw_dir, img_name)
            img = cv2.imread(img_path)
            if img is None:
                continue
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            h, w = img_rgb.shape[:2]

            # Look for corresponding mask or polygon annotation
            mask_candidate = os.path.join(raw_dir, f"{base_name}_mask.png")
            vector_candidates = [
                os.path.join(raw_dir, f"{base_name}_boundaries.geojson"),
                os.path.join(raw_dir, f"{base_name}_boundaries.gpkg")
            ]
            vector_candidate = next((path for path in vector_candidates if os.path.exists(path)), None)
            if vector_candidate:
                import rasterio
                geometries, geometry_crs = load_boundary_geometries(vector_candidate)
                with rasterio.open(img_path) as raster:
                    if raster.crs is None or raster.transform is None:
                        raise ValueError(f"Georeferenced raster required for vector labels: {img_path}")
                    mask = rasterize_boundary_geometries(
                        geometries,
                        width=w,
                        height=h,
                        image_transform=raster.transform,
                        image_crs=raster.crs,
                        geometry_crs=geometry_crs,
                        boundary_width_px=3
                    )
            elif os.path.exists(mask_candidate):
                mask = cv2.imread(mask_candidate, cv2.IMREAD_GRAYSCALE)
            else:
                raise FileNotFoundError(
                    "REAL CADASTREVISION DATA NOT FOUND: missing labelled mask for "
                    f"'{img_name}'. Expected '{mask_candidate}' or a matching '*_boundaries.geojson/.gpkg'."
                )
            if mask is None:
                raise ValueError(f"Unable to read mask: {mask_candidate}")
            validate_image_mask_alignment((h, w), mask)
            mask = (mask > 0).astype(np.uint8) * 255

            patches = extract_patches(img_rgb, mask, patch_size=patch_size, overlap_ratio=overlap)
            for p in patches:
                out_img_name = f"{base_name}_{p['patch_id']}.png"
                out_mask_name = f"{base_name}_{p['patch_id']}_mask.png"
                p_img_path = os.path.join(img_out_dir, out_img_name)
                p_mask_path = os.path.join(mask_out_dir, out_mask_name)

                Image.fromarray(p["image"]).save(p_img_path)
                Image.fromarray(p["mask"]).save(p_mask_path)

                manifest_samples.append({
                    "sample_id": f"{base_name}_{p['patch_id']}",
                    "scene_id": scene_id,
                    "image_path": p_img_path,
                    "mask_path": p_mask_path,
                    "width": patch_size,
                    "height": patch_size,
                    "boundary_pixels": p["boundary_pixels"]
                })

    manifest = {
        "dataset_name": "Synthetic_Development_Fixture" if allow_synthetic_fixture else "CadastreVision_Real_Subset",
        "is_synthetic": bool(allow_synthetic_fixture),
        "total_patches": len(manifest_samples),
        "patch_size": patch_size,
        "overlap_ratio": overlap,
        "samples": manifest_samples
    }

    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"[SUCCESS] Prepared {len(manifest_samples)} patches in {output_dir}")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare CadastreVision dataset subset.")
    parser.add_argument("--raw_dir", type=str, default="data/raw_cadastrevision", help="Directory with raw tiles")
    parser.add_argument("--output_dir", type=str, default="data/cadastrevision", help="Directory for processed patches")
    parser.add_argument("--patch_size", type=int, default=512, help="Patch width/height")
    parser.add_argument("--overlap", type=float, default=0.15, help="Sliding window overlap ratio")
    args = parser.parse_args()

    prepare_cadastrevision_subset(args.raw_dir, args.output_dir, args.patch_size, args.overlap)
