import os
import json
import uuid
import hmac
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

class UsageTracker:
    """
    Part 14: Measurable Usage & Event Metering.
    Tracks actual project counts, storage bytes, processed area (m²),
    AI jobs, and API calls. Never fabricates metrics.
    """

    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = storage_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "results", "usage"
        )
        os.makedirs(self.storage_dir, exist_ok=True)
        self.usage_log = os.path.join(self.storage_dir, "usage_events.jsonl")

    def record_usage(
        self,
        org_id: str,
        event_type: str, # "AREA_PROCESSED_SQM" | "STORAGE_BYTES" | "AI_INFERENCE_JOB" | "API_CALL"
        quantity: float,
        unit: str,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        event = {
            "usage_id": f"usg_{uuid.uuid4().hex[:8]}",
            "org_id": org_id,
            "project_id": project_id,
            "user_id": user_id,
            "event_type": event_type,
            "quantity": float(quantity),
            "unit": unit,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(self.usage_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
        return event

    def get_org_summary(self, org_id: str) -> Dict[str, Any]:
        """Aggregates actual usage metrics for an organization."""
        total_api_calls = 0
        total_area_sqm = 0.0
        total_ai_jobs = 0

        if os.path.exists(self.usage_log):
            with open(self.usage_log, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    ev = json.loads(line)
                    if ev.get("org_id") == org_id:
                        et = ev.get("event_type")
                        qty = ev.get("quantity", 0.0)
                        if et == "API_CALL":
                            total_api_calls += int(qty)
                        elif et == "AREA_PROCESSED_SQM":
                            total_area_sqm += qty
                        elif et == "AI_INFERENCE_JOB":
                            total_ai_jobs += int(qty)

        return {
            "org_id": org_id,
            "total_api_calls": total_api_calls,
            "total_area_processed_sqm": round(total_area_sqm, 2),
            "total_ai_jobs": total_ai_jobs
        }

class WebhookManager:
    """Part 14: Webhook Event Dispatcher with HMAC-SHA256 Signatures."""

    @classmethod
    def sign_payload(cls, secret: str, payload_bytes: bytes) -> str:
        return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()

    @classmethod
    def verify_signature(cls, secret: str, payload_bytes: bytes, header_sig: str) -> bool:
        expected = cls.sign_payload(secret, payload_bytes)
        return hmac.compare_digest(expected, header_sig)
