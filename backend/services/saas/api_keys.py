import os
import json
import uuid
import hashlib
import secrets
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timezone

class APIKeyManager:
    """
    Part 14: API Authentication & Scoped Key Management.
    Stores only SHA-256 hashed secrets. Validates granular scopes.
    """

    SUPPORTED_SCOPES = {
        "projects:read", "projects:write",
        "imagery:upload", "analysis:run",
        "parcels:read", "changes:read",
        "reviews:read", "reviews:write",
        "reports:read", "exports:create"
    }

    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = storage_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "results", "api_keys"
        )
        os.makedirs(self.storage_dir, exist_ok=True)

    def generate_key(
        self,
        org_id: str,
        name: str,
        scopes: List[str]
    ) -> Dict[str, Any]:
        """
        Generates a new API key. Returns raw secret ONLY ONCE in this response.
        The storage only contains the SHA-256 hash.
        """
        raw_secret = f"gc_live_{secrets.token_hex(20)}"
        hashed_secret = hashlib.sha256(raw_secret.encode("utf-8")).hexdigest()
        key_id = f"key_{uuid.uuid4().hex[:8]}"
        prefix = raw_secret[:12] + "..."

        # Validate scopes
        clean_scopes = [s for s in scopes if s in self.SUPPORTED_SCOPES]

        record = {
            "key_id": key_id,
            "org_id": org_id,
            "name": name,
            "prefix": prefix,
            "hashed_secret": hashed_secret,
            "scopes": clean_scopes,
            "revoked": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_used_at": None
        }
        self._save_key(record)

        return {
            "key_id": key_id,
            "name": name,
            "prefix": prefix,
            "secret_key": raw_secret, # Only returned on creation
            "scopes": clean_scopes,
            "notice": "Store this key safely. It will not be shown again."
        }

    def authenticate_key(self, raw_secret: str, required_scope: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Authenticates an API request using the secret key."""
        hashed = hashlib.sha256(raw_secret.encode("utf-8")).hexdigest()
        for fn in os.listdir(self.storage_dir):
            if fn.startswith("key_") and fn.endswith(".json"):
                with open(os.path.join(self.storage_dir, fn), "r") as f:
                    rec = json.load(f)
                    if rec.get("hashed_secret") == hashed and not rec.get("revoked", False):
                        if required_scope and required_scope not in rec.get("scopes", []):
                            raise PermissionError(f"API key missing required scope: {required_scope}")
                        # Update last used
                        rec["last_used_at"] = datetime.now(timezone.utc).isoformat()
                        self._save_key(rec)
                        return rec
        return None

    def revoke_key(self, key_id: str) -> bool:
        p = os.path.join(self.storage_dir, f"{key_id}.json")
        if os.path.exists(p):
            with open(p, "r") as f:
                rec = json.load(f)
            rec["revoked"] = True
            rec["revoked_at"] = datetime.now(timezone.utc).isoformat()
            self._save_key(rec)
            return True
        return False

    def _save_key(self, data: Dict[str, Any]) -> None:
        p = os.path.join(self.storage_dir, f"{data['key_id']}.json")
        with open(p, "w") as f:
            json.dump(data, f, indent=2)
