import os
import sys
import unittest

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from services.geospatial import MeasurementService, PixelMeasurement, CalibratedMeasurement, GeographicMeasurement

class TestMeasurementService(unittest.TestCase):
    def test_pixel_measurement(self):
        formatter = PixelMeasurement()
        self.assertEqual(formatter.format_area(25000), "25,000 px²")
        self.assertEqual(formatter.format_distance(500), "500 px")

    def test_calibrated_measurement_scale(self):
        # 500 px = 100 m -> 0.2 m/px
        m_per_px = 100 / 500
        self.assertEqual(m_per_px, 0.2)
        formatter = CalibratedMeasurement(m_per_px)
        
        # Test 2: 25000 px² at 0.2 m/px -> 1000 m²
        formatted_area = formatter.format_area(25000)
        self.assertIn("1,000.0 m²", formatted_area)
        self.assertIn("0.100 ha", formatted_area)
        
        # Test 3: 750 px at 0.2 m/px -> 150 m
        formatted_dist = formatter.format_distance(750)
        self.assertEqual(formatted_dist, "150.0 m")

    def test_service_factory_uncalibrated(self):
        meta = {}
        formatter = MeasurementService.get_formatter("calibrated", meta)
        self.assertIsInstance(formatter, PixelMeasurement)

    def test_service_factory_calibrated(self):
        meta = {"calibration": {"meters_per_pixel": 0.5}}
        formatter = MeasurementService.get_formatter("calibrated", meta)
        self.assertIsInstance(formatter, CalibratedMeasurement)
        self.assertIn("250.0 m²", formatter.format_area(1000))

    def test_service_factory_geographic_unavailable(self):
        meta = {"is_georeferenced": False}
        formatter = MeasurementService.get_formatter("geographic", meta)
        self.assertIsInstance(formatter, PixelMeasurement)

    def test_service_factory_geographic_available(self):
        meta = {
            "is_georeferenced": True,
            "crs": "EPSG:32643",
            "transform": [0.5, 0.0, 500000.0, 0.0, -0.5, 1450000.0]
        }
        formatter = MeasurementService.get_formatter("geographic", meta)
        self.assertIsInstance(formatter, GeographicMeasurement)
        # 100 px with 0.5m x 0.5m = 25 m²
        self.assertIn("25.0 m²", formatter.format_area(100))

if __name__ == '__main__':
    unittest.main()
