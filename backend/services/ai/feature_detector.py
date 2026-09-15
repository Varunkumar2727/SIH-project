import os
import cv2
import numpy as np
from typing import Dict, Any, List, Optional
from shapely.geometry import Polygon, MultiPolygon, mapping
from shapely.validation import make_valid
from shapely import simplify

from .model_manager import ModelManager

class FeatureDetector:
    """
    Executes real semantic segmentation and geometric polygonization on aerial imagery.
    Integrates with ModelManager for tiled processing and outputs valid Shapely polygons
    with real pixel and georeferenced properties.
    """

    CLASS_THRESHOLDS = {
        "building": 0.28,
        "road": 0.25,
        "vegetation": 0.25,
        "water": 0.28,
        "bare_land": 0.25
    }

    MIN_AREA_PX = {
        "building": 75,
        "road": 90,
        "vegetation": 75,
        "water": 90,
        "bare_land": 75
    }

    def __init__(self, model_manager: Optional[ModelManager] = None):
        self.manager = model_manager or ModelManager.get_instance()

    def detect_features(
        self,
        image_path: str,
        meta: Optional[Dict[str, Any]] = None,
        tile_size: int = 512,
        overlap_ratio: float = 0.15
    ) -> Dict[str, Any]:
        """
        Loads the image, runs tiled inference, cleans masks, vectorizes into polygons,
        and computes metrics without any fabricated data.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found at {image_path}")

        img_bgr = cv2.imread(image_path)
        if img_bgr is None:
            raise ValueError(f"Unable to read image file: {image_path}")

        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        h, w = img_rgb.shape[:2]

        probs = self.manager.run_tiled_inference(
            img_rgb,
            tile_size=tile_size,
            overlap_ratio=overlap_ratio
        )

        features: Dict[str, List[Dict[str, Any]]] = {
            "buildings": [],
            "roads": [],
            "vegetation": [],
            "water": [],
            "bare_land": []
        }

        # Class indices: 0: background, 1: building, 2: road, 3: vegetation, 4: water, 5: bare_land
        # Priority order: Hard structures & infrastructure first, followed by natural terrain
        ordered_classes = [
            (1, "building", "buildings"),
            (2, "road", "roads"),
            (4, "water", "water"),
            (3, "vegetation", "vegetation"),
            (5, "bare_land", "bare_land")
        ]

        transform = None
        crs = None
        if meta:
            transform = meta.get("transform") or (meta.get("geospatial", {}).get("transform"))
            crs = meta.get("crs") or (meta.get("geospatial", {}).get("crs"))

        total_detected_features = 0

        # Multi-class competitive argmax: each pixel is allocated to its dominant class
        pred_classes = np.argmax(probs, axis=-1)
        winner_prob = np.max(probs, axis=-1)
        allocated_mask = np.zeros((h, w), dtype=bool)

        for class_idx, class_name, key_name in ordered_classes:
            class_prob = probs[:, :, class_idx]
            threshold = self.CLASS_THRESHOLDS.get(class_name, 0.25)
            # Mutual exclusion: pixel must be dominant winner, exceed threshold, and not overlap existing higher-priority layers
            class_mask = (pred_classes == class_idx) & (winner_prob >= threshold) & (~allocated_mask)
            binary_mask = class_mask.astype(np.uint8) * 255

            # Morphological noise suppression:
            # 1. Opening removes isolated pixel speckles
            kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            cleaned_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel_open)
            # 2. Closing bridges hairline cracks and consolidates footprints
            kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            cleaned_mask = cv2.morphologyEx(cleaned_mask, cv2.MORPH_CLOSE, kernel_close)

            # Mark allocated pixels to guarantee zero overlap across layers
            allocated_mask |= (cleaned_mask > 0)

            # Find contours
            contours, hierarchy = cv2.findContours(
                cleaned_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            # Class-specific epsilon: tighter for buildings/roads to preserve rectilinear cadastral geometry
            epsilon_factors = {
                "building": 0.005,   # Sharp 90-degree corners and clean edges
                "road": 0.008,       # Straight road corridors
                "vegetation": 0.012, # Organic tree canopy contours
                "water": 0.012,      # Smooth water boundaries
                "bare_land": 0.015   # Natural open earth contours
            }
            eps_factor = epsilon_factors.get(class_name, 0.010)

            for cnt_idx, cnt in enumerate(contours):
                # Polygon approximation
                epsilon = eps_factor * cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, epsilon, True)
                
                if len(approx) < 3:
                    continue

                pts = approx.reshape(-1, 2)
                raw_polygon = Polygon(pts)
                if not raw_polygon.is_valid:
                    raw_polygon = make_valid(raw_polygon)
                    if not raw_polygon.is_valid or raw_polygon.is_empty:
                        continue

                # Orthogonal cadastral snapping for buildings: convert wavy contours to sharp 90-degree surveyor footprints
                if class_name == "building" and len(pts) >= 4:
                    try:
                        rect = cv2.minAreaRect(pts.astype(np.float32))
                        box = cv2.boxPoints(rect)
                        box_poly = Polygon(box)
                        if box_poly.is_valid and box_poly.area > 0 and raw_polygon.area > 0:
                            iou = raw_polygon.intersection(box_poly).area / (raw_polygon.union(box_poly).area + 1e-6)
                            if iou >= 0.65:
                                pts = np.array([[round(float(p[0]), 1), round(float(p[1]), 1)] for p in box])
                                raw_polygon = box_poly
                    except Exception:
                        pass

                area_px = float(raw_polygon.area)
                if area_px < self.MIN_AREA_PX.get(class_name, 50):
                    continue

                # Measure actual mean confidence within the contour
                c_mask = np.zeros((h, w), dtype=np.uint8)
                cv2.drawContours(c_mask, [approx], -1, 255, -1)
                mean_conf = float(np.mean(class_prob[c_mask == 255])) if np.any(c_mask == 255) else float(threshold)

                # Pixel coordinates list [[x, y], ...]
                coords = [[float(p[0]), float(p[1])] for p in pts]
                # Close loop
                if coords and coords[0] != coords[-1]:
                    coords.append(coords[0])

                feature_id = f"feat_{class_name[:4]}_{cnt_idx}_{int(area_px)}"
                feature_obj = {
                    "id": feature_id,
                    "type": class_name,
                    "confidence": round(mean_conf, 4),
                    "area_px": round(area_px, 2),
                    "perimeter_px": round(float(raw_polygon.length), 2),
                    "polygon": coords,
                    "bbox": [float(b) for b in raw_polygon.bounds] # [minx, miny, maxx, maxy]
                }

                # Georeference coordinates if transform is available
                if transform:
                    from services.geospatial import pixel_to_world
                    geo_coords = []
                    for px, py in coords:
                        wx, wy = pixel_to_world(px, py, transform)
                        geo_coords.append([round(wx, 4), round(wy, 4)])
                    feature_obj["geo_polygon"] = geo_coords
                    feature_obj["crs"] = crs

                features[key_name].append(feature_obj)
                total_detected_features += 1

        # Open land alias for frontend layer toggle
        features["open_land"] = features["bare_land"]

        stats = {
            "total_features": total_detected_features,
            "buildings_count": len(features["buildings"]),
            "roads_count": len(features["roads"]),
            "vegetation_count": len(features["vegetation"]),
            "water_count": len(features["water"]),
            "bare_land_count": len(features["bare_land"]),
            "buildings_detected": len(features["buildings"]),
            "road_areas": len(features["roads"]),
            "vegetation_areas": len(features["vegetation"]),
            "open_land_areas": len(features["open_land"]),
            "model_version": self.manager.get_model_metadata(self.manager.active_model_id).get("version", "1.0.0"),
            "inference_device": self.manager.device
        }

        return {
            "features": features,
            "stats": stats,
            "image_dimensions": {"width": w, "height": h}
        }
