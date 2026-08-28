import math

class PixelMeasurement:
    def format_area(self, area_px: float) -> str:
        return f"{int(area_px):,} px²"
        
    def format_distance(self, distance_px: float) -> str:
        return f"{int(distance_px):,} px"


class CalibratedMeasurement:
    def __init__(self, meters_per_pixel: float):
        self.m_per_px = meters_per_pixel
        
    def format_area(self, area_px: float) -> str:
        # Area scale is squared
        real_area_m2 = area_px * (self.m_per_px ** 2)
        hectares = real_area_m2 / 10000
        acres = real_area_m2 / 4046.86
        return f"{int(real_area_m2):,} m²\n≈ {hectares:.3f} hectares\n≈ {acres:.3f} acres"
        
    def format_distance(self, distance_px: float) -> str:
        real_distance = distance_px * self.m_per_px
        return f"{int(real_distance):,} m"


class GeographicMeasurement:
    def __init__(self, crs=None, transform=None):
        self.crs = crs
        self.transform = transform
        
    def format_area(self, area_px: float) -> str:
        if self.transform:
            # Simplistic placeholder logic for GeoTIFF transforms
            # Area of 1 pixel = pixel width * pixel height
            px_width = abs(self.transform[0])
            px_height = abs(self.transform[4])
            real_area_m2 = area_px * (px_width * px_height)
            return f"{int(real_area_m2):,} m²\n(Geographic)"
        return "Geographic Measurement Unavailable"
        
    def format_distance(self, distance_px: float) -> str:
        if self.transform:
            px_width = abs(self.transform[0])
            return f"{int(distance_px * px_width):,} m\n(Geographic)"
        return "N/A"


class MeasurementService:
    @staticmethod
    def get_formatter(mode: str, meta: dict = None):
        if mode == "calibrated":
            calibration = meta.get("calibration", {}) if meta else {}
            m_per_px = calibration.get("meters_per_pixel")
            if m_per_px:
                return CalibratedMeasurement(m_per_px)
            # Fallback to pixels if no calibration data is present
            return PixelMeasurement()
            
        elif mode == "geographic":
            is_georef = meta.get("is_georeferenced", False) if meta else False
            if is_georef:
                return GeographicMeasurement(crs=meta.get("crs"))
            # Fallback
            return PixelMeasurement()
            
        # Default
        return PixelMeasurement()
