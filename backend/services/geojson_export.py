def export_to_geojson(detection_results: dict, meta: dict = None) -> dict:
    """
    Converts detected feature polygons and AI-proposed parcel boundaries
    into valid GeoJSON FeatureCollection.

    If the image is georeferenced, coordinates are in geographic space.
    If the image is NOT georeferenced, pixel coordinates [[x, y], ...] are used without inventing fake Lat/Lon.
    """
    is_georeferenced = meta.get("is_georeferenced", False) if meta else False
    crs_info = meta.get("crs", "Image is not georeferenced") if meta else "Image is not georeferenced"

    features = []

    # 1. Process standard land features (Buildings, Roads, Vegetation, Open Land)
    all_features = detection_results.get("features", {})
    for category, item_list in all_features.items():
        for item in item_list:
            polygon_pts = item.get("polygon", [])
            if len(polygon_pts) < 3:
                continue

            # Ensure polygon loop is closed
            closed_pts = list(polygon_pts)
            if closed_pts[0] != closed_pts[-1]:
                closed_pts.append(closed_pts[0])

            props = {
                "feature_id": item.get("id"),
                "feature_type": item.get("feature_type"),
                "area_px": item.get("area_px")
            }
            if "confidence" in item:
                props["confidence"] = item["confidence"]
            if "bbox" in item:
                props["bbox_px"] = item["bbox"]

            feature_obj = {
                "type": "Feature",
                "properties": props,
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [closed_pts]
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

        feature_obj = {
            "type": "Feature",
            "properties": {
                "parcel_id": parcel.get("parcel_id"),
                "type": parcel.get("type", "proposed_parcel"),
                "status": parcel.get("status", "requires_verification"),
                "area_px": parcel.get("area_px"),
                "disclaimer": "AI-proposed boundary requiring surveyor/government verification."
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [closed_pts]
            }
        }
        features.append(feature_obj)

    geojson_doc = {
        "type": "FeatureCollection",
        "metadata": {
            "image_id": detection_results.get("image_id"),
            "detection_mode": detection_results.get("detection_mode"),
            "is_georeferenced": is_georeferenced,
            "crs": crs_info,
            "total_features": len(features)
        },
        "features": features
    }

    return geojson_doc
