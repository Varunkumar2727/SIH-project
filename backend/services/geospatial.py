"""
Geospatial Utility Service for GeoCadastral AI
Handles GeoTIFF metadata extraction, pixel-to-world & world-to-pixel coordinate transforms,
CRS transformations via PyProj, real geodesic and projected distance/area calculations,
and measurement formatters (Geographic, Calibrated, Pixel).
"""

import math
from typing import Dict, Any, Tuple, List, Optional, Union
import affine
import rasterio
import rasterio.crs
import pyproj
from shapely.geometry import Polygon


def _to_affine(transform: Union[affine.Affine, List[float], Tuple[float, ...]]) -> affine.Affine:
    """Normalize transform representation to affine.Affine."""
    if isinstance(transform, affine.Affine):
        return transform
    if isinstance(transform, (list, tuple)):
        # Take the first 6 elements [a, b, c, d, e, f]
        return affine.Affine(*transform[:6])
    raise ValueError(f"Unsupported transform format: {type(transform)}")


def extract_geotiff_metadata(file_path: str) -> Dict[str, Any]:
    """
    Reads comprehensive geospatial metadata from a GeoTIFF file.
    
    Returns a structured dictionary containing:
      - georeferenced: bool
      - crs: str (e.g. 'EPSG:32643')
      - epsg: int or None
      - coordinate_type: 'projected' | 'geographic' | 'unknown'
      - units: 'metre' | 'degree' | str
      - transform: list of 6 floats [a, b, c, d, e, f]
      - bounds: dict {left, bottom, right, top}
      - pixel_size: dict {x, y}
      - width: int
      - height: int
      - wgs84_bounds: dict {min_lon, min_lat, max_lon, max_lat} (optional if reprojectable)
    """
    try:
        with rasterio.open(file_path) as src:
            width = int(src.width)
            height = int(src.height)

            if src.crs is None:
                return {
                    "georeferenced": False,
                    "reason": "CRS missing",
                    "crs": None,
                    "epsg": None,
                    "coordinate_type": "pixel",
                    "units": "pixels",
                    "width": width,
                    "height": height,
                    "transform": None,
                    "bounds": None,
                    "pixel_size": None
                }

            # Check transform validity
            t = src.transform
            det = t.a * t.e - t.b * t.d
            if det == 0 or math.isnan(det) or math.isinf(det):
                return {
                    "georeferenced": False,
                    "reason": "Invalid or singular affine transform",
                    "crs": str(src.crs),
                    "epsg": src.crs.to_epsg(),
                    "coordinate_type": "unknown",
                    "units": "unknown",
                    "width": width,
                    "height": height,
                    "transform": list(t)[:6],
                    "bounds": None,
                    "pixel_size": None
                }

            crs_str = str(src.crs)
            epsg_code = src.crs.to_epsg()
            is_proj = getattr(src.crs, "is_projected", True)
            coord_type = "projected" if is_proj else "geographic"
            units = getattr(src.crs, "linear_units", "metre" if is_proj else "degree") or ("metre" if is_proj else "degree")

            bounds_dict = {
                "left": float(src.bounds.left),
                "bottom": float(src.bounds.bottom),
                "right": float(src.bounds.right),
                "top": float(src.bounds.top)
            }

            pixel_size = {
                "x": float(abs(t.a)),
                "y": float(abs(t.e))
            }

            transform_list = [float(val) for val in list(t)[:6]]

            # Compute WGS84 bounds (EPSG:4326)
            wgs84_bounds = None
            try:
                tf_4326 = pyproj.Transformer.from_crs(src.crs, "EPSG:4326", always_xy=True)
                # Reproject 4 corners to find min/max lon/lat
                corners = [
                    (bounds_dict["left"], bounds_dict["bottom"]),
                    (bounds_dict["right"], bounds_dict["bottom"]),
                    (bounds_dict["right"], bounds_dict["top"]),
                    (bounds_dict["left"], bounds_dict["top"]),
                ]
                lons, lats = [], []
                for cx, cy in corners:
                    lon, lat = tf_4326.transform(cx, cy)
                    lons.append(lon)
                    lats.append(lat)
                wgs84_bounds = {
                    "min_lon": float(min(lons)),
                    "min_lat": float(min(lats)),
                    "max_lon": float(max(lons)),
                    "max_lat": float(max(lats))
                }
            except Exception:
                wgs84_bounds = None

            return {
                "georeferenced": True,
                "crs": crs_str,
                "epsg": epsg_code,
                "coordinate_type": coord_type,
                "units": units,
                "transform": transform_list,
                "bounds": bounds_dict,
                "pixel_size": pixel_size,
                "width": width,
                "height": height,
                "wgs84_bounds": wgs84_bounds
            }
    except Exception as e:
        return {
            "georeferenced": False,
            "reason": f"Failed to read GeoTIFF: {str(e)}",
            "crs": None,
            "epsg": None,
            "coordinate_type": "unknown",
            "units": "pixels"
        }


def pixel_to_world(
    x: float,
    y: float,
    transform: Union[affine.Affine, List[float], Tuple[float, ...]]
) -> Tuple[float, float]:
    """
    Converts image pixel coordinate (x=column, y=row) to real-world coordinate (world_x, world_y)
    in the GeoTIFF's native CRS using the affine transform.
    
    Convention:
      x = column (horizontal pixel offset from left)
      y = row (vertical pixel offset from top)
    """
    af = _to_affine(transform)
    world_x = af.a * x + af.b * y + af.c
    world_y = af.d * x + af.e * y + af.f
    return float(world_x), float(world_y)


def world_to_pixel(
    world_x: float,
    world_y: float,
    transform: Union[affine.Affine, List[float], Tuple[float, ...]]
) -> Tuple[float, float]:
    """
    Converts native real-world coordinate (world_x, world_y) back into image pixel coordinate (x=col, y=row)
    using the inverted affine transform.
    """
    af = _to_affine(transform)
    inv_af = ~af
    px_x = inv_af.a * world_x + inv_af.b * world_y + inv_af.c
    px_y = inv_af.d * world_x + inv_af.e * world_y + inv_af.f
    return float(px_x), float(px_y)


def transform_coordinates(
    x: float,
    y: float,
    src_crs: Any,
    dst_crs: Any = "EPSG:4326"
) -> Tuple[float, float]:
    """
    Transforms a single coordinate pair (x, y) from source CRS to destination CRS (default: EPSG:4326).
    Returns (dst_x, dst_y). When dst_crs is EPSG:4326, returns (lon, lat).
    """
    if str(src_crs) == str(dst_crs):
        return float(x), float(y)
    try:
        transformer = pyproj.Transformer.from_crs(src_crs, dst_crs, always_xy=True)
        dst_x, dst_y = transformer.transform(x, y)
        return float(dst_x), float(dst_y)
    except Exception as e:
        raise ValueError(f"CRS Transformation error from {src_crs} to {dst_crs}: {str(e)}")


def transform_coordinates_list(
    coords: List[Tuple[float, float]],
    src_crs: Any,
    dst_crs: Any = "EPSG:4326"
) -> List[Tuple[float, float]]:
    """
    Transforms a list of (x, y) coordinates from source CRS to destination CRS.
    """
    if str(src_crs) == str(dst_crs):
        return [(float(x), float(y)) for x, y in coords]
    try:
        transformer = pyproj.Transformer.from_crs(src_crs, dst_crs, always_xy=True)
        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]
        res_xs, res_ys = transformer.transform(xs, ys)
        return list(zip([float(x) for x in res_xs], [float(y) for y in res_ys]))
    except Exception as e:
        raise ValueError(f"Batch CRS Transformation error: {str(e)}")


def calculate_real_distance(
    pt1: Tuple[float, float],
    pt2: Tuple[float, float],
    crs: Any = None,
    is_pixel: bool = False,
    transform: Optional[Any] = None
) -> float:
    """
    Calculates the real distance between two points in meters.
    
    If is_pixel is True and transform is provided, points are first converted
    from pixel coordinates to world coordinates.
    
    If the CRS is projected (units: meters), Euclidean distance is calculated.
    If the CRS is geographic (degrees / lat-lon), geodesic calculation using WGS84 ellipsoid is used.
    """
    p1 = pt1
    p2 = pt2

    if is_pixel and transform:
        p1 = pixel_to_world(pt1[0], pt1[1], transform)
        p2 = pixel_to_world(pt2[0], pt2[1], transform)

    # Determine if geographic or projected
    is_geo = False
    if crs is not None:
        try:
            proj_crs = pyproj.CRS.from_user_input(crs)
            is_geo = proj_crs.is_geographic
        except Exception:
            is_geo = False

    if is_geo:
        # Geodesic distance on WGS84 ellipsoid: (lon1, lat1, lon2, lat2)
        geod = pyproj.Geod(ellps="WGS84")
        _, _, distance_m = geod.inv(p1[0], p1[1], p2[0], p2[1])
        return float(abs(distance_m))
    else:
        # Projected Euclidean distance in meters
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        return float(math.sqrt(dx * dx + dy * dy))


def calculate_real_area(
    polygon_coords: List[Tuple[float, float]],
    crs: Any = None,
    is_pixel: bool = False,
    transform: Optional[Any] = None
) -> Dict[str, float]:
    """
    Calculates the real-world area of a polygon.
    Returns:
      {
        "m2": float,
        "hectares": float,
        "acres": float
      }
    """
    if len(polygon_coords) < 3:
        return {"m2": 0.0, "hectares": 0.0, "acres": 0.0}

    coords = polygon_coords
    if is_pixel and transform:
        coords = [pixel_to_world(x, y, transform) for x, y in polygon_coords]

    # Check closed loop
    if coords[0] != coords[-1]:
        coords = list(coords) + [coords[0]]

    is_geo = False
    if crs is not None:
        try:
            proj_crs = pyproj.CRS.from_user_input(crs)
            is_geo = proj_crs.is_geographic
        except Exception:
            is_geo = False

    if is_geo:
        # Use pyproj.Geod polygon area
        geod = pyproj.Geod(ellps="WGS84")
        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        area_m2, _ = geod.polygon_area_perimeter(lons, lats)
        area_m2 = abs(float(area_m2))
    else:
        # Euclidean polygon area using Shapely
        poly = Polygon(coords)
        area_m2 = float(poly.area)

    hectares = area_m2 / 10000.0
    acres = area_m2 / 4046.8564224

    return {
        "m2": area_m2,
        "hectares": hectares,
        "acres": acres
    }


# =====================================================================
# Measurement Formatter Classes
# =====================================================================

class PixelMeasurement:
    """Default fallback when image is not georeferenced and not calibrated."""
    def format_area(self, area_px: float) -> str:
        return f"{int(area_px):,} px²"
        
    def format_distance(self, distance_px: float) -> str:
        return f"{int(distance_px):,} px"


class CalibratedMeasurement:
    """Manual two-point calibration measurement for non-georeferenced JPG/PNG images."""
    def __init__(self, meters_per_pixel: float):
        self.m_per_px = float(meters_per_pixel)
        
    def format_area(self, area_px: float) -> str:
        real_area_m2 = float(area_px) * (self.m_per_px ** 2)
        hectares = real_area_m2 / 10000.0
        acres = real_area_m2 / 4046.8564224
        return f"{real_area_m2:,.1f} m²\n≈ {hectares:.3f} ha\n≈ {acres:.3f} acres"
        
    def format_distance(self, distance_px: float) -> str:
        real_distance = float(distance_px) * self.m_per_px
        if real_distance >= 1000.0:
            return f"{real_distance:,.1f} m ({real_distance / 1000.0:.2f} km)"
        return f"{real_distance:,.1f} m"


class GeographicMeasurement:
    """
    Real-world GIS measurement based on native GeoTIFF CRS and affine transform.
    Supports both projected (e.g. UTM, Indian Grid) and geographic (WGS84 degrees) CRSs.
    """
    def __init__(
        self,
        crs: Any = None,
        transform: Optional[Any] = None,
        units: str = "metre",
        coordinate_type: str = "projected"
    ):
        self.crs = crs
        self.transform = _to_affine(transform) if transform else None
        self.units = units or "metre"
        self.coordinate_type = coordinate_type
        self.is_geographic = False
        if crs:
            try:
                proj_crs = pyproj.CRS.from_user_input(crs)
                self.is_geographic = proj_crs.is_geographic
            except Exception:
                self.is_geographic = False

    def format_area(self, area_px: float, polygon: Optional[List[Tuple[float, float]]] = None) -> str:
        if not self.transform:
            return "Geographic Measurement Unavailable (No Transform)"

        if polygon and len(polygon) >= 3:
            area_res = calculate_real_area(polygon, crs=self.crs, is_pixel=True, transform=self.transform)
            area_m2 = area_res["m2"]
            hectares = area_res["hectares"]
            acres = area_res["acres"]
        else:
            # Determinant of affine transform gives area scale factor per pixel
            det = abs(self.transform.a * self.transform.e - self.transform.b * self.transform.d)
            if self.is_geographic:
                # Approximate 1 degree ~ 111,320m
                # Center latitude approximation from transform offset
                center_lat = self.transform.f
                deg_lat_m = 111320.0
                deg_lon_m = 111320.0 * math.cos(math.radians(center_lat))
                m2_per_px = det * deg_lat_m * deg_lon_m
                area_m2 = float(area_px) * m2_per_px
            else:
                # Projected CRS with meters
                area_m2 = float(area_px) * det

            hectares = area_m2 / 10000.0
            acres = area_m2 / 4046.8564224

        return f"{area_m2:,.1f} m²\n≈ {hectares:.4f} ha\n≈ {acres:.4f} acres"

    def format_distance(self, distance_px: float) -> str:
        if not self.transform:
            return "N/A"

        # Effective ground resolution per pixel
        px_res = math.sqrt(abs(self.transform.a * self.transform.e - self.transform.b * self.transform.d))
        if self.is_geographic:
            center_lat = self.transform.f
            avg_deg_m = 111320.0 * math.sqrt(math.cos(math.radians(center_lat)))
            distance_m = float(distance_px) * px_res * avg_deg_m
        else:
            distance_m = float(distance_px) * px_res

        if distance_m >= 1000.0:
            return f"{distance_m:,.1f} m ({distance_m / 1000.0:.2f} km)"
        return f"{distance_m:,.1f} m"


class MeasurementService:
    """
    Factory for obtaining the appropriate measurement formatter based on the requested
    mode and available metadata, following the strict priority hierarchy:
      1. GCP-based georeferencing (when active)
      2. Proper GeoTIFF native georeferencing
      3. Manual 2-point calibration
      4. Pixel units
    """
    @staticmethod
    def get_formatter(mode: Optional[str] = None, meta: Optional[dict] = None):
        meta = meta or {}
        geospatial = meta.get("geospatial") or {}
        gcp_trans = meta.get("gcp_transformation") or {}
        gcp_active = (meta.get("active_georeferencing") == "gcp") or gcp_trans.get("active", False)
        has_gcp = gcp_active and bool(gcp_trans.get("transform")) and bool(gcp_trans.get("crs"))

        is_georef = meta.get("is_georeferenced", False) or geospatial.get("georeferenced", False) or has_gcp
        has_transform = bool(meta.get("transform") or geospatial.get("transform")) or has_gcp

        # 1. Explicitly requested geographic or gcp mode
        if mode in ("geographic", "gcp"):
            if has_gcp:
                return GeographicMeasurement(
                    crs=gcp_trans["crs"],
                    transform=gcp_trans["transform"],
                    units="metre",
                    coordinate_type="projected"
                )
            if is_georef and has_transform:
                crs = meta.get("crs") or geospatial.get("crs")
                transform = meta.get("transform") or geospatial.get("transform")
                units = geospatial.get("units", "metre")
                coord_type = geospatial.get("coordinate_type", "projected")
                return GeographicMeasurement(crs=crs, transform=transform, units=units, coordinate_type=coord_type)
            return PixelMeasurement()

        # 2. Calibrated mode explicitly requested
        elif mode == "calibrated":
            calibration = meta.get("calibration", {})
            m_per_px = calibration.get("meters_per_pixel")
            if m_per_px:
                return CalibratedMeasurement(m_per_px)
            return PixelMeasurement()

        # 3. Pixel mode explicitly requested
        elif mode == "pixels":
            return PixelMeasurement()

        # 4. Mode is None: follow strict priority hierarchy
        # Priority 1: GCP-based georeferencing (if active)
        if has_gcp:
            return GeographicMeasurement(
                crs=gcp_trans["crs"],
                transform=gcp_trans["transform"],
                units="metre",
                coordinate_type="projected"
            )

        # Priority 2: GeoTIFF native georeferencing
        if is_georef and has_transform:
            crs = meta.get("crs") or geospatial.get("crs")
            transform = meta.get("transform") or geospatial.get("transform")
            units = geospatial.get("units", "metre")
            coord_type = geospatial.get("coordinate_type", "projected")
            return GeographicMeasurement(crs=crs, transform=transform, units=units, coordinate_type=coord_type)

        # Priority 3: Manual calibration
        calibration = meta.get("calibration", {})
        m_per_px = calibration.get("meters_per_pixel")
        if m_per_px:
            return CalibratedMeasurement(m_per_px)

        # Priority 4: Pixel units
        return PixelMeasurement()
