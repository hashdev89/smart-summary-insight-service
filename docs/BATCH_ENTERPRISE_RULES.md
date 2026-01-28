# Batch Processing: Enterprise Rules & Implementation

This document maps each enterprise rule to how it is implemented in the Smart Summary & Insight Service.

---

## 1. Claude API rate limit: 50 requests/minute

**Rule:** Do not exceed the provider’s limit (50 requests/minute for Claude).

**Implementation:**
- **Config:** `CLAUDE_REQUESTS_PER_MINUTE=50` (default) in `app/config.py`.
- **Service:** `app/services/rate_limiter.py` — sliding-window limiter; `acquire()` blocks until a slot is free.
- **Usage:** Every batch LLM call calls `await rate_limiter.acquire()` before `ai_service.analyze()`.

---

## 2. Maximum concurrent LLM calls should be configurable

**Rule:** Cap how many LLM requests run at once (to stay under rate limits and control load).

**Implementation:**
- **Config:** `BATCH_MAX_CONCURRENT_LLM_CALLS=5` (default) in `app/config.py`.
- **Usage:** In `_process_batch`, an `asyncio.Semaphore(concurrency)` limits concurrent `_process_one_record` tasks that call the LLM. Concurrency is read from settings.

---

## 3. Results must be persisted (not just in-memory)

**Rule:** Batch job state and results must survive process restarts.

**Implementation:**
- **Config:** `BATCH_PERSISTENCE_BACKEND=memory|file|sqlite` in `app/config.py`.
- **Backend `memory`:** In-memory only (default, suitable for dev).
- **Backend `file`:** Each job is stored as `{job_id}.json` under `BATCH_JOB_STORAGE_PATH`. Every create/update writes to disk. `get_job` loads from disk if the job is not in memory.
- **Backend `sqlite`:** Results are stored in tables: `batch_jobs` (job_id, status, total_records, completed_count, failed_count, total_tokens_used, created_at, updated_at) and `batch_results` (job_id, record_index, success, response_json, error). DB path: `BATCH_SQLITE_PATH` (default `data/batch.db`). Use **GET /api/v1/batch/jobs** to list persisted jobs for table display.

---

## 4. Enterprise SLA: 99.9% availability

**Rule:** Service should be deployable with high availability (99.9% SLA).

**Implementation:**
- **Readiness:** `GET /api/v1/ready` — returns 200 only when the app can serve traffic. For `batch_persistence_backend=file`, it checks that the batch storage directory exists and is writable (create + write + delete a probe file). Use this in Kubernetes/orchestrator as the readiness probe; do not send traffic until ready.
- **Liveness:** `GET /api/v1/health` — simple liveness check.
- **Operational:** Achieving 99.9% uptime also requires deployment practices: multiple replicas, health/readiness probes, and resilient persistence (e.g. shared or replicated storage for `file` backend, or a DB/Redis in a future version).

---

## 5. Allow partial results retrieval before batch completes

**Rule:** Clients can fetch results for records that are already done while the batch is still running.

**Implementation:**
- **API:** `GET /api/v1/batch/{job_id}/status` returns `results` as soon as any record is processed. `results` is a list of `BatchRecordResult` (index, success, response or error); it grows as more records complete.
- **Store:** Each `append_result` is persisted immediately when `batch_persistence_backend=file`, so partial results are visible after restarts as well.

---

## 6. Handle failures gracefully—don’t fail entire batch for one bad record

**Rule:** A single bad or failing record must not abort the whole batch.

**Implementation:**
- **Per-record isolation:** Each record is processed in `_process_one_record`. Exceptions are caught per record; on failure we call `batch_job_store.append_result(job_id, idx, False, error=str(e))` and continue. Other records are still processed.
- **Retries:** Configurable `BATCH_RECORD_RETRY_COUNT` (default 1). Each record is retried up to `1 + BATCH_RECORD_RETRY_COUNT` times before being marked failed.
- **Fatal errors:** Only unexpected errors in the batch runner itself (e.g. in `asyncio.gather`) call `set_job_failed(job_id, message=...)`; individual record failures do not.

---

## 7. Rate limit awareness—respect LLM provider limits

**Rule:** Stay within the LLM provider’s rate limits.

**Implementation:**
- Same as **§1**: `RateLimiter(requests_per_minute=50)` and `acquire()` before each LLM call in batch processing. No LLM request is sent without first acquiring a slot. Concurrency is further limited by **§2** so that burst and sustained rate stay within the configured limit.

---

## 8. Cost tracking per batch (tokens used)

**Rule:** Track token usage (and optionally cost) per batch.

**Implementation:**
- **Storage:** Each job has `total_tokens_used`. On every successful record we add `response.metadata.tokens_used` (if present) via `append_result(..., tokens_used=...)`.
- **API:** `GET /api/v1/batch/{job_id}/status` returns:
  - `total_tokens_used`: sum of tokens for all successful LLM calls in that batch.
  - `estimated_cost`: optional; computed when `BATCH_COST_PER_1K_INPUT_TOKENS` and/or `BATCH_COST_PER_1K_OUTPUT_TOKENS` are set (rough 50/50 input/output split for the estimate).

---

## Configuration summary

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAUDE_REQUESTS_PER_MINUTE` | 50 | Max LLM requests per minute (rate limiter). |
| `BATCH_MAX_CONCURRENT_LLM_CALLS` | 5 | Max concurrent LLM calls per batch. |
| `BATCH_PERSISTENCE_BACKEND` | memory | `memory`, `file`, or `sqlite` (table persistence). |
| `BATCH_JOB_STORAGE_PATH` | data/batch_jobs | Directory for file backend. |
| `BATCH_SQLITE_PATH` | data/batch.db | SQLite DB path for table persistence. |
| `BATCH_RECORD_RETRY_COUNT` | 1 | Retries per record before marking failed. |
| `BATCH_COST_PER_1K_INPUT_TOKENS` | (none) | Optional; for `estimated_cost`. |
| `BATCH_COST_PER_1K_OUTPUT_TOKENS` | (none) | Optional; for `estimated_cost`. |

---

## Quick reference: where each rule is implemented

| Rule | Primary location |
|------|------------------|
| 50 req/min rate limit | `app/services/rate_limiter.py`, used in `app/api/routes.py` (`_process_one_record`) |
| Configurable concurrency | `app/config.py`, `app/api/routes.py` (`_process_batch` semaphore) |
| Persistence | `app/services/batch_job_store.py` (file backend + `_persist` / `_load_from_file`) |
| 99.9% SLA / readiness | `app/api/routes.py` (`GET /ready`) |
| Partial results | `app/services/batch_job_store.py` (append + return `results`), `BatchStatusResponse` |
| Graceful failure | `app/api/routes.py` (`_process_one_record` try/except, retry loop) |
| Rate limit awareness | Same as first row |
| Cost tracking | `app/services/batch_job_store.py` (`total_tokens_used`, `estimated_cost`), `BatchStatusResponse` |
