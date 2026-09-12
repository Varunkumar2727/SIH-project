"""
Comprehensive Test Suite for Geospatial Coordinates & Services
Verifies the 6 foundational tests required for GeoCadastral AI:
  1. Load a georeferenced GeoTIFF (CRS, transform, bounds detected)
  2. Convert pixel -> world (reasonable native coordinates)
  3. Convert world -> pixel (inverts and recovers pixel position)
  4. Convert native CRS -> EPSG:4326 (WGS84 Lat/Lon)
  5. Export detected polygon to GeoJSON (real geographic coordinates in EPSG:4326)
  6. Non-georeferenced images (JPG/PNG manual calibration / pixel fallback)
"""

import os
import sys
import tempfile
import unittest
import numpy as np
import rasterio
from rasterio.transform import from_origin
from PIL import Image

# Ensure backend root is on sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from services.geospatial import (
    extract_geotiff_metadata,
    pixel_to_world,
    world_to_pixel,
    transform_coordinates,
    calculate_real_distance,
    calculate_real_area,
    MeasurementService,
    PixelMeasurement,
    CalibratedMeasurement,
    GeographicMeasurement
)
from services.geojson_export import export_to_geojson


class TestGeospatialFoundation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        
        # 1. Create a synthetic georeferenced GeoTIFF in UTM 43N (South India / Karnataka region)
        # Origin: Easting 500,000 m, Northing 1,450,000 m, Resolution 0.5m/px, 200x200 pixels
        cls.geotiff_path = os.path.join(cls.temp_dir.name, "sample_utm43n.tif")
        transform = from_origin(500000.0, 1450000.0, 0.5, 0.5)
        data = np.full((1, 200, 200), 128, dtype=np.uint8)
        with rasterio.open(
            cls.geotiff_path,
            'w',
            driver='GTiff',
            height=200,
            width=200,
            count=1,
            dtype=data.dtype,
            crs='EPSG:32643',
            transform=transform
        ) as dst:
            dst.write(data)

        # 2. Create a synthetic non-georeferenced JPG
        cls.jpg_path = os.path.join(cls.temp_dir.name, "sample_drone.jpg")
        img = Image.new("RGB", (400, 300), color=(200, 180, 150))
        img.save(cls.jpg_path, "JPEG")

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    # =========================================================================
    # Test 1: Load a georeferenced GeoTIFF
    # Verify: CRS detected, transform detected, bounds detected
    # =========================================================================
    def test_01_load_geotiff_metadata(self):
        meta = extract_geotiff_metadata(self.geotiff_path)

        self.assertTrue(meta["georeferenced"], "GeoTIFF should be marked as georeferenced")
        self.assertEqual(meta["crs"], "EPSG:32643")
        self.assertEqual(meta["epsg"], 32643)
        self.assertEqual(meta["coordinate_type"], "projected")
        self.assertEqual(meta["units"], "metre")
        self.assertEqual(meta["width"], 200)
        self.assertEqual(meta["height"], 200)

        # Check transform
        self.assertIsNotNone(meta["transform"])
        self.assertEqual(len(meta["transform"]), 6)
        self.assertAlmostEqual(meta["transform"][0], 0.5)   # pixel width
        self.assertAlmostEqual(meta["transform"][4], -0.5)  # pixel height (negative for top-down)
        self.assertAlmostEqual(meta["transform"][2], 500000.0) # top-left x
        self.assertAlmostEqual(meta["transform"][5], 1450000.0) # top-left y

        # Check bounds
        bounds = meta["bounds"]
        self.assertIsNotNone(bounds)
        self.assertAlmostEqual(bounds["left"], 500000.0)
        self.assertAlmostEqual(bounds["top"], 1450000.0)
        self.assertAlmostEqual(bounds["right"], 500100.0)
        self.assertAlmostEqual(bounds["bottom"], 1449900.0)

        # Check pixel resolution
        self.assertAlmostEqual(meta["pixel_size"]["x"], 0.5)
        self.assertAlmostEqual(meta["pixel_size"]["y"], 0.5)

    # =========================================================================
    # Test 2: Convert pixel -> world
    # Verify: reasonable coordinates
    # =========================================================================
    def test_02_pixel_to_world(self):
        meta = extract_geotiff_metadata(self.geotiff_path)
        transform = meta["transform"]

        # Pixel (0, 0) top-left corner
        wx_0, wy_0 = pixel_to_world(0, 0, transform)
        self.assertAlmostEqual(wx_0, 500000.0)
        self.assertAlmostEqual(wy_0, 1450000.0)

        # Pixel (100, 100) center
        wx_mid, wy_mid = pixel_to_world(100, 100, transform)
        # 500000 + 100 * 0.5 = 500050.0
        # 1450000 - 100 * 0.5 = 1449950.0
        self.assertAlmostEqual(wx_mid, 500050.0)
        self.assertAlmostEqual(wy_mid, 1449950.0)

        # Pixel (200, 200) bottom-right corner
        wx_end, wy_end = pixel_to_world(200, 200, transform)
        self.assertAlmostEqual(wx_end, 500100.0)
        self.assertAlmostEqual(wy_end, 1449900.0)

    # =========================================================================
    # Test 3: Convert world -> pixel
    # Verify: the original pixel position is approximately recovered
    # =========================================================================
    def test_03_world_to_pixel_roundtrip(self):
        meta = extract_geotiff_metadata(self.geotiff_path)
        transform = meta["transform"]

        test_pixels = [(0.0, 0.0), (45.5, 78.2), (100.0, 100.0), (199.0, 199.0)]
        for px_x, px_y in test_pixels:
            world_x, world_y = pixel_to_world(px_x, px_y, transform)
            rec_x, rec_y = world_to_pixel(world_x, world_y, transform)
            self.assertAlmostEqual(px_x, rec_x, places=5, msg=f"Pixel X recovery failed for ({px_x}, {px_y})")
            self.assertAlmostEqual(px_y, rec_y, places=5, msg=f"Pixel Y recovery failed for ({px_x}, {px_y})")

    # =========================================================================
    # Test 4: Convert native CRS -> EPSG:4326
    # Verify: coordinates reproject to legitimate Indian WGS84 lat/lon
    # =========================================================================
    def test_04_crs_transformation_to_wgs84(self):
        meta = extract_geotiff_metadata(self.geotiff_path)
        transform = meta["transform"]

        # Center point world coordinates
        wx, wy = pixel_to_world(100, 100, transform)
        lon, lat = transform_coordinates(wx, wy, src_crs=meta["crs"], dst_crs="EPSG:4326")

        # UTM 43N (around 75°E, 13.1°N Karnataka, India)
        self.assertGreater(lon, 74.0)
        self.assertLess(lon, 76.0)
        self.assertGreater(lat, 12.0)
        self.assertLess(lat, 14.5)

        # Inverse transformation
        back_x, back_y = transform_coordinates(lon, lat, src_crs="EPSG:4326", dst_crs=meta["crs"])
        self.assertAlmostEqual(wx, back_x, places=2)
        self.assertAlmostEqual(wy, back_y, places=2)

    # =========================================================================
    # Test 5: Export detected polygon to GeoJSON
    # Verify: GeoJSON contains real geographic coordinates instead of pixel coordinates
    # =========================================================================
    def test_05_geojson_export_real_coordinates(self):
        meta = extract_geotiff_metadata(self.geotiff_path)
        meta_dict = {
            "image_id": "img_test123",
            "is_georeferenced": True,
            "crs": meta["crs"],
            "transform": meta["transform"],
            "geospatial": meta
        }

        # A parcel polygon in pixel coordinates
        sample_detection = {
            "image_id": "img_test123",
            "detection_mode": "Prototype Computer Vision",
            "features": {
                "buildings": [
                    {
                        "id": "bld_1",
                        "feature_type": "building",
                        "area_px": 400.0,
                        "polygon": [[10, 10], [30, 10], [30, 30], [10, 30], [10, 10]]
                    }
                ]
            },
            "parcels": [
                {
                    "parcel_id": "PARCEL_001",
                    "area_px": 1600.0,
                    "polygon": [[10, 10], [50, 10], [50, 50], [10, 50], [10, 10]]
                }
            ]
        }

        geojson_out = export_to_geojson(sample_detection, meta_dict)

        self.assertEqual(geojson_out["type"], "FeatureCollection")
        self.assertTrue(geojson_out["metadata"]["is_georeferenced"])
        self.assertEqual(geojson_out["metadata"]["crs"], "EPSG:4326")
        self.assertEqual(geojson_out["metadata"]["native_crs"], "EPSG:32643")
        self.assertEqual(geojson_out["metadata"]["native_epsg"], 32643)
        self.assertEqual(len(geojson_out["features"]), 2)

        # Check geometry of the first feature (building)
        bld_feat = geojson_out["features"][0]
        coords = bld_feat["geometry"]["coordinates"][0]

        for pt in coords:
            lon, lat = pt[0], pt[1]
            # Real WGS84 coordinates in India, NOT image pixel coords like (10, 10)
            self.assertGreater(lon, 70.0, "Coordinate must be geographic Longitude, not pixel X")
            self.assertGreater(lat, 8.0, "Coordinate must be geographic Latitude, not pixel Y")
            self.assertLess(lon, 90.0)
            self.assertLess(lat, 35.0)

        # Verify real-world area calculation is populated in properties
        props = bld_feat["properties"]
        self.assertIn("area_m2", props)
        # 20px x 20px with 0.5m resolution = 10m x 10m = 100 m²
        self.assertAlmostEqual(props["area_m2"], 100.0, places=1)
        self.assertAlmostEqual(props["area_hectares"], 0.01, places=3)

    # =========================================================================
    # Test 6: Non-georeferenced JPG workflow
    # Verify: pixel and manual calibration workflow still works intact
    # =========================================================================
    def test_06_non_georeferenced_jpg_and_manual_calibration(self):
        # 1. Uncalibrated JPG metadata
        meta_uncalibrated = {
            "image_id": "img_drone_jpg",
            "is_georeferenced": False,
            "crs": "Image is not georeferenced",
            "width": 400,
            "height": 300
        }

        # MeasurementService default priority -> PixelMeasurement
        formatter_px = MeasurementService.get_formatter("pixels", meta_uncalibrated)
        self.assertIsInstance(formatter_px, PixelMeasurement)
        self.assertEqual(formatter_px.format_distance(500), "500 px")
        self.assertEqual(formatter_px.format_area(25000), "25,000 px²")

        # 2. Calibrated 2-point measurement
        meta_calibrated = {
            "image_id": "img_drone_jpg",
            "is_georeferenced": False,
            "crs": "Image is not georeferenced",
            "calibration": {
                "pixel_distance": 500.0,
                "real_distance": 100.0,
                "unit": "meters",
                "meters_per_pixel": 0.2
            }
        }
        formatter_cal = MeasurementService.get_formatter("calibrated", meta_calibrated)
        self.assertIsInstance(formatter_cal, CalibratedMeasurement)
        self.assertEqual(formatter_cal.format_distance(750), "150.0 m")
        formatted_area = formatter_cal.format_area(25000)
        self.assertIn("1,000.0 m²", formatted_area)
        self.assertIn("0.100 ha", formatted_area)

        # 3. GeoJSON export for uncalibrated JPG must retain pixel coordinates
        sample_detection = {
            "image_id": "img_drone_jpg",
            "features": {
                "open_land": [
                    {
                        "id": "land_1",
                        "feature_type": "open_land",
                        "area_px": 5000.0,
                        "polygon": [[50, 50], [150, 50], [150, 150], [50, 150], [50, 50]]
                    }
                ]
            },
            "parcels": []
        }
        geojson_jpg = export_to_geojson(sample_detection, meta_uncalibrated)
        self.assertFalse(geojson_jpg["metadata"]["is_georeferenced"])
        self.assertEqual(geojson_jpg["metadata"]["crs"], "Pixel (CRS.Simple)")
        coords = geojson_jpg["features"][0]["geometry"]["coordinates"][0]
        # Must retain original pixel coords, NOT invent fake lat/lon
        self.assertEqual(coords[0], [50, 50])
        self.assertEqual(coords[1], [150, 50])


if __name__ == '__main__':
    unittest.main()
