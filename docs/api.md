# GeoCadastral AI — Public REST API (v1) Reference

The GeoCadastral AI public API enables enterprise integration, automated raster ingestion, parcel query, change monitoring, and survey case review.

## Base URL
`/api/v1`

---

## Authentication
Every request to the v1 API requires an active API key passed in the `X-API-Key` HTTP header:

```http
X-API-Key: gc_live_xxxxxxxxxxxxxxxxxxxxxxxx
```

API keys are created via the SaaS Platform modal or organization admin endpoints. Key secrets are hashed with SHA-256 upon generation and never stored in plaintext.

---

## Standard Error Response Format
All v1 error responses return a uniform JSON format:

```json
{
  "detail": {
    "code": "PROJECT_NOT_FOUND",
    "message": "Project 'proj_123' not found.",
    "request_id": "9f1b2c3d4e5f"
  }
}
```

---

## Endpoints

### 1. Projects
#### `GET /api/v1/projects`
Lists all active projects belonging to the authenticated organization.
* **Scope required**: `projects:read`
* **Response**:
```json
{
  "status": "success",
  "count": 2,
  "data": [
    {
      "id": "p_bengaluru_01",
      "name": "Bengaluru East Survey",
      "geographic_region": "urban",
      "created_at": "2026-09-04T12:00:00Z"
    }
  ]
}
```

#### `GET /api/v1/projects/{project_id}`
Returns details of a specific project.
* **Scope required**: `projects:read`

---

### 2. AI Analysis & Inference Jobs
#### `POST /api/v1/analysis`
Submits an asynchronous AI segmentation and parcel delineation job.
* **Scope required**: `analysis:run`
* **Supported Headers**: `Idempotency-Key` (prevents duplicate job runs)
* **Request Body**:
```json
{
  "image_id": "img_a1b2c3d4",
  "project_id": "p_bengaluru_01",
  "tile_size": 512
}
```
* **Response**:
```json
{
  "status": "QUEUED",
  "job_id": "job_e5f6g7h8",
  "message": "Analysis job submitted to GPU queue.",
  "poll_url": "/api/v1/jobs/job_e5f6g7h8"
}
```

#### `GET /api/v1/jobs/{job_id}`
Returns the current execution status and progress of a background job.
* **Response**:
```json
{
  "status": "success",
  "data": {
    "job_id": "job_e5f6g7h8",
    "task_name": "v1_api_analysis",
    "status": "COMPLETED",
    "progress_pct": 100,
    "completed_at": "2026-09-04T12:05:12Z"
  }
}
```

---

### 3. Survey Officer Review Queue
#### `GET /api/v1/reviews`
Lists verification cases with optional filters.
* **Query parameters**: `project_id`, `status` (`UNREVIEWED`, `CONFIRMED`, `FIELD_VERIFICATION_REQUIRED`, `REJECTED`)
* **Scope required**: `reviews:read`

#### `POST /api/v1/reviews/{case_id}/decision`
Records an attestation decision with an immutable audit log entry.
* **Scope required**: `reviews:write`
* **Request Body**:
```json
{
  "decision": "CONFIRMED",
  "officer_name": "Survey Officer Rajesh Kumar",
  "notes": "Verified against physical boundary survey."
}
```

---

### 4. Organization Usage & Metrics
#### `GET /api/v1/usage`
Returns measured usage statistics for the authenticated tenant:
```json
{
  "status": "success",
  "data": {
    "org_id": "org_karnataka_rev",
    "total_api_calls": 1842,
    "total_area_processed_sqm": 142500.0,
    "total_ai_jobs": 28
  }
}
```
