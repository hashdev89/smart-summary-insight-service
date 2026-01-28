"""
Batch job store: progress tracking and optional persistence.

Enterprise rules:
- Results are persisted when batch_persistence_backend=file or sqlite (not just in-memory).
- Cost tracking: total_tokens_used (and optional estimated_cost) per batch.
- Partial results: clients can retrieve results before batch completes.
- SQLite backend: results stored in tables (batch_jobs, batch_results) for querying.
"""
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import threading

from app.config import settings
from app.models.schemas import (
    BatchJobStatus,
    BatchRecordResult,
    AnalyzeResponse,
)


def _serialize_result(r: BatchRecordResult) -> Dict[str, Any]:
    return {
        "index": r.index,
        "success": r.success,
        "response": r.response.model_dump() if r.response else None,
        "error": r.error,
    }


def _deserialize_result(d: Dict[str, Any]) -> BatchRecordResult:
    resp = d.get("response")
    return BatchRecordResult(
        index=d["index"],
        success=d["success"],
        response=AnalyzeResponse(**resp) if resp else None,
        error=d.get("error"),
    )


def _serialize_datetime(dt: datetime) -> str:
    return dt.isoformat() if dt else None


def _deserialize_datetime(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


class BatchJobStore:
    """
    Store batch job state with optional file or SQLite persistence.
    - memory: in-memory only (default, dev).
    - file: persist each job to a JSON file; survives restarts.
    - sqlite: persist to SQLite tables (batch_jobs, batch_results) for querying.
    Tracks total_tokens_used per batch for cost tracking.
    """

    def __init__(self):
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._backend = getattr(settings, "batch_persistence_backend", "memory") or "memory"
        self._storage_path = Path(getattr(settings, "batch_job_storage_path", "data/batch_jobs"))
        self._sqlite_path = getattr(settings, "batch_sqlite_path", "data/batch.db")

    def _get_sqlite_conn(self) -> sqlite3.Connection:
        Path(self._sqlite_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self._sqlite_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_sqlite(self, conn: sqlite3.Connection) -> None:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS batch_jobs (
                job_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                total_records INTEGER NOT NULL,
                completed_count INTEGER NOT NULL DEFAULT 0,
                failed_count INTEGER NOT NULL DEFAULT 0,
                total_tokens_used INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS batch_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                record_index INTEGER NOT NULL,
                success INTEGER NOT NULL,
                response_json TEXT,
                error TEXT,
                FOREIGN KEY (job_id) REFERENCES batch_jobs(job_id)
            );
            CREATE INDEX IF NOT EXISTS idx_batch_results_job_id ON batch_results(job_id);
        """)
        conn.commit()

    def _persist_sqlite(self, job_id: str) -> None:
        """Persist job to SQLite tables (batch_jobs + batch_results)."""
        job = self._jobs.get(job_id)
        if not job:
            return
        conn = self._get_sqlite_conn()
        try:
            self._init_sqlite(conn)
            status_val = job["status"].value if hasattr(job["status"], "value") else str(job["status"])
            created = _serialize_datetime(job["created_at"])
            updated = _serialize_datetime(job["updated_at"])
            conn.execute(
                """INSERT OR REPLACE INTO batch_jobs
                   (job_id, status, total_records, completed_count, failed_count, total_tokens_used, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    job_id,
                    status_val,
                    job["total_records"],
                    job["completed_count"],
                    job["failed_count"],
                    job.get("total_tokens_used", 0),
                    created,
                    updated,
                ),
            )
            conn.execute("DELETE FROM batch_results WHERE job_id = ?", (job_id,))
            for r in job["results"]:
                resp_json = json.dumps(r.response.model_dump()) if r.response else None
                conn.execute(
                    """INSERT INTO batch_results (job_id, record_index, success, response_json, error)
                       VALUES (?, ?, ?, ?, ?)""",
                    (job_id, r.index, 1 if r.success else 0, resp_json, r.error),
                )
            conn.commit()
        finally:
            conn.close()

    def _persist(self, job_id: str) -> None:
        """Persist job to file or SQLite according to backend. No-op for memory."""
        if self._backend == "sqlite":
            self._persist_sqlite(job_id)
            return
        if self._backend != "file":
            return
        job = self._jobs.get(job_id)
        if not job:
            return
        self._storage_path.mkdir(parents=True, exist_ok=True)
        path = self._storage_path / f"{job_id}.json"
        payload = {
            "job_id": job_id,
            "status": job["status"].value if hasattr(job["status"], "value") else str(job["status"]),
            "total_records": job["total_records"],
            "completed_count": job["completed_count"],
            "failed_count": job["failed_count"],
            "total_tokens_used": job.get("total_tokens_used", 0),
            "results": [_serialize_result(r) for r in job["results"]],
            "created_at": _serialize_datetime(job["created_at"]),
            "updated_at": _serialize_datetime(job["updated_at"]),
        }
        with open(path, "w") as f:
            json.dump(payload, f, indent=2)

    def _load_from_sqlite(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Load job from SQLite tables. Used when job not in memory (e.g. after restart)."""
        if self._backend != "sqlite":
            return None
        conn = self._get_sqlite_conn()
        try:
            self._init_sqlite(conn)
            row = conn.execute(
                "SELECT job_id, status, total_records, completed_count, failed_count, total_tokens_used, created_at, updated_at FROM batch_jobs WHERE job_id = ?",
                (job_id,),
            ).fetchone()
            if not row:
                return None
            status_val = row["status"]
            try:
                status = BatchJobStatus(status_val)
            except ValueError:
                status = BatchJobStatus.COMPLETED
            results = []
            for r in conn.execute(
                "SELECT record_index, success, response_json, error FROM batch_results WHERE job_id = ? ORDER BY record_index",
                (job_id,),
            ):
                success = bool(r["success"])
                resp = None
                if success and r["response_json"]:
                    try:
                        resp = AnalyzeResponse(**json.loads(r["response_json"]))
                    except Exception:
                        pass
                results.append(
                    BatchRecordResult(
                        index=r["record_index"],
                        success=success,
                        response=resp,
                        error=r["error"],
                    )
            )
            return {
                "job_id": job_id,
                "status": status,
                "total_records": row["total_records"],
                "completed_count": row["completed_count"],
                "failed_count": row["failed_count"],
                "total_tokens_used": row["total_tokens_used"] or 0,
                "results": results,
                "created_at": _deserialize_datetime(row["created_at"]),
                "updated_at": _deserialize_datetime(row["updated_at"]),
            }
        finally:
            conn.close()

    def _load_from_file(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Load job from file if it exists. Used when job not in memory (e.g. after restart)."""
        if self._backend != "file":
            return None
        path = self._storage_path / f"{job_id}.json"
        if not path.exists():
            return None
        try:
            with open(path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return None
        results = []
        for r in data.get("results", []):
            try:
                results.append(_deserialize_result(r))
            except Exception:
                results.append(BatchRecordResult(index=r.get("index", 0), success=False, error=r.get("error", "Parse error")))
        status_val = data.get("status", "completed")
        try:
            status = BatchJobStatus(status_val)
        except ValueError:
            status = BatchJobStatus.COMPLETED
        return {
            "job_id": job_id,
            "status": status,
            "total_records": data["total_records"],
            "completed_count": data["completed_count"],
            "failed_count": data["failed_count"],
            "total_tokens_used": data.get("total_tokens_used", 0),
            "results": results,
            "created_at": _deserialize_datetime(data.get("created_at")),
            "updated_at": _deserialize_datetime(data.get("updated_at")),
        }

    def create_job(self, total_records: int) -> str:
        """Create a new batch job and return its job_id."""
        job_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        with self._lock:
            self._jobs[job_id] = {
                "job_id": job_id,
                "status": BatchJobStatus.ACCEPTED,
                "total_records": total_records,
                "completed_count": 0,
                "failed_count": 0,
                "total_tokens_used": 0,
                "results": [],
                "created_at": now,
                "updated_at": now,
            }
        self._persist(job_id)
        return job_id

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job state by job_id. For file/sqlite backend, loads from storage if not in memory."""
        with self._lock:
            if job_id in self._jobs:
                return self._jobs[job_id]
        loaded = self._load_from_sqlite(job_id) if self._backend == "sqlite" else self._load_from_file(job_id)
        if loaded:
            with self._lock:
                self._jobs[job_id] = loaded
            return loaded
        return None

    def set_processing(self, job_id: str) -> bool:
        """Mark job as processing. Returns False if job not found."""
        with self._lock:
            if job_id not in self._jobs:
                return False
            self._jobs[job_id]["status"] = BatchJobStatus.PROCESSING
            self._jobs[job_id]["updated_at"] = datetime.now(timezone.utc)
        self._persist(job_id)
        return True

    def append_result(
        self,
        job_id: str,
        index: int,
        success: bool,
        response: Optional[Any] = None,
        error: Optional[str] = None,
        tokens_used: Optional[int] = None,
    ) -> bool:
        """Append a single record result and update counts. Optional tokens_used for cost tracking."""
        with self._lock:
            if job_id not in self._jobs:
                return False
            job = self._jobs[job_id]
            job["results"].append(
                BatchRecordResult(
                    index=index,
                    success=success,
                    response=response,
                    error=error,
                )
            )
            if success:
                job["completed_count"] += 1
                if tokens_used is not None:
                    job["total_tokens_used"] = job.get("total_tokens_used", 0) + tokens_used
            else:
                job["failed_count"] += 1
            job["updated_at"] = datetime.now(timezone.utc)
        self._persist(job_id)
        return True

    def set_job_completed(self, job_id: str) -> bool:
        """Mark job as completed. Returns False if job not found."""
        with self._lock:
            if job_id not in self._jobs:
                return False
            self._jobs[job_id]["status"] = BatchJobStatus.COMPLETED
            self._jobs[job_id]["updated_at"] = datetime.now(timezone.utc)
        self._persist(job_id)
        return True

    def set_job_failed(self, job_id: str, message: Optional[str] = None) -> bool:
        """Mark job as failed (e.g. fatal error). Returns False if job not found."""
        with self._lock:
            if job_id not in self._jobs:
                return False
            self._jobs[job_id]["status"] = BatchJobStatus.FAILED
            self._jobs[job_id]["updated_at"] = datetime.now(timezone.utc)
            if message:
                self._jobs[job_id]["failure_message"] = message
        self._persist(job_id)
        return True

    def get_status_response(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Build BatchStatusResponse-compatible dict (includes partial results and cost tracking)."""
        job = self.get_job(job_id)
        if not job:
            return None
        total = job["total_records"]
        completed = job["completed_count"]
        failed = job["failed_count"]
        done = completed + failed
        progress = (done / total * 100.0) if total else 0.0
        total_tokens = job.get("total_tokens_used", 0)
        # Optional estimated cost if config has per-token rates (simplified: treat all as output for estimate)
        estimated_cost = None
        c_in = getattr(settings, "batch_cost_per_1k_input_tokens", None)
        c_out = getattr(settings, "batch_cost_per_1k_output_tokens", None)
        if (c_in is not None or c_out is not None) and total_tokens:
            # Rough: assume half input / half output for estimate
            cost = 0
            if c_in is not None:
                cost += (total_tokens / 2) / 1000 * c_in
            if c_out is not None:
                cost += (total_tokens / 2) / 1000 * c_out
            estimated_cost = round(cost, 6)
        return {
            "job_id": job_id,
            "status": job["status"],
            "total_records": total,
            "completed_count": completed,
            "failed_count": failed,
            "progress_percent": round(progress, 2),
            "total_tokens_used": total_tokens,
            "estimated_cost": estimated_cost,
            "results": job["results"] if job["results"] else None,
            "created_at": job["created_at"],
            "updated_at": job["updated_at"],
        }

    def list_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List persisted batch jobs for table display (most recent first).
        Returns list of dicts with job_id, status, total_records, completed_count, failed_count,
        total_tokens_used, created_at, updated_at.
        """
        if self._backend == "sqlite":
            conn = self._get_sqlite_conn()
            try:
                self._init_sqlite(conn)
                rows = conn.execute(
                    """SELECT job_id, status, total_records, completed_count, failed_count,
                              total_tokens_used, created_at, updated_at
                       FROM batch_jobs ORDER BY created_at DESC LIMIT ?""",
                    (limit,),
                ).fetchall()
                return [
                    {
                        "job_id": r["job_id"],
                        "status": r["status"],
                        "total_records": r["total_records"],
                        "completed_count": r["completed_count"],
                        "failed_count": r["failed_count"],
                        "total_tokens_used": r["total_tokens_used"] or 0,
                        "created_at": r["created_at"],
                        "updated_at": r["updated_at"],
                    }
                    for r in rows
                ]
            finally:
                conn.close()
        if self._backend == "file":
            self._storage_path.mkdir(parents=True, exist_ok=True)
            jobs = []
            for path in sorted(self._storage_path.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
                job_id = path.stem
                try:
                    with open(path) as f:
                        data = json.load(f)
                    jobs.append({
                        "job_id": job_id,
                        "status": data.get("status", "completed"),
                        "total_records": data.get("total_records", 0),
                        "completed_count": data.get("completed_count", 0),
                        "failed_count": data.get("failed_count", 0),
                        "total_tokens_used": data.get("total_tokens_used", 0),
                        "created_at": data.get("created_at"),
                        "updated_at": data.get("updated_at"),
                    })
                except (json.JSONDecodeError, OSError):
                    continue
                if len(jobs) >= limit:
                    break
            return jobs
        # memory: from _jobs
        with self._lock:
            all_jobs = list(self._jobs.values())
        _min_dt = datetime(1970, 1, 1, tzinfo=timezone.utc)
        all_jobs.sort(key=lambda j: (j["created_at"] or _min_dt), reverse=True)
        return [
            {
                "job_id": j["job_id"],
                "status": j["status"].value if hasattr(j["status"], "value") else str(j["status"]),
                "total_records": j["total_records"],
                "completed_count": j["completed_count"],
                "failed_count": j["failed_count"],
                "total_tokens_used": j.get("total_tokens_used", 0),
                "created_at": _serialize_datetime(j["created_at"]),
                "updated_at": _serialize_datetime(j["updated_at"]),
            }
            for j in all_jobs[:limit]
        ]


# Global store instance (uses settings for persistence backend)
batch_job_store = BatchJobStore()
