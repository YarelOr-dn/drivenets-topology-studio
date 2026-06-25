# Concurrency & Multi-User Hardening Regression Suite

Regression guards for the Wave 2 / Wave 6 / Wave 7 fixes to the
scaler-bridge push pipeline. Run **all** of these any time the
following modules change:

| Module | What changes break these tests |
|---|---|
| `topology/routes/operations.py` | push/commit/cancel/delete flow |
| `topology/routes/_device_scheduler.py` | per-device lock, global push slot, per-user cap, device queue cap |
| `topology/routes/_reaper.py` | stale dry-run reaper |
| `topology/routes/_authz.py` | push authorization policy |
| `topology/routes/_audit_log.py` | audit event writer |
| `topology/routes/_worker_pool.py` | bounded thread pools for push/upgrade |
| `topology/routes/_state.py` | owner normalisation helpers |
| `topology/routes/bridge_helpers.py` | SSH pool in-use tracking |

## Tests

### `test_wave2_scheduler.py`

Validates the Wave 2 `DeviceOpScheduler`: two pushes to the SAME
`mgmt_ip` serialize (user sees "queued behind ..."), pushes to
DIFFERENT IPs parallelize, dry-run holds the lock across commit /
cancel endpoints, and no token is leaked into SSE responses.

Uses a FastAPI `TestClient` with a monkey-patched `ConfigPusher` --
no live device required. Runs with `TP_AUTH_ENFORCE=never` because
the test mounts `operations.router` standalone without the bridge's
JWT middleware.

```bash
cd /home/dn/drivenets-topology-studio
PYTHONPATH="topology:scaler" TP_AUTH_ENFORCE=never \
    python3 topology/tests/concurrency/test_wave2_scheduler.py
```

### `test_wave6_storm.py`

100-user concurrent push storm. Verifies all four Wave 6 admission
controls:

* Scenario A: 100 users on 100 unique devices -> global push slot cap
  throttles to `TP_GLOBAL_PUSH_SLOTS` (default 20).
* Scenario B: 1 user firing 8 pushes -> `TP_PER_USER_PUSH_MAX` (5)
  trips, other 3 get HTTP 429.
* Scenario C: 100 users on 1 device -> `TP_DEVICE_QUEUE_MAX` (10)
  returns HTTP 503 for the overflow.
* Scenario D: bounded `ThreadPoolExecutor` holds 50 workers, never
  spawns 100 threads.
* Scenario E: observability snapshot exposes the four counters.

```bash
cd /home/dn/drivenets-topology-studio
PYTHONPATH="topology:scaler" \
    python3 topology/tests/concurrency/test_wave6_storm.py
```

### `test_wave7_hardening.py`

Unit-level smoke for the Wave 7 primitives: owner normalisation
across whitespace variants, reaper reaping stale dry-runs while
sparing fresh ones, `push_commit` returning 410 for a reaped job,
audit log redaction, per-user job quota eviction, and SSH pool
in-use refcount protecting checked-out clients from LRU eviction.

Runs entirely against the underscore-prefixed helpers (no HTTP
round-trip). 31 checks.

```bash
cd /home/dn/drivenets-topology-studio
PYTHONPATH="topology:scaler" \
    python3 topology/tests/concurrency/test_wave7_hardening.py
```

### `test_wave7_integration.py`

End-to-end HTTP integration of the Wave 7 authz + reaper path. Uses
a FastAPI `TestClient` with a micro middleware that stamps
`request.state.user` / `request.state.role` from test headers
(simulating a JWT). Runs with `TP_AUTH_ENFORCE=always` so the real
authorization gate is active.

Covers:

* Unauthenticated push -> 401 `auth_required`
* Viewer role -> 403 `insufficient_role`
* Whitespace-variant usernames share the same cap bucket (`alice`,
  ` alice`, `alice `, ` alice ` all count as `alice`)
* 6th push after hitting the cap -> 429 with retry-after
* Per-user job quota caps `_push_jobs` entries at
  `TP_PER_USER_JOB_MAX`
* Abandoned dry-run reaped, commit returns 410 `session_reaped`,
  user counter released
* No concurrency primitive leaks after the full workload
* Audit log and reaper stats counters advanced

25 checks. Requires `TP_DRYRUN_TTL_S=1` and `TP_REAPER_INTERVAL_S=1`
(set automatically by the script) to keep runtime under 10 seconds.

```bash
cd /home/dn/drivenets-topology-studio
PYTHONPATH="topology:scaler" \
    python3 topology/tests/concurrency/test_wave7_integration.py
```

## One-shot runner

Run all four tests in sequence. Exits non-zero if any fail:

```bash
cd /home/dn/drivenets-topology-studio
bash topology/tests/concurrency/run_all.sh
```

## Environment knobs (set per-test as needed)

| Var | Default | Purpose |
|---|---|---|
| `TP_GLOBAL_PUSH_SLOTS` | 20 | concurrent pushes across all users |
| `TP_PER_USER_PUSH_MAX` | 5 | concurrent pushes per user |
| `TP_DEVICE_QUEUE_MAX` | 10 | pushes queued per-device before 503 |
| `TP_PUSH_EXECUTOR_SIZE` | 50 | bounded push worker pool size |
| `TP_SSH_POOL_MAX` | 200 | max pooled paramiko clients |
| `TP_PER_USER_JOB_MAX` | 100 | per-user cap on `_push_jobs` rows |
| `TP_DRYRUN_TTL_S` | 600 | reaper abandonment threshold (seconds) |
| `TP_REAPER_INTERVAL_S` | 60 | reaper scan period (seconds) |
| `TP_REAPER_ENABLED` | 1 | disable reaper by setting to `0` |
| `TP_AUTH_ENFORCE` | `auto` | `always`, `never`, or `auto` (detect) |
| `TP_AUDIT_LOG_ENABLED` | 1 | disable audit log by setting to `0` |

`auto` means "follow `scaler_bridge._multiuser_available` if the
bridge is importable, else fall back to `api.auth.service` import
probe". Tests set it explicitly so behaviour is deterministic.
