import time
import uuid
import threading
from typing import Dict, Any, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

class JobManager:
    """
    Part 11: Production Background Job Queue & Worker Manager.
    Features separate CPU and GPU task queues. GPU queue serializes heavy AI
    inference/fine-tuning tasks to protect the 4GB VRAM on RTX 3050 from OOM crashes.
    """
    _instance = None

    def __init__(self, max_cpu_workers: int = 4, max_gpu_workers: int = 1):
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.cpu_executor = ThreadPoolExecutor(max_workers=max_cpu_workers, thread_name_prefix="cpu_worker")
        self.gpu_executor = ThreadPoolExecutor(max_workers=max_gpu_workers, thread_name_prefix="gpu_worker")
        self.lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def submit_job(
        self,
        task_name: str,
        func: Callable[..., Any],
        args: Optional[tuple] = None,
        kwargs: Optional[dict] = None,
        queue_type: str = "cpu", # "cpu" | "gpu"
        project_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> str:
        """
        Enqueues a background job.
        """
        job_id = f"job_{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc).isoformat()
        job_record = {
            "job_id": job_id,
            "task_name": task_name,
            "queue_type": queue_type,
            "status": "QUEUED",
            "progress_pct": 0,
            "project_id": project_id,
            "user_id": user_id,
            "submitted_at": now,
            "started_at": None,
            "completed_at": None,
            "result": None,
            "error": None
        }

        with self.lock:
            self.jobs[job_id] = job_record

        executor = self.gpu_executor if queue_type == "gpu" else self.cpu_executor
        executor.submit(self._run_job_wrapper, job_id, func, args or (), kwargs or {})
        return job_id

    def _run_job_wrapper(self, job_id: str, func: Callable, args: tuple, kwargs: dict):
        with self.lock:
            if job_id not in self.jobs:
                return
            self.jobs[job_id]["status"] = "RUNNING"
            self.jobs[job_id]["started_at"] = datetime.now(timezone.utc).isoformat()

        try:
            result = func(*args, **kwargs)
            with self.lock:
                self.jobs[job_id]["status"] = "COMPLETED"
                self.jobs[job_id]["progress_pct"] = 100
                self.jobs[job_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
                self.jobs[job_id]["result"] = result
        except Exception as e:
            with self.lock:
                self.jobs[job_id]["status"] = "FAILED"
                self.jobs[job_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
                self.jobs[job_id]["error"] = str(e)

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            return self.jobs.get(job_id)

    def list_jobs(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.lock:
            jobs_list = list(self.jobs.values())
        if project_id:
            jobs_list = [j for j in jobs_list if j.get("project_id") == project_id]
        return sorted(jobs_list, key=lambda x: x["submitted_at"], reverse=True)
