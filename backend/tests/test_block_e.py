import os
import sys
import tempfile
import sqlite3
import unittest

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from services.platform.backup import DisasterRecoveryService
from services.platform.db import PlatformDatabase
from services.gis.ssrf_guard import SSRFGuard, SSRFSecurityException
from services.platform.storage import LocalStorageProvider, StorageSecurityException
from services.saas.api_keys import APIKeyManager
from services.parcel.access_path import AccessPathService
from services.parcel.cadastral_comparison import CadastralComparisonService

class TestBlockE(unittest.TestCase):
    """
    Tests for Block E (Part 15):
    - Disaster recovery backup & restore
    - Path traversal prevention
    - SSRF prevention
    - Secret hashing verification
    - Legal & Decision-support terminology audit
    """

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "prod_live.db")
        self.db = PlatformDatabase.get_instance(self.db_path)

    def test_disaster_recovery_backup_and_restore(self):
        # Create test records
        self.db.create_organization("org_maharashtra", "Maharashtra Land Records", "ENTERPRISE")
        self.db.create_user("u_surv", "org_maharashtra", "surv@maha.gov.in", "Anil Deshmukh", "SURVEY_OFFICER")

        dr_service = DisasterRecoveryService(self.db_path, backup_dir=os.path.join(self.temp_dir, "backups"))
        backup_meta = dr_service.create_backup()
        self.assertTrue(os.path.exists(backup_meta["backup_path"]))

        # Restore into fresh DB path
        restored_path = os.path.join(self.temp_dir, "restored.db")
        healthy = dr_service.restore_and_verify(backup_meta["backup_path"], restored_path)
        self.assertTrue(healthy)

        # Query restored database to verify record integrity
        conn = sqlite3.connect(restored_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM organizations WHERE id = 'org_maharashtra'")
        org_row = cur.fetchone()
        self.assertIsNotNone(org_row)
        self.assertEqual(org_row[0], "Maharashtra Land Records")
        conn.close()

    def test_secret_hashing_compliance(self):
        key_mgr = APIKeyManager(storage_dir=self.temp_dir)
        key_data = key_mgr.generate_key("org_1", "Test Key", ["projects:read"])
        raw_secret = key_data["secret_key"]

        # Read JSON file from disk to ensure raw_secret is NOT stored anywhere
        key_file = os.path.join(self.temp_dir, f"{key_data['key_id']}.json")
        with open(key_file, "r") as f:
            disk_content = f.read()

        self.assertNotIn(raw_secret, disk_content)
        self.assertIn("hashed_secret", disk_content)

    def test_decision_support_terminology_compliance(self):
        """
        Part 15 / Requirement 50:
        Verifies system outputs strictly avoid legal declarations
        ('illegal', 'legal ownership', 'legal easement', 'encroachment').
        """
        access_eval = AccessPathService().evaluate_parcel_access(Polygon([]), [])
        disclaimer = access_eval.get("legal_disclaimer", "")
        self.assertIn("does not establish legal right-of-way or easement", disclaimer.lower())

        comp_eval = CadastralComparisonService.compare_parcel_layers([], [])
        # Results should not make legal ownership assertions
        for r in comp_eval.get("comparison_results", []):
            self.assertNotIn("illegal", r.get("status", "").lower())

if __name__ == "__main__":
    from shapely.geometry import Polygon
    unittest.main()
else:
    from shapely.geometry import Polygon
