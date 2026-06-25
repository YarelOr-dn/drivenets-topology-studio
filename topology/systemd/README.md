# Topology Studio - systemd user units

This directory holds the systemd **user** unit templates for the
Topology Studio runtime. They are not loaded automatically -- the
operator copies (or symlinks) them into `~/.config/systemd/user/` and
runs `systemctl --user daemon-reload`.

The main app unit (`topology-app.service`) is already documented in
the deployment notes; the files here cover the **external health
monitor** added in 2026-04.

## Files

| File | Purpose |
|------|---------|
| `topology-health-monitor.service` | Oneshot that runs `health_monitor.py --once --auto-restart` |
| `topology-health-monitor.timer` | Fires the oneshot 30s after boot, then every 60s |

The script itself lives at `topology/health_monitor.py` and is
deployed to `/home/dn/CURSOR/health_monitor.py` per the standard
worktree -> CURSOR sync pattern.

## Install

```bash
# 1. Make sure the script is in the live deployment dir
cp /home/dn/drivenets-topology-studio/topology/health_monitor.py /home/dn/CURSOR/health_monitor.py

# 2. Drop the units into the user systemd dir
cp /home/dn/drivenets-topology-studio/topology/systemd/topology-health-monitor.service ~/.config/systemd/user/
cp /home/dn/drivenets-topology-studio/topology/systemd/topology-health-monitor.timer   ~/.config/systemd/user/

# 3. Reload + enable
systemctl --user daemon-reload
systemctl --user enable --now topology-health-monitor.timer

# 4. Verify
systemctl --user list-timers --all | grep topology-health
journalctl --user -u topology-health-monitor.service -n 50 --no-pager
cat /home/dn/.topology_health/status.json | python3 -m json.tool
curl -s http://127.0.0.1:8080/api/monitor/health | python3 -m json.tool
```

## What it checks

| Probe | URL | Critical | Notes |
|-------|-----|----------|-------|
| `serve` | `http://127.0.0.1:8080/api/health` | yes | Aggregate status reported by `serve.py`. Also fails the probe if the JSON reports any child as not-`ok`. |
| `discovery_api` | `http://127.0.0.1:8765/api/health` | yes | Direct probe of `discovery_api.py`. |
| `scaler_bridge` | `http://127.0.0.1:8766/api/health` | yes | Direct probe of the FastAPI bridge. |
| `scaler_bridge_concurrency` | `http://127.0.0.1:8766/api/health/concurrency` | no | Observability snapshot. Non-critical: failures here do not flip overall_healthy. |

## Recovery semantics

Auto-restart is **on** in the shipped unit and is gated by:

* `--fail-threshold=3` consecutive failures (~3 minutes at the 60s timer cadence)
* `--restart-cooldown=600` seconds between restarts
* `--restart-burst=3` restarts inside a `--restart-window=1800` second window
* Restart is only attempted when the **aggregate** probe (`serve`) **and** at
  least one upstream probe (`discovery_api`/`scaler_bridge`) are failing. A
  single-port blip never bounces the whole stack.

Disable recovery without removing monitoring by editing the unit and
dropping `--auto-restart`:

```bash
systemctl --user edit topology-health-monitor.service
# in the override drop-in:
[Service]
ExecStart=
ExecStart=/usr/bin/python3 /home/dn/CURSOR/health_monitor.py --once --timeout=4
systemctl --user daemon-reload
```

## Files written by the monitor

All under `${TOPOLOGY_HEALTH_DIR}` (default `/home/dn/.topology_health`):

| File | Purpose |
|------|---------|
| `status.json` | Latest probe report (the one served at `/api/monitor/health`). |
| `failures.json` | Persistent counters + restart bookkeeping. |
| `health_monitor.log` | Human-readable log. |

The monitor never writes per-user state. It is safe to delete the
state directory at any time -- it is recreated on the next run.
