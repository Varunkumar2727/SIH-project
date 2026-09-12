"""
GeoJSON Export Service for GeoCadastral AI
Converts detected land features and proposed parcels into valid GeoJSON FeatureCollection.

For georeferenced GeoTIFFs:
  Pixel coordinates -> Native world coordinates (via Affine transform) -> WGS84 Geographic coordinates (EPSG:4326 via PyProj).
  Preserves native CRS metadata in the FeatureCollection metadata block.

For non-georeferenced images (JPG/PNG):
  Maintains pixel coordinates [[x, y], ...] without inventing fake Lat/Lon coordinates.
"""

from typing import Dict, Any, List, Optional
from services.geospatial import pixel_to_world, transform_coordinates, calculate_real_area


def export_to_geojson(detection_results: dict, meta: Optional[dict] = None) -> dict:
    """
    Converts detected feature polygons and AI-proposed parcel boundaries
    into a valid GeoJSON FeatureCollection.
    """
    meta = meta or {}
    geospatial = meta.get("geospatial") or {}
    gcp_trans = meta.get("gcp_transformation") or {}
    gcp_active = (meta.get("active_georeferencing") == "gcp") or gcp_trans.get("active", False)
    has_gcp = gcp_active and bool(gcp_trans.get("transform")) and bool(gcp_trans.get("crs"))

    if has_gcp:
        is_georeferenced = True
        native_crs = gcp_trans["crs"]
        native_epsg = None
        transform = gcp_trans["transform"]
        georef_method = "GCP Affine Transformation"
        gcp_rmse = gcp_trans.get("rmse")
    else:
        is_georeferenced = meta.get("is_georeferenced", False) or geospatial.get("georeferenced", False)
        native_crs = meta.get("crs") or geospatial.get("crs")
        native_epsg = geospatial.get("epsg")
        transform = meta.get("transform") or geospatial.get("transform")
        georef_method = "GeoTIFF Native CRS/Transform" if is_georeferenced else "Pixel (CRS.Simple)"
        gcp_rmse = None

    # Only do real coordinate transformation if georeferenced AND valid transform is present
    can_transform = is_georeferenced and (transform is not None) and (native_crs is not None)

    def convert_polygon_coords(pts: List[List[float]]) -> List[List[float]]:
        """Converts pixel points to WGS84 [lon, lat] if georeferenced, else keeps [x, y]."""
        if not can_transform:
            return pts

        converted = []
        for pt in pts:
            px, py = pt[0], pt[1]
            try:
                wx, wy = pixel_to_world(px, py, transform)
                lon, lat = transform_coordinates(wx, wy, src_crs=native_crs, dst_crs="EPSG:4326")
                converted.append([round(lon, 7), round(lat, 7)])
            except Exception:
                # Fallback to world or raw if single coordinate fails
                converted.append([round(px, 2), round(py, 2)])
        return converted

    features = []
    all_lons: List[float] = []
    all_lats: List[float] = []

    # 1. Process standard land features (Buildings, Roads, Vegetation, Open Land)
    all_features = detection_results.get("features", {})
    for category, item_list in all_features.items():
        for item in item_list:
            polygon_pts = item.get("polygon", [])
            if len(polygon_pts) < 3:
                continue

            closed_pts = list(polygon_pts)
            if closed_pts[0] != closed_pts[-1]:
                closed_pts.append(closed_pts[0])

            geo_coords = convert_polygon_coords(closed_pts)
            if can_transform:
                for c in geo_coords:
                    all_lons.append(c[0])
                    all_lats.append(c[1])

            props = {
                "feature_id": item.get("id"),
                "feature_type": item.get("feature_type"),
                "area_px": item.get("area_px")
            }
            if "confidence" in item:
                props["confidence"] = item["confidence"]
            if "bbox" in item:
                props["bbox_px"] = item["bbox"]

            if can_transform:
                area_res = calculate_real_area(closed_pts, crs=native_crs, is_pixel=True, transform=transform)
                props["area_m2"] = round(area_res["m2"], 2)
                props["area_hectares"] = round(area_res["hectares"], 4)
                props["area_acres"] = round(area_res["acres"], 4)

            feature_obj = {
                "type": "Feature",
                "properties": props,
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [geo_coords]
                }
            }
            features.append(feature_obj)

    # 2. Process AI-Proposed Parcels
    parcels = detection_results.get("parcels", [])
    for parcel in parcels:
        polygon_pts = parcel.get("polygon", [])
        if len(polygon_pts) < 3:
            continue

        closed_pts = list(polygon_pts)
        if closed_pts[0] != closed_pts[-1]:
            closed_pts.append(closed_pts[0])

        geo_coords = convert_polygon_coords(closed_pts)
        if can_transform:
            for c in geo_coords:
                all_lons.append(c[0])
                all_lats.append(c[1])

        props = {
            "parcel_id": parcel.get("parcel_id"),
            "type": parcel.get("type", "proposed_parcel"),
            "status": parcel.get("status", "requires_verification"),
            "area_px": parcel.get("area_px"),
            "disclaimer": "AI-proposed boundary requiring surveyor/government verification."
        }

        if can_transform:
            area_res = calculate_real_area(closed_pts, crs=native_crs, is_pixel=True, transform=transform)
            props["area_m2"] = round(area_res["m2"], 2)
            props["area_hectares"] = round(area_res["hectares"], 4)
            props["area_acres"] = round(area_res["acres"], 4)

        feature_obj = {
            "type": "Feature",
            "properties": props,
            "geometry": {
                "type": "Polygon",
                "coordinates": [geo_coords]
            }
        }
        features.append(feature_obj)

    # Build GeoJSON Document
    geojson_doc: Dict[str, Any] = {
        "type": "FeatureCollection",
        "metadata": {
            "image_id": detection_results.get("image_id"),
            "detection_mode": detection_results.get("detection_mode"),
            "is_georeferenced": can_transform,
            "georeferencing_method": georef_method,
            "crs": "EPSG:4326" if can_transform else "Pixel (CRS.Simple)",
            "native_crs": str(native_crs) if can_transform else None,
            "native_epsg": native_epsg if can_transform else None,
            "native_transform": list(transform) if (can_transform and transform) else None,
            "gcp_rmse": gcp_rmse,
            "total_features": len(features)
        },
        "features": features
    }

    if can_transform and all_lons and all_lats:
        geojson_doc["bbox"] = [
            round(min(all_lons), 7),
            round(min(all_lats), 7),
            round(max(all_lons), 7),
            round(max(all_lats), 7)
        ]

    return geojson_doc
