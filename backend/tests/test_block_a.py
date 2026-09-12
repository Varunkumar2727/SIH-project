import os
import sys
import unittest
import numpy as np
from shapely.geometry import Polygon

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from services.ai.model_manager import ModelManager
from services.ai.feature_detector import FeatureDetector
from services.parcel.access_path import AccessPathService
from services.parcel.parcel_engine import ParcelEngine
from services.parcel.cadastral_comparison import CadastralComparisonService
from services.temporal.change_detector import TemporalChangeDetector

class TestBlockA(unittest.TestCase):
    """
    Tests for Block A:
    - Part 3: ModelManager & FeatureDetector
    - Part 4: AccessPathService
    - Part 5: ParcelEngine & CadastralComparisonService
    - Part 6: TemporalChangeDetector
    """

    def test_model_manager_tiled_inference(self):
        manager = ModelManager.get_instance()
        # Synthetic aerial image 600x600x3
        img = np.zeros((600, 600, 3), dtype=np.uint8)
        img[100:250, 100:250] = [200, 200, 200] # Building
        img[300:350, :] = [80, 80, 80]          # Road
        img[400:550, 400:550] = [20, 180, 30]   # Vegetation

        probs = manager.run_tiled_inference(img, tile_size=512, overlap_ratio=0.15)
        self.assertEqual(probs.shape, (600, 600, 6))
        # Softmax sum along class axis should be approximately 1.0 everywhere
        sums = np.sum(probs, axis=2)
        np.testing.assert_allclose(sums, 1.0, atol=1e-4)

    def test_access_path_frontage_classification(self):
        access_service = AccessPathService()
        road_feat = {
            "id": "road_1",
            "polygon": [[0, 100], [500, 100], [500, 120], [0, 120], [0, 100]]
        }
        access_service.build_road_network([road_feat])
        
        # Parcel 1: Directly adjacent to road (distance < 15 px)
        poly_direct = Polygon([[50, 60], [150, 60], [150, 95], [50, 95], [50, 60]])
        res_direct = access_service.evaluate_parcel_access(poly_direct, [Polygon(road_feat["polygon"]).exterior])
        self.assertEqual(res_direct["access_status"], "DIRECT_ACCESS")
        self.assertTrue(res_direct["direct_frontage"])

        # Parcel 2: Far away from road (distance > 60 px)
        poly_remote = Polygon([[50, 300], [150, 300], [150, 400], [50, 400], [50, 300]])
        res_remote = access_service.evaluate_parcel_access(poly_remote, [Polygon(road_feat["polygon"]).exterior])
        self.assertEqual(res_remote["access_status"], "PHYSICAL_ACCESS_CONCERN")
        self.assertFalse(res_remote["direct_frontage"])

    def test_parcel_engine_deterministic_hash(self):
        coords_a = [[10.0, 20.0], [50.0, 20.0], [50.0, 60.0], [10.0, 60.0], [10.0, 20.0]]
        # Slightly noisy floating point coordinates that round to same canonical value
        coords_b = [[10.04, 19.96], [50.02, 20.01], [49.98, 60.03], [10.01, 59.97], [10.04, 19.96]]

        id_a = ParcelEngine.generate_parcel_id(coords_a)
        id_b = ParcelEngine.generate_parcel_id(coords_b)
        self.assertEqual(id_a, id_b)
        self.assertTrue(id_a.startswith("AI-P-"))

    def test_cadastral_comparison(self):
        # 1 AI parcel perfectly matching cadastral
        ai_parcels = [
            {
                "id": "AI-P-1111",
                "polygon": [[100, 100], [200, 100], [200, 200], [100, 200], [100, 100]]
            },
            {
                "id": "AI-P-2222", # New unregistered building parcel
                "polygon": [[500, 500], [600, 500], [600, 600], [500, 600], [500, 500]]
            }
        ]
        cadastral_parcels = [
            {
                "id": "CAD-P-9999",
                "polygon": [[100, 100], [200, 100], [200, 200], [100, 200], [100, 100]]
            }
        ]

        comp = CadastralComparisonService.compare_parcel_layers(ai_parcels, cadastral_parcels)
        self.assertEqual(comp["summary"]["matched_count"], 1)
        self.assertEqual(comp["summary"]["unmatched_count"], 1)

    def test_temporal_change_chronology_and_detection(self):
        # Chronology validation test
        with self.assertRaises(ValueError):
            TemporalChangeDetector.validate_chronology("2025-01-01", "2024-01-01")

        scene_t1 = {
            "features": {
                "buildings": [
                    {"id": "b1", "polygon": [[50, 50], [100, 50], [100, 100], [50, 100], [50, 50]], "confidence": 0.9}
                ]
            }
        }
        scene_t2 = {
            "features": {
                "buildings": [
                    # b1 remained
                    {"id": "b1_curr", "polygon": [[50, 50], [100, 50], [100, 100], [50, 100], [50, 50]], "confidence": 0.9},
                    # b2 is brand new
                    {"id": "b2_curr", "polygon": [[300, 300], [380, 300], [380, 380], [300, 380], [300, 300]], "confidence": 0.88}
                ]
            }
        }

        changes = TemporalChangeDetector.detect_changes(scene_t1, scene_t2, t1_date="2023-01-01", t2_date="2024-01-01")
        self.assertEqual(changes["summary"]["new_constructions"], 1)
        self.assertEqual(changes["summary"]["total_changes_detected"], 1)

if __name__ == "__main__":
    unittest.main()
