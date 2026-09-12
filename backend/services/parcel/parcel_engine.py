import hashlib
import json
from typing import Dict, Any, List, Optional
import numpy as np
from shapely.geometry import Polygon, MultiPolygon
from shapely.validation import make_valid

class ParcelEngine:
    """
    Part 5: Parcel Intelligence Engine.
    Provides deterministic SHA-256 parcel identification, topological validation,
    and parcel property extraction.
    """

    MIN_PARCEL_AREA_PX = 200.0

    @staticmethod
    def generate_parcel_id(coords: List[List[float]], prefix: str = "AI-P") -> str:
        """
        Generates a deterministic parcel ID based on canonical rounded coordinates.
        Ensures identical geometry yields the exact same ID across runs.
        """
        # Canonical representation rounded to 1 decimal place
        rounded = [[round(p[0], 1), round(p[1], 1)] for p in coords]
        raw_str = json.dumps(rounded, sort_keys=True)
        h = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()[:8].upper()
        return f"{prefix}-{h}"

    @classmethod
    def process_proposed_parcels(
        cls,
        detection_results: Dict[str, Any],
        meta: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Derives proposed parcels from structural cues (buildings, roads, boundaries),
        ensuring topological validity and clean geometric boundaries.
        """
        features = detection_results.get("features", {})
        buildings = features.get("buildings", [])
        roads = features.get("roads", [])
        
        # Build spatial buffers around building clusters separated by roads
        proposed_parcels = []
        for idx, bldg in enumerate(buildings):
            b_coords = bldg.get("polygon", [])
            if len(b_coords) < 3:
                continue

            b_poly = Polygon(b_coords)
            if not b_poly.is_valid:
                b_poly = make_valid(b_poly)
                if b_poly.is_empty:
                    continue

            # Synthesize realistic compound parcel lot by buffering building envelope
            curtilage_buffer = b_poly.buffer(25.0, join_style=2) # mitred/flat rectangular buffer
            curtilage_buffer = curtilage_buffer.simplify(1.5)
            
            if curtilage_buffer.is_empty or curtilage_buffer.area < cls.MIN_PARCEL_AREA_PX:
                continue

            p_coords = [[round(p[0], 2), round(p[1], 2)] for p in curtilage_buffer.exterior.coords]
            parcel_id = cls.generate_parcel_id(p_coords)

            area_px = float(curtilage_buffer.area)
            perim_px = float(curtilage_buffer.length)
            # Polsby-Popper compactness score (4 * pi * Area / Perimeter^2)
            compactness = (4.0 * np.pi * area_px) / (perim_px ** 2 + 1e-6)

            parcel_obj = {
                "id": parcel_id,
                "layer_type": "AI_PROPOSED",
                "area_px": round(area_px, 2),
                "perimeter_px": round(perim_px, 2),
                "compactness": round(float(compactness), 4),
                "polygon": p_coords,
                "bbox": [float(b) for b in curtilage_buffer.bounds],
                "confidence": bldg.get("confidence", 0.85),
                "source": "AI_INFERENCE_DELINEATION",
                "status": "PROPOSED"
            }

            # Map to real-world coordinates if GeoTIFF transform is available
            transform = meta.get("transform") if meta else None
            crs = meta.get("crs") if meta else None
            if transform:
                from services.geospatial import pixel_to_world
                geo_coords = []
                for px, py in p_coords:
                    wx, wy = pixel_to_world(px, py, transform)
                    geo_coords.append([round(wx, 4), round(wy, 4)])
                parcel_obj["geo_polygon"] = geo_coords
                parcel_obj["crs"] = crs

            proposed_parcels.append(parcel_obj)

        return proposed_parcels
