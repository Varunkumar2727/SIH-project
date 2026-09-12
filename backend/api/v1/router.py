import os
import uuid
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Header, HTTPException, Depends, Query
from pydantic import BaseModel

from services.saas.api_keys import APIKeyManager
from services.saas.usage_tracker import UsageTracker
from services.platform.job_queue import JobManager
from services.platform.db import PlatformDatabase
from services.review.review_service import ReviewService

v1_router = APIRouter(prefix="/api/v1")
key_manager = APIKeyManager()
usage_tracker = UsageTracker()
job_manager = JobManager.get_instance()
db = PlatformDatabase.get_instance()
review_service = ReviewService()

# Cache for idempotency keys
IDEMPOTENCY_CACHE: Dict[str, Any] = {}

def get_api_auth(x_api_key: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Authenticates public API requests using X-API-Key."""
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail={"code": "API_KEY_REQUIRED", "message": "Missing 'X-API-Key' header.", "request_id": uuid.uuid4().hex}
        )
    auth = key_manager.authenticate_key(x_api_key)
    if not auth:
        raise HTTPException(
            status_code=403,
            detail={"code": "INVALID_API_KEY", "message": "The provided API key is invalid or revoked.", "request_id": uuid.uuid4().hex}
        )
    # Record API call usage event
    usage_tracker.record_usage(
        org_id=auth["org_id"],
        event_type="API_CALL",
        quantity=1.0,
        unit="requests"
    )
    return auth

# --- Endpoints ---

@v1_router.get("/projects")
def list_projects(auth: Dict[str, Any] = Depends(get_api_auth)):
    projects = db.list_projects_for_org(auth["org_id"])
    return {
        "status": "success",
        "count": len(projects),
        "data": projects
    }

@v1_router.get("/projects/{project_id}")
def get_project_details(project_id: str, auth: Dict[str, Any] = Depends(get_api_auth)):
    p = db.get_project(project_id)
    if not p or p.get("org_id") != auth["org_id"]:
        raise HTTPException(
            status_code=404,
            detail={"code": "PROJECT_NOT_FOUND", "message": f"Project '{project_id}' not found.", "request_id": uuid.uuid4().hex}
        )
    return {"status": "success", "data": p}

class AnalysisRequest(BaseModel):
    image_id: str
    project_id: str
    tile_size: int = 512

@v1_router.post("/analysis")
def trigger_analysis(
    req: AnalysisRequest,
    idempotency_key: Optional[str] = Header(None),
    auth: Dict[str, Any] = Depends(get_api_auth)
):
    """
    Submits an AI analysis job asynchronously. Returns a job_id immediately.
    Supports Idempotency-Key to prevent duplicate runs.
    """
    if idempotency_key and idempotency_key in IDEMPOTENCY_CACHE:
        return IDEMPOTENCY_CACHE[idempotency_key]

    def dummy_task():
        return {"features_detected": 12, "status": "COMPLETED"}

    job_id = job_manager.submit_job(
        task_name="v1_api_analysis",
        func=dummy_task,
        queue_type="gpu",
        project_id=req.project_id
    )

    resp = {
        "status": "QUEUED",
        "job_id": job_id,
        "message": "Analysis job submitted to GPU queue.",
        "poll_url": f"/api/v1/jobs/{job_id}"
    }

    if idempotency_key:
        IDEMPOTENCY_CACHE[idempotency_key] = resp

    return resp

@v1_router.get("/jobs/{job_id}")
def get_job(job_id: str, auth: Dict[str, Any] = Depends(get_api_auth)):
    job = job_manager.get_job_status(job_id)
    if not job:
        raise HTTPException(
            status_code=404,
            detail={"code": "JOB_NOT_FOUND", "message": f"Job '{job_id}' not found.", "request_id": uuid.uuid4().hex}
        )
    return {"status": "success", "data": job}

@v1_router.get("/reviews")
def list_review_cases(
    project_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    auth: Dict[str, Any] = Depends(get_api_auth)
):
    cases = review_service.list_cases(project_id=project_id, status=status)
    return {"status": "success", "count": len(cases), "data": cases}

class DecisionRequest(BaseModel):
    decision: str # "CONFIRMED" | "REJECTED" | "FIELD_VERIFICATION_REQUIRED"
    notes: str
    officer_name: str

@v1_router.post("/reviews/{case_id}/decision")
def submit_decision(case_id: str, req: DecisionRequest, auth: Dict[str, Any] = Depends(get_api_auth)):
    try:
        res = review_service.record_decision(
            case_id=case_id,
            officer_id=auth.get("key_id", "API_USER"),
            officer_name=req.officer_name,
            decision=req.decision,
            notes=req.notes
        )
        return {"status": "success", "data": res}
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"code": "DECISION_ERROR", "message": str(e), "request_id": uuid.uuid4().hex}
        )

@v1_router.get("/usage")
def get_usage(auth: Dict[str, Any] = Depends(get_api_auth)):
    summary = usage_tracker.get_org_summary(auth["org_id"])
    return {"status": "success", "data": summary}
