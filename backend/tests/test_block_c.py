import os
import sys
import tempfile
import time
import unittest

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from services.platform.db import PlatformDatabase
from services.platform.rbac import RoleBasedAccessControl
from services.platform.job_queue import JobManager
from services.platform.storage import LocalStorageProvider, StorageSecurityException

class TestBlockC(unittest.TestCase):
    """
    Tests for Block C:
    - Part 10: Multi-tenant DB & RBAC
    - Part 11: JobManager queue & Secure Storage
    """

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_platform.db")
        self.db = PlatformDatabase.get_instance(self.db_path)

    def test_multi_tenant_db_entities(self):
        org = self.db.create_organization("org_karnataka_rev", "Karnataka Revenue Department", "ENTERPRISE")
        self.assertEqual(org["id"], "org_karnataka_rev")

        user = self.db.create_user("u_officer1", "org_karnataka_rev", "surveyor1@karnataka.gov.in", "Suresh Rao", "SURVEY_OFFICER")
        self.assertEqual(user["full_name"], "Suresh Rao")

        proj = self.db.create_project("p_bangalore_east", "org_karnataka_rev", "Bangalore East Cadastral Survey", "u_officer1")
        self.assertEqual(proj["name"], "Bangalore East Cadastral Survey")

        fetched_proj = self.db.get_project("p_bangalore_east")
        self.assertIsNotNone(fetched_proj)
        self.assertEqual(fetched_proj["org_id"], "org_karnataka_rev")

    def test_rbac_and_tenant_isolation(self):
        # Organization Admin can manage org and users
        self.assertTrue(RoleBasedAccessControl.can_perform("ORGANIZATION_ADMIN", "user:manage"))
        self.assertTrue(RoleBasedAccessControl.can_perform("ORGANIZATION_ADMIN", "project:delete"))

        # Survey Officer can record decisions, cannot manage users or delete projects
        self.assertTrue(RoleBasedAccessControl.can_perform("SURVEY_OFFICER", "review:decide"))
        self.assertFalse(RoleBasedAccessControl.can_perform("SURVEY_OFFICER", "user:manage"))
        self.assertFalse(RoleBasedAccessControl.can_perform("SURVEY_OFFICER", "project:delete"))

        # Tenant isolation
        self.assertTrue(RoleBasedAccessControl.enforce_tenant_isolation("org_A", "org_A"))
        with self.assertRaises(PermissionError):
            RoleBasedAccessControl.enforce_tenant_isolation("org_A", "org_B")

    def test_job_queue_execution(self):
        mgr = JobManager(max_cpu_workers=2, max_gpu_workers=1)

        def add_task(a, b):
            return a + b

        job_id = mgr.submit_job(task_name="test_addition", func=add_task, args=(15, 27), queue_type="cpu")
        # Give worker a moment to process
        time.sleep(0.1)
        status = mgr.get_job_status(job_id)
        self.assertEqual(status["status"], "COMPLETED")
        self.assertEqual(status["result"], 42)

    def test_storage_path_traversal_defense(self):
        storage = LocalStorageProvider(base_dir=self.temp_dir)
        # Valid save & read
        saved = storage.save_file("projects/img1.bin", b"test_imagery_data")
        self.assertTrue(os.path.exists(saved["absolute_path"]))
        self.assertEqual(storage.read_file("projects/img1.bin"), b"test_imagery_data")

        # Malicious traversal attempt should raise StorageSecurityException
        with self.assertRaises(StorageSecurityException):
            storage.save_file("../../outside.txt", b"malicious")

        with self.assertRaises(StorageSecurityException):
            storage.read_file("../../windows/system32/drivers/etc/hosts")

if __name__ == "__main__":
    unittest.main()
