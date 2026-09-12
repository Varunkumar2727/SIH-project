import os
import hashlib
from typing import Dict, Any, Optional

class StorageSecurityException(Exception):
    pass

class LocalStorageProvider:
    """
    Part 11 / Part 15: Secure Storage Provider.
    Implements path traversal defense, file validation, and SHA-256 integrity checksums.
    """

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = os.path.abspath(base_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "uploads"
        ))
        os.makedirs(self.base_dir, exist_ok=True)

    def _sanitize_path(self, relative_path: str) -> str:
        """
        Guards against directory traversal attacks (e.g., ../../etc/passwd).
        Ensures the resolved path strictly lies within self.base_dir.
        """
        # Strip leading slashes
        clean_rel = os.path.normpath(relative_path).lstrip("/\\")
        full_path = os.path.abspath(os.path.join(self.base_dir, clean_rel))

        if not full_path.startswith(self.base_dir):
            raise StorageSecurityException(f"Path traversal detected: {relative_path}")
        return full_path

    def save_file(self, relative_path: str, data: bytes) -> Dict[str, Any]:
        target_path = self._sanitize_path(relative_path)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        sha256 = hashlib.sha256(data).hexdigest()
        with open(target_path, "wb") as f:
            f.write(data)

        return {
            "relative_path": relative_path,
            "absolute_path": target_path,
            "size_bytes": len(data),
            "sha256": sha256
        }

    def read_file(self, relative_path: str) -> bytes:
        target_path = self._sanitize_path(relative_path)
        if not os.path.exists(target_path):
            raise FileNotFoundError(f"File not found: {relative_path}")
        with open(target_path, "rb") as f:
            return f.read()

    def file_exists(self, relative_path: str) -> bool:
        try:
            target_path = self._sanitize_path(relative_path)
            return os.path.exists(target_path)
        except StorageSecurityException:
            return False
