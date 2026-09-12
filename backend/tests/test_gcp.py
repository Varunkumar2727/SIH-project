"""
Comprehensive Test Suite for Ground Control Points (GCP) & Survey Control
Covers the 9 foundational tests required for Part 2:
  Test 1 — GCP creation & validation (3+ GCPs)
  Test 2 — Pixel -> world coordinate conversion
  Test 3 — World -> pixel reverse conversion
  Test 4 — 2D Affine transformation recovery with synthetic points
  Test 5 — Residual error & RMSE calculation with noisy points
  Test 6 — Cross-CRS transformation (e.g. EPSG:4326 Lat/Lon -> UTM EPSG:32643)
  Test 7 — GeoJSON export with active GCP georeferencing
  Test 8 — Persistence across reloads in metadata
  Test 9 — Existing Part 1 functionality preserved intact
"""

import os
import sys
import json
import tempfile
import unittest
import numpy as np
import rasterio
from rasterio.transform import from_origin

# Ensure backend root is on sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from services.gcp import (
    validate_gcp,
    normalize_gcp,
    check_gcp_distribution,
    calculate_gcp_transformation,
    gcp_pixel_to_world,
    gcp_world_to_pixel
)
from services.geospatial import (
    extract_geotiff_metadata,
    pixel_to_world,
    world_to_pixel,
    transform_coordinates,
    MeasurementService,
    PixelMeasurement,
    CalibratedMeasurement,
    GeographicMeasurement
)
from services.geojson_export import export_to_geojson


class TestGCPFoundation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()

        # Known synthetic affine transformation parameters:
        # X = 0.5 * x + 0.0 * y + 500000.0 (UTM 43N Easting)
        # Y = 0.0 * x - 0.5 * y + 1450000.0 (UTM 43N Northing)
        cls.true_a = 0.5
        cls.true_b = 0.0
        cls.true_c = 500000.0
        cls.true_d = 0.0
        cls.true_e = -0.5
        cls.true_f = 1450000.0

        # Sample pixel locations spanning four corners of a 1000x1000 image
        cls.sample_pixels = [
            (100.0, 100.0),
            (900.0, 100.0),
            (900.0, 900.0),
            (100.0, 900.0),
            (500.0, 500.0)
        ]

        cls.exact_gcps = []
        for i, (px, py) in enumerate(cls.sample_pixels):
            wx = cls.true_a * px + cls.true_b * py + cls.true_c
            wy = cls.true_d * px + cls.true_e * py + cls.true_f
            cls.exact_gcps.append({
                "id": f"gcp_{i+1}",
                "name": f"GCP-0{i+1}",
                "image_x": px,
                "image_y": py,
                "coordinate_type": "projected",
                "world_x": wx,
                "world_y": wy,
                "crs": "EPSG:32643",
                "elevation": 750.0 + i * 5.0
            })

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    # =========================================================================
    # Test 1: GCP creation & validation
    # =========================================================================
    def test_01_gcp_validation_and_creation(self):
        # Valid projected GCP
        valid_gcp = {
            "image_x": 250.0,
            "image_y": 350.0,
            "coordinate_type": "projected",
            "world_x": 500125.0,
            "world_y": 1449825.0,
            "crs": "EPSG:32643"
        }
        ok, msg = validate_gcp(valid_gcp)
        self.assertTrue(ok, f"Validation failed unexpectedly: {msg}")

        norm = normalize_gcp(valid_gcp, index=1)
        self.assertEqual(norm["name"], "GCP-01")
        self.assertEqual(norm["world_x"], 500125.0)
        self.assertEqual(norm["world_y"], 1449825.0)

        # Invalid negative pixel coordinates
        invalid_px = {"image_x": -10.0, "image_y": 50.0, "crs": "EPSG:32643", "world_x": 100, "world_y": 200}
        ok, msg = validate_gcp(invalid_px)
        self.assertFalse(ok)
        self.assertIn("non-negative", msg)

        # Invalid geographic coordinates
        invalid_geo = {
            "image_x": 100.0,
            "image_y": 100.0,
            "coordinate_type": "geographic",
            "latitude": 95.0, # out of bounds (> 90)
            "longitude": 77.0,
            "crs": "EPSG:4326"
        }
        ok, msg = validate_gcp(invalid_geo)
        self.assertFalse(ok)
        self.assertIn("Latitude must be between -90 and +90", msg)

    # =========================================================================
    # Test 2: Pixel -> world coordinate conversion
    # =========================================================================
    def test_02_pixel_to_world_conversion(self):
        transform = [self.true_a, self.true_b, self.true_c, self.true_d, self.true_e, self.true_f]
        wx, wy = gcp_pixel_to_world(200.0, 400.0, transform)

        expected_x = 0.5 * 200.0 + 500000.0  # 500100.0
        expected_y = -0.5 * 400.0 + 1450000.0 # 1449800.0

        self.assertAlmostEqual(wx, expected_x, places=3)
        self.assertAlmostEqual(wy, expected_y, places=3)

    # =========================================================================
    # Test 3: Reverse conversion (world -> pixel)
    # =========================================================================
    def test_03_world_to_pixel_roundtrip(self):
        transform = [self.true_a, self.true_b, self.true_c, self.true_d, self.true_e, self.true_f]
        test_points = [(150.0, 250.0), (450.5, 780.2), (890.0, 120.0)]

        for px, py in test_points:
            wx, wy = gcp_pixel_to_world(px, py, transform)
            rec_px, rec_py = gcp_world_to_pixel(wx, wy, transform)
            self.assertAlmostEqual(px, rec_px, places=5)
            self.assertAlmostEqual(py, rec_py, places=5)

    # =========================================================================
    # Test 4: Affine transformation recovery with synthetic points
    # =========================================================================
    def test_04_affine_transformation_recovery(self):
        res = calculate_gcp_transformation(
            gcps=self.exact_gcps,
            target_crs="EPSG:32643",
            image_width=1000.0,
            image_height=1000.0
        )

        self.assertEqual(res["status"], "ready")
        self.assertEqual(res["gcp_count"], 5)
        self.assertAlmostEqual(res["rmse"], 0.0, places=4)

        t = res["transform"]
        self.assertAlmostEqual(t[0], self.true_a, places=5) # a
        self.assertAlmostEqual(t[1], self.true_b, places=5) # b
        self.assertAlmostEqual(t[2], self.true_c, places=2) # c
        self.assertAlmostEqual(t[3], self.true_d, places=5) # d
        self.assertAlmostEqual(t[4], self.true_e, places=5) # e
        self.assertAlmostEqual(t[5], self.true_f, places=2) # f

        # Verify spatial distribution is marked Good
        self.assertFalse(res["distribution"]["is_clustered"])
        self.assertEqual(res["distribution"]["status"], "Good")

    # =========================================================================
    # Test 5: Residual error and RMSE with slightly noisy GCPs
    # =========================================================================
    def test_05_residual_error_and_rmse(self):
        noisy_gcps = []
        noise = [0.10, -0.15, 0.20, -0.05, 0.12]

        for i, gcp in enumerate(self.exact_gcps):
            g = dict(gcp)
            g["world_x"] += noise[i]
            g["world_y"] -= noise[i]
            noisy_gcps.append(g)

        res = calculate_gcp_transformation(noisy_gcps, target_crs="EPSG:32643")

        self.assertGreater(res["rmse"], 0.0)
        self.assertLess(res["rmse"], 0.5)  # reasonable bounds for small noise
        self.assertIn("residuals", res)
        self.assertEqual(len(res["residuals"]), 5)
        for g_id, residual_m in res["residuals"].items():
            self.assertGreaterEqual(residual_m, 0.0)

    # =========================================================================
    # Test 6: Cross-CRS handling (Geographic EPSG:4326 GCP -> Projected UTM image)
    # =========================================================================
    def test_06_cross_crs_transformation(self):
        geo_gcps = []
        for g in self.exact_gcps:
            # Reproject projected coordinates to WGS84 Lat/Lon
            lon, lat = transform_coordinates(g["world_x"], g["world_y"], src_crs="EPSG:32643", dst_crs="EPSG:4326")
            geo_gcps.append({
                "id": g["id"],
                "name": g["name"],
                "image_x": g["image_x"],
                "image_y": g["image_y"],
                "coordinate_type": "geographic",
                "latitude": lat,
                "longitude": lon,
                "crs": "EPSG:4326"
            })

        # Calculate transformation into target CRS EPSG:32643
        res = calculate_gcp_transformation(geo_gcps, target_crs="EPSG:32643")
        self.assertEqual(res["status"], "ready")
        self.assertEqual(res["crs"], "EPSG:32643")
        self.assertLess(res["rmse"], 0.05)  # reprojection roundtrip error is negligible

    # =========================================================================
    # Test 7: GeoJSON export with active GCP georeferencing
    # =========================================================================
    def test_07_geojson_export_with_gcp(self):
        res = calculate_gcp_transformation(self.exact_gcps, target_crs="EPSG:32643")

        meta = {
            "image_id": "img_gcp_test",
            "is_georeferenced": False, # Plain JPG initially
            "active_georeferencing": "gcp",
            "gcp_transformation": res,
            "gcps": self.exact_gcps
        }

        detection_data = {
            "image_id": "img_gcp_test",
            "detection_mode": "Survey Photogrammetry",
            "features": {
                "buildings": [
                    {
                        "id": "bld_gcp_1",
                        "feature_type": "building",
                        "area_px": 400.0,
                        "polygon": [[100, 100], [200, 100], [200, 200], [100, 200], [100, 100]]
                    }
                ]
            },
            "parcels": []
        }

        geojson_doc = export_to_geojson(detection_data, meta)
        self.assertTrue(geojson_doc["metadata"]["is_georeferenced"])
        self.assertEqual(geojson_doc["metadata"]["georeferencing_method"], "GCP Affine Transformation")
        self.assertEqual(geojson_doc["metadata"]["crs"], "EPSG:4326")

        coords = geojson_doc["features"][0]["geometry"]["coordinates"][0]
        for pt in coords:
            lon, lat = pt[0], pt[1]
            self.assertGreater(lon, 74.0)
            self.assertLess(lon, 76.0)
            self.assertGreater(lat, 12.0)
            self.assertLess(lat, 14.5)

    # =========================================================================
    # Test 8: Persistence across metadata reloads
    # =========================================================================
    def test_08_gcp_persistence(self):
        meta_file = os.path.join(self.temp_dir.name, "sample_meta.json")
        res = calculate_gcp_transformation(self.exact_gcps, target_crs="EPSG:32643")

        initial_meta = {
            "image_id": "test_persistence_id",
            "gcps": self.exact_gcps,
            "gcp_transformation": res,
            "active_georeferencing": "gcp"
        }

        with open(meta_file, "w") as f:
            json.dump(initial_meta, f)

        # Simulate reopening / reloading project
        with open(meta_file, "r") as f:
            reloaded_meta = json.load(f)

        self.assertEqual(len(reloaded_meta["gcps"]), 5)
        self.assertEqual(reloaded_meta["active_georeferencing"], "gcp")
        self.assertAlmostEqual(reloaded_meta["gcp_transformation"]["rmse"], 0.0, places=3)
        self.assertEqual(reloaded_meta["gcp_transformation"]["transform"], res["transform"])

    # =========================================================================
    # Test 9: Existing Part 1 functionality remains completely working
    # =========================================================================
    def test_09_part1_functionality_preserved(self):
        # 1. PixelMeasurement
        px_fmt = MeasurementService.get_formatter("pixels", {})
        self.assertIsInstance(px_fmt, PixelMeasurement)
        self.assertEqual(px_fmt.format_distance(500), "500 px")

        # 2. CalibratedMeasurement
        cal_meta = {"calibration": {"meters_per_pixel": 0.25}}
        cal_fmt = MeasurementService.get_formatter("calibrated", cal_meta)
        self.assertIsInstance(cal_fmt, CalibratedMeasurement)
        self.assertIn("125.0 m", cal_fmt.format_distance(500))

        # 3. GeoTIFF Native Measurement
        geotiff_meta = {
            "is_georeferenced": True,
            "crs": "EPSG:32643",
            "transform": [0.5, 0.0, 500000.0, 0.0, -0.5, 1450000.0]
        }
        geo_fmt = MeasurementService.get_formatter("geographic", geotiff_meta)
        self.assertIsInstance(geo_fmt, GeographicMeasurement)
        self.assertIn("25.0 m²", geo_fmt.format_area(100))


if __name__ == '__main__':
    unittest.main()
