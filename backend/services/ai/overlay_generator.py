import os
import cv2
import numpy as np
from typing import Dict, Any, List

def generate_ai_overlay(
    image_path: str,
    image_id: str,
    detection_results: Dict[str, Any],
    parcels: List[Dict[str, Any]],
    results_dir: str
) -> str:
    """
    Renders high-contrast, semi-transparent cadastral overlay with AI-detected
    buildings, road infrastructure, vegetation canopy, and proposed parcel boundaries.
    """
    img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        return ""

    h, w = img_bgr.shape[:2]
    overlay_img = img_bgr.copy()
    mask_layer = np.zeros_like(img_bgr)

    features = detection_results.get("features", {})

    # 1. Bare Land / Open Land: Amber Yellow
    open_land_list = features.get("open_land") or features.get("bare_land", [])
    for land in open_land_list:
        pts = np.array(land.get("polygon", []), dtype=np.int32)
        if len(pts) >= 3:
            cv2.fillPoly(mask_layer, [pts], (0, 215, 255))
            cv2.polylines(overlay_img, [pts], True, (0, 180, 220), 1)

    # 2. Vegetation: Emerald Green
    for veg in features.get("vegetation", []):
        pts = np.array(veg.get("polygon", []), dtype=np.int32)
        if len(pts) >= 3:
            cv2.fillPoly(mask_layer, [pts], (50, 205, 50))
            cv2.polylines(overlay_img, [pts], True, (30, 160, 30), 1)

    # 3. Roads: Slate Cyan
    for road in features.get("roads", []):
        pts = np.array(road.get("polygon", []), dtype=np.int32)
        if len(pts) >= 3:
            cv2.fillPoly(mask_layer, [pts], (255, 180, 0))
            cv2.polylines(overlay_img, [pts], True, (200, 140, 0), 2)

    # 4. Buildings: Bright Coral/Red
    for bld in features.get("buildings", []):
        pts = np.array(bld.get("polygon", []), dtype=np.int32)
        if len(pts) >= 3:
            cv2.fillPoly(mask_layer, [pts], (0, 90, 255))
            cv2.polylines(overlay_img, [pts], True, (0, 50, 200), 2)

    # 5. Blend color masks
    alpha = 0.40
    cv2.addWeighted(mask_layer, alpha, overlay_img, 1.0 - alpha, 0, overlay_img)

    # 6. Draw crisp Purple Parcel Boundaries
    for parcel in parcels:
        pts = np.array(parcel.get("polygon", []), dtype=np.int32)
        if len(pts) >= 3:
            cv2.polylines(overlay_img, [pts], True, (247, 85, 168), 2)

    overlay_filename = f"{image_id}_overlay.png"
    overlay_path = os.path.join(results_dir, overlay_filename)
    cv2.imwrite(overlay_path, overlay_img)

    return f"/api/images/result/{overlay_filename}"
