"""
Ground Control Points (GCP) & Survey Control Service for GeoCadastral AI
Handles GCP data modeling, validation, spatial distribution analysis,
2D affine transformation estimation (least-squares), residual error calculation (RMSE),
and forward/inverse pixel-to-world coordinate transformations.
"""

import math
import uuid
from typing import Dict, Any, Tuple, List, Optional, Union
import numpy as np
import pyproj
import affine

from services.geospatial import (
    pixel_to_world,
    world_to_pixel,
    transform_coordinates,
    calculate_real_distance,
    _to_affine
)


def validate_gcp(gcp: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validates a GCP data dictionary.
    Ensures pixel coordinates are non-negative, CRS is valid,
    and real-world coordinates adhere to their coordinate system.
    """
    if "image_x" not in gcp or "image_y" not in gcp:
        return False, "Missing image pixel coordinates (image_x, image_y)."

    try:
        ix = float(gcp["image_x"])
        iy = float(gcp["image_y"])
        if ix < 0 or iy < 0:
            return False, f"Image pixel coordinates must be non-negative. Got X={ix}, Y={iy}."
    except (ValueError, TypeError):
        return False, "Image pixel coordinates must be numeric."

    crs_str = gcp.get("crs")
    if not crs_str:
        return False, "Coordinate Reference System (CRS) is required for Ground Control Points."

    try:
        proj_crs = pyproj.CRS.from_user_input(crs_str)
    except Exception as e:
        return False, f"Invalid or unrecognized CRS '{crs_str}': {str(e)}"

    coord_type = gcp.get("coordinate_type", "projected").lower()

    if coord_type == "geographic":
        lat = gcp.get("latitude")
        lon = gcp.get("longitude")
        if lat is None or lon is None:
            # Check if world_x, world_y were supplied instead
            if gcp.get("world_x") is not None and gcp.get("world_y") is not None:
                lon = gcp.get("world_x")
                lat = gcp.get("world_y")
            else:
                return False, "Geographic GCP requires latitude and longitude."
        try:
            lat_f = float(lat)
            lon_f = float(lon)
            if not (-90.0 <= lat_f <= 90.0):
                return False, f"Latitude must be between -90 and +90 degrees. Got {lat_f}."
            if not (-180.0 <= lon_f <= 180.0):
                return False, f"Longitude must be between -180 and +180 degrees. Got {lon_f}."
        except (ValueError, TypeError):
            return False, "Latitude and longitude must be valid numeric values."
    else:
        # Projected coordinates (Easting, Northing)
        wx = gcp.get("world_x")
        wy = gcp.get("world_y")
        if wx is None or wy is None:
            return False, "Projected GCP requires world_x (Easting) and world_y (Northing)."
        try:
            float(wx)
            float(wy)
        except (ValueError, TypeError):
            return False, "Easting (world_x) and Northing (world_y) must be valid numeric values."

    return True, None


def normalize_gcp(gcp: Dict[str, Any], index: int = 1) -> Dict[str, Any]:
    """
    Standardizes a GCP record to ensure consistent fields:
    id, name, image_x, image_y, coordinate_type, world_x, world_y, latitude, longitude, crs, etc.
    """
    gcp_id = gcp.get("id") or f"gcp_{uuid.uuid4().hex[:8]}"
    name = gcp.get("name") or f"GCP-{index:02d}"
    coord_type = gcp.get("coordinate_type", "projected").lower()
    crs_str = gcp.get("crs", "EPSG:32643")

    ix = float(gcp["image_x"])
    iy = float(gcp["image_y"])

    elevation = None
    if gcp.get("elevation") is not None:
        try:
            elevation = float(gcp["elevation"])
        except (ValueError, TypeError):
            elevation = None

    accuracy = None
    if gcp.get("accuracy") is not None:
        try:
            accuracy = float(gcp["accuracy"])
        except (ValueError, TypeError):
            accuracy = None

    if coord_type == "geographic":
        lat = float(gcp.get("latitude") if gcp.get("latitude") is not None else gcp.get("world_y"))
        lon = float(gcp.get("longitude") if gcp.get("longitude") is not None else gcp.get("world_x"))
        wx = lon
        wy = lat
    else:
        wx = float(gcp["world_x"])
        wy = float(gcp["world_y"])
        # Attempt to compute Lat/Lon for inspection/export
        try:
            lon, lat = transform_coordinates(wx, wy, src_crs=crs_str, dst_crs="EPSG:4326")
        except Exception:
            lat = None
            lon = None

    return {
        "id": gcp_id,
        "name": name,
        "image_x": round(ix, 2),
        "image_y": round(iy, 2),
        "coordinate_type": coord_type,
        "world_x": round(wx, 3),
        "world_y": round(wy, 3),
        "latitude": round(lat, 7) if lat is not None else None,
        "longitude": round(lon, 7) if lon is not None else None,
        "elevation": round(elevation, 2) if elevation is not None else None,
        "crs": crs_str,
        "description": gcp.get("description", ""),
        "source": gcp.get("source", "Field Survey"),
        "accuracy": accuracy
    }


def check_gcp_distribution(
    gcps: List[Dict[str, Any]],
    image_width: float = 1000.0,
    image_height: float = 1000.0
) -> Dict[str, Any]:
    """
    Analyzes the spatial distribution of GCPs across the aerial survey area.
    Flags warnings if GCPs are clustered or concentrated in one corner.
    """
    n = len(gcps)
    if n < 3:
        return {
            "is_clustered": True,
            "status": "Insufficient",
            "message": f"At least 3 GCPs required for affine georeferencing (currently {n}).",
            "span_x": 0.0,
            "span_y": 0.0,
            "quadrants_covered": 0
        }

    xs = [float(g["image_x"]) for g in gcps]
    ys = [float(g["image_y"]) for g in gcps]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    w = max(image_width, 1.0)
    h = max(image_height, 1.0)

    span_x = (max_x - min_x) / w
    span_y = (max_y - min_y) / h
    area_ratio = span_x * span_y

    # Check quadrant coverage (1: top-left, 2: top-right, 3: bottom-left, 4: bottom-right)
    mid_x = w / 2.0
    mid_y = h / 2.0
    quadrants = set()
    for x, y in zip(xs, ys):
        if x <= mid_x and y <= mid_y:
            quadrants.add(1)
        elif x > mid_x and y <= mid_y:
            quadrants.add(2)
        elif x <= mid_x and y > mid_y:
            quadrants.add(3)
        else:
            quadrants.add(4)

    # Clustered if bounding box is very small (< 15% area) or only 1 quadrant covered
    is_clustered = (area_ratio < 0.15) or (span_x < 0.25) or (span_y < 0.25) or (len(quadrants) <= 1)

    if is_clustered:
        status = "Clustered"
        msg = "⚠ GCPs are poorly distributed across the survey area. Place additional control points across other quadrants."
    else:
        status = "Good"
        msg = "✓ Good spatial distribution across survey area."

    return {
        "is_clustered": is_clustered,
        "status": status,
        "message": msg,
        "span_x": round(span_x, 3),
        "span_y": round(span_y, 3),
        "area_ratio": round(area_ratio, 3),
        "quadrants_covered": len(quadrants)
    }


def calculate_gcp_transformation(
    gcps: List[Dict[str, Any]],
    target_crs: Optional[str] = None,
    image_width: Optional[float] = None,
    image_height: Optional[float] = None
) -> Dict[str, Any]:
    """
    Estimates a 2D affine transformation between image pixel coordinates and real-world coordinates
    using NumPy least-squares regression.
    
    Model:
      X = a*x + b*y + c
      Y = d*x + e*y + f
      
    Calculates residual errors for each GCP and overall RMSE.
    """
    n = len(gcps)
    if n < 3:
        raise ValueError(f"At least 3 Ground Control Points are required for 2D affine transformation (received {n}).")

    # Determine target working CRS
    # Priority: explicitly requested target_crs -> first projected GCP CRS -> first GCP CRS -> 'EPSG:32643'
    if not target_crs:
        for g in gcps:
            if g.get("coordinate_type") == "projected" and g.get("crs"):
                target_crs = g["crs"]
                break
        if not target_crs:
            target_crs = gcps[0].get("crs", "EPSG:32643")

    # Build design matrix M and target vectors
    pixel_pts = []
    target_worlds = []

    for g in gcps:
        px = float(g["image_x"])
        py = float(g["image_y"])
        gcp_crs = g.get("crs", target_crs)

        if g.get("coordinate_type") == "geographic" or ("longitude" in g and "latitude" in g):
            wx = float(g.get("longitude", g.get("world_x", 0.0)))
            wy = float(g.get("latitude", g.get("world_y", 0.0)))
        else:
            wx = float(g.get("world_x", g.get("longitude", 0.0)))
            wy = float(g.get("world_y", g.get("latitude", 0.0)))

        # Reproject to common target CRS if different
        if str(gcp_crs) != str(target_crs):
            wx, wy = transform_coordinates(wx, wy, src_crs=gcp_crs, dst_crs=target_crs)

        pixel_pts.append([px, py])
        target_worlds.append([wx, wy])

    pixel_arr = np.array(pixel_pts, dtype=float)
    world_arr = np.array(target_worlds, dtype=float)

    # Design matrix M = [x, y, 1]
    M = np.column_stack([pixel_arr, np.ones(n, dtype=float)])

    # Check for collinearity / rank deficiency
    rank = np.linalg.matrix_rank(M)
    if rank < 3:
        raise ValueError("Collinear GCPs detected. All control points lie on a single straight line, preventing unique 2D transformation.")

    # Solve least-squares: M * [a, b, c]^T = X_vec  and  M * [d, e, f]^T = Y_vec
    params_x, _, _, _ = np.linalg.lstsq(M, world_arr[:, 0], rcond=None)
    params_y, _, _, _ = np.linalg.lstsq(M, world_arr[:, 1], rcond=None)

    a, b, c = float(params_x[0]), float(params_x[1]), float(params_x[2])
    d, e, f = float(params_y[0]), float(params_y[1]), float(params_y[2])

    transform_list = [a, b, c, d, e, f]

    # Compute predicted world coordinates
    pred_x = M @ params_x
    pred_y = M @ params_y

    # Calculate residuals in meters
    try:
        proj_crs = pyproj.CRS.from_user_input(target_crs)
        is_geo = proj_crs.is_geographic
    except Exception:
        is_geo = False

    residuals = {}
    err_list = []

    for i, g in enumerate(gcps):
        gcp_id = g["id"]
        if is_geo:
            # Geodesic distance in meters for geographic CRS
            err_m = calculate_real_distance(
                (pred_x[i], pred_y[i]),
                (world_arr[i, 0], world_arr[i, 1]),
                crs=target_crs
            )
        else:
            # Projected Euclidean distance in meters
            dx = pred_x[i] - world_arr[i, 0]
            dy = pred_y[i] - world_arr[i, 1]
            err_m = math.sqrt(dx * dx + dy * dy)

        residuals[gcp_id] = round(float(err_m), 4)
        err_list.append(float(err_m))

    err_arr = np.array(err_list, dtype=float)
    rmse = float(np.sqrt(np.mean(err_arr ** 2)))
    max_err = float(np.max(err_arr))
    mean_err = float(np.mean(err_arr))

    # Spatial distribution check
    dist_info = check_gcp_distribution(gcps, image_width or 1000.0, image_height or 1000.0)

    # Determine status quality message
    if n == 3:
        status_msg = "Minimum 3 points available (exact fit)"
    elif n >= 4:
        status_msg = "Ready for georeferencing (overdetermined solution)"
    else:
        status_msg = "Calculated"

    return {
        "status": "ready",
        "method": "affine",
        "status_message": status_msg,
        "gcp_count": n,
        "transform": transform_list,
        "crs": str(target_crs),
        "rmse": round(rmse, 4),
        "max_error": round(max_err, 4),
        "mean_error": round(mean_err, 4),
        "residuals": residuals,
        "distribution": dist_info
    }


def gcp_pixel_to_world(
    x: float,
    y: float,
    transform: Union[affine.Affine, List[float], Tuple[float, ...]]
) -> Tuple[float, float]:
    """
    Converts image pixel coordinate (x=col, y=row) to GCP-corrected real-world coordinate (world_x, world_y)
    using the estimated affine transformation matrix.
    """
    return pixel_to_world(x, y, transform)


def gcp_world_to_pixel(
    world_x: float,
    world_y: float,
    transform: Union[affine.Affine, List[float], Tuple[float, ...]]
) -> Tuple[float, float]:
    """
    Converts real-world coordinate (world_x, world_y) back to image pixel coordinate (x=col, y=row)
    using the inverted GCP affine transformation matrix.
    """
    return world_to_pixel(world_x, world_y, transform)
