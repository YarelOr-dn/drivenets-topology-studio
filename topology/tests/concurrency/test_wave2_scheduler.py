"""Wave 2.1 smoke test: DeviceOpScheduler serializes concurrent pushes
to the same mgmt_ip while allowing different IPs to run in parallel.

Runs without a live DNOS device by monkey-patching the bits of
ConfigPusher / _resolve_mgmt_ip / _get_credentials that touch the network.
"""
from __future__ import annotations

import sys
import os
import time
import threading
from pathlib import Path

REPO = Path("/home/dn/drivenets-topology-studio")
sys.path.insert(0, str(REPO / "scaler"))
sys.path.insert(0, str(REPO / "topology"))

os.environ.setdefault("TP_AUTH_ENFORCE", "never")

# ---------------------------------------------------------------------------
# Monkeypatch config_pusher BEFORE operations imports it.
# ---------------------------------------------------------------------------
import scaler.config_pusher as cp

class _FakePusher:
    def push_config_terminal_paste(self, device, config_text, dry_run=False,
                                   progress_callback=None, live_output_callback=None,
                                   cancel_check=None):
        if progress_callback:
            progress_callback("pushing", 30)
        if live_output_callback:
            live_output_callback(f"[FAKE] starting paste on {device.ip}")
        time.sleep(0.4)
        if live_output_callback:
            live_output_callback(f"[FAKE] paste done on {device.ip}")
        return True, "ok"

    def push_config(self, *a, **kw):
        return True, "ok"

    def push_config_merge(self, *a, **kw):
        return True, "ok"

    def push_config_terminal_check_and_hold(self, *a, **kw):
        return True, "ok", object(), object()

    def cancel_held_session(self, channel, client, live_output_callback=None):
        if live_output_callback:
            live_output_callback("[FAKE] session discarded")
        return True, "cancelled"

    def commit_held_session(self, channel, client, live_output_callback=None):
        if live_output_callback:
            live_output_callback("[FAKE] committed")
        return True, "committed"

    @staticmethod
    def extract_platform_from_config(*_a, **_kw):
        return "generic"

cp.ConfigPusher = _FakePusher
def _fake_get_estimates(*a, **kw):
    return {"estimates": {"terminal_paste": {"total": 1}}}
cp.get_accurate_push_estimates = _fake_get_estimates
def _fake_save_timing(*a, **kw):
    pass
cp.save_timing_record = _fake_save_timing

# ---------------------------------------------------------------------------
# Now import routes and patch the *module-local* _resolve_mgmt_ip + creds.
# Patching bridge_helpers after the `from ... import ...` is a no-op because
# operations.py already bound the names.
# ---------------------------------------------------------------------------
from routes import operations
from routes._state import _push_jobs, _push_jobs_lock
from routes._device_scheduler import scheduler

def _fake_resolve(device_id, ssh_host=""):
    return device_id, device_id, "dns"
operations._resolve_mgmt_ip = _fake_resolve

def _fake_creds():
    return ("dnroot", "dnroot")
operations._get_credentials = _fake_creds

# Build a minimal FastAPI test client.
import fastapi
from fastapi.testclient import TestClient
app = fastapi.FastAPI()
app.include_router(operations.router)
client = TestClient(app)

def wait_done(job_id, timeout=6.0):
    t_start = time.time()
    while time.time() - t_start < timeout:
        with _push_jobs_lock:
            j = _push_jobs.get(job_id)
            if j and j.get("done"):
                return dict(j)
        time.sleep(0.02)
    return None

# ---------------------------------------------------------------------------
# Test A: two pushes to SAME mgmt_ip serialize
# ---------------------------------------------------------------------------
print("[test A] two pushes to SAME mgmt_ip should serialize")
results_a = {}
def fire_push(label, device_id):
    t0 = time.time()
    r = client.post("/api/operations/push", json={
        "device_id": device_id,
        "ssh_host": "",
        "config": "network-services evpn instance FOO\nadmin-state enabled\n!\n",
        "push_method": "terminal_paste",
        "dry_run": False,
    })
    assert r.status_code == 200, f"push submit failed: {r.status_code} {r.text}"
    results_a[label] = {"job_id": r.json().get("job_id"), "submit_at": t0}

t1 = threading.Thread(target=fire_push, args=("alice", "10.99.99.1"))
t2 = threading.Thread(target=fire_push, args=("bob", "10.99.99.1"))
t1.start()
time.sleep(0.05)
t2.start()
t1.join(); t2.join()

done_alice = wait_done(results_a["alice"]["job_id"])
done_bob = wait_done(results_a["bob"]["job_id"])
assert done_alice, "alice job did not finish"
assert done_bob, "bob job did not finish"

t_end = time.time()
total = t_end - results_a["alice"]["submit_at"]
assert total >= 0.75, f"same-IP pushes appear parallel (total={total:.2f}s)"
bob_lines = " ".join(done_bob.get("terminal_lines") or [])
assert "queued behind" in bob_lines.lower(), \
    f"bob's job did not log a queued notice; lines={bob_lines[:200]}"
print(f"  PASS: total={total:.2f}s (>=0.75 expected), bob saw 'queued behind'")

# ---------------------------------------------------------------------------
# Test B: two pushes to DIFFERENT mgmt_ip run in parallel
# ---------------------------------------------------------------------------
print("[test B] two pushes to DIFFERENT mgmt_ip should parallelize")
results_b = {}
t_start_b = time.time()
def fire_push_b(label, device_id):
    r = client.post("/api/operations/push", json={
        "device_id": device_id,
        "ssh_host": "",
        "config": "network-services evpn instance BAR\nadmin-state enabled\n!\n",
        "push_method": "terminal_paste",
        "dry_run": False,
    })
    assert r.status_code == 200
    results_b[label] = {"job_id": r.json().get("job_id")}

t1 = threading.Thread(target=fire_push_b, args=("carol", "10.99.99.10"))
t2 = threading.Thread(target=fire_push_b, args=("dave", "10.99.99.11"))
t1.start(); t2.start()
t1.join(); t2.join()

done_carol = wait_done(results_b["carol"]["job_id"])
done_dave = wait_done(results_b["dave"]["job_id"])
assert done_carol and done_dave
t_end_b = time.time()
total_b = t_end_b - t_start_b
assert total_b <= 0.75, f"different-IP pushes appear serialized (total={total_b:.2f}s)"
carol_lines = " ".join(done_carol.get("terminal_lines") or [])
assert "queued behind" not in carol_lines.lower(), \
    "carol should not have queued behind anyone"
print(f"  PASS: total={total_b:.2f}s (<=0.75 expected), no queued notice")

# ---------------------------------------------------------------------------
# Test C: scheduler snapshot reports idle after all done
# ---------------------------------------------------------------------------
print("[test C] scheduler snapshot should be idle after all pushes complete")
snap = scheduler.snapshot()
assert snap["busy"] == {}, f"expected no busy devices, got {snap['busy']}"
assert snap["stats"]["acquires"] >= 4, snap
print(f"  PASS: busy={snap['busy']}, total_acquires={snap['stats']['acquires']}")

# ---------------------------------------------------------------------------
# Test D: dry-run held session keeps lock across commit
# ---------------------------------------------------------------------------
print("[test D] dry_run should keep the lock across commit endpoint")
r = client.post("/api/operations/push", json={
    "device_id": "10.99.99.50",
    "ssh_host": "",
    "config": "!\n",
    "push_method": "terminal_paste",
    "dry_run": True,
})
assert r.status_code == 200
dry_job_id = r.json()["job_id"]

# Wait for the dry-run to reach awaiting_decision.
t_start = time.time()
while time.time() - t_start < 3.0:
    with _push_jobs_lock:
        j = _push_jobs.get(dry_job_id) or {}
        if j.get("awaiting_decision"):
            break
    time.sleep(0.02)
assert j.get("awaiting_decision"), f"dry_run never reached awaiting_decision: {j}"

# Verify the lock IS held (scheduler busy for this device).
snap = scheduler.snapshot()
assert "10.99.99.50" in snap["busy"], f"expected 10.99.99.50 busy during dry-run hold, snap={snap}"
# Verify the token moved into the job dict.
with _push_jobs_lock:
    jj = _push_jobs[dry_job_id]
    assert jj.get("_sched_token") is not None, "token should be transferred to job dict"
# Verify _sched_token is sanitized out of API responses.
from routes.bridge_helpers import _sanitize_job
safe = _sanitize_job(jj)
assert "_sched_token" not in safe, "token leaked through _sanitize_job"
print(f"  PASS: dry_run holds lock (busy={list(snap['busy'].keys())}), token stashed & sanitized")

# Simulate cancel to release.
r = client.post(f"/api/operations/push/{dry_job_id}/cancel")
assert r.status_code == 200
snap2 = scheduler.snapshot()
assert "10.99.99.50" not in snap2["busy"], f"cancel did not release lock: {snap2}"
print(f"  PASS: cancel released lock")

print()
print("ALL WAVE 2.1 SMOKE TESTS PASSED")
