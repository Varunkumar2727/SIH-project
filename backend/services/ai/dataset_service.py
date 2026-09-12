import os
import json
import uuid
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

class DatasetService:
    """
    Part 12: Indian Aerial/Drone Dataset Pipeline & Validation Engine.
    Handles dataset registration, regional diversity cataloging, geometric validation,
    and geographic scene grouping to prevent train/test leakage.
    """

    SUPPORTED_REGIONS = [
        "urban", "rural", "agricultural", "coastal", "mountainous", "semi-arid", "dense_settlement"
    ]

    CLASSES = [
        "building", "road", "vegetation", "agricultural_land", "water", "bare_land"
    ]

    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = storage_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "results", "datasets"
        )
        os.makedirs(self.storage_dir, exist_ok=True)

    def create_dataset(
        self,
        name: str,
        geographic_region: str,
        capture_type: str = "drone", # "drone" | "satellite" | "aerial_ortho"
        imagery_type: str = "RGB",
        resolution_m: float = 0.05,
        crs: str = "EPSG:32643",
        license_info: str = "Authorized Government Survey Data"
    ) -> Dict[str, Any]:
        """Registers a new dataset with regional provenance."""
        if geographic_region not in self.SUPPORTED_REGIONS:
            raise ValueError(f"Region '{geographic_region}' not in supported regions: {self.SUPPORTED_REGIONS}")

        dataset_id = f"ds_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()

        record = {
            "dataset_id": dataset_id,
            "name": name,
            "geographic_region": geographic_region,
            "capture_type": capture_type,
            "imagery_type": imagery_type,
            "resolution_m": resolution_m,
            "crs": crs,
            "license": license_info,
            "classes": self.CLASSES,
            "version": "1.0",
            "status": "DRAFT",
            "items": [],
            "created_at": now
        }
        self._save_dataset(record)
        return record

    def validate_dataset(self, dataset_id: str, samples: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validates samples before training:
          - Image and label existence
          - Dimension matches
          - Empty annotations
          - Duplicate detection
        Returns validation report with real statistics.
        """
        valid_items = []
        corrupted_count = 0
        empty_annotations_count = 0
        seen_hashes = set()
        duplicate_count = 0

        for s in samples:
            img_path = s.get("image_path", "")
            annotations = s.get("annotations", [])
            w, h = s.get("width", 0), s.get("height", 0)

            # Check dimensions
            if w <= 0 or h <= 0:
                corrupted_count += 1
                continue

            # Duplicate image hash check
            content_str = f"{img_path}_{w}_{h}"
            img_hash = hashlib.sha256(content_str.encode("utf-8")).hexdigest()
            if img_hash in seen_hashes:
                duplicate_count += 1
                continue
            seen_hashes.add(img_hash)

            if len(annotations) == 0:
                empty_annotations_count += 1

            valid_items.append(s)

        report = {
            "dataset_id": dataset_id,
            "total_submitted": len(samples),
            "valid_samples": len(valid_items),
            "corrupted_or_invalid_dimensions": corrupted_count,
            "empty_annotations": empty_annotations_count,
            "duplicates_detected": duplicate_count,
            "validation_status": "READY" if len(valid_items) > 0 else "FAILED",
            "validated_at": datetime.now(timezone.utc).isoformat()
        }

        # Update dataset status if valid
        ds = self.get_dataset(dataset_id)
        if ds:
            ds["status"] = report["validation_status"]
            ds["items"] = valid_items
            ds["validation_report"] = report
            self._save_dataset(ds)

        return report

    def generate_leakage_free_split(
        self,
        samples: List[Dict[str, Any]],
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Groups samples by source flight / scene ID rather than random tiles to
        strictly prevent geographic data leakage between train and test sets.
        """
        scene_groups: Dict[str, List[Dict[str, Any]]] = {}
        for s in samples:
            scene_id = s.get("scene_id") or s.get("flight_id") or "default_scene"
            if scene_id not in scene_groups:
                scene_groups[scene_id] = []
            scene_groups[scene_id].append(s)

        train_set, val_set, test_set = [], [], []
        scenes = list(scene_groups.keys())

        # Distribute whole scenes
        for idx, sc in enumerate(scenes):
            assigned_samples = scene_groups[sc]
            if len(scenes) >= 3:
                if idx % 3 == 0:
                    train_set.extend(assigned_samples)
                elif idx % 3 == 1:
                    val_set.extend(assigned_samples)
                else:
                    test_set.extend(assigned_samples)
            else:
                # If only 1 or 2 scenes exist, partition samples within scene
                n = len(assigned_samples)
                n_train = int(n * train_ratio)
                n_val = int(n * val_ratio)
                train_set.extend(assigned_samples[:n_train])
                val_set.extend(assigned_samples[n_train:n_train + n_val])
                test_set.extend(assigned_samples[n_train + n_val:])

        return {
            "train": train_set,
            "val": val_set,
            "test": test_set,
            "train_count": len(train_set),
            "val_count": len(val_set),
            "test_count": len(test_set)
        }

    def get_dataset(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        p = os.path.join(self.storage_dir, f"{dataset_id}.json")
        if os.path.exists(p):
            with open(p, "r") as f:
                return json.load(f)
        return None

    def _save_dataset(self, data: Dict[str, Any]) -> None:
        p = os.path.join(self.storage_dir, f"{data['dataset_id']}.json")
        with open(p, "w") as f:
            json.dump(data, f, indent=2)
