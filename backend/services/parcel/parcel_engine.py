import hashlib
import json
from typing import Dict, Any, List, Optional
import numpy as np
from shapely.geometry import Polygon, MultiPolygon
from shapely.validation import make_valid
from shapely.ops import unary_union

class ParcelEngine:
    """
    Part 5: Parcel Intelligence Engine.
    Provides deterministic SHA-256 parcel identification, topological validation,
    and parcel property extraction.
    """

    MIN_PARCEL_AREA_PX = 150.0

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
        ensuring topological validity, road-corridor exclusion, and clean geometric boundaries.
        """
        features = detection_results.get("features", {})
        buildings = features.get("buildings", [])
        roads = features.get("roads", [])
        
        # Build unified road corridor to prevent parcels from overlapping street infrastructure
        road_polys = []
        for r in roads:
            r_coords = r.get("polygon", [])
            if len(r_coords) >= 3:
                try:
                    rp = Polygon(r_coords)
                    if not rp.is_valid:
                        rp = make_valid(rp)
                    if not rp.is_empty and rp.area > 30:
                        road_polys.append(rp)
                except Exception:
                    pass
        road_corridor = unary_union(road_polys) if road_polys else None

        # 1. Generate candidate curtilage buffers for each building
        raw_parcel_candidates = []
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
            # Mitred/flat rectangular buffer with snapping
            buffer_distance = max(12.0, min(28.0, np.sqrt(b_poly.area) * 0.35))
            curtilage_buffer = b_poly.buffer(buffer_distance, join_style=2)
            curtilage_buffer = curtilage_buffer.simplify(1.0)

            # Exclude road corridors so parcel lines respect street frontages
            if road_corridor is not None and not road_corridor.is_empty:
                try:
                    curtilage_buffer = curtilage_buffer.difference(road_corridor)
                except Exception:
                    pass

            if curtilage_buffer.is_empty:
                continue

            # If difference generated a MultiPolygon, pick the section containing the building
            if isinstance(curtilage_buffer, MultiPolygon):
                valid_parts = [p for p in curtilage_buffer.geoms if p.area >= cls.MIN_PARCEL_AREA_PX]
                if not valid_parts:
                    continue
                containing = [p for p in valid_parts if p.intersects(b_poly)]
                curtilage_buffer = containing[0] if containing else max(valid_parts, key=lambda p: p.area)

            if curtilage_buffer.area < cls.MIN_PARCEL_AREA_PX:
                continue

            raw_parcel_candidates.append((bldg, curtilage_buffer, idx))

        # 2. Planar Partition: Prevent overlapping parcel boundaries
        # Deduplicate heavily overlapping compound lots (>40% overlap) and clip boundary lines
        proposed_parcels = []
        claimed_land = None

        # Sort candidate parcels by area descending so primary parcels establish clean boundaries first
        raw_parcel_candidates.sort(key=lambda item: item[1].area, reverse=True)

        for bldg, curtilage_buffer, orig_idx in raw_parcel_candidates:
            if claimed_land is not None and curtilage_buffer.intersects(claimed_land):
                try:
                    intersection = curtilage_buffer.intersection(claimed_land)
                    # If significant overlap with existing plot (>35%), it's part of the same parcel / compound
                    if intersection.area / (curtilage_buffer.area + 1e-6) > 0.35:
                        continue

                    # Otherwise, cleanly partition at the property line without overlap
                    curtilage_buffer = curtilage_buffer.difference(claimed_land)
                    if curtilage_buffer.is_empty:
                        continue
                    if isinstance(curtilage_buffer, MultiPolygon):
                        valid_sub = [p for p in curtilage_buffer.geoms if p.area >= cls.MIN_PARCEL_AREA_PX]
                        if not valid_sub:
                            continue
                        curtilage_buffer = max(valid_sub, key=lambda p: p.area)
                except Exception:
                    pass

            if curtilage_buffer.is_empty or curtilage_buffer.area < cls.MIN_PARCEL_AREA_PX:
                continue

            if not curtilage_buffer.is_valid:
                curtilage_buffer = make_valid(curtilage_buffer)
                if isinstance(curtilage_buffer, MultiPolygon):
                    valid_sub = [p for p in curtilage_buffer.geoms if p.area >= cls.MIN_PARCEL_AREA_PX]
                    if not valid_sub:
                        continue
                    curtilage_buffer = max(valid_sub, key=lambda p: p.area)

            # Update planar partition claimed land
            try:
                claimed_land = unary_union([claimed_land, curtilage_buffer]) if claimed_land is not None else curtilage_buffer
            except Exception:
                pass

            p_coords = [[round(p[0], 2), round(p[1], 2)] for p in curtilage_buffer.exterior.coords]
            parcel_id = cls.generate_parcel_id(p_coords)

            area_px = float(curtilage_buffer.area)
            perim_px = float(curtilage_buffer.length)
            # Polsby-Popper compactness score (4 * pi * Area / Perimeter^2)
            compactness = (4.0 * np.pi * area_px) / (perim_px ** 2 + 1e-6)

            parcel_obj = {
                "id": parcel_id,
                "parcel_id": parcel_id,
                "layer_type": "AI_PROPOSED",
                "area_px": round(area_px, 2),
                "formatted_area": f"{round(area_px, 1)} px²",
                "perimeter_px": round(perim_px, 2),
                "compactness": round(float(compactness), 4),
                "polygon": p_coords,
                "bbox": [float(b) for b in curtilage_buffer.bounds],
                "confidence": bldg.get("confidence", 0.85),
                "source": "AI_INFERENCE_DELINEATION",
                "status": "requires_verification",
                "associated_building": bldg.get("id", f"bld_{orig_idx+1}")
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
