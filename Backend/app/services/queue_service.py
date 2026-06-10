# app/services/queue_service.py
"""
Service de File d'Attente IA (Simulation Architecture Résiliente) — V3.0
=========================================================================
Simule une architecture à files d'attente (RabbitMQ/Kafka-like) en utilisant
FastAPI BackgroundTasks + un compteur de jobs en mémoire.

En production bancaire réelle : RabbitMQ ou Kafka.
Pour ce PFE : BackgroundTasks FastAPI — démonstration de l'architecture
sans infrastructure externe.

Endpoints exposés :
  GET /ai/queue-status  → état de la queue (jobs en attente, terminés)
"""

import asyncio
import uuid
from datetime import datetime, timezone
from collections import deque
from typing import Callable, Optional, Awaitable


# ─────────────────────────────────────────────────────────────────────────────
# Store en mémoire de la queue
# ─────────────────────────────────────────────────────────────────────────────

class JobStatus:
    PENDING    = "PENDING"
    PROCESSING = "PROCESSING"
    DONE       = "DONE"
    FAILED     = "FAILED"


class AIJobQueue:
    """
    File d'attente de jobs IA en mémoire.
    Compatible avec BackgroundTasks FastAPI.
    """

    def __init__(self, max_history: int = 50):
        self._pending:    deque = deque()
        self._history:    list  = []       # Jobs terminés (max max_history)
        self._running:    int   = 0
        self._max_history = max_history
        self._total_enqueued   = 0
        self._total_completed  = 0
        self._total_failed     = 0

    def enqueue(self, job_fn: Callable, job_name: str = "AI_JOB", *args, **kwargs) -> str:
        """
        Ajoute un job à la file d'attente.
        Retourne l'ID unique du job.
        """
        job_id = str(uuid.uuid4())[:8].upper()
        job = {
            "id":          job_id,
            "name":        job_name,
            "status":      JobStatus.PENDING,
            "enqueued_at": datetime.now(timezone.utc).isoformat(),
            "started_at":  None,
            "finished_at": None,
            "error":       None,
        }
        self._pending.append((job, job_fn, args, kwargs))
        self._total_enqueued += 1
        print(f" [QUEUE] Job {job_id} ({job_name}) enqueued  File: {len(self._pending)}")
        return job_id

    async def process_next(self):
        """Traite le prochain job en attente (appelé en BackgroundTask)."""
        if not self._pending:
            return

        job, job_fn, args, kwargs = self._pending.popleft()
        job["status"]     = JobStatus.PROCESSING
        job["started_at"] = datetime.now(timezone.utc).isoformat()
        self._running    += 1

        print(f"  [QUEUE] Job {job['id']} ({job['name']})  PROCESSING")

        try:
            if asyncio.iscoroutinefunction(job_fn):
                await job_fn(*args, **kwargs)
            else:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, lambda: job_fn(*args, **kwargs))

            job["status"]      = JobStatus.DONE
            job["finished_at"] = datetime.now(timezone.utc).isoformat()
            self._total_completed += 1
            print(f"[OK] [QUEUE] Job {job['id']}  DONE")

        except Exception as e:
            job["status"]      = JobStatus.FAILED
            job["error"]       = str(e)
            job["finished_at"] = datetime.now(timezone.utc).isoformat()
            self._total_failed += 1
            print(f"[X] [QUEUE] Job {job['id']}  FAILED : {e}")

        finally:
            self._running -= 1
            self._history.append(job)
            # Limiter l'historique en mémoire
            if len(self._history) > self._max_history:
                self._history.pop(0)

    def get_status(self) -> dict:
        """Retourne l'état actuel de la queue (pour l'endpoint /ai/queue-status)."""
        return {
            "queue_type":      "BackgroundTasks FastAPI (Simulation RabbitMQ/Kafka)",
            "pending_jobs":    len(self._pending),
            "running_jobs":    self._running,
            "total_enqueued":  self._total_enqueued,
            "total_completed": self._total_completed,
            "total_failed":    self._total_failed,
            "recent_jobs":     list(reversed(self._history[-10:])),
        }


# Singleton global de la queue
ai_queue = AIJobQueue()