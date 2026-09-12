# GeoCadastral AI — System Administrator & Operations Guide

## 1. System Requirements & Setup
* **Operating System**: Windows 11 / Linux (Ubuntu 22.04 LTS+)
* **Python**: 3.12+ (tested and operational on Python 3.14.6)
* **GPU**: NVIDIA GPU with CUDA support (e.g., RTX 3050 Laptop GPU, 4GB VRAM)
* **Node.js**: v18+ for React/Vite frontend

---

## 2. Service Startup

### Backend (FastAPI)
Activate the Python virtual environment and run Uvicorn:
```powershell
.\venv\Scripts\activate
python backend\main.py
```
* API Server: `http://localhost:8000`
* Swagger Interactive Docs: `http://localhost:8000/docs`
* ReDoc API Docs: `http://localhost:8000/redoc`

### Frontend (React / Vite)
```powershell
cd frontend
npm run dev
```
* Web Dashboard: `http://localhost:5173`

---

## 3. Background Worker & Queue Configuration
The platform uses `JobManager` with two thread pools:
* **CPU Queue**: Concurrency limit default `4`. Handles raster metadata extraction, polygonization, CSV export, and PDF generation.
* **GPU Queue**: Concurrency limit `1`. Serializes heavy neural network inference and fine-tuning passes to prevent CUDA Out-of-Memory (OOM) on 4GB VRAM cards.

---

## 4. Database Operations & Backups
The database is located at `backend/results/platform.db` (SQLite in WAL mode).

### Live Database Backup
To create a safe online snapshot without pausing services:
```python
from services.platform.backup import DisasterRecoveryService
dr = DisasterRecoveryService("backend/results/platform.db")
meta = dr.create_backup()
print("Backup created at:", meta["backup_path"])
```

### Disaster Recovery Restore
To verify or restore a backup into production:
```python
dr.restore_and_verify(backup_path="backend/results/backups/backup_xxxx.db", restore_target_path="backend/results/platform.db")
```

---

## 5. Security & SSRF Configuration
The `SSRFGuard` service restricts outbound GIS queries. To add trusted internal GIS servers to the allowlist, update `SSRFGuard.BLOCKED_HOSTS` in `backend/services/gis/ssrf_guard.py`.
