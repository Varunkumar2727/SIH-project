import os
import sys
import tempfile
import unittest

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from services.review.review_service import ReviewService
from services.reporting.reportlab_generator import GovernmentReportGenerator
from services.reporting.export_package import ExportPackageService
from services.analytics.scoring_engine import DecisionScoringEngine
from services.analytics.hotspot_service import HotspotAnalysisService

class TestBlockB(unittest.TestCase):
    """
    Tests for Block B:
    - Part 7: ReviewService & immutable audit trail
    - Part 8: ReportLab PDF & ExportPackageService
    - Part 9: DecisionScoringEngine & HotspotAnalysisService
    """

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def test_review_service_lifecycle_and_audit(self):
        rev_service = ReviewService(storage_dir=self.temp_dir)
        case = rev_service.create_case(
            project_id="proj_101",
            entity_id="chg_001",
            entity_type="change",
            evidence_summary={"change_type": "NEW_CONSTRUCTION", "delta_px": 450}
        )
        self.assertEqual(case["status"], "UNREVIEWED")

        # Officer confirms
        updated = rev_service.record_decision(
            case_id=case["case_id"],
            officer_id="officer_rajesh",
            officer_name="Rajesh Kumar",
            decision="CONFIRMED",
            notes="Ground reality matches satellite image."
        )
        self.assertEqual(updated["status"], "CONFIRMED")
        self.assertEqual(updated["decision"], "CONFIRMED")

        # Audit trail check
        trail = rev_service.get_audit_trail(case_id=case["case_id"])
        self.assertEqual(len(trail), 2) # CREATE + DECISION
        self.assertEqual(trail[1]["officer_id"], "officer_rajesh")
        self.assertEqual(trail[1]["action"], "DECISION_CONFIRMED")

    def test_field_task_generation(self):
        rev_service = ReviewService(storage_dir=self.temp_dir)
        case = rev_service.create_case(
            project_id="proj_101",
            entity_id="disc_002",
            entity_type="discrepancy",
            evidence_summary={"discrepancy_type": "BOUNDARY_MISALIGNMENT"}
        )
        updated = rev_service.record_decision(
            case_id=case["case_id"],
            officer_id="officer_priya",
            officer_name="Priya Sharma",
            decision="FIELD_VERIFICATION_REQUIRED",
            notes="Discrepancy of 4.5m detected; physical boundary inspection necessary.",
            field_task_details={
                "target_coordinates": [77.5946, 12.9716],
                "instructions": "Inspect fence position on east boundary."
            }
        )
        self.assertIsNotNone(updated.get("field_task_id"))

    def test_pdf_dossier_generation(self):
        pdf_path = os.path.join(self.temp_dir, "test_dossier.pdf")
        meta = {"project_id": "PRJ-TEST-88", "crs": "EPSG:32643", "georeferencing_method": "GCP Affine"}
        parcels = [{"id": "AI-P-9001", "area_px": 1200.5, "compactness": 0.82, "accessibility": {"access_status": "DIRECT_ACCESS"}}]
        changes = [{"change_id": "CHG-101", "change_type": "NEW_CONSTRUCTION", "area_delta_px": 250, "status": "CONFIRMED"}]

        out = GovernmentReportGenerator.generate_project_dossier(
            pdf_path, project_meta=meta, parcel_data=parcels, change_data=changes
        )
        self.assertTrue(os.path.exists(out))
        self.assertGreater(os.path.getsize(out), 1000)

    def test_csv_and_bundle_export(self):
        csv_path = os.path.join(self.temp_dir, "parcels.csv")
        zip_path = os.path.join(self.temp_dir, "survey_bundle.zip")
        parcels = [{"id": "AI-P-1", "area_px": 500.0, "accessibility": {"access_status": "DIRECT_ACCESS"}}]

        ExportPackageService.export_parcels_csv(parcels, csv_path)
        self.assertTrue(os.path.exists(csv_path))

        ExportPackageService.create_offline_survey_bundle(zip_path, csv_path=csv_path, metadata={"survey_date": "2026-09-04"})
        self.assertTrue(os.path.exists(zip_path))

    def test_decision_scoring_engine(self):
        parcel = {
            "id": "AI-P-1234",
            "compactness": 0.8,
            "accessibility": {"access_status": "DIRECT_ACCESS"}
        }
        cad_comp = {"status": "MATCHED", "iou": 0.92}
        res = DecisionScoringEngine.evaluate_parcel_readiness(parcel, cad_comp)
        self.assertGreaterEqual(res["development_readiness_score"], 80.0)
        self.assertLessEqual(res["discrepancy_risk_score"], 20.0)
        self.assertEqual(res["priority_category"], "ROUTINE_MONITORING")

    def test_hotspot_service(self):
        items = [
            {"id": "p1", "polygon": [[10, 10], [20, 10], [20, 20], [10, 20]]},
            {"id": "p2", "polygon": [[15, 15], [25, 15], [25, 25], [15, 25]]},
            {"id": "p_far", "polygon": [[800, 800], [820, 800], [820, 820], [800, 820]]}
        ]
        hotspots = HotspotAnalysisService.identify_hotspots(items, grid_size_px=100.0, min_cluster_size=2)
        self.assertEqual(len(hotspots), 1)
        self.assertEqual(hotspots[0]["item_count"], 2)

if __name__ == "__main__":
    unittest.main()
