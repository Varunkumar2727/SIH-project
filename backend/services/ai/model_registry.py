import os
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

class ModelRegistry:
    """
    Part 12: Model Registry & Deployment Manager.
    Manages model versioning, authorized promotions, and model pinning.
    """

    VALID_STATUSES = {"TRAINING", "VALIDATING", "AVAILABLE", "DEPLOYED", "DEPRECATED"}

    def __init__(self, registry_dir: Optional[str] = None):
        self.registry_dir = registry_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "results", "model_registry"
        )
        os.makedirs(self.registry_dir, exist_ok=True)
        self.active_model_file = os.path.join(self.registry_dir, "active_deployment.json")

    def register_model(
        self,
        name: str,
        version: str,
        dataset_version: str,
        metrics: Dict[str, Any],
        weights_reference: str,
        classes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Registers a trained model in the catalog."""
        model_id = f"mod_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()

        model_record = {
            "model_id": model_id,
            "name": name,
            "version": version,
            "dataset_version": dataset_version,
            "metrics": metrics,
            "weights_reference": weights_reference,
            "classes": classes or ["building", "road", "vegetation", "water", "bare_land"],
            "status": "AVAILABLE",
            "registered_at": now
        }
        self._save_model(model_record)
        return model_record

    def deploy_model(self, model_id: str, authorized_by: str) -> Dict[str, Any]:
        """Promotes and pins a model as the active deployment."""
        model = self.get_model(model_id)
        if not model:
            raise KeyError(f"Model '{model_id}' not found in registry.")

        model["status"] = "DEPLOYED"
        model["deployed_at"] = datetime.now(timezone.utc).isoformat()
        model["deployed_by"] = authorized_by
        self._save_model(model)

        # Pin active deployment
        with open(self.active_model_file, "w") as f:
            json.dump({
                "active_model_id": model_id,
                "version": model["version"],
                "deployed_at": model["deployed_at"],
                "authorized_by": authorized_by
            }, f, indent=2)

        return model

    def get_active_model(self) -> Optional[Dict[str, Any]]:
        if os.path.exists(self.active_model_file):
            with open(self.active_model_file, "r") as f:
                active_meta = json.load(f)
                return self.get_model(active_meta.get("active_model_id"))
        return None

    def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        p = os.path.join(self.registry_dir, f"{model_id}.json")
        if os.path.exists(p):
            with open(p, "r") as f:
                return json.load(f)
        return None

    def list_models(self) -> List[Dict[str, Any]]:
        models = []
        for fn in os.listdir(self.registry_dir):
            if fn.startswith("mod_") and fn.endswith(".json"):
                with open(os.path.join(self.registry_dir, fn), "r") as f:
                    models.append(json.load(f))
        return sorted(models, key=lambda x: x.get("registered_at", ""), reverse=True)

    def _save_model(self, data: Dict[str, Any]) -> None:
        p = os.path.join(self.registry_dir, f"{data['model_id']}.json")
        with open(p, "w") as f:
            json.dump(data, f, indent=2)
