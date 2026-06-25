#!/usr/bin/env python3
"""
Wave 7 hardening smoke test.

Scenarios exercised (each scenario is independent and prints PASS/FAIL):

A. Owner normalization
   * ``" Alice "`` and ``"alice"`` must NOT collide on the scheduler
     counter AFTER normalization -- we DO preserve case but DO strip
     whitespace. The same user logging in as "alice" twice (raw and
     with trailing spaces from an over-eager header parser) should
     therefore produce one bucket, not two.

B. Reaper reaps an abandoned dry-run
   * Manually plant a job with ``awaiting_decision=True``, an old
     ``awaiting_since_ts``, and a stashed scheduler token + push slot +
     user-push reservation. One ``reap_now()`` call must release all
     three, mark the job status=reaped, and flip awaiting_decision to
     False.

C. Reaper does NOT reap a fresh dry-run
   * Same setup as B but timestamp is ``now``. After ``reap_now()`` the
     job must still be awaiting_decision=True and all resources still
     held.

D. Commit after reaper returns 410 with a clean message
   * We simulate the HTTP layer by calling the internal ``push_commit``
     logic path; the job being ``status="reaped"`` MUST raise 410 Gone.

E. Audit log records a push_rejected event with redacted detail
   * Record an event carrying a ``password`` field in the detail; the
     line on disk must have ``[REDACTED]`` instead of the value.

F. Per-user job quota blocks runaway callers
   * Fill ``_push_jobs`` with 100 rows owned by ``"alice"`` (all done),
     then attempt to enforce_per_user_job_quota for alice -- the oldest
     DONE rows must be evicted. With 100 in-flight rows (not done) the
     function must raise HTTPException 429.

G. SSH pool in-use refcount + LRU safety
   * Simulate 3 pool entries. Mark entry #2 as in_use=1, set its
     last_used to the lowest value. Trigger _evict_lru(): entry #2
     MUST NOT be evicted. The second-oldest idle entry is picked
     instead.

The test runs as a standalone Python script and does NOT require the
FastAPI server to be live. It imports the route modules directly.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import traceback
import unittest.mock as _mock

HERE = os.path.dirname(os.path.abspath(__file__))
# We need the topology/ package root on PYTHONPATH so ``routes.*``
# imports resolve. The test is designed to run from anywhere.
_topology_root = "/home/dn/drivenets-topology-studio/topology"
if _topology_root not in sys.path:
    sys.path.insert(0, _topology_root)
_scaler_root = "/home/dn/drivenets-topology-studio/scaler"
if _scaler_root not in sys.path:
    sys.path.insert(0, _scaler_root)


_results = []


def _check(name, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    print(f"[{tag}] {name}" + (f"  -- {detail}" if detail else ""))
    _results.append((name, bool(cond), detail))
    return cond


# --------------------------------------------------------------------
# A. Owner normalization
# --------------------------------------------------------------------
def scenario_a_owner_norm():
    print("\n== A: owner normalization ==")
    from routes._state import normalize_owner, normalize_owner_lax

    _check("A.1 empty -> ''", normalize_owner("") == "", detail="got=" + repr(normalize_owner("")))
    _check("A.2 None -> ''", normalize_owner(None) == "")
    _check("A.3 whitespace-only -> ''", normalize_owner("   ") == "")
    _check("A.4 strip preserved case", normalize_owner(" Alice ") == "Alice")
    _check("A.5 lax '' -> 'default'", normalize_owner_lax("") == "default")
    _check("A.6 lax None -> 'default'", normalize_owner_lax(None) == "default")
    _check("A.7 strip collision: ' alice ' == 'alice'",
           normalize_owner_lax(" alice ") == normalize_owner_lax("alice"))
    # Critical: reserving + releasing with pre-normalized identities must
    # not strand a counter bucket.
    from routes._device_scheduler import scheduler
    # Snapshot current counter so we're insulated from other scenarios
    start = scheduler.user_push_count(" alice ")
    scheduler.reserve_user_push(" alice ")
    after_res = scheduler.user_push_count("alice")
    scheduler.release_user_push("alice")
    final = scheduler.user_push_count(" alice ")
    _check("A.8 reserve(' alice ') visible as count('alice')",
           after_res == start + 1,
           detail=f"start={start} after_res={after_res}")
    _check("A.9 release('alice') clears ' alice ' bucket",
           final == start, detail=f"final={final} start={start}")


# --------------------------------------------------------------------
# B + C + D. Reaper
# --------------------------------------------------------------------
def _plant_awaiting_job(job_id, owner, mgmt_ip, awaiting_since_ts,
                       reserve_push_slot=True, reserve_user_push=True,
                       reserve_sched=True):
    from routes._state import _push_jobs, _push_jobs_lock
    from routes._device_scheduler import scheduler

    sched_token = None
    push_slot = None
    if reserve_sched:
        sched_token = scheduler.acquire(mgmt_ip, op="dryrun-test",
                                        owner=owner, job_id=job_id)
    if reserve_push_slot:
        push_slot = scheduler.acquire_global_push_slot(
            op="dryrun-test", owner=owner, job_id=job_id
        )
    if reserve_user_push:
        scheduler.reserve_user_push(owner)

    with _push_jobs_lock:
        _push_jobs[job_id] = {
            "job_id": job_id,
            "owner": owner,
            "status": "awaiting_decision",
            "phase": "awaiting_decision",
            "awaiting_decision": True,
            "awaiting_since_ts": awaiting_since_ts,
            "started_at_ts": awaiting_since_ts,
            "device_id": "TEST-DEV",
            "mgmt_ip": mgmt_ip,
            "_sched_token": sched_token,
            "_push_slot_handle": push_slot,
            "_user_push_reserved": reserve_user_push,
            "_channel": None,  # no real SSH -- reaper must still close cleanly
            "_client": None,
            "_pusher": None,
            "_live_output": None,
            "done": False,
        }


def _clear_job(job_id):
    from routes._state import _push_jobs, _push_jobs_lock
    with _push_jobs_lock:
        _push_jobs.pop(job_id, None)


def scenario_b_reaper_reaps_stale():
    print("\n== B: reaper reaps stale dry-run ==")
    from routes._reaper import reap_now, DRYRUN_TTL_S
    from routes._state import _push_jobs, _push_jobs_lock
    from routes._device_scheduler import scheduler

    owner = "alice"
    job = "WAVE7-B-JOB"
    mgmt = "10.99.0.1"
    before_count = scheduler.user_push_count(owner)
    # Plant a job stamped 2*TTL in the past so the reaper must pick it.
    planted_at = time.time() - max(120, 2 * DRYRUN_TTL_S)
    _plant_awaiting_job(job, owner, mgmt, planted_at)

    mid_count = scheduler.user_push_count(owner)
    _check("B.1 user counter incremented on plant",
           mid_count == before_count + 1)

    reaped = reap_now()
    _check("B.2 reaper reports >=1 reaped", reaped >= 1,
           detail=f"reaped={reaped}")
    with _push_jobs_lock:
        j = _push_jobs.get(job) or {}
    _check("B.3 job marked reaped", j.get("status") == "reaped"
           and j.get("reaped") is True)
    _check("B.4 awaiting_decision cleared",
           j.get("awaiting_decision") is False)
    _check("B.5 resources stripped",
           j.get("_sched_token") is None
           and j.get("_push_slot_handle") is None
           and j.get("_user_push_reserved") is None)
    end_count = scheduler.user_push_count(owner)
    _check("B.6 user counter released",
           end_count == before_count,
           detail=f"before={before_count} end={end_count}")
    _clear_job(job)


def scenario_c_reaper_spares_fresh():
    print("\n== C: reaper leaves fresh dry-run alone ==")
    from routes._reaper import reap_now
    from routes._state import _push_jobs, _push_jobs_lock
    from routes._device_scheduler import scheduler

    owner = "bob"
    job = "WAVE7-C-JOB"
    mgmt = "10.99.0.2"
    before_count = scheduler.user_push_count(owner)
    _plant_awaiting_job(job, owner, mgmt, time.time())
    reap_now()
    with _push_jobs_lock:
        j = _push_jobs.get(job) or {}
    _check("C.1 job still awaiting",
           j.get("awaiting_decision") is True
           and j.get("status") == "awaiting_decision",
           detail=f"status={j.get('status')!r}")
    _check("C.2 user counter still incremented",
           scheduler.user_push_count(owner) == before_count + 1)
    # Manual cleanup so later scenarios don't see leftover state.
    with _push_jobs_lock:
        j2 = _push_jobs.get(job) or {}
        tok = j2.pop("_sched_token", None)
        slot = j2.pop("_push_slot_handle", None)
        user_res = j2.pop("_user_push_reserved", False)
    try:
        scheduler.release(tok)
    except Exception:
        pass
    try:
        scheduler.release_global_push_slot(slot)
    except Exception:
        pass
    if user_res:
        scheduler.release_user_push(owner)
    _clear_job(job)


def scenario_d_commit_after_reap_410():
    print("\n== D: commit after reap returns 410 ==")
    from routes._state import _push_jobs, _push_jobs_lock

    owner = "carol"
    job = "WAVE7-D-JOB"
    with _push_jobs_lock:
        _push_jobs[job] = {
            "job_id": job, "owner": owner,
            "status": "reaped", "reaped": True,
            "awaiting_decision": False,
            "device_id": "TEST-DEV", "mgmt_ip": "10.99.0.3",
            "done": True,
        }

    # Simulate HTTP commit: the handler logic reproduces the 410 branch.
    from fastapi import HTTPException
    from routes import operations as ops

    class _Req:
        class state:
            user = owner
            role = "admin"
    try:
        ops.push_commit(job_id=job, request=_Req())  # type: ignore[arg-type]
        _check("D.1 push_commit raised 410", False,
               detail="no exception")
    except HTTPException as exc:
        _check("D.1 push_commit raised 410",
               exc.status_code == 410,
               detail=f"status={exc.status_code}")
        detail = exc.detail if isinstance(exc.detail, dict) else {}
        _check("D.2 error tag = session_reaped",
               detail.get("error") == "session_reaped")
    except Exception as exc:
        _check("D.1 push_commit raised 410", False,
               detail=f"wrong exception: {exc!r}")
    _clear_job(job)


# --------------------------------------------------------------------
# E. Audit log redaction
# --------------------------------------------------------------------
def scenario_e_audit_redacts():
    print("\n== E: audit log records event with redaction ==")
    tmp = tempfile.NamedTemporaryFile(prefix="wave7_audit_", suffix=".log",
                                      delete=False)
    tmp.close()
    os.environ["TP_AUDIT_LOG_PATH"] = tmp.name
    # Reload the audit module so it picks the new path.
    if "routes._audit_log" in sys.modules:
        del sys.modules["routes._audit_log"]
    from routes._audit_log import record_event, audit_stats, AUDIT_PATH
    ok = record_event(
        action="push_rejected", owner="alice", role="user",
        device_id="PE-1", mgmt_ip="10.0.0.1", job_id="j-123",
        result="forbidden_role",
        detail={"password": "supersecret", "reason": "viewer role",
                "nested": {"token": "abcd"}},
    )
    _check("E.1 record_event returned True", ok)
    with open(AUDIT_PATH, "r", encoding="utf-8") as fh:
        line = fh.readline().strip()
    try:
        data = json.loads(line)
    except Exception as exc:
        data = {}
        _check("E.2 JSONL parse", False, detail=str(exc))
    _check("E.3 secret redacted",
           data.get("detail", {}).get("password") == "[REDACTED]",
           detail=str(data.get("detail")))
    _check("E.4 nested token redacted",
           data.get("detail", {}).get("nested", {}).get("token")
           == "[REDACTED]")
    _check("E.5 reason preserved",
           data.get("detail", {}).get("reason") == "viewer role")
    stats = audit_stats()
    _check("E.6 stats counter incremented",
           stats.get("events_written", 0) >= 1)
    try:
        os.unlink(tmp.name)
    except OSError:
        pass


# --------------------------------------------------------------------
# F. Per-user job quota
# --------------------------------------------------------------------
def scenario_f_job_quota():
    print("\n== F: per-user job quota ==")
    from routes.operations import (
        _enforce_per_user_job_quota, _PER_USER_JOB_MAX,
    )
    from routes._state import _push_jobs, _push_jobs_lock
    from fastapi import HTTPException

    owner = "dave"
    cap = _PER_USER_JOB_MAX
    # Clean slate for dave.
    with _push_jobs_lock:
        drop = [jid for jid, j in _push_jobs.items()
                if isinstance(j, dict) and j.get("owner") == owner]
        for jid in drop:
            _push_jobs.pop(jid, None)

    # F.1 -- Fill exactly cap rows, all DONE. Quota must evict oldest.
    base_ts = time.time() - 3600
    with _push_jobs_lock:
        for i in range(cap):
            _push_jobs[f"FQUOTA-F1-{i}"] = {
                "job_id": f"FQUOTA-F1-{i}",
                "owner": owner,
                "done": True,
                "awaiting_decision": False,
                "status": "completed",
                "started_at_ts": base_ts + i,
            }
    # Should NOT raise -- eviction path.
    try:
        _enforce_per_user_job_quota(owner)
        _check("F.1 quota evicted oldest (no exception)", True)
    except HTTPException as exc:
        _check("F.1 quota evicted oldest (no exception)", False,
               detail=f"status={exc.status_code}")
    with _push_jobs_lock:
        remaining = sum(1 for _, j in _push_jobs.items()
                        if isinstance(j, dict) and j.get("owner") == owner)
    _check("F.2 after quota < cap rows remain",
           remaining < cap,
           detail=f"remaining={remaining} cap={cap}")

    # F.3 -- Fill cap rows all IN-FLIGHT. Quota must raise 429.
    with _push_jobs_lock:
        drop = [jid for jid, j in _push_jobs.items()
                if isinstance(j, dict) and j.get("owner") == owner]
        for jid in drop:
            _push_jobs.pop(jid, None)
        for i in range(cap):
            _push_jobs[f"FQUOTA-F3-{i}"] = {
                "job_id": f"FQUOTA-F3-{i}",
                "owner": owner,
                "done": False,
                "awaiting_decision": True,
                "status": "awaiting_decision",
                "started_at_ts": base_ts + i,
            }
    try:
        _enforce_per_user_job_quota(owner)
        _check("F.3 in-flight full -> 429", False,
               detail="no exception raised")
    except HTTPException as exc:
        _check("F.3 in-flight full -> 429",
               exc.status_code == 429,
               detail=f"status={exc.status_code}")
        detail = exc.detail if isinstance(exc.detail, dict) else {}
        _check("F.4 error tag = per_user_job_quota",
               detail.get("error") == "per_user_job_quota")

    # Clean up so later scenarios / other tests have a clean store.
    with _push_jobs_lock:
        drop = [jid for jid, j in _push_jobs.items()
                if isinstance(j, dict) and j.get("owner") == owner]
        for jid in drop:
            _push_jobs.pop(jid, None)


# --------------------------------------------------------------------
# G. SSH pool in-use + LRU safety
# --------------------------------------------------------------------
def scenario_g_ssh_pool_inuse():
    print("\n== G: SSH pool in-use refcount ==")
    from routes.bridge_helpers import _ssh_pool

    # Reach into the pool dict directly to build a controlled
    # scenario WITHOUT opening real SSH connections.
    with _ssh_pool._lock:
        # Clear pool for a deterministic test.
        _ssh_pool._pool.clear()
        # Install a trivial fake client (has minimal API used by _evict_lru).
        class _FakeClient:
            closed = False

            def close(self):
                self.closed = True

            def get_transport(self):
                class _T:
                    def is_active(self_inner):
                        return True
                    def set_keepalive(self_inner, *_a, **_k):
                        pass
                return _T()

        now = time.monotonic()
        _ssh_pool._pool["alice@10.0.0.1"] = {
            "client": _FakeClient(), "user": "u", "app_user": "alice",
            "last_used": now - 10,  # oldest
            "created_at": now - 100, "in_use": 1,
        }
        _ssh_pool._pool["bob@10.0.0.2"] = {
            "client": _FakeClient(), "user": "u", "app_user": "bob",
            "last_used": now - 5,   # middle
            "created_at": now - 50, "in_use": 0,
        }
        _ssh_pool._pool["carol@10.0.0.3"] = {
            "client": _FakeClient(), "user": "u", "app_user": "carol",
            "last_used": now - 1,   # newest
            "created_at": now - 10, "in_use": 0,
        }
    # Call the LRU evict. The alice entry is oldest but is in use, so
    # bob (second-oldest, idle) must be the victim.
    _ssh_pool._evict_lru()
    with _ssh_pool._lock:
        present = set(_ssh_pool._pool.keys())
    _check("G.1 in-use entry survived LRU",
           "alice@10.0.0.1" in present,
           detail=f"present={present}")
    _check("G.2 oldest idle entry evicted",
           "bob@10.0.0.2" not in present,
           detail=f"present={present}")
    _check("G.3 newest entry untouched",
           "carol@10.0.0.3" in present)
    # Clean up.
    with _ssh_pool._lock:
        _ssh_pool._pool.clear()


# --------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------
def main():
    print("=" * 70)
    print("Wave 7 hardening smoke test")
    print("=" * 70)
    for fn in (
        scenario_a_owner_norm,
        scenario_b_reaper_reaps_stale,
        scenario_c_reaper_spares_fresh,
        scenario_d_commit_after_reap_410,
        scenario_e_audit_redacts,
        scenario_f_job_quota,
        scenario_g_ssh_pool_inuse,
    ):
        try:
            fn()
        except Exception as exc:
            traceback.print_exc()
            _results.append((fn.__name__, False, f"EXC: {exc}"))

    print("\n" + "=" * 70)
    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"SUMMARY: {passed}/{total} checks passed")
    print("=" * 70)
    for name, ok, detail in _results:
        if not ok:
            print(f"  FAIL: {name}  {detail}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
