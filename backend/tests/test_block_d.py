import os
import sys
import tempfile
import unittest
import numpy as np

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from services.ai.dataset_service import DatasetService
from services.ai.trainer import ModelTrainer
from services.ai.model_registry import ModelRegistry
from services.gis.ssrf_guard import SSRFGuard, SSRFSecurityException
from services.gis.providers import ShapefileValidator
from services.saas.entitlement import EntitlementService
from services.saas.api_keys import APIKeyManager
from services.saas.usage_tracker import UsageTracker

class TestBlockD(unittest.TestCase):
    """
    Tests for Block D:
    - Part 12: DatasetService, ModelTrainer, ModelRegistry
    - Part 13: SSRFGuard & ShapefileValidator
    - Part 14: EntitlementService, APIKeyManager, UsageTracker
    """

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def test_dataset_leakage_free_split_and_validation(self):
        ds_service = DatasetService(storage_dir=self.temp_dir)
        ds = ds_service.create_dataset(
            name="Karnataka Rural Aerial 2026",
            geographic_region="rural",
            capture_type="drone",
            resolution_m=0.05
        )
        self.assertEqual(ds["geographic_region"], "rural")

        # Samples across 3 distinct survey scenes
        samples = [
            {"image_path": "scene1_tile1.png", "width": 512, "height": 512, "scene_id": "flight_A", "annotations": [{"class": "building"}]},
            {"image_path": "scene1_tile2.png", "width": 512, "height": 512, "scene_id": "flight_A", "annotations": [{"class": "road"}]},
            {"image_path": "scene2_tile1.png", "width": 512, "height": 512, "scene_id": "flight_B", "annotations": [{"class": "building"}]},
            {"image_path": "scene3_tile1.png", "width": 512, "height": 512, "scene_id": "flight_C", "annotations": [{"class": "vegetation"}]},
        ]

        val_rep = ds_service.validate_dataset(ds["dataset_id"], samples)
        self.assertEqual(val_rep["validation_status"], "READY")
        self.assertEqual(val_rep["valid_samples"], 4)

        splits = ds_service.generate_leakage_free_split(samples)
        self.assertGreater(splits["train_count"], 0)
        self.assertGreater(splits["val_count"], 0)
        self.assertGreater(splits["test_count"], 0)

    def test_real_segmentation_metrics(self):
        gt = np.array([[1, 1], [0, 2]])
        pred = np.array([[1, 0], [0, 2]])
        metrics = ModelTrainer.calculate_segmentation_metrics(gt, pred, num_classes=3)
        self.assertIn("mean_iou", metrics)
        self.assertIn("building", metrics["per_class"])
        # Class 1 (building): TP=1, FP=0, FN=1 -> IoU = 1 / (1 + 0 + 1) = 0.5
        self.assertEqual(metrics["per_class"]["building"]["iou"], 0.5)

    def test_model_registry_and_deployment_pinning(self):
        reg = ModelRegistry(registry_dir=self.temp_dir)
        mod = reg.register_model(
            name="GeoCadastral-Karnataka-Dense",
            version="1.2.0",
            dataset_version="ds_rural_v1",
            metrics={"mIoU": 0.784, "F1": 0.812},
            weights_reference="models/weights_v1.2.onnx"
        )
        self.assertEqual(mod["status"], "AVAILABLE")

        deployed = reg.deploy_model(mod["model_id"], authorized_by="Director_GIS")
        self.assertEqual(deployed["status"], "DEPLOYED")

        active = reg.get_active_model()
        self.assertIsNotNone(active)
        self.assertEqual(active["version"], "1.2.0")

    def test_ssrf_protection(self):
        # Disallow loopback
        with self.assertRaises(SSRFSecurityException):
            SSRFGuard.validate_url("http://localhost:8000/geoserver/wms")

        with self.assertRaises(SSRFSecurityException):
            SSRFGuard.validate_url("http://127.0.0.1/cadastral")

        # Disallow private subnet
        with self.assertRaises(SSRFSecurityException):
            SSRFGuard.validate_url("http://192.168.1.100/gis")

        # Disallow cloud metadata
        with self.assertRaises(SSRFSecurityException):
            SSRFGuard.validate_url("http://169.254.169.254/latest/meta-data")

        # Allow valid public endpoints
        valid_url = "https://bhuvan-vec1.nrsc.gov.in/bhuvan/wms"
        self.assertEqual(SSRFGuard.validate_url(valid_url), valid_url)

    def test_entitlement_service(self):
        self.assertTrue(EntitlementService.can_use_feature("PRO", "TEMPORAL_ANALYSIS"))
        self.assertFalse(EntitlementService.can_use_feature("FREE", "API_ACCESS"))
        self.assertTrue(EntitlementService.can_use_feature("ENTERPRISE", "CUSTOM_MODELS"))

    def test_api_key_management_and_usage(self):
        key_mgr = APIKeyManager(storage_dir=self.temp_dir)
        usage = UsageTracker(storage_dir=self.temp_dir)

        created = key_mgr.generate_key(
            org_id="org_delhi_gis",
            name="Production Ingestion Key",
            scopes=["projects:read", "analysis:run"]
        )
        raw_secret = created["secret_key"]
        self.assertTrue(raw_secret.startswith("gc_live_"))

        # Authenticate
        auth = key_mgr.authenticate_key(raw_secret, required_scope="projects:read")
        self.assertIsNotNone(auth)
        self.assertEqual(auth["org_id"], "org_delhi_gis")

        # Record usage
        usage.record_usage("org_delhi_gis", "API_CALL", 1.0, "requests")
        usage.record_usage("org_delhi_gis", "AREA_PROCESSED_SQM", 4500.0, "m2")

        summary = usage.get_org_summary("org_delhi_gis")
        self.assertEqual(summary["total_api_calls"], 1)
        self.assertEqual(summary["total_area_processed_sqm"], 4500.0)

if __name__ == "__main__":
    unittest.main()
