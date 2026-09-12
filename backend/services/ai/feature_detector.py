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
        "building": 0.45,
        "road": 0.40,
        "vegetation": 0.50,
        "water": 0.55,
        "bare_land": 0.40
    }

    MIN_AREA_PX = {
        "building": 60,
        "road": 100,
        "vegetation": 120,
        "water": 150,
        "bare_land": 150
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
        class_map = {
            1: ("building", "buildings"),
            2: ("road", "roads"),
            3: ("vegetation", "vegetation"),
            4: ("water", "water"),
            5: ("bare_land", "bare_land")
        }

        transform = None
        crs = None
        if meta:
            transform = meta.get("transform") or (meta.get("geospatial", {}).get("transform"))
            crs = meta.get("crs") or (meta.get("geospatial", {}).get("crs"))

        total_detected_features = 0

        for class_idx, (class_name, key_name) in class_map.items():
            class_prob = probs[:, :, class_idx]
            threshold = self.CLASS_THRESHOLDS.get(class_name, 0.5)
            binary_mask = (class_prob >= threshold).astype(np.uint8) * 255

            # Morphological smoothing to remove isolated noise and close micro-holes
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            cleaned_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel)
            cleaned_mask = cv2.morphologyEx(cleaned_mask, cv2.MORPH_CLOSE, kernel)

            # Find contours
            contours, hierarchy = cv2.findContours(
                cleaned_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            for cnt_idx, cnt in enumerate(contours):
                # Polygon approximation
                epsilon = 0.015 * cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, epsilon, True)
                
                if len(approx) < 3:
                    continue

                pts = approx.reshape(-1, 2)
                raw_polygon = Polygon(pts)
                if not raw_polygon.is_valid:
                    raw_polygon = make_valid(raw_polygon)
                    if not raw_polygon.is_valid or raw_polygon.is_empty:
                        continue

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

        stats = {
            "total_features": total_detected_features,
            "buildings_count": len(features["buildings"]),
            "roads_count": len(features["roads"]),
            "vegetation_count": len(features["vegetation"]),
            "water_count": len(features["water"]),
            "bare_land_count": len(features["bare_land"]),
            "model_version": self.manager.get_model_metadata(self.manager.active_model_id).get("version", "1.0.0"),
            "inference_device": self.manager.device
        }

        return {
            "features": features,
            "stats": stats,
            "image_dimensions": {"width": w, "height": h}
        }
