# GeoCadastral AI — System Architecture (Parts 1–15)

## 1. Executive Summary
**GeoCadastral AI** is an AI-assisted geospatial land intelligence platform for cadastral mapping, land-change monitoring, parcel intelligence, and survey decision support. It is built to assist revenue departments, survey authorities, and enterprise GIS teams without making unauthorized legal ownership determinations.

---

## 2. End-to-End Conceptual Architecture

```
                     USERS (Survey Officers / GIS Analysts / Admins)
                                     │
                                     ▼
                        MODERN REACT / VITE CLIENT
                                     │
                                     ▼
                             FASTAPI GATEWAY
                     (REST /api & Versioned /api/v1)
                                     │
                                     ▼
                ┌────────────────────┼────────────────────┐
                ▼                    ▼                    ▼
         AUTHENTICATION       ORGANIZATION /       ENTITLEMENTS &
       (Session / API Key)      MULTI-TENANT         USAGE TRACKER
                │                    │                    │
                └────────────────────┼────────────────────┘
                                     │
                                     ▼
                              PROJECT CONTEXT
                                     │
             ┌───────────────────────┼───────────────────────┐
             ▼                       ▼                       ▼
      AERIAL IMAGERY            GROUND CONTROL         EXTERNAL GIS
   (GeoTIFF / Drone Ortho)       POINTS (GCP)        (WMS/WFS/Shapefile)
             │                       │                       │
             └───────────────────────┼───────────────────────┘
                                     │
                                     ▼
                         BACKGROUND JOB QUEUE
                  (CPU Workers vs. GPU Workers Serialization)
                                     │
                                     ▼
                       AI & SPATIAL ENGINE CORE
           ┌─────────────────────────┼─────────────────────────┐
           ▼                         ▼                         ▼
     AI SEGMENTATION           ACCESS NETWORK            PARCEL ENGINE
  (Tiled 512x512, ONNX)       (NetworkX Graph)         (Deterministic IDs)
           │                         │                         │
           └─────────────────────────┼─────────────────────────┘
                                     │
                                     ▼
                     TEMPORAL CHANGE & CADASTRAL OVERLAY
             (Baseline T1 vs Current T2 / Discrepancy Analysis)
                                     │
                                     ▼
                    ADVANCED DECISION INTELLIGENCE
          (Explainable 0–100 Readiness & Risk Scores, Hotspots)
                                     │
                                     ▼
                    HUMAN-IN-THE-LOOP VERIFICATION
          (Survey Officer Review Queue & Immutable Audit Trail)
                                     │
                                     ▼
                          FIELD DISPATCH & TASKS
                                     │
                                     ▼
                    GOVERNMENT REPORTS & DELIVERABLES
         (ReportLab PDF Dossiers, CSV, GeoPackage, Offline ZIPs)
```

---

## 3. Subsystem Breakdown

### 3.1 Geospatial & GCP Subsystems (Parts 1 & 2)
* **GeoTIFF Reader**: Extract CRS (Projected/Geographic), affine transforms, bounds, pixel dimensions via `rasterio`.
* **Coordinate Conversion**: Native coordinate calculations with `pyproj` transforms to EPSG:4326 WGS84 coordinates.
* **Ground Control Points (GCP)**: Solves 2D affine least-squares transformations, calculates residual errors, and produces root mean square error (RMSE).

### 3.2 AI Inference & Indian Dataset Pipeline (Parts 3 & 12)
* **Model Manager**: ONNX Runtime engine with automatic CUDA detection and CPU fallback.
* **Tiled Inference**: 512x512 sliding window with 15% overlap and Hann window smoothing to eliminate boundary stitching artifacts and respect 4GB VRAM limits.
* **Indian Aerial Pipeline**: Categorizes datasets by regional diversity (urban, rural, agricultural, coastal, mountainous).
* **Leakage Prevention**: Groups samples strictly by geographic flight/scene rather than random overlapping tiles.
* **Model Registry & Pinning**: Full model lifecycle (`TRAINING` &rarr; `AVAILABLE` &rarr; `DEPLOYED`) with version pinning.

### 3.3 Parcel Intelligence & Access Paths (Parts 4 & 5)
* **Access Network**: Vectorizes road centerlines into a topological `networkx.Graph`. Evaluates frontage distance and assigns physical accessibility (`DIRECT_ACCESS`, `MARGINAL_ACCESS`, `PHYSICAL_ACCESS_CONCERN`).
* **Deterministic Parcel Engine**: SHA-256 canonical coordinate hash (`AI-P-{hash}`) ensures persistent parcel identification.
* **Cadastral Comparison**: Real polygon IoU, area difference percentages, and boundary displacement against authoritative survey layers.

### 3.4 Temporal Land Changes & Decision Intelligence (Parts 6 & 9)
* **Chronological Validation**: Enforces `t1_date < t2_date`.
* **Change Classification**: Flags `NEW_CONSTRUCTION`, `MODIFIED_FOOTPRINT`, and `STRUCTURE_REMOVAL`.
* **Scoring Engine**: Computes deterministic, explainable 0–100 Development Readiness and Discrepancy Risk scores.
* **Spatial Hotspots**: Clusters anomalies using spatial binning.

### 3.5 Human-in-the-Loop Review & Reporting (Parts 7 & 8)
* **Review Queue**: Officer decision states (`CONFIRMED`, `REJECTED`, `FIELD_VERIFICATION_REQUIRED`).
* **Audit Trail**: Append-only JSONL log recording every action, officer identity, timestamp, and notes.
* **Government Dossiers**: Official ReportLab PDF generator complete with statutory disclaimers, metadata blocks, and signature fields.

### 3.6 Enterprise Platform, SaaS API & Infrastructure (Parts 10, 11, 13, 14, 15)
* **Multi-Tenant Relational Schema**: SQLite with WAL mode and foreign keys enabled.
* **6 RBAC Roles**: Organization Admin, Project Manager, GIS Analyst, Survey Officer, Field Verifier, Viewer.
* **Production Job Manager**: Dedicated CPU and GPU worker queues. GPU queue serializes heavy tasks to prevent CUDA out-of-memory errors.
* **Enterprise GIS Connectors**: WMS, WMTS, WFS, and Shapefile validators with strict SSRF protection.
* **Versioned REST API v1**: Scoped API keys, SHA-256 hashed secrets, idempotency keys, HMAC-signed webhooks, and measured usage tracking.
* **Disaster Recovery**: SQLite online backup API for safe, non-blocking snapshots.
