"""Mutable shared state for scaler bridge."""
import threading

_push_jobs = {}
_push_jobs_lock = threading.Lock()
