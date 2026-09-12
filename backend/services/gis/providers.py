import os
import zipfile
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from .ssrf_guard import SSRFGuard

class IntegrationProvider:
    """Base class for GIS external integration providers."""
    def __init__(self, name: str, source_type: str):
        self.name = name
        self.source_type = source_type

class WMSProvider(IntegrationProvider):
    """Part 13: Web Map Service (WMS) Connector."""
    def __init__(self, endpoint: str, layer_name: str, crs: str = "EPSG:3857"):
        super().__init__(name="WMS", source_type="WMS")
        self.endpoint = SSRFGuard.validate_url(endpoint)
        self.layer_name = layer_name
        self.crs = crs

    def get_capabilities_meta(self) -> Dict[str, Any]:
        return {
            "type": "WMS",
            "endpoint": self.endpoint,
            "layer": self.layer_name,
            "crs": self.crs,
            "provenance": {
                "registered_at": datetime.now(timezone.utc).isoformat(),
                "status": "ACTIVE"
            }
        }

class WFSProvider(IntegrationProvider):
    """Part 13: Web Feature Service (WFS) Vector Connector."""
    def __init__(self, endpoint: str, type_name: str, crs: str = "EPSG:4326"):
        super().__init__(name="WFS", source_type="WFS")
        self.endpoint = SSRFGuard.validate_url(endpoint)
        self.type_name = type_name
        self.crs = crs

    def get_capabilities_meta(self) -> Dict[str, Any]:
        return {
            "type": "WFS",
            "endpoint": self.endpoint,
            "type_name": self.type_name,
            "crs": self.crs,
            "supports_paging": True,
            "max_features_limit": 5000
        }

class ShapefileValidator:
    """Part 13: Validates Shapefile ZIP archives requiring .shp, .shx, and .dbf."""
    REQUIRED_EXTENSIONS = {".shp", ".shx", ".dbf"}

    @classmethod
    def validate_archive(cls, zip_path: str) -> Dict[str, Any]:
        if not os.path.exists(zip_path):
            raise FileNotFoundError(f"Shapefile archive not found at {zip_path}")

        found_exts = set()
        with zipfile.ZipFile(zip_path, "r") as zf:
            for name in zf.namelist():
                ext = os.path.splitext(name)[1].lower()
                found_exts.add(ext)

        missing = cls.REQUIRED_EXTENSIONS - found_exts
        if missing:
            raise ValueError(f"Incomplete Shapefile archive. Missing mandatory components: {list(missing)}")

        has_prj = ".prj" in found_exts
        return {
            "valid": True,
            "found_extensions": list(found_exts),
            "has_projection_prj": has_prj,
            "archive_size_bytes": os.path.getsize(zip_path)
        }
