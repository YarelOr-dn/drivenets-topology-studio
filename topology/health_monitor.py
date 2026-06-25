#!/usr/bin/env python3
"""
Topology Studio external health monitor.

Probes the three app services (serve.py 8080, discovery_api.py 8765,
scaler_bridge.py 8766) using their /api/health endpoints, records the
result, and after a configurable streak of consecutive confirmed failures
restarts the systemd user service `topology-app.service`.

Designed to be run by a systemd user timer every 60 seconds. Safe to run
manually with `--once` for ad-hoc checks or `--watch` for a foreground loop.

State (deployment-wide, no user data):
  /home/dn/.topology_health/status.json    -- latest probe result
  /home/dn/.topology_health/failures.json  -- consecutive-failure counters + restart bookkeeping
  /home/dn/.topology_health/health_monitor.log  -- human-readable log

Recovery is intentionally conservative:
  * A service is "failing" only after `--fail-threshold` consecutive failures
    (default 3 -> ~3 minutes with the 60s timer).
  * Auto-restart is gated by `--restart-cooldown` seconds since the last
    restart attempt (default 600s) and `--restart-burst` restarts inside
    `--restart-window` seconds (default 3 / 1800s) to avoid restart storms.
  * Restart is only attempted when explicitly enabled (`--auto-restart`)
    AND the aggregate-health probe (8080) AND at least one of the
    upstream probes (8765/8766) are failing. Single-port blips don't
    bounce the whole stack.

This script never touches per-user data, never reads JWTs, and writes only
to its own state directory. It is safe for any process running as the
service owner (typically `dn`).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_STATE_DIR = Path(os.environ.get("TOPOLOGY_HEALTH_DIR", "/home/dn/.topology_health"))
DEFAULT_SERVICE_UNIT = os.environ.get("TOPOLOGY_HEALTH_UNIT", "topology-app.service")

PROBES: List[Dict[str, Any]] = [
    {
        "name": "serve",
        "url": "http://127.0.0.1:8080/api/health",
        "port": 8080,
        "critical": True,
        "expect_keys": ("serve",),
    },
    {
        "name": "discovery_api",
        "url": "http://127.0.0.1:8765/api/health",
        "port": 8765,
        "critical": True,
        "expect_keys": ("status",),
    },
    {
        "name": "scaler_bridge",
        "url": "http://127.0.0.1:8766/api/health",
        "port": 8766,
        "critical": True,
        "expect_keys": ("status",),
    },
    {
        "name": "scaler_bridge_concurrency",
        "url": "http://127.0.0.1:8766/api/health/concurrency",
        "port": 8766,
        "critical": False,
        "expect_keys": (),
    },
]


# ---------------------------------------------------------------------------
# State models
# ---------------------------------------------------------------------------

@dataclass
class ProbeResult:
    name: str
    url: str
    port: int
    healthy: bool
    http_code: Optional[int] = None
    latency_ms: Optional[int] = None
    error: Optional[str] = None
    detail: Optional[Dict[str, Any]] = None
    critical: bool = True

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "url": self.url,
            "port": self.port,
            "healthy": self.healthy,
            "http_code": self.http_code,
            "latency_ms": self.latency_ms,
            "error": self.error,
            "critical": self.critical,
            "detail": self.detail,
        }


@dataclass
class MonitorReport:
    checked_at: str
    overall_healthy: bool
    probes: List[Dict[str, Any]] = field(default_factory=list)
    consecutive_failures: Dict[str, int] = field(default_factory=dict)
    restart_attempted: bool = False
    restart_reason: Optional[str] = None
    restart_outcome: Optional[str] = None
    notes: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ensure_state_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(path, 0o755)
    except OSError:
        pass


def _setup_logging(log_path: Path, level: str = "INFO") -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    fmt = "%(asctime)s %(levelname)s %(message)s"
    handlers: List[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    try:
        handlers.append(logging.FileHandler(log_path, mode="a", encoding="utf-8"))
    except OSError as exc:
        sys.stderr.write(f"[health_monitor] cannot open log {log_path}: {exc}\n")
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format=fmt, handlers=handlers, force=True)


def _read_json(path: Path, default: Any) -> Any:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return default
    except Exception as exc:
        logging.warning("failed to read %s: %s", path, exc)
        return default


def _write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True, default=str)
    os.replace(tmp, path)


# ---------------------------------------------------------------------------
# Probing
# ---------------------------------------------------------------------------

def _probe_one(probe: Dict[str, Any], timeout_s: float) -> ProbeResult:
    name = probe["name"]
    url = probe["url"]
    port = probe["port"]
    critical = bool(probe.get("critical", True))
    expect_keys = probe.get("expect_keys", ())

    started = time.monotonic()

    sock_ok = False
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=min(timeout_s, 2.0)):
            sock_ok = True
    except OSError as exc:
        return ProbeResult(
            name=name, url=url, port=port, healthy=False,
            error=f"port closed: {exc}", critical=critical,
        )

    if not sock_ok:
        return ProbeResult(name=name, url=url, port=port, healthy=False, error="port closed", critical=critical)

    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            body = resp.read()
            latency_ms = int((time.monotonic() - started) * 1000)
            code = resp.status
            detail: Optional[Dict[str, Any]] = None
            try:
                detail = json.loads(body.decode("utf-8", errors="replace")) if body else None
            except Exception:
                detail = {"raw": body[:200].decode("utf-8", errors="replace")} if body else None

            healthy = 200 <= code < 400
            if healthy and expect_keys and isinstance(detail, dict):
                if not any(k in detail for k in expect_keys):
                    healthy = False

            if healthy and isinstance(detail, dict):
                bad = []
                for child in ("discovery_api", "scaler_bridge"):
                    sub = detail.get(child)
                    if isinstance(sub, dict) and sub.get("status") not in (None, "ok"):
                        bad.append(f"{child}={sub.get('status')}")
                if bad:
                    healthy = False
                    return ProbeResult(
                        name=name, url=url, port=port, healthy=False,
                        http_code=code, latency_ms=latency_ms,
                        error="aggregate reports degraded child: " + ", ".join(bad),
                        detail=detail, critical=critical,
                    )

            return ProbeResult(
                name=name, url=url, port=port, healthy=healthy,
                http_code=code, latency_ms=latency_ms,
                error=None if healthy else f"http {code}",
                detail=detail, critical=critical,
            )
    except urllib.error.HTTPError as exc:
        latency_ms = int((time.monotonic() - started) * 1000)
        return ProbeResult(
            name=name, url=url, port=port, healthy=False,
            http_code=exc.code, latency_ms=latency_ms,
            error=f"http {exc.code} {exc.reason}", critical=critical,
        )
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return ProbeResult(
            name=name, url=url, port=port, healthy=False,
            error=f"transport: {exc}", critical=critical,
        )


def probe_all(timeout_s: float) -> List[ProbeResult]:
    return [_probe_one(p, timeout_s) for p in PROBES]


# ---------------------------------------------------------------------------
# Counter / cooldown bookkeeping
# ---------------------------------------------------------------------------

def _load_failures(path: Path) -> Dict[str, Any]:
    data = _read_json(path, default={})
    if not isinstance(data, dict):
        data = {}
    data.setdefault("counters", {})
    data.setdefault("last_restart_at", 0.0)
    data.setdefault("recent_restarts", [])
    return data


def _save_failures(path: Path, payload: Dict[str, Any]) -> None:
    _write_json_atomic(path, payload)


def _update_counters(state: Dict[str, Any], results: List[ProbeResult]) -> Dict[str, int]:
    counters = state["counters"]
    for r in results:
        prev = int(counters.get(r.name, 0))
        if r.healthy:
            counters[r.name] = 0
        else:
            counters[r.name] = prev + 1
    return {k: int(v) for k, v in counters.items()}


def _should_restart(
    counters: Dict[str, int],
    fail_threshold: int,
    state: Dict[str, Any],
    cooldown_s: int,
    burst_limit: int,
    burst_window_s: int,
    now: float,
) -> tuple[bool, str]:
    serve_failed = counters.get("serve", 0) >= fail_threshold
    upstream_failed = (
        counters.get("discovery_api", 0) >= fail_threshold
        or counters.get("scaler_bridge", 0) >= fail_threshold
    )
    if not (serve_failed and upstream_failed):
        return False, "threshold not reached"

    last = float(state.get("last_restart_at") or 0.0)
    if now - last < cooldown_s:
        return False, f"cooldown active ({int(cooldown_s - (now - last))}s remaining)"

    recent = [t for t in state.get("recent_restarts", []) if (now - float(t)) < burst_window_s]
    state["recent_restarts"] = recent
    if len(recent) >= burst_limit:
        return False, f"burst limit reached ({len(recent)} restarts in {burst_window_s}s)"

    failing = [n for n, c in counters.items() if c >= fail_threshold]
    return True, f"consecutive failures: {failing}"


def _announce_restart(reason: str, eta_seconds: int, source: str, settle_s: float = 1.5) -> tuple[bool, str]:
    """Tell live browser tabs that an intentional restart is imminent.

    POSTs to the loopback-only /api/monitor/announce-restart endpoint
    (added in serve.py) which broadcasts a `service-restart` SSE event
    to every open tab. We then sleep ``settle_s`` so the event has a
    chance to flush before the supervisor takes the process down.

    Returns (ok, detail). Any failure (server already down, endpoint
    missing on older builds, transport error) is logged and ignored --
    the announce is a best-effort UX nicety, NOT a precondition for the
    restart itself.
    """
    payload = json.dumps({
        "reason": reason,
        "eta_seconds": int(eta_seconds),
        "source": source,
    }).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:8080/api/monitor/announce-restart",
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            ok = 200 <= resp.status < 400
            body = resp.read()[:200].decode("utf-8", errors="replace")
        if ok and settle_s > 0:
            time.sleep(settle_s)
        return ok, f"http {resp.status}: {body}"
    except urllib.error.HTTPError as exc:
        return False, f"http {exc.code} {exc.reason}"
    except Exception as exc:
        return False, f"transport: {exc}"


def _do_restart(unit: str, dry_run: bool, reason: str = "auto-recovery") -> tuple[bool, str]:
    cmd = ["systemctl", "--user", "restart", unit]
    if dry_run:
        return True, f"DRY RUN: would have run `{' '.join(cmd)}`"
    # Best-effort heads-up to live browser tabs BEFORE the process dies
    # so the frontend graceful-restart coordinator can pause polls and
    # render a friendly banner instead of a wall of red ConnectionRefused
    # errors. Failure to announce is non-fatal.
    ann_ok, ann_detail = _announce_restart(
        reason=reason,
        eta_seconds=15,
        source=f"health_monitor:{unit}",
        settle_s=1.5,
    )
    if not ann_ok:
        logging.info("graceful announce skipped: %s", ann_detail)
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if proc.returncode == 0:
            return True, "restart ok"
        return False, f"systemctl exit {proc.returncode}: {proc.stderr.strip() or proc.stdout.strip()}"
    except Exception as exc:
        return False, f"systemctl error: {exc}"


# ---------------------------------------------------------------------------
# Main run
# ---------------------------------------------------------------------------

def run_once(args: argparse.Namespace) -> MonitorReport:
    state_dir: Path = args.state_dir
    _ensure_state_dir(state_dir)

    status_path = state_dir / "status.json"
    failures_path = state_dir / "failures.json"

    results = probe_all(args.timeout)
    state = _load_failures(failures_path)
    counters = _update_counters(state, results)

    overall_healthy = all(r.healthy for r in results if r.critical)

    report = MonitorReport(
        checked_at=_now_iso(),
        overall_healthy=overall_healthy,
        probes=[r.as_dict() for r in results],
        consecutive_failures=dict(counters),
    )

    for r in results:
        msg = (
            f"probe {r.name} {'OK' if r.healthy else 'FAIL'}"
            f" code={r.http_code} latency_ms={r.latency_ms}"
            f"{' err=' + r.error if r.error else ''}"
        )
        (logging.info if r.healthy else logging.warning)(msg)

    if not overall_healthy and args.auto_restart:
        now = time.time()
        should, reason = _should_restart(
            counters,
            fail_threshold=args.fail_threshold,
            state=state,
            cooldown_s=args.restart_cooldown,
            burst_limit=args.restart_burst,
            burst_window_s=args.restart_window,
            now=now,
        )
        report.notes.append(f"recovery decision: {reason}")
        if should:
            ok, detail = _do_restart(args.service_unit, dry_run=args.dry_run, reason=reason)
            report.restart_attempted = True
            report.restart_reason = reason
            report.restart_outcome = ("ok" if ok else "failed") + ": " + detail
            if ok and not args.dry_run:
                state["last_restart_at"] = now
                state.setdefault("recent_restarts", []).append(now)
                logging.warning("restarted %s after %s -- %s", args.service_unit, reason, detail)
            elif args.dry_run:
                logging.warning("DRY RUN restart for %s after %s -- %s", args.service_unit, reason, detail)
            else:
                logging.error("restart of %s failed: %s", args.service_unit, detail)
    elif not overall_healthy:
        report.notes.append("auto-restart disabled; not attempting recovery")

    _save_failures(failures_path, state)
    _write_json_atomic(status_path, report.as_dict())

    return report


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Topology Studio external health monitor")
    p.add_argument("--state-dir", type=Path, default=DEFAULT_STATE_DIR,
                   help=f"directory for status/failures/log files (default {DEFAULT_STATE_DIR})")
    p.add_argument("--service-unit", default=DEFAULT_SERVICE_UNIT,
                   help=f"systemd user unit to restart (default {DEFAULT_SERVICE_UNIT})")
    p.add_argument("--timeout", type=float, default=4.0, help="HTTP probe timeout seconds")
    p.add_argument("--fail-threshold", type=int, default=3,
                   help="consecutive failures before a probe is considered failing (default 3)")
    p.add_argument("--restart-cooldown", type=int, default=600,
                   help="minimum seconds between auto-restart attempts (default 600)")
    p.add_argument("--restart-burst", type=int, default=3,
                   help="max restarts inside the burst window (default 3)")
    p.add_argument("--restart-window", type=int, default=1800,
                   help="burst-protection window in seconds (default 1800)")
    p.add_argument("--auto-restart", action="store_true",
                   help="enable systemctl --user restart of the service when failures persist")
    p.add_argument("--dry-run", action="store_true",
                   help="log restart actions but do not actually invoke systemctl")
    p.add_argument("--once", action="store_true", help="run a single check and exit")
    p.add_argument("--watch", type=int, default=0,
                   help="run forever, sleeping N seconds between checks (foreground)")
    p.add_argument("--log-level", default="INFO", help="logging level (default INFO)")
    p.add_argument("--print-status", action="store_true",
                   help="print the resulting status JSON to stdout")
    p.add_argument("--announce", metavar="REASON", default=None,
                   help="broadcast a graceful-restart announce to live clients and exit "
                        "(does NOT restart anything). Useful for manual deploys: "
                        "`--announce 'deploy: serve.py update' --announce-eta 20` then "
                        "run `systemctl --user restart topology-app.service` yourself.")
    p.add_argument("--announce-eta", type=int, default=15,
                   help="ETA seconds advertised to clients with --announce (default 15)")
    p.add_argument("--announce-source", default="manual",
                   help="source label advertised to clients with --announce (default 'manual')")
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    _ensure_state_dir(args.state_dir)
    log_path = args.state_dir / "health_monitor.log"
    _setup_logging(log_path, level=args.log_level)

    if args.announce:
        ok, detail = _announce_restart(
            reason=args.announce,
            eta_seconds=args.announce_eta,
            source=args.announce_source,
            settle_s=0.0,
        )
        logging.info("announce result: ok=%s detail=%s", ok, detail)
        print(json.dumps({"ok": ok, "detail": detail,
                          "reason": args.announce,
                          "eta_seconds": args.announce_eta,
                          "source": args.announce_source}, default=str))
        return 0 if ok else 2

    if args.watch and args.watch > 0:
        logging.info("starting watch loop (interval=%ss)", args.watch)
        try:
            while True:
                report = run_once(args)
                if args.print_status:
                    print(json.dumps(report.as_dict(), indent=2, default=str))
                time.sleep(args.watch)
        except KeyboardInterrupt:
            logging.info("watch loop interrupted, exiting")
            return 0

    report = run_once(args)
    if args.print_status:
        print(json.dumps(report.as_dict(), indent=2, default=str))
    return 0 if report.overall_healthy else 1


if __name__ == "__main__":
    raise SystemExit(main())
