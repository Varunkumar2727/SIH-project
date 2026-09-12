import os
import sqlite3
import shutil
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime, timezone

class DisasterRecoveryService:
    """
    Part 15: Backup, Disaster Recovery & Data Integrity Verification Engine.
    Uses SQLite's online backup API for safe, non-blocking snapshot creation
    and performs end-to-end restore validation.
    """

    def __init__(self, db_path: str, backup_dir: Optional[str] = None):
        self.db_path = db_path
        self.backup_dir = backup_dir or os.path.join(os.path.dirname(db_path), "backups")
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_backup(self) -> Dict[str, Any]:
        """
        Creates a consistent online snapshot of the database without locking readers.
        """
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{timestamp_str}.db"
        target_path = os.path.join(self.backup_dir, backup_filename)

        source_conn = sqlite3.connect(self.db_path)
        dest_conn = sqlite3.connect(target_path)
        try:
            with dest_conn:
                source_conn.backup(dest_conn)
        finally:
            dest_conn.close()
            source_conn.close()

        meta = {
            "backup_filename": backup_filename,
            "backup_path": target_path,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "size_bytes": os.path.getsize(target_path)
        }

        with open(os.path.join(self.backup_dir, f"{backup_filename}.meta.json"), "w") as f:
            json.dump(meta, f, indent=2)

        return meta

    def restore_and_verify(self, backup_path: str, restore_target_path: str) -> bool:
        """
        Simulates disaster recovery: restores from backup_path into restore_target_path
        and verifies table integrity.
        """
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup file not found at {backup_path}")

        # Copy backup file to target
        shutil.copy2(backup_path, restore_target_path)

        # Verify restored DB
        conn = sqlite3.connect(restore_target_path)
        try:
            cur = conn.cursor()
            cur.execute("PRAGMA integrity_check;")
            res = cur.fetchone()
            is_healthy = (res[0] == "ok")
            return is_healthy
        finally:
            conn.close()
