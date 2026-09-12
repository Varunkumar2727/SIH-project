import os
import json
import time
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

class ReviewService:
    """
    Part 7: Survey Officer Verification & Review Workflow.
    Maintains the human-in-the-loop review queue, enforces valid state transitions,
    records an append-only audit trail, and generates field verification tasks.
    """

    VALID_STATES = {
        "UNREVIEWED",
        "IN_REVIEW",
        "CONFIRMED",
        "REJECTED",
        "FIELD_VERIFICATION_REQUIRED"
    }

    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = storage_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "results", "reviews"
        )
        os.makedirs(self.storage_dir, exist_ok=True)
        self.audit_log_path = os.path.join(self.storage_dir, "audit_trail.jsonl")

    def create_case(
        self,
        project_id: str,
        entity_id: str,
        entity_type: str, # "change" | "discrepancy" | "parcel"
        evidence_summary: Dict[str, Any],
        priority: str = "MEDIUM"
    ) -> Dict[str, Any]:
        """
        Creates a review case for a detected change or cadastral discrepancy.
        """
        case_id = f"rev_{uuid.uuid4().hex[:8]}"
        case_data = {
            "case_id": case_id,
            "project_id": project_id,
            "entity_id": entity_id,
            "entity_type": entity_type,
            "status": "UNREVIEWED",
            "priority": priority,
            "evidence": evidence_summary,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "assigned_officer": None,
            "decision": None,
            "decision_notes": None,
            "field_task_id": None
        }

        self._save_case(case_data)
        self._append_audit(
            case_id=case_id,
            officer_id="SYSTEM",
            officer_name="AI Detection Subsystem",
            action="CREATE_CASE",
            previous_status=None,
            new_status="UNREVIEWED",
            notes=f"Auto-generated review case for {entity_type} {entity_id}"
        )
        return case_data

    def record_decision(
        self,
        case_id: str,
        officer_id: str,
        officer_name: str,
        decision: str,
        notes: str,
        field_task_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Records an authoritative survey officer decision with append-only audit logging.
        """
        decision_upper = decision.upper()
        if decision_upper not in self.VALID_STATES:
            raise ValueError(f"Invalid decision state '{decision}'. Must be one of {self.VALID_STATES}")

        case_data = self.get_case(case_id)
        if not case_data:
            raise KeyError(f"Case '{case_id}' does not exist.")

        prev_status = case_data["status"]
        case_data["status"] = decision_upper
        case_data["decision"] = decision_upper
        case_data["decision_notes"] = notes
        case_data["assigned_officer"] = officer_id
        case_data["decided_at"] = datetime.now(timezone.utc).isoformat()

        if decision_upper == "FIELD_VERIFICATION_REQUIRED" and field_task_details:
            field_task_id = f"ft_{uuid.uuid4().hex[:8]}"
            case_data["field_task_id"] = field_task_id
            task_obj = {
                "field_task_id": field_task_id,
                "case_id": case_id,
                "target_coordinates": field_task_details.get("target_coordinates"),
                "instructions": field_task_details.get("instructions", "Verify boundaries and ground reality on-site."),
                "priority": case_data["priority"],
                "status": "ASSIGNED",
                "assigned_verifier": field_task_details.get("assigned_verifier", officer_id),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            self._save_field_task(task_obj)

        self._save_case(case_data)
        self._append_audit(
            case_id=case_id,
            officer_id=officer_id,
            officer_name=officer_name,
            action=f"DECISION_{decision_upper}",
            previous_status=prev_status,
            new_status=decision_upper,
            notes=notes
        )
        return case_data

    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        path = os.path.join(self.storage_dir, f"{case_id}.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return None

    def list_cases(self, project_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        cases = []
        for fn in os.listdir(self.storage_dir):
            if fn.startswith("rev_") and fn.endswith(".json"):
                with open(os.path.join(self.storage_dir, fn), "r") as f:
                    c = json.load(f)
                    if project_id and c.get("project_id") != project_id:
                        continue
                    if status and c.get("status") != status:
                        continue
                    cases.append(c)
        return sorted(cases, key=lambda x: x.get("created_at", ""), reverse=True)

    def get_audit_trail(self, case_id: Optional[str] = None) -> List[Dict[str, Any]]:
        trail = []
        if not os.path.exists(self.audit_log_path):
            return trail
        with open(self.audit_log_path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    entry = json.loads(line)
                    if case_id is None or entry.get("case_id") == case_id:
                        trail.append(entry)
        return trail

    def _save_case(self, case_data: Dict[str, Any]) -> None:
        path = os.path.join(self.storage_dir, f"{case_data['case_id']}.json")
        with open(path, "w") as f:
            json.dump(case_data, f, indent=2)

    def _save_field_task(self, task_data: Dict[str, Any]) -> None:
        path = os.path.join(self.storage_dir, f"{task_data['field_task_id']}.json")
        with open(path, "w") as f:
            json.dump(task_data, f, indent=2)

    def _append_audit(
        self,
        case_id: str,
        officer_id: str,
        officer_name: str,
        action: str,
        previous_status: Optional[str],
        new_status: str,
        notes: str
    ) -> None:
        entry = {
            "audit_id": f"aud_{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "case_id": case_id,
            "officer_id": officer_id,
            "officer_name": officer_name,
            "action": action,
            "previous_status": previous_status,
            "new_status": new_status,
            "notes": notes
        }
        with open(self.audit_log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
