import os
import cv2
import numpy as np
from services.image_processing import load_image_cv, preprocess_image

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


def analyze_image(image_path: str, image_id: str = None, meta: dict = None) -> dict:
    """
    Analyzes real-world aerial/satellite imagery to detect land features:
    - Buildings (Slate blue/gray, terracotta red/orange, light concrete roofs)
    - Roads (Paved asphalt highways & unpaved dirt access paths)
    - Vegetation (Trees, grass, gardens)
    - Open Land (Bare soil, vacant plots)
    """
    if image_id is None:
        image_id = os.path.splitext(os.path.basename(image_path))[0]

    img_bgr = load_image_cv(image_path)
    height, width = img_bgr.shape[:2]
    total_pixels = height * width

    # Preprocess image
    prep = preprocess_image(img_bgr)
    hsv = prep["hsv"]
    gray = prep["gray"]
    edges = prep["edges"]

    # -------------------------------------------------------------
    # 1. VEGETATION DETECTION (Green Trees & Lawn Canopy)
    # -------------------------------------------------------------
    lower_green = np.array([25, 25, 25])
    upper_green = np.array([90, 255, 255])
    veg_mask = cv2.inRange(hsv, lower_green, upper_green)

    kernel_veg = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    veg_mask = cv2.morphologyEx(veg_mask, cv2.MORPH_OPEN, kernel_veg)
    veg_mask = cv2.morphologyEx(veg_mask, cv2.MORPH_CLOSE, kernel_veg)

    veg_contours, _ = cv2.findContours(veg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    vegetation_features = []
    min_veg_area = max(50, total_pixels * 0.00025)

    for i, cnt in enumerate(veg_contours):
        area = cv2.contourArea(cnt)
        if area >= min_veg_area:
            epsilon = 0.015 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)
            pts = approx.reshape(-1, 2).tolist()
            if len(pts) >= 3:
                vegetation_features.append({
                    "id": f"veg_{i+1}",
                    "feature_type": "vegetation",
                    "polygon": pts,
                    "area_px": round(area, 2)
                })

    # -------------------------------------------------------------
    # 2. ROAD DETECTION (Asphalt Highways & Unpaved Dirt Paths)
    # -------------------------------------------------------------
    # Paved asphalt (slate gray)
    lower_asphalt = np.array([0, 0, 40])
    upper_asphalt = np.array([180, 50, 210])
    asphalt_mask = cv2.inRange(hsv, lower_asphalt, upper_asphalt)

    # Unpaved dirt paths (tan/gray pathways)
    lower_dirt = np.array([10, 15, 80])
    upper_dirt = np.array([32, 85, 220])
    dirt_mask = cv2.inRange(hsv, lower_dirt, upper_dirt)

    road_mask = cv2.bitwise_or(asphalt_mask, dirt_mask)
    road_mask = cv2.bitwise_and(road_mask, cv2.bitwise_not(veg_mask))

    # Directional morphology to connect elongated transport paths
    k_horiz = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 3))
    k_vert = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 21))
    road_horiz = cv2.morphologyEx(road_mask, cv2.MORPH_OPEN, k_horiz)
    road_vert = cv2.morphologyEx(road_mask, cv2.MORPH_OPEN, k_vert)
    combined_road_mask = cv2.bitwise_or(road_horiz, road_vert)

    kernel_road_close = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
    combined_road_mask = cv2.morphologyEx(combined_road_mask, cv2.MORPH_CLOSE, kernel_road_close)

    road_contours, _ = cv2.findContours(combined_road_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    road_features = []
    min_road_area = max(120, total_pixels * 0.0004)

    for i, cnt in enumerate(road_contours):
        area = cv2.contourArea(cnt)
        if area >= min_road_area:
            epsilon = 0.018 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)
            pts = approx.reshape(-1, 2).tolist()
            if len(pts) >= 3:
                road_features.append({
                    "id": f"road_{i+1}",
                    "feature_type": "road",
                    "polygon": pts,
                    "area_px": round(area, 2)
                })

    # -------------------------------------------------------------
    # 3. BUILDING DETECTION (Multi-Spectrum Roof Segmentation)
    # -------------------------------------------------------------
    # Exclude vegetation and roads
    non_veg_road = cv2.bitwise_and(cv2.bitwise_not(veg_mask), cv2.bitwise_not(combined_road_mask))

    # Spectrum A: Terracotta Red / Orange Clay Roofs
    roof_red1 = cv2.inRange(hsv, np.array([0, 35, 60]), np.array([22, 255, 255]))
    roof_red2 = cv2.inRange(hsv, np.array([160, 35, 60]), np.array([180, 255, 255]))
    roof_red = cv2.bitwise_or(roof_red1, roof_red2)

    # Spectrum B: Blue / Charcoal Slate Roofs
    roof_slate = cv2.inRange(hsv, np.array([85, 15, 30]), np.array([135, 220, 180]))

    # Spectrum C: High Brightness / Concrete Roofs
    roof_bright = cv2.inRange(hsv, np.array([0, 0, 180]), np.array([180, 40, 255]))

    # Combine roof masks
    roof_combined = cv2.bitwise_or(roof_red, roof_slate)
    roof_combined = cv2.bitwise_or(roof_combined, roof_bright)
    roof_candidates = cv2.bitwise_and(roof_combined, non_veg_road)

    # Clean roof candidates with morphological opening & closing
    kernel_bld = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    roof_candidates = cv2.morphologyEx(roof_candidates, cv2.MORPH_OPEN, kernel_bld)
    roof_candidates = cv2.morphologyEx(roof_candidates, cv2.MORPH_CLOSE, kernel_bld)

    bld_contours, _ = cv2.findContours(roof_candidates, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    building_features = []
    min_bld_area = max(80, total_pixels * 0.0002)
    max_bld_area = total_pixels * 0.12

    for i, cnt in enumerate(bld_contours):
        area = cv2.contourArea(cnt)
        if min_bld_area <= area <= max_bld_area:
            x, y, w, h = cv2.boundingRect(cnt)
            rect_area = w * h
            extent = float(area) / rect_area if rect_area > 0 else 0
            aspect_ratio = float(w) / h if h > 0 else 0

            # Filter building shapes (rectangular extent >= 0.42, aspect ratio 0.15..6.0)
            if extent >= 0.42 and 0.15 <= aspect_ratio <= 6.0:
                epsilon = 0.018 * cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, epsilon, True)
                pts = approx.reshape(-1, 2).tolist()
                if len(pts) >= 3:
                    confidence = round(min(0.98, max(0.72, extent * 1.12)), 2)
                    building_features.append({
                        "id": f"bld_{i+1}",
                        "feature_type": "building",
                        "polygon": pts,
                        "bbox": [x, y, w, h],
                        "confidence": confidence,
                        "area_px": round(area, 2)
                    })

    # -------------------------------------------------------------
    # 4. OPEN LAND DETECTION (Vacant Ground & Soil Patches)
    # -------------------------------------------------------------
    occupied_mask = cv2.bitwise_or(veg_mask, combined_road_mask)
    for bld in building_features:
        pts = np.array(bld["polygon"], dtype=np.int32)
        cv2.fillPoly(occupied_mask, [pts], 255)

    open_land_mask = cv2.bitwise_not(occupied_mask)
    kernel_land = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
    open_land_mask = cv2.morphologyEx(open_land_mask, cv2.MORPH_OPEN, kernel_land)

    land_contours, _ = cv2.findContours(open_land_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    open_land_features = []
    min_land_area = max(250, total_pixels * 0.0008)

    for i, cnt in enumerate(land_contours):
        area = cv2.contourArea(cnt)
        if area >= min_land_area:
            epsilon = 0.02 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)
            pts = approx.reshape(-1, 2).tolist()
            if len(pts) >= 3:
                open_land_features.append({
                    "id": f"land_{i+1}",
                    "feature_type": "open_land",
                    "polygon": pts,
                    "area_px": round(area, 2)
                })

    # -------------------------------------------------------------
    # 5. GENERATE OVERLAY IMAGE WITH ACCENT COLORS
    # -------------------------------------------------------------
    overlay_img = img_bgr.copy()
    mask_layer = np.zeros_like(img_bgr)

    # Open Land: Amber Yellow
    for land in open_land_features:
        pts = np.array(land["polygon"], dtype=np.int32)
        cv2.fillPoly(mask_layer, [pts], (0, 215, 255))
        cv2.polylines(overlay_img, [pts], True, (0, 180, 220), 2)

    # Vegetation: Emerald Green
    for veg in vegetation_features:
        pts = np.array(veg["polygon"], dtype=np.int32)
        cv2.fillPoly(mask_layer, [pts], (50, 205, 50))
        cv2.polylines(overlay_img, [pts], True, (30, 160, 30), 2)

    # Roads: Slate Cyan
    for road in road_features:
        pts = np.array(road["polygon"], dtype=np.int32)
        cv2.fillPoly(mask_layer, [pts], (255, 180, 0))
        cv2.polylines(overlay_img, [pts], True, (200, 140, 0), 2)

    # Buildings: Bright Orange/Red
    for bld in building_features:
        pts = np.array(bld["polygon"], dtype=np.int32)
        cv2.fillPoly(mask_layer, [pts], (0, 90, 255))
        cv2.polylines(overlay_img, [pts], True, (0, 50, 200), 2)

    alpha = 0.42
    cv2.addWeighted(mask_layer, alpha, overlay_img, 1 - alpha, 0, overlay_img)

    overlay_filename = f"{image_id}_overlay.png"
    overlay_path = os.path.join(RESULTS_DIR, overlay_filename)
    cv2.imwrite(overlay_path, overlay_img)

    results = {
        "image_id": image_id,
        "detection_mode": "Prototype Computer Vision",
        "overlay_url": f"/api/images/result/{overlay_filename}",
        "dimensions": {"width": width, "height": height},
        "stats": {
            "buildings_detected": len(building_features),
            "road_areas": len(road_features),
            "vegetation_areas": len(vegetation_features),
            "open_land_areas": len(open_land_features),
            "proposed_parcels": 0
        },
        "features": {
            "buildings": building_features,
            "roads": road_features,
            "vegetation": vegetation_features,
            "open_land": open_land_features
        }
    }

    return results
