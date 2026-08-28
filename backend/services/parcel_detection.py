import shapely.geometry as sg
from shapely.ops import polygonize, unary_union
import numpy as np


def generate_proposed_parcels(detection_results: dict, meta: dict = None) -> dict:
    """
    Synthesizes AI-proposed parcel boundaries based on detected visible structures,
    building buffer zones, and open land boundaries.

    Each parcel object includes:
    {
      "parcel_id": "AI-P001",
      "type": "proposed_parcel",
      "status": "requires_verification",
      "polygon": [[x, y], ...],
      "area_px": float
    }

    Note: These are AI-assisted proposals requiring surveyor/government verification.
    """
    buildings = detection_results.get("features", {}).get("buildings", [])
    open_land = detection_results.get("features", {}).get("open_land", [])
    roads = detection_results.get("features", {}).get("roads", [])
    width = detection_results.get("dimensions", {}).get("width", 1000)
    height = detection_results.get("dimensions", {}).get("height", 1000)

    parcels = []
    parcel_counter = 1

    # Strategy A: Create buffered property envelope around detected buildings
    building_polys = []
    for bld in buildings:
        pts = bld.get("polygon", [])
        if len(pts) >= 3:
            try:
                poly = sg.Polygon(pts)
                if poly.is_valid and poly.area > 10:
                    # Buffer building by ~15-25% of its size to represent property parcel envelope
                    buf_dist = max(10, min(35, np.sqrt(poly.area) * 0.25))
                    envelope = poly.buffer(buf_dist, cap_style=3, join_style=2)
                    building_polys.append(envelope)
            except Exception:
                pass

    if building_polys:
        # Merge overlapping buffers and intersect with image boundary
        img_bounds = sg.box(0, 0, width, height)
        for i, env in enumerate(building_polys):
            try:
                clipped = env.intersection(img_bounds)
                if clipped.is_valid and not clipped.is_empty:
                    if clipped.geom_type == 'Polygon':
                        coords = [list(pt) for pt in clipped.exterior.coords[:-1]]
                        if len(coords) >= 3:
                            parcels.append({
                                "parcel_id": f"AI-P{parcel_counter:03d}",
                                "type": "proposed_parcel",
                                "status": "requires_verification",
                                "polygon": coords,
                                "area_px": round(clipped.area, 2),
                                "associated_building": f"bld_{i+1}"
                            })
                            parcel_counter += 1
                    elif clipped.geom_type == 'MultiPolygon':
                        for sub_poly in clipped.geoms:
                            coords = [list(pt) for pt in sub_poly.exterior.coords[:-1]]
                            if len(coords) >= 3:
                                parcels.append({
                                    "parcel_id": f"AI-P{parcel_counter:03d}",
                                    "type": "proposed_parcel",
                                    "status": "requires_verification",
                                    "polygon": coords,
                                    "area_px": round(sub_poly.area, 2),
                                    "associated_building": f"bld_{i+1}"
                                })
                                parcel_counter += 1
            except Exception:
                pass

    # Strategy B: Open land parcel proposals
    for land in open_land:
        pts = land.get("polygon", [])
        if len(pts) >= 3:
            try:
                poly = sg.Polygon(pts)
                if poly.is_valid and poly.area > 500:
                    coords = [list(pt) for pt in poly.exterior.coords[:-1]]
                    parcels.append({
                        "parcel_id": f"AI-P{parcel_counter:03d}",
                        "type": "proposed_parcel",
                        "status": "requires_verification",
                        "polygon": coords,
                        "area_px": round(poly.area, 2),
                        "land_type": "open_parcel"
                    })
                    parcel_counter += 1
            except Exception:
                pass

    return {
        "parcels": parcels,
        "count": len(parcels),
        "disclaimer": "AI-proposed parcel boundaries. Requires verification by an authorized surveyor/government authority."
    }
