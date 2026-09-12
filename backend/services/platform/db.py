import os
import sqlite3
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

class PlatformDatabase:
    """
    Part 10: Multi-Tenant Enterprise Persistence Layer.
    Uses SQLite with WAL mode, foreign keys, and indexes for zero-dependency local setup,
    fully structured to match production PostgreSQL schemas.
    """
    _instance = None

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "results", "platform.db"
        )
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    @classmethod
    def get_instance(cls, db_path: Optional[str] = None):
        if cls._instance is None or (db_path and cls._instance.db_path != db_path):
            cls._instance = cls(db_path)
        return cls._instance

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    def _init_db(self):
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                # 1. Organizations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS organizations (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    plan_tier TEXT DEFAULT 'PRO',
                    created_at TEXT NOT NULL
                )
            """)

            # 2. Users
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    org_id TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (org_id) REFERENCES organizations (id) ON DELETE CASCADE
                )
            """)

            # 3. Projects
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    org_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    geographic_region TEXT,
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (org_id) REFERENCES organizations (id) ON DELETE CASCADE,
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            """)

            # 4. Project Memberships
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_memberships (
                    project_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    project_role TEXT NOT NULL,
                    granted_at TEXT NOT NULL,
                    PRIMARY KEY (project_id, user_id),
                    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)

            # 5. Activity Log
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    org_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    metadata_json TEXT,
                    created_at TEXT NOT NULL
                )
            """)
        finally:
            conn.close()

    # --- Organization CRUD ---
    def create_organization(self, org_id: str, name: str, plan_tier: str = "PRO") -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        conn = self.get_connection()
        try:
            with conn:
                conn.execute(
                    "INSERT INTO organizations (id, name, plan_tier, created_at) VALUES (?, ?, ?, ?)",
                    (org_id, name, plan_tier, now)
                )
        finally:
            conn.close()
        return {"id": org_id, "name": name, "plan_tier": plan_tier, "created_at": now}

    def get_organization(self, org_id: str) -> Optional[Dict[str, Any]]:
        conn = self.get_connection()
        try:
            cur = conn.execute("SELECT * FROM organizations WHERE id = ?", (org_id,))
            row = cur.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    # --- User CRUD ---
    def create_user(self, user_id: str, org_id: str, email: str, full_name: str, role: str) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        conn = self.get_connection()
        try:
            with conn:
                conn.execute(
                    "INSERT INTO users (id, org_id, email, full_name, role, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (user_id, org_id, email, full_name, role, now)
                )
        finally:
            conn.close()
        return {"id": user_id, "org_id": org_id, "email": email, "full_name": full_name, "role": role, "created_at": now}

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        conn = self.get_connection()
        try:
            cur = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cur.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    # --- Project CRUD ---
    def create_project(self, project_id: str, org_id: str, name: str, created_by: str, description: str = "", region: str = "India") -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        conn = self.get_connection()
        try:
            with conn:
                conn.execute(
                    "INSERT INTO projects (id, org_id, name, description, geographic_region, created_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (project_id, org_id, name, description, region, created_by, now)
                )
        finally:
            conn.close()
        return {"id": project_id, "org_id": org_id, "name": name, "created_by": created_by, "created_at": now}

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        conn = self.get_connection()
        try:
            cur = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            row = cur.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def list_projects_for_org(self, org_id: str) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        try:
            cur = conn.execute("SELECT * FROM projects WHERE org_id = ? ORDER BY created_at DESC", (org_id,))
            return [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()
