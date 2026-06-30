#!/usr/bin/env python3
"""
spirent_tool.py -- CLI wrapper around stcrestclient for Spirent TestCenter automation.
Called directly by the /SPIRENT agent command (like bgp_tool.py for /BGP).

Usage:
    python3 spirent_tool.py connect [--session-name NAME]
    python3 spirent_tool.py reserve
    python3 spirent_tool.py create-stream --vlan VLAN_ID [--dst-mac MAC] [--src-mac MAC]
                                          [--dst-ip IP] [--src-ip IP] [--rate-mbps RATE]
                                          [--frame-size SIZE] [--name NAME] [--protocol PROTO]
    python3 spirent_tool.py start [--stream-name NAME]   # NAME -> flip that StreamBlock.Active=TRUE then GeneratorStart; no name -> GeneratorStart as-is
    python3 spirent_tool.py stop  [--stream-name NAME]   # NAME -> flip that StreamBlock.Active=FALSE (other streams keep running); no name -> GeneratorStop (all)
    python3 spirent_tool.py release
    python3 spirent_tool.py stats [--json]
    python3 spirent_tool.py cleanup
    python3 spirent_tool.py list-sessions
    python3 spirent_tool.py status

    # BGP Protocol Emulation (Phase 1+)
    python3 spirent_tool.py create-device --ip IP --gateway GW [--vlan VLAN] [--name NAME]
    python3 spirent_tool.py bgp-peer --device-name NAME --as AS --dut-as DUT_AS [--neighbor IP]
    python3 spirent_tool.py bgp-status [--device-name NAME] [--json]
    python3 spirent_tool.py list-devices

Requires: pip install stcrestclient
Config:   ~/.spirent_config.json
State:    ~/SCALER/SPIRENT/sessions/
"""

import argparse
import contextlib
import fcntl
import ipaddress
import json
import os
import re
import struct
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

CONFIG_PATH = os.path.expanduser("~/.spirent_config.json")
SESSION_DIR = os.path.expanduser("~/SCALER/SPIRENT/sessions")
STATS_DIR = os.path.expanduser("~/SCALER/SPIRENT/stats")
NDP_SAFE_RATE_PPS = 2

# Session persistence (Lab Server crash post-mortem 2026-03-03)
MAX_SESSION_RETRIES = 3
SESSION_RETRY_BACKOFF = 10
FIXED_SESSION_NAME = "dn_spirent_main"
FALLBACK_SESSION_PREFIX = "dn_spirent_fb"
MAX_TOTAL_SESSION_ATTEMPTS = 5

# HTTP timeout for ALL StcHttp connections (Lab Server resilience 2026-03-05)
STC_HTTP_TIMEOUT = 60
STC_HEALTH_TIMEOUT = 15
STC_MAX_FALLBACK_NAMES = 3

# Connection cache: reuse StcHttp within same process (avoids redundant REST connections
# when a command calls get_stc() multiple times, or internal helpers need the stc handle).
_stc_cache = {"stc": None, "sess": None, "server": None}


class SpirentSessionError(Exception):
    """Raised when we cannot safely bind to the Lab Server session.

    Callers should catch this and present the message to the user rather than
    silently creating a new BLL subprocess (which wipes port reservation,
    emulated devices, and running streams).
    """


# F3: REST rate limiter (token bucket).  Lab Server's stcweb python service
# handles REST traffic serially -- sustained rates above ~10 req/s from the
# SAME user add queuing latency + make the launcher ragged.  When the
# orchestrator forks many short-lived subprocess calls, they all want to
# punch through at once.  This token bucket throttles each process so we
# don't DDOS the server.
_rate_bucket = {"tokens": 0.0, "last": 0.0}
_rate_lock = threading.Lock()
REST_RATE_PER_SEC = float(os.environ.get("SPIRENT_REST_RATE", "10"))
REST_RATE_BURST = float(os.environ.get("SPIRENT_REST_BURST", "15"))


def _rest_throttle():
    """Block until at least one REST token is available.

    Cost is ~0.1s per call at the default 10 req/s.  Opt-out by exporting
    ``SPIRENT_REST_RATE=0`` or ``SPIRENT_REST_BURST=0`` (debugging only).
    """
    if REST_RATE_PER_SEC <= 0 or REST_RATE_BURST <= 0:
        return
    with _rate_lock:
        now = time.monotonic()
        last = _rate_bucket["last"] or now
        _rate_bucket["tokens"] = min(
            REST_RATE_BURST,
            _rate_bucket["tokens"] + (now - last) * REST_RATE_PER_SEC,
        )
        _rate_bucket["last"] = now
        if _rate_bucket["tokens"] < 1.0:
            wait = (1.0 - _rate_bucket["tokens"]) / REST_RATE_PER_SEC
            time.sleep(wait)
            _rate_bucket["tokens"] = 0.0
            _rate_bucket["last"] = time.monotonic()
        else:
            _rate_bucket["tokens"] -= 1.0


# ---------------------------------------------------------------------------
# Silent-swallow forensics (SW-xxx audit, 2026-04)
# ---------------------------------------------------------------------------
# This file has ~160 broad-except handlers.  The vast majority are defensive
# recovery around STC's REST SDK, which throws very liberally on perfectly
# normal "child not present yet" / "handle just ended" cases -- removing them
# would destabilise the tool.  But when something really does go wrong
# (disk-full on a session save, REST timeout on a critical create, a
# permission error on heal --deep) a bare ``pass`` leaves zero forensic trail
# and the bug looks like silence.
#
# ``_swallowed()`` preserves the swallowing behaviour (defensive recovery
# stays intact) AND gives us an opt-in forensic breadcrumb.  Enable with
# ``SPIRENT_TOOL_DEBUG=1`` to write one line per silenced exception to
# /tmp/spirent_tool_swallowed.log.  Default is off -> zero runtime cost.
_SWALLOWED_LOG = "/tmp/spirent_tool_swallowed.log"
_SWALLOWED_ENABLED = os.environ.get("SPIRENT_TOOL_DEBUG", "") not in ("", "0", "false", "False")


def _swallowed(exc, context=""):
    """Log a silently-handled exception (opt-in via SPIRENT_TOOL_DEBUG=1).

    The caller still swallows -- this helper never re-raises and never
    changes control flow.  Safe to call from any cleanup/recovery path:
    if even the log write fails the helper silently returns so the caller
    keeps its original defensive behaviour.
    """
    if not _SWALLOWED_ENABLED:
        return
    try:
        with open(_SWALLOWED_LOG, "a") as f:
            f.write(
                f"[{datetime.utcnow().isoformat()}] "
                f"{context or '(no-context)'}: "
                f"{type(exc).__name__}: {str(exc)[:200]}\n"
            )
    except Exception:
        pass


@contextlib.contextmanager
def _session_file_lock(name: str, timeout: float = 30.0):
    """Cross-process advisory lock around a named session file.

    Needed because the orchestrator sometimes spawns several
    ``spirent_tool.py`` subprocesses back-to-back (e.g. bgp-peer, isis-peer,
    ldp-peer).  Each call does load->modify->save on the same JSON.  Without
    a lock one write can clobber another and the file ends up with stale
    device lists (the old "devices: []" phantom bug).

    The lock file lives next to the session JSON and is only advisory.  The
    whole thing is a cheap fcntl.flock; readers also take it briefly so they
    never observe a half-written file.
    """
    os.makedirs(SESSION_DIR, exist_ok=True)
    lock_path = os.path.join(SESSION_DIR, f"{name}.lock")
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o644)
    try:
        deadline = time.monotonic() + timeout
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise TimeoutError(
                        f"Could not acquire session lock {lock_path} within {timeout}s "
                        "(another spirent_tool.py invocation is holding it)"
                    )
                time.sleep(0.05)
        yield
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)

try:
    from stcrestclient import stchttp
except ImportError:
    print("ERROR: stcrestclient not installed. Run: pip3 install stcrestclient")
    sys.exit(1)

# Shared validator primitives (canonical home: scaler/scaler/validators.py).
# Used by /TEST orchestrators AND /SPIRENT here. Import is path-safe: the
# module is run as a script from various working directories, so we add the
# repo `scaler/` and the live `~/SCALER/` parent to sys.path before importing.
def _import_validators():
    candidate_roots = []
    here = Path(__file__).resolve().parent
    candidate_roots.append(here.parent)
    candidate_roots.append(Path(os.path.expanduser("~/SCALER")))
    workspace_scaler = Path("/home/dn/drivenets-topology-studio/scaler")
    if workspace_scaler.exists():
        candidate_roots.append(workspace_scaler)
    for root in candidate_roots:
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
    try:
        from scaler.validators import poll_until, ValidationResult
        return poll_until, ValidationResult
    except ImportError:
        return None, None


poll_until, ValidationResult = _import_validators()
if poll_until is None:
    print("[WARN] scaler.validators not importable -- /SPIRENT will fall back to legacy waits.",
          file=sys.stderr)


def load_config():
    if not os.path.exists(CONFIG_PATH):
        print(f"ERROR: Config file not found: {CONFIG_PATH}")
        print("Run /SPIRENT setup to create it.")
        sys.exit(1)
    with open(CONFIG_PATH) as f:
        return json.load(f)


def save_session(session_data):
    """Atomic, lock-protected write of a session file (F3).

    The file lock prevents torn reads when multiple ``spirent_tool.py``
    processes mutate the same session.  ``os.replace`` keeps the write
    atomic on POSIX so readers never see a partial JSON blob.
    """
    os.makedirs(SESSION_DIR, exist_ok=True)
    session_id = session_data.get("session_name", "default")
    path = os.path.join(SESSION_DIR, f"{session_id}.json")
    tmp_path = path + ".tmp"
    with _session_file_lock(session_id):
        with open(tmp_path, "w") as f:
            json.dump(session_data, f, indent=2)
        os.replace(tmp_path, path)
    return path


def load_session(session_name=None):
    """Load session file under advisory lock (F3).

    Uses FIXED_SESSION_NAME when session_name is None.  No fallback search.
    Held lock is brief -- just long enough to avoid racing with an
    in-flight save_session().
    """
    name = session_name or FIXED_SESSION_NAME
    path = os.path.join(SESSION_DIR, f"{name}.json")
    if not os.path.exists(path):
        return None
    with _session_file_lock(name, timeout=10.0):
        with open(path) as f:
            return json.load(f)


def _stc_http(config):
    """Create a StcHttp instance with timeout.  Applies REST rate-limit
    (F3) to all new HTTP connections -- a new ``StcHttp`` kicks off
    session-list/auth traffic, so we count it like any other REST call.
    """
    _rest_throttle()
    return stchttp.StcHttp(
        config["lab_server"],
        port=config.get("lab_server_port", 80),
        timeout=STC_HTTP_TIMEOUT,
    )


def _health_probe(config):
    """Fast health check: GET /stcapi/sessions with STC_HEALTH_TIMEOUT.
    Returns (ok, sessions_list_or_error_msg)."""
    import urllib.request
    base = f"http://{config['lab_server']}:{config.get('lab_server_port', 80)}"
    try:
        resp = urllib.request.urlopen(f"{base}/stcapi/sessions", timeout=STC_HEALTH_TIMEOUT)
        body = json.loads(resp.read().decode())
        return True, body
    except Exception as e:
        return False, str(e)


def _kill_zombie_session(config, session_id):
    """Force-kill a zombie session that exists in REST list but can't be joined.
    Attempts graceful BGP protocol stop before killing to minimize DUT-side disruption."""
    import urllib.request

    _try_graceful_bgp_stop(config, session_id)

    encoded = session_id.replace(" ", "%20")
    base = f"http://{config['lab_server']}:{config.get('lab_server_port', 80)}"
    try:
        req = urllib.request.Request(f"{base}/stcapi/sessions/{encoded}", method="DELETE")
        urllib.request.urlopen(req, timeout=STC_HEALTH_TIMEOUT)
        print(f"  Zombie session deleted via REST: {session_id}")
        return True
    except Exception:
        pass
    try:
        stc_tmp = _stc_http(config)
        stc_tmp.new_session(
            user_name=config.get("user_name", "dn_spirent"),
            session_name=session_id.split(" - ")[0],
            kill_existing=True,
        )
        stc_tmp.end_session(end_tcsession=True)
        print(f"  Zombie session killed via recreate+end: {session_id}")
        return True
    except Exception as e2:
        print(f"  WARNING: Could not kill zombie session {session_id}: {e2}")
        return False


def _try_graceful_bgp_stop(config, session_id):
    """Best-effort: join a zombie session briefly to stop BGP protocols before killing it.
    Prevents DUT-side NOTIFICATION/reset from abrupt TCP teardown."""
    try:
        stc_tmp = _stc_http(config)
        parts = session_id.split(" - ")
        stc_tmp.join_session(parts[0] if len(parts) == 1 else session_id)
        project = stc_tmp.get("system1", "children-Project")
        if project:
            devs = stc_tmp.get(project.split()[0], "children-EmulatedDevice") or ""
            if devs.strip():
                stc_tmp.perform("DeviceStopCommand", DeviceList=devs)
                time.sleep(1)
                print(f"  Graceful BGP stop on zombie {session_id} before kill")
    except Exception:
        pass


def _clean_stale_local_sessions(config):
    """Mark local session files inactive if their server-side session no longer exists."""
    try:
        stc_tmp = _stc_http(config)
        server_sessions = set(stc_tmp.sessions())
    except Exception:
        return
    for sf in Path(SESSION_DIR).glob("*.json"):
        try:
            with open(sf) as f:
                sd = json.load(f)
            if sd.get("active") and sd.get("session_id_on_server") not in server_sessions:
                sd["active"] = False
                sd["_stale_reason"] = "server session gone"
                with open(sf, "w") as f:
                    json.dump(sd, f, indent=2)
        except Exception as e:
            _swallowed(e, f"_check_remote_session_state sync {sf.name}")


def _validate_handles(stc, sess):
    """Verify port_handle and project_handle are still valid in the BLL.
    Returns (ok, error_msg). Clears handles from session if stale."""
    port = sess.get("port_handle")
    project = sess.get("project_handle")
    issues = []
    if project:
        try:
            stc.get(project, "Name")
        except Exception:
            issues.append(f"project_handle '{project}' is stale (BLL restarted?)")
            sess["project_handle"] = None
    if port:
        try:
            stc.get(port, "Name")
        except Exception:
            issues.append(f"port_handle '{port}' is stale (BLL restarted?)")
            sess["port_handle"] = None
            sess["port_reserved"] = False
    if issues:
        save_session(sess)
        return False, "; ".join(issues)
    _reconcile_devices(stc, sess)
    return True, None


def _reconcile_devices(stc, sess):
    """Detect orphan STC devices not tracked in session JSON and stale JSON entries.
    Adopts orphans into session or warns about mismatches."""
    project = sess.get("project_handle")
    if not project:
        return
    try:
        stc_devs_raw = stc.get(project, "children-EmulatedDevice") or ""
        stc_handles = stc_devs_raw.split() if stc_devs_raw.strip() else []
    except Exception:
        return

    json_handles = {d["handle"] for d in sess.get("devices", []) if d.get("handle")}
    json_names = {d["name"] for d in sess.get("devices", [])}

    orphans = [h for h in stc_handles if h not in json_handles]
    stale_json = [d for d in sess.get("devices", [])
                  if d.get("handle") and d["handle"] not in stc_handles]

    if orphans:
        for oh in orphans:
            try:
                name = stc.get(oh, "Name")
                ip = "unknown"
                try:
                    ipv4 = stc.get(oh, "children-Ipv4If")
                    if ipv4:
                        ip = stc.get(ipv4.split()[0], "Address")
                except Exception:
                    pass
                print(f"[WARN] Orphan STC device '{name}' ({oh}, ip={ip}) not in session JSON")
                if name not in json_names:
                    sess.setdefault("devices", []).append({
                        "name": name, "handle": oh, "ip": ip,
                        "adopted": True, "adopted_at": datetime.utcnow().isoformat(),
                    })
                    print(f"[INFO] Adopted orphan '{name}' into session")
            except Exception:
                print(f"[WARN] Orphan handle {oh} exists in STC but can't read its Name")

    if stale_json:
        for sd in stale_json:
            print(f"[WARN] Session device '{sd['name']}' ({sd['handle']}) missing from STC -- removing from JSON")
        sess["devices"] = [d for d in sess.get("devices", [])
                           if d.get("handle") in stc_handles or not d.get("handle")]

    if orphans or stale_json:
        save_session(sess)


def _require_ready(config):
    """Combined validation (F4-hardened): load session, verify port, JOIN
    the BLL (never create), check handles are still alive, and detect BLL
    respawn (port Location mismatch).

    Returns (stc, sess) or sys.exit on failure.  A single REST connection
    covers the whole check.  Error messages now point at ``heal`` first
    (non-destructive) and only fall back to ``connect --force-new`` as a
    last resort.
    """
    sess = load_session()
    if not sess or not sess.get("port_reserved"):
        print("ERROR: Port not reserved. Run 'spirent_tool.py connect' then 'reserve' first.")
        sys.exit(1)
    ok, err = _validate_session(config, sess)
    if not ok:
        print(f"ERROR: {err}")
        print("[INFO] Try: spirent_tool.py heal   (rebuilds local view from live BLL)")
        sys.exit(1)
    try:
        stc, _ = get_stc(config, force_new=False, allow_create=False)
    except SpirentSessionError as e:
        print(f"[ERROR] {e}")
        sys.exit(2)
    ok, err = _validate_handles(stc, sess)
    if not ok:
        print(f"[WARN] Stale handles detected: {err}")
        print("[INFO] BLL was probably respawned.  Recommended recovery:")
        print("       1) spirent_tool.py heal            # resync local JSON with live BLL")
        print("       2) spirent_tool.py reserve         # re-attach port (if heal cleared it)")
        print("       3) re-provision anything heal reports as dropped")
        print("       (only use 'connect --force-new' as a last resort -- it kills the BLL)")
        sys.exit(1)

    # BLL-respawn trip-wire: port_handle looks good but Location no longer
    # matches our configured port => this is a different BLL subprocess.
    port = sess.get("port_handle")
    configured_loc = config.get("port_location")
    if port and configured_loc:
        try:
            live_loc = stc.get(port, "Location") or ""
            if live_loc and live_loc != configured_loc:
                print(f"[ERROR] BLL port_handle '{port}' Location='{live_loc}' does not match "
                      f"configured '{configured_loc}'.")
                print("[INFO] BLL was respawned with a different port.  Run:")
                print("       spirent_tool.py heal   # rebind to the correct live handles")
                sys.exit(1)
        except Exception:
            pass

    return stc, sess


def _require_device(stc, sess, name):
    """Resolve an emulated-device handle by NAME before a device-specific
    operation (F4).

    Why: the old flow passed a cached handle straight into ``stc.create(...,
    under=device_handle)`` which raises ``500 Lost network connection`` when
    the handle is stale -- a very misleading error.  Here we (a) consult the
    cached JSON, (b) verify via ``stc.get(handle, 'Name')`` that it's alive,
    and (c) fall back to a ``children-EmulatedDevice`` scan if the cache is
    wrong.  Callers get back a live handle or a clean exit with actionable
    instructions.
    """
    cached = next((d for d in (sess.get("devices") or []) if d.get("name") == name), None)
    if cached and cached.get("handle"):
        try:
            live_name = stc.get(cached["handle"], "Name")
            if live_name == name:
                return cached["handle"], cached
        except Exception:
            # Cached handle stale -- fall through to BLL scan
            pass

    project = sess.get("project_handle")
    if not project:
        print(f"ERROR: No project handle in session. Run 'spirent_tool.py heal'.")
        sys.exit(1)
    try:
        dev_handles = (stc.get(project, "children-EmulatedDevice") or "").split()
    except Exception as e:
        print(f"ERROR: BLL unreachable while scanning devices: {e}")
        print("[INFO] Try: spirent_tool.py heal")
        sys.exit(1)

    for dh in dev_handles:
        try:
            if stc.get(dh, "Name") == name:
                # Update cache opportunistically
                if cached:
                    cached["handle"] = dh
                    cached["_healed_at"] = datetime.utcnow().isoformat()
                else:
                    sess.setdefault("devices", []).append({
                        "name": name, "handle": dh, "adopted": True,
                        "adopted_at": datetime.utcnow().isoformat(),
                    })
                save_session(sess)
                return dh, {"name": name, "handle": dh}
        except Exception:
            continue

    # No such device anywhere
    live_names = []
    for dh in dev_handles:
        try:
            live_names.append(stc.get(dh, "Name"))
        except Exception:
            pass
    print(f"ERROR: Device '{name}' not found in BLL.")
    print(f"       BLL currently has these emulated devices: {live_names or '(none)'}")
    print(f"       Local JSON lists: {[d.get('name') for d in (sess.get('devices') or [])]}")
    print("[INFO] Either create the device first, or run 'spirent_tool.py heal' if you")
    print("       believe it should exist.")
    sys.exit(1)


def _retry_rest(fn, retries=3, backoff=2, dont_retry=None, max_total=5):
    """Retry a REST call with exponential backoff on transient failures.
    dont_retry: callable(e) -> bool; if True, raise immediately without retry.
    max_total: hard cap on total attempts per invocation (prevents retry storm)."""
    dont_retry = dont_retry or (lambda e: False)
    retries = min(retries, max_total)
    for attempt in range(retries):
        try:
            return fn()
        except Exception as e:
            if dont_retry(e):
                raise
            if attempt == retries - 1:
                raise
            time.sleep(backoff * (attempt + 1))


def _validate_session(config, sess):
    """Verify local session exists on server. Mark inactive if not. Returns (success, error_msg)."""
    if not sess or not sess.get("active"):
        return False, "No active session"
    sid = sess.get("session_id_on_server")
    if not sid:
        return False, "Session missing session_id_on_server"
    try:
        stc_tmp = _stc_http(config)
        server_sessions = set(stc_tmp.sessions())
    except Exception as e:
        return False, f"Lab Server unreachable: {e}"
    if sid not in server_sessions:
        sess["active"] = False
        sess["_stale_reason"] = "server session gone"
        save_session(sess)
        return False, f"Session {sid} no longer on server (marked inactive)"
    return True, None


def get_stc(config, session_name=None, force_new=False, allow_create=None):
    """Connect to the Lab Server BLL.

    BLL lifecycle fact: each session on the Lab Server is a separate
    TestCenterSession subprocess (~480 MB RSS).  When that process dies or is
    killed, ALL in-memory state (port reservations, emulated devices, streams)
    is lost.  The REST tier keeps responding but any handle we cached becomes
    stale.  That used to cause silent session destruction because Phase 1
    (join) fall-through executed Phase 2 (create a fresh BLL), wiping the
    user's devices/streams/port reservation.

    New behaviour (F1):
    - ``allow_create=False`` (default when ``force_new`` is False): JOIN-ONLY.
      Raise ``SpirentSessionError`` with actionable recovery if join fails so
      the caller sees "session is gone" instead of getting an empty BLL.
    - ``allow_create=True`` (or ``force_new=True``): legacy behaviour, will
      create a fresh BLL if no joinable session exists.  ``connect
      --create-if-missing`` sets this.

    Resilient pieces still active:
    - StcHttp cache inside the process (avoids redundant HTTP connections)
    - Health probe (catches dead stcweb before STC API call)
    - HTTP timeout (no infinite hangs)
    - Fallback session names on primary zombie
    - Handle validation detects stale port/project/device handles
    - Hard cap at ``MAX_TOTAL_SESSION_ATTEMPTS`` total attempts per call
    """
    # Legacy callers pass ``force_new``; default ``allow_create`` mirrors it to
    # preserve behaviour where an explicit ``force_new=True`` is a clear
    # "recreate" intent.  All other paths get JOIN-ONLY.
    if allow_create is None:
        allow_create = bool(force_new)

    if not force_new and _stc_cache["stc"] is not None and _stc_cache["server"] == config.get("lab_server"):
        try:
            _stc_cache["stc"].get("system1", "Name")
            return _stc_cache["stc"], _stc_cache["sess"]
        except Exception:
            _stc_cache["stc"] = None

    user = config.get("user_name", "dn_spirent")
    attempt_count = [0]

    def _inc_and_check():
        attempt_count[0] += 1
        if attempt_count[0] > MAX_TOTAL_SESSION_ATTEMPTS:
            print(f"[ERROR] Session attempt limit reached ({MAX_TOTAL_SESSION_ATTEMPTS}). Stopping.")
            sys.exit(1)
        print(f"[WARN] Session attempt {attempt_count[0]}/{MAX_TOTAL_SESSION_ATTEMPTS}...")

    # Phase 0: Health probe (catches dead stcweb before we block on STC API)
    ok, result = _health_probe(config)
    if not ok:
        print(f"[ERROR] Lab Server health probe failed: {result}")
        print("[INFO] stcweb may be crashed. Try: ssh to Lab Server -> docker exec spirent-labserver supervisorctl restart stcweb")
        sys.exit(1)
    server_sessions = result if isinstance(result, list) else []

    # Build candidate session names: primary first, then fallbacks
    names_to_try = [FIXED_SESSION_NAME]
    for i in range(STC_MAX_FALLBACK_NAMES):
        names_to_try.append(f"{FALLBACK_SESSION_PREFIX}_{i}")

    def _cache_and_return(stc_obj, sess_obj):
        _stc_cache["stc"] = stc_obj
        _stc_cache["sess"] = sess_obj
        _stc_cache["server"] = config.get("lab_server")
        return stc_obj, sess_obj

    # Phase 1: Join path (fast, no BLL spawn) -- try each name
    join_errors = []
    if not force_new:
        for name in names_to_try:
            sess = load_session(name)
            if sess and sess.get("active") and sess.get("session_id_on_server"):
                sid = sess["session_id_on_server"]
                if sid not in server_sessions:
                    sess["active"] = False
                    sess["_stale_reason"] = "server session gone (health probe)"
                    save_session(sess)
                    join_errors.append(f"{name}: server session gone")
                    continue
                try:
                    stc = _stc_http(config)
                    stc.join_session(sid)
                    sess["last_joined"] = datetime.utcnow().isoformat()
                    sess["join_count"] = sess.get("join_count", 0) + 1
                    return _cache_and_return(stc, sess)
                except Exception as e:
                    print(f"[WARN] Join failed for {name}: {e}")
                    join_errors.append(f"{name}: {e}")

    # Also try to discover a server session that we don't yet have a local
    # JSON for -- lets the user recover after accidentally deleting the
    # session file (or on a fresh clone).  Whenever we recover via this path
    # we IMMEDIATELY heal the JSON from live BLL state so the caller never
    # sees a skeleton session (F2 auto-resync).
    if not force_new and not join_errors:
        for sid in server_sessions:
            if not isinstance(sid, str):
                continue
            if sid.endswith(f" - {user}") or sid.split(" - ")[0] in names_to_try:
                try:
                    stc = _stc_http(config)
                    stc.join_session(sid)
                    name = sid.split(" - ")[0]
                    sess = _make_sess_data(config, name, sid, {})
                    sess["_discovered_via"] = "server_scan"
                    try:
                        _heal_session(stc, sess)
                        print(f"[OK] Joined discovered server session: {sid} (auto-healed)")
                    except Exception as heal_err:
                        save_session(sess)
                        print(f"[OK] Joined discovered server session: {sid}")
                        print(f"[WARN] auto-heal failed -- run 'spirent_tool.py heal' manually: {heal_err}")
                    return _cache_and_return(stc, sess)
                except Exception as e:
                    join_errors.append(f"discover {sid}: {e}")

    # F1: bail out here unless creation was explicitly requested.  The legacy
    # silent fall-through into Phase 2 is what caused the BLL to get respawned
    # and wipe the user's state.
    if not allow_create:
        raise SpirentSessionError(
            "JOIN-only mode: no joinable Lab Server session found and "
            "--create-if-missing was not passed.\n"
            "  server sessions: " + (", ".join(server_sessions) if server_sessions else "(none)") + "\n"
            "  join errors    : " + ("; ".join(join_errors) if join_errors else "(none attempted)") + "\n"
            "Next steps:\n"
            "  - If the BLL was respawned but you have local state, run: "
            "spirent_tool.py heal\n"
            "  - If you really want a fresh session, run: "
            "spirent_tool.py connect --create-if-missing\n"
            "  - If stcweb looks stuck, run: spirent_tool.py recover --level stcweb"
        )

    # Phase 2: Create path -- try primary, then fallback names on zombie
    for name in names_to_try:
        session_id = f"{name} - {user}"
        _inc_and_check()
        stc = _stc_http(config)

        for create_attempt in range(MAX_SESSION_RETRIES):
            try:
                stc.new_session(user_name=user, session_name=name, kill_existing=force_new)
                sess_data = _make_sess_data(config, name, session_id, {})
                sess_data["creation_attempts"] = 1
                print(f"[OK] Created session: {session_id}")
                return _cache_and_return(stc, sess_data)
            except Exception as e:
                err_str = str(e).lower()
                if "409" in err_str or "already exists" in err_str or "conflict" in err_str:
                    try:
                        stc2 = _stc_http(config)
                        stc2.join_session(session_id)
                        print(f"  Rejoined existing session: {session_id}")
                        sess = load_session(name) or {}
                        sess_data = _make_sess_data(config, name, session_id, sess)
                        return _cache_and_return(stc2, sess_data)
                    except Exception:
                        print(f"  Zombie detected on '{name}' -- killing...")
                        _kill_zombie_session(config, session_id)
                        time.sleep(SESSION_RETRY_BACKOFF)
                        _inc_and_check()
                        continue
                elif "timeout" in err_str or "timed out" in err_str:
                    print(f"  [WARN] Timeout on '{name}' -- trying fallback name...")
                    break
                if create_attempt == MAX_SESSION_RETRIES - 1:
                    print(f"  [WARN] All retries exhausted for '{name}'")
                    break
                time.sleep(SESSION_RETRY_BACKOFF * (create_attempt + 1))
        else:
            continue
        continue

    print("[ERROR] All session names exhausted. Lab Server may need full restart.")
    print("[INFO] Try: ssh Lab Server -> docker restart spirent-labserver")
    sys.exit(1)


def _make_sess_data(config, name, session_id, existing):
    """Build session data dict with tracking fields."""
    return {
        "session_name": name,
        "session_id_on_server": session_id,
        "lab_server": config["lab_server"],
        "chassis_ip": config["chassis_ip"],
        "port_location": config["port_location"],
        "active": True,
        "created": existing.get("created") or datetime.utcnow().isoformat(),
        "last_joined": datetime.utcnow().isoformat(),
        "join_count": existing.get("join_count", 0) + 1,
        "creation_attempts": existing.get("creation_attempts", 0),
        "last_error": None,
        "streams": existing.get("streams", []),
        "devices": existing.get("devices", []),
        "port_reserved": existing.get("port_reserved", False),
        "project_handle": existing.get("project_handle"),
        "port_handle": existing.get("port_handle"),
    }


# ────────────────────────────────────────────
# Subcommands
# ────────────────────────────────────────────

def cmd_connect(args):
    """Connect to Lab Server -- JOIN-only by default (F1).

    Flags:
        --force-new            Kill existing session and create fresh (legacy).
        --create-if-missing    Create BLL session if nothing to join (explicit opt-in).

    Without either flag: if no joinable session exists, we raise and tell the
    user to run ``heal`` or ``connect --create-if-missing``.  This prevents
    the silent BLL respawn that used to wipe port reservation + devices.
    """
    config = load_config()

    _clean_stale_local_sessions(config)

    force_new = bool(getattr(args, "force_new", False))
    allow_create = force_new or bool(getattr(args, "create_if_missing", False))

    try:
        stc, sess = get_stc(config, force_new=force_new, allow_create=allow_create)
    except SpirentSessionError as e:
        print(f"[ERROR] {e}")
        sys.exit(2)

    if sess.get("project_handle"):
        project = sess["project_handle"]
        # Verify the cached handle is still alive -- if the BLL was respawned,
        # project1 may look valid string-wise but point at nothing.
        try:
            stc.get(project, "Name")
            print(f"Reusing existing project: {project}")
        except Exception:
            print(f"[WARN] Cached project handle '{project}' is stale -- creating new project")
            project = stc.create("project")
            sess["project_handle"] = project
            sess["port_handle"] = None
            sess["port_reserved"] = False
    else:
        project = stc.create("project")
        sess["project_handle"] = project

    save_session(sess)

    print(f"Connected to Lab Server: {config['lab_server']}:{config.get('lab_server_port', 80)}")
    print(f"Session: {sess['session_id_on_server']}")
    print(f"Project: {project}")
    print(json.dumps(sess, indent=2))


def cmd_reserve(args):
    """Reserve the configured Spirent port."""
    config = load_config()
    sess = load_session()
    if not sess or not sess.get("active"):
        print("ERROR: No active session. Run 'connect' first.")
        sys.exit(1)

    stc, sess = get_stc(config)

    project = sess.get("project_handle")
    if not project:
        project = stc.create("project")
        sess["project_handle"] = project

    port_loc = config["port_location"]
    port = sess.get("port_handle")
    if port:
        try:
            live_loc = stc.get(port, "Location")
            if live_loc != port_loc:
                print(f"[WARN] Cached port {port} points to {live_loc}, expected {port_loc}; creating a new port object")
                port = None
        except Exception:
            port = None
    if not port:
        port = stc.create("port", under=project, location=port_loc, useDefaultHost="False")

    try:
        stc.perform("AttachPorts",
                    portList=port,
                    autoConnect="true",
                    RevokeOwner="true")
    except Exception as e:
        if "already reserved" in str(e).lower() or "could not be brought online" in str(e).lower():
            print(f"WARNING: Port attach issue (may already be reserved): {e}")
            print("Continuing with port handle...")
        else:
            raise
    stc.apply()

    try:
        online = stc.get(port, "Online")
        if online and online.lower() != "true":
            all_ports_raw = stc.get(project, "children-Port") or ""
            for candidate in all_ports_raw.split():
                if candidate == port:
                    continue
                try:
                    c_online = stc.get(candidate, "Online")
                    if c_online and c_online.lower() == "true":
                        print(f"[INFO] Port {port} is offline but {candidate} is online (BLL restart detected)")
                        print(f"[INFO] Switching to online port {candidate}")
                        port = candidate
                        break
                except Exception:
                    pass
    except Exception:
        pass

    sess["port_handle"] = port
    sess["port_reserved"] = True
    save_session(sess)

    print(f"Port reserved: {port_loc}")
    print(f"Port handle: {port}")


def _mac_bytes(mac):
    parts = str(mac or "").split(":")
    if len(parts) != 6:
        raise ValueError(f"invalid MAC address: {mac!r}")
    return bytes(int(part, 16) for part in parts)


def _ones_complement_checksum(data):
    if len(data) % 2:
        data += b"\x00"
    total = 0
    for idx in range(0, len(data), 2):
        total += (data[idx] << 8) + data[idx + 1]
        total = (total & 0xFFFF) + (total >> 16)
    return (~total) & 0xFFFF


def _icmpv6_checksum(src_ip, dst_ip, payload):
    src = ipaddress.IPv6Address(src_ip).packed
    dst = ipaddress.IPv6Address(dst_ip).packed
    pseudo = src + dst + struct.pack("!I3xB", len(payload), 58)
    return _ones_complement_checksum(pseudo + payload)


def _icmpv6_na_payload(src_ip, dst_ip, target_ip, target_mac, *, router=False, solicited=False, override=True):
    flags = 0
    if router:
        flags |= 1 << 31
    if solicited:
        flags |= 1 << 30
    if override:
        flags |= 1 << 29
    # Type 136, code 0, checksum filled after pseudo-header calculation.
    option = b"\x02\x01" + _mac_bytes(target_mac)  # Target Link-Layer Address, len=1 (8 bytes).
    payload_wo_csum = struct.pack("!BBH", 136, 0, 0) + struct.pack("!I", flags) + ipaddress.IPv6Address(target_ip).packed + option
    checksum = _icmpv6_checksum(src_ip, dst_ip, payload_wo_csum)
    return struct.pack("!BBH", 136, 0, checksum) + payload_wo_csum[4:]


def _ipv6_packet(src_ip, dst_ip, next_header, payload, hop_limit=255):
    src = ipaddress.IPv6Address(src_ip).packed
    dst = ipaddress.IPv6Address(dst_ip).packed
    header = struct.pack("!IHBB16s16s", 0x60000000, len(payload), next_header, hop_limit, src, dst)
    return header + payload


def _ipv6_unicast_to_solicited_node_mac(ipv6_addr: str) -> str:
    """RFC 4291 / 4861: derive solicited-node multicast L2 MAC from an IPv6.

    The L2 destination MAC for IPv6 solicited-node multicast is 33:33:ff:XX:XX:XX
    where XX:XX:XX are the low 24 bits of the target IPv6. Unsolicited NA frames
    SHOULD use ff02::1 (all-nodes) with L2 33:33:00:00:00:01; solicited NA
    frames use the requester's L2 MAC. We never fall back to L2 broadcast
    (ff:ff:ff:ff:ff:ff) for IPv6 -- that yields malformed frames that most
    routers (including DNOS NDP punt) silently drop.
    """
    try:
        import ipaddress
        ip = ipaddress.IPv6Address(ipv6_addr)
        b = ip.packed
        return "33:33:ff:{:02x}:{:02x}:{:02x}".format(b[13], b[14], b[15])
    except Exception:
        return "33:33:00:00:00:01"


def _safe_icmpv6_dst_mac(dst_ip: str, target_ip: str | None) -> tuple[str, str]:
    """Return (dst_mac, warning_or_empty) for an icmpv6 NA frame.

    Rules (RFC 4861 + DNOS Proxy ARP/NDP design):
      * dst_ip = ff02::1  -> 33:33:00:00:00:01 (all-nodes; canonical unsolicited NA)
      * dst_ip in ff02::1:ff00:0/104 (solicited-node) -> 33:33:ff:XX:XX:XX
      * dst_ip multicast (any other ff..) -> 33:33:LL:LL:LL:LL low 32 bits
      * dst_ip unicast -> rewrite to ff02::1 with multicast L2 (warn caller)
    """
    ip_str = str(dst_ip or "").lower()
    if ip_str in {"ff02::1", "ff02:0:0:0:0:0:0:1"}:
        return "33:33:00:00:00:01", ""
    if ip_str.startswith("ff02::1:ff"):
        return _ipv6_unicast_to_solicited_node_mac(ip_str), ""
    if ip_str.startswith("ff"):
        try:
            import ipaddress
            packed = ipaddress.IPv6Address(ip_str).packed
            return "33:33:{:02x}:{:02x}:{:02x}:{:02x}".format(packed[12], packed[13], packed[14], packed[15]), ""
        except Exception:
            return "33:33:00:00:00:01", "[WARN] could not parse multicast IPv6 dst; defaulting to 33:33:00:00:00:01"
    sol_node_target = target_ip or dst_ip
    return _ipv6_unicast_to_solicited_node_mac(sol_node_target), (
        f"[WARN] icmpv6-na: dst_ip {dst_ip!r} is unicast; "
        "an unsolicited NA MUST use IPv6 multicast (ff02::1) with L2 33:33:00:00:00:01. "
        "Using solicited-node multicast MAC; consider setting --dst-ip ff02::1."
    )


def _create_icmpv6_na_stream(stc, sess, args, stream_name, outer_vlan, inner_vlan_id, frame_size, rate_mbps, load_unit):
    src_mac = args.src_mac or args.target_mac or "00:10:94:00:00:01"
    target_mac = args.target_mac or src_mac
    src_ip = args.src_ip or args.target_ipv6
    target_ip = args.target_ipv6 or src_ip
    dst_ip = args.dst_ip or "ff02::1"
    solicited = bool(args.icmpv6_na_solicited)
    if solicited:
        if str(dst_ip).lower().startswith("ff"):
            raise ValueError(
                "icmpv6-na solicited NA requires a unicast --dst-ip copied from the NS sender; "
                "DNOS rejects solicited NA frames sent to multicast destinations."
            )
        if not args.dst_mac:
            raise ValueError(
                "icmpv6-na solicited NA requires --dst-mac set to the requester/IRB MAC. "
                "Without it Spirent cannot build the unicast NA reply that DNOS proxy-NDP learns."
            )
    if args.dst_mac:
        dst_mac = args.dst_mac
        dst_mac_warning = ""
    else:
        dst_mac, dst_mac_warning = _safe_icmpv6_dst_mac(dst_ip, target_ip)
    if dst_mac_warning:
        print(dst_mac_warning)
    if dst_mac.lower() == "ff:ff:ff:ff:ff:ff":
        raise ValueError(
            "icmpv6-na dst_mac=ff:ff:ff:ff:ff:ff is invalid for IPv6. "
            "Set --dst-ip ff02::1 (unsolicited) or pass --dst-mac 33:33:... explicitly."
        )
    if not src_ip or not target_ip:
        raise ValueError("--protocol icmpv6-na requires --src-ip and/or --target-ipv6")

    payload = _icmpv6_na_payload(
        src_ip,
        dst_ip,
        target_ip,
        target_mac,
        router=bool(args.icmpv6_na_router),
        solicited=solicited,
        override=bool(args.icmpv6_na_override),
    )
    ipv6_payload_hex = _ipv6_packet(src_ip, dst_ip, 58, payload).hex()

    vlan_xml = ""
    if outer_vlan is not None:
        vlan_xml = f'<vlans><Vlan name="outer"><id>{outer_vlan}</id><pri>0</pri><cfi>0</cfi></Vlan>'
        if inner_vlan_id is not None:
            vlan_xml += f'<Vlan name="inner"><id>{inner_vlan_id}</id><pri>0</pri><cfi>0</cfi></Vlan>'
        vlan_xml += '</vlans>'

    frame_xml = (
        '<frame><config><pdus>'
        f'<pdu name="eth1" pdu="ethernet:EthernetII">'
        f'<dstMac>{dst_mac}</dstMac><srcMac>{src_mac}</srcMac>'
        f'{vlan_xml}'
        f'<etherType>86dd</etherType>'
        f'</pdu>'
        f'<pdu name="ipv6_nd_na" pdu="custom:Custom"><pattern>{ipv6_payload_hex}</pattern></pdu>'
        '</pdus></config></frame>'
    )
    sb = stc.create("StreamBlock", under=sess["port_handle"],
                    FixedFrameLength=str(frame_size),
                    Name=stream_name,
                    insertSig="true")
    stc.config(sb, FrameConfig=frame_xml, Load=str(rate_mbps), LoadUnit=load_unit)
    return sb, {
        "src_mac": src_mac,
        "dst_mac": dst_mac,
        "src_ip": src_ip,
        "dst_ip": dst_ip,
        "target_ipv6": target_ip,
        "target_mac": target_mac,
        "icmpv6_type": 136,
        "icmpv6_code": 0,
        "icmpv6_na_flags": {
            "router": bool(args.icmpv6_na_router),
            "solicited": bool(args.icmpv6_na_solicited),
            "override": bool(args.icmpv6_na_override),
        },
        "packet_method": "native_frameconfig_custom_ipv6_icmpv6_na",
        "payload_hex": ipv6_payload_hex,
    }


def cmd_create_stream(args):
    """Create a VLAN-tagged traffic stream on the reserved port."""
    config = load_config()
    stc, sess = _require_ready(config)

    stream_name = args.name or f"stream_{len(sess.get('streams', []))}"

    port_handle = sess["port_handle"]
    reuse_policy = (getattr(args, "reuse_policy", None) or "error").lower()
    existing_sbs = stc.get(port_handle, 'children-StreamBlock')
    if existing_sbs:
        for sb_h in existing_sbs.split():
            try:
                if stc.get(sb_h, 'name') == stream_name:
                    if reuse_policy == "reuse":
                        print(f"[OK] Stream '{stream_name}' already exists -- reusing (no stc.apply)")
                        return
                    if reuse_policy == "replace":
                        print(f"[INFO] Stream '{stream_name}' already exists -- deleting before recreating (reuse-policy=replace)")
                        try:
                            stc.delete(sb_h)
                        except Exception as exc:
                            raise RuntimeError(
                                f"Failed to delete pre-existing stream '{stream_name}': {exc}"
                            ) from exc
                        sess["streams"] = [
                            s for s in sess.get("streams", [])
                            if s.get("name") != stream_name
                        ]
                        break
                    raise RuntimeError(
                        f"Stream '{stream_name}' already exists on the reserved port. "
                        "Silent reuse is disabled because the existing StreamBlock may carry "
                        "stale encoding from a previous create-stream call. Resolve by one of: "
                        "(a) `--reuse-policy replace` to delete and recreate with the requested "
                        "encoding, (b) `--reuse-policy reuse` to keep the existing block as-is, "
                        "(c) remove-stream --name "
                        f"'{stream_name}' first. See spirent_create_stream descriptor for details."
                    )
            except RuntimeError:
                raise
            except Exception:
                pass

    frame_size = int(args.frame_size) if args.frame_size else 128
    if (args.protocol or "").lower() == "l2" and frame_size < 128:
        print(
            f"[INFO] L2 stream frame-size {frame_size} is too small for "
            "signed STC frames; using 128 bytes"
        )
        frame_size = 128
    proto_lower = (args.protocol or "").lower()

    load_unit = "MEGABITS_PER_SECOND"
    if args.rate_pps:
        load_unit = "FRAMES_PER_SECOND"
        rate_mbps = float(args.rate_pps)
    elif proto_lower == "icmpv6-na" and not args.rate_mbps:
        load_unit = "FRAMES_PER_SECOND"
        rate_mbps = float(NDP_SAFE_RATE_PPS)
        print(f"[INFO] icmpv6-na defaulting to CPRL-safe {NDP_SAFE_RATE_PPS} fps; pass --rate-pps or --rate-mbps to override")
    else:
        rate_mbps = float(args.rate_mbps) if args.rate_mbps else 1.0

    stream_rate_gbps = (rate_mbps / 1000.0) if load_unit == "MEGABITS_PER_SECOND" else (rate_mbps * frame_size * 8) / 1e9
    _preflight_capacity_warn(config, sess, stream_rate_gbps=stream_rate_gbps)

    no_qinq = getattr(args, "no_qinq", False)
    excl_raw = getattr(args, "exclude_inner_vlans", None)
    excl_set = set(int(v) for v in excl_raw.split(",") if v.strip()) if excl_raw else None
    outer_vlan, inner_vlan_id = _resolve_qinq_vlans(
        config, sess, args.vlan, getattr(args, "inner_vlan", None), no_qinq=no_qinq, exclude_inner=excl_set
    )
    if inner_vlan_id is not None:
        print(f"[INFO] Auto Q-in-Q: outer={outer_vlan} inner={inner_vlan_id}")

    port_handle = sess["port_handle"]

    packet_info = {}
    if proto_lower == "icmpv6-na":
        sb, packet_info = _create_icmpv6_na_stream(
            stc, sess, args, stream_name, outer_vlan, inner_vlan_id,
            frame_size, rate_mbps, load_unit
        )
        src_mac = packet_info["src_mac"]
        dst_mac = packet_info["dst_mac"]
    else:
        sb = stc.create("streamBlock", under=port_handle,
                         insertSig="true",
                         frameLengthMode="FIXED",
                         FixedFrameLength=str(frame_size),
                         load=str(rate_mbps),
                         loadUnit=load_unit,
                         name=stream_name)

        src_mac = args.src_mac or "00:10:94:00:00:01"
        dst_mac = args.dst_mac or "ff:ff:ff:ff:ff:ff"

        eth = stc.get(sb, "children-ethernet:EthernetII")
        if eth:
            stc.config(eth, srcMac=src_mac, dstMac=dst_mac)
        else:
            eth = stc.create("ethernet:EthernetII", under=sb,
                              srcMac=src_mac, dstMac=dst_mac)

        if outer_vlan is not None:
            vlans_container = stc.create("vlans", under=eth)
            stc.create("Vlan", under=vlans_container, id=str(outer_vlan), pri="0", cfi="0")

        if inner_vlan_id is not None:
            if outer_vlan is None:
                vlans_container = stc.create("vlans", under=eth)
            stc.create("Vlan", under=vlans_container, id=str(inner_vlan_id), pri="0", cfi="0")

        if args.dst_ip or args.src_ip:
            if proto_lower == "l2":
                # Pure L2: user annotated an IP but explicitly asked for no L3 header.
                # Record the IPs in session metadata for downstream test logic but
                # do NOT build an IPv4/IPv6 header on the wire. Before this change
                # --protocol l2 --dst-ip X silently produced an L2+IPv4 frame,
                # which broke MAC-learning tests that required a bare broadcast.
                print(f"[INFO] --protocol l2 with dst/src IP annotation -- no L3 header added (pure L2 frame)")
            else:
                src_ip = args.src_ip or "10.0.0.1"
                dst_ip = args.dst_ip or "10.0.0.2"
                ip_args = {"sourceAddr": src_ip, "destAddr": dst_ip}
                existing_ip = stc.get(sb, "children-ipv4:IPv4")
                if proto_lower == "ipv6":
                    stc.create("ipv6:IPv6", under=sb, **ip_args)
                elif existing_ip:
                    stc.config(existing_ip, **ip_args)
                else:
                    stc.create("ipv4:IPv4", under=sb, **ip_args)

    stc.apply()

    stream_info = {
        "name": stream_name,
        "handle": sb,
        "vlan": outer_vlan,
        "inner_vlan": inner_vlan_id,
        "src_mac": src_mac,
        "dst_mac": dst_mac,
        "src_ip": args.src_ip,
        "dst_ip": args.dst_ip,
        "rate": rate_mbps,
        "rate_unit": load_unit,
        "frame_size": frame_size,
        "protocol": args.protocol or "ipv4",
        "created": datetime.utcnow().isoformat(),
    }
    stream_info.update(packet_info)
    sess["streams"] = [
        s for s in sess.get("streams", [])
        if s.get("name") != stream_name
    ]
    sess.setdefault("streams", []).append(stream_info)
    save_session(sess)

    print(f"Stream created: {stream_name}")
    print(json.dumps(stream_info, indent=2))


def _mac_to_int(mac):
    parts = mac.split(":")
    if len(parts) != 6:
        raise ValueError(f"invalid MAC address: {mac}")
    value = 0
    for part in parts:
        value = (value << 8) | int(part, 16)
    return value


def _mac_from_int(value):
    if value < 0 or value > 0xffffffffffff:
        raise ValueError(f"MAC integer outside 48-bit range: {value}")
    return ":".join(f"{(value >> shift) & 0xff:02x}" for shift in range(40, -1, -8))


def _validate_mac_range(start_mac, step_mac, count, label):
    start = _mac_to_int(start_mac)
    step = _mac_to_int(step_mac)
    last = start + (step * (count - 1))
    if last > 0xffffffffffff:
        raise ValueError(f"{label} MAC range exceeds 48-bit address space")
    return _mac_from_int(last)


def _create_range_modifier(
    stc,
    stream_handle,
    *,
    name,
    offset_reference,
    mask,
    step_value,
    data,
    count,
    enable_stream,
):
    return stc.create(
        "RangeModifier",
        under=stream_handle,
        Name=name,
        ModifierMode="INCR",
        Mask=str(mask),
        StepValue=str(step_value),
        Data=str(data),
        RecycleCount=str(count),
        RepeatCount="0",
        DataType="NATIVE",
        EnableStream="TRUE" if enable_stream else "FALSE",
        Active="TRUE",
        Offset="0",
        OffsetReference=offset_reference,
    )


def cmd_create_modifier_stream(args):
    """Create one StreamBlock whose RangeModifiers fan out VLAN/MAC values.

    This is for PW scale tests where hundreds of logical L2 flows must be sent
    without creating hundreds of high-speed result-analysis StreamBlocks.
    """
    config = load_config()
    stc, sess = _require_ready(config)

    stream_name = args.name
    count = int(args.count)
    if count < 1:
        print("ERROR: --count must be >= 1")
        sys.exit(1)
    if not (1 <= int(args.inner_vlan_start) <= 4094):
        print("ERROR: --inner-vlan-start must be 1..4094")
        sys.exit(1)
    if int(args.inner_vlan_start) + count - 1 > 4094:
        print("ERROR: inner VLAN range exceeds 4094")
        sys.exit(1)

    src_last = _validate_mac_range(args.src_mac, args.src_mac_step, count, "src")
    dst_last = _validate_mac_range(args.dst_mac, args.dst_mac_step, count, "dst")

    port_handle = sess["port_handle"]
    existing_sbs = stc.get(port_handle, "children-StreamBlock")
    if existing_sbs:
        for sb_h in existing_sbs.split():
            try:
                if stc.get(sb_h, "name") == stream_name or stc.get(sb_h, "Name") == stream_name:
                    print(f"[OK] Modifier stream '{stream_name}' already exists -- reusing (no stc.apply)")
                    return
            except Exception:
                pass

    frame_size = int(args.frame_size) if args.frame_size else 128
    if frame_size < 128:
        print(f"[INFO] L2 modifier stream frame-size {frame_size} is too small for signed STC frames; using 128 bytes")
        frame_size = 128
    rate_mbps = float(args.rate_mbps) if args.rate_mbps else 1.0

    load_unit = "MEGABITS_PER_SECOND"
    if args.rate_pps:
        load_unit = "FRAMES_PER_SECOND"
        rate_mbps = float(args.rate_pps)

    stream_rate_gbps = (rate_mbps / 1000.0) if load_unit == "MEGABITS_PER_SECOND" else (rate_mbps * frame_size * 8) / 1e9
    _preflight_capacity_warn(config, sess, stream_rate_gbps=stream_rate_gbps)

    sb = stc.create(
        "streamBlock",
        under=port_handle,
        insertSig="true",
        frameLengthMode="FIXED",
        FixedFrameLength=str(frame_size),
        load=str(rate_mbps),
        loadUnit=load_unit,
        name=stream_name,
        Active="FALSE",
    )

    eth = stc.get(sb, "children-ethernet:EthernetII")
    if eth:
        stc.config(eth, name="eth", srcMac=args.src_mac, dstMac=args.dst_mac)
    else:
        eth = stc.create(
            "ethernet:EthernetII",
            under=sb,
            name="eth",
            srcMac=args.src_mac,
            dstMac=args.dst_mac,
        )

    vlans_container = stc.create("vlans", under=eth)
    stc.create(
        "Vlan",
        under=vlans_container,
        name="outer",
        id=str(args.outer_vlan),
        pri="0",
        cfi="0",
    )
    stc.create(
        "Vlan",
        under=vlans_container,
        name="inner",
        id=str(args.inner_vlan_start),
        pri="0",
        cfi="0",
    )

    enable_stream = bool(getattr(args, "enable_flow_stats", False))
    modifiers = [
        _create_range_modifier(
            stc,
            sb,
            name=f"{stream_name}_inner_vlan",
            offset_reference="eth.vlans.inner.id",
            mask="4095",
            step_value=str(args.inner_vlan_step),
            data=str(args.inner_vlan_start),
            count=count,
            enable_stream=enable_stream,
        ),
        _create_range_modifier(
            stc,
            sb,
            name=f"{stream_name}_src_mac",
            offset_reference="eth.srcMac",
            mask="00:00:00:00:ff:ff",
            step_value=args.src_mac_step,
            data=args.src_mac,
            count=count,
            enable_stream=enable_stream,
        ),
        _create_range_modifier(
            stc,
            sb,
            name=f"{stream_name}_dst_mac",
            offset_reference="eth.dstMac",
            mask="00:00:00:00:ff:ff",
            step_value=args.dst_mac_step,
            data=args.dst_mac,
            count=count,
            enable_stream=enable_stream,
        ),
    ]

    stc.apply()

    stream_info = {
        "name": stream_name,
        "handle": sb,
        "type": "modifier_l2_qinq",
        "outer_vlan": args.outer_vlan,
        "inner_vlan_start": args.inner_vlan_start,
        "inner_vlan_step": args.inner_vlan_step,
        "count": count,
        "src_mac_start": args.src_mac,
        "src_mac_step": args.src_mac_step,
        "src_mac_end": src_last,
        "dst_mac_start": args.dst_mac,
        "dst_mac_step": args.dst_mac_step,
        "dst_mac_end": dst_last,
        "rate": rate_mbps,
        "rate_unit": load_unit,
        "frame_size": frame_size,
        "modifiers": modifiers,
        "enable_flow_stats": enable_stream,
        "active": "FALSE",
        "created": datetime.utcnow().isoformat(),
    }
    sess.setdefault("streams", []).append(stream_info)
    save_session(sess)

    print(f"[OK] Modifier StreamBlock created: {stream_name}")
    print(json.dumps(stream_info, indent=2))


def cmd_isis_peer(args):
    """Configure ISIS on an emulated device for IGP adjacency with the DUT.

    Creates IsisRouterConfig under the device, optionally advertises a loopback
    prefix so the DUT can resolve the device's loopback via IGP + LDP.
    """
    config = load_config()
    stc, sess = _require_ready(config)
    device_handle, dev = _require_device(stc, sess, args.device_name)
    system_id = args.system_id
    area_id = args.area_id
    level = args.level

    def _area_to_stc_hex(area_dotted: str) -> str:
        """Convert dotted ISIS area notation to STC concatenated hex.

        STC Area1 expects concatenated hex digits with no separators:
        '49.0001' -> '490001'
        '49.0002' -> '490002'
        Already-hex input like '490001' passes through unchanged.
        """
        if "." not in area_dotted:
            return area_dotted
        return "".join(area_dotted.split("."))

    stc_area = _area_to_stc_hex(area_id)

    isis_attrs = {
        "IpVersion": "IPV4",
        "Level": level,
        "NetworkType": "P2P",
    }

    isis = stc.create("IsisRouterConfig", under=device_handle, **isis_attrs)

    try:
        stc.config(isis, SystemId=system_id)
    except Exception as e:
        print(f"  [WARN] ISIS SystemId config: {e}")

    try:
        stc.config(isis, Area1=stc_area)
    except Exception as e:
        print(f"  [WARN] ISIS Area1 config (tried '{stc_area}' from '{area_id}'): {e}")

    if getattr(args, "wide_metric", True):
        try:
            stc.config(isis, MetricMode="MODIFIED")
        except Exception:
            pass

    loopback = args.loopback
    if loopback:
        try:
            lsp = stc.create("IsisLspConfig", under=isis,
                             HostName=f"spirent_vpls_{args.device_name}")
            ipv4_route = stc.create("Ipv4IsisRoutesConfig", under=lsp)
            ipv4_block = stc.get(ipv4_route, "children-Ipv4NetworkBlock")
            if ipv4_block:
                stc.config(ipv4_block.split()[0],
                           StartIpList=loopback,
                           PrefixLength="32",
                           NetworkCount="1")
            stc.config(ipv4_route, Metric=str(args.loopback_metric))
            print(f"  [OK] ISIS will advertise {loopback}/32 (metric {args.loopback_metric})")
        except Exception as e:
            print(f"  [WARN] ISIS loopback route config: {e}")

    ipv4_if = stc.get(device_handle, "children-Ipv4If")
    if ipv4_if:
        try:
            stc.config(isis, **{"UsesIf-targets": [ipv4_if.split()[0]]})
        except Exception:
            pass

    stc.apply()

    dev["isis_handle"] = isis
    dev["isis_system_id"] = system_id
    dev["isis_area_id"] = area_id
    dev["isis_loopback"] = loopback
    save_session(sess)

    print(f"[OK] ISIS configured on {args.device_name}")
    print(f"  System-ID: {system_id}, Area: {area_id} (STC hex: {stc_area}), Level: {level}")
    if loopback:
        print(f"  Loopback: {loopback}/32")


def cmd_ldp_peer(args):
    """Configure LDP on an emulated device for label distribution with the DUT.

    Creates LdpRouterConfig under the device. LDP Hello runs on the connected
    interface. Labels are allocated for the device's loopback prefix.
    """
    config = load_config()
    stc, sess = _require_ready(config)
    device_handle, dev = _require_device(stc, sess, args.device_name)

    loopback = dev.get("isis_loopback") or dev.get("ip")
    router_id = args.router_id or loopback
    transport_addr = args.transport_address or loopback
    fec_prefix = args.fec_prefix or loopback

    ldp_attrs = {
        "KeepAliveInterval": str(args.keepalive_interval),
        "DutIp": args.dut_ip or dev.get("gateway", ""),
    }
    hello_interval = getattr(args, "hello_interval", None)
    if hello_interval is not None:
        ldp_attrs["HelloInterval"] = str(hello_interval)
        ldp_attrs["HoldTime"] = str(max(int(hello_interval) * 3, 15))

    ldp = stc.create("LdpRouterConfig", under=device_handle, **ldp_attrs)

    try:
        stc.config(ldp, TransportTlvMode="TLTV_ADDR")
    except Exception:
        pass

    ipv4_if = stc.get(device_handle, "children-Ipv4If")
    if ipv4_if:
        try:
            stc.config(ldp, **{"UsesIf-targets": [ipv4_if.split()[0]]})
        except Exception:
            pass

    if fec_prefix:
        try:
            ipv4_fec = stc.create("Ipv4PrefixLsp", under=ldp)
            fec_block = stc.get(ipv4_fec, "children-Ipv4NetworkBlock")
            if fec_block:
                stc.config(fec_block.split()[0],
                           StartIpList=fec_prefix,
                           PrefixLength="32",
                           NetworkCount="1")
            print(f"  [OK] LDP will advertise label for {fec_prefix}/32")
        except Exception as e:
            print(f"  [WARN] LDP FEC config: {e}")

    stc.apply()

    dev["ldp_handle"] = ldp
    dev["ldp_router_id"] = router_id
    dev["ldp_transport"] = transport_addr
    save_session(sess)

    print(f"[OK] LDP configured on {args.device_name}")
    print(f"  DUT-IP: {ldp_attrs['DutIp']}, FEC: {fec_prefix or 'none'}")
    print(f"  Keepalive: {args.keepalive_interval}s")


def cmd_vpls_stream(args):
    """Create an MPLS-encapsulated L2 stream for VPLS PW MAC learning/mobility."""
    config = load_config()
    stc, sess = _require_ready(config)

    stream_name = args.name or f"vpls_pw_{args.mpls_label}"
    frame_size = int(args.frame_size) if args.frame_size else 128
    rate_mbps = float(args.rate_mbps) if args.rate_mbps else 1.0

    port_handle = sess["port_handle"]

    existing_sbs = stc.get(port_handle, 'children-StreamBlock')
    if existing_sbs:
        for sb_h in existing_sbs.split():
            try:
                if stc.get(sb_h, 'name') == stream_name:
                    print(f"[OK] VPLS stream '{stream_name}' already exists -- reusing (no stc.apply)")
                    return
            except Exception:
                pass

    sb = stc.create("StreamBlock", under=port_handle,
                     FixedFrameLength=str(frame_size),
                     Name=stream_name)

    outer_vlan = args.outer_vlan
    inner_vlan = args.inner_vlan
    mpls_label = args.mpls_label
    dst_mac_outer = args.dst_mac or "ff:ff:ff:ff:ff:ff"
    src_mac_outer = args.src_mac_outer or "00:10:94:00:06:06"
    inner_src_mac = args.inner_src_mac or "00:DE:AD:00:01:01"
    inner_dst_mac = args.inner_dst_mac or "FF:FF:FF:FF:FF:FF"
    cw_pattern = args.control_word or "00000000"

    vlan_xml = ""
    if outer_vlan is not None:
        vlan_xml = f'<vlans><Vlan name="outer"><id>{outer_vlan}</id><pri>0</pri></Vlan>'
        if inner_vlan is not None:
            vlan_xml += f'<Vlan name="inner"><id>{inner_vlan}</id><pri>0</pri></Vlan>'
        vlan_xml += '</vlans>'

    frame_xml = (
        '<frame><config><pdus>'
        f'<pdu name="eth1" pdu="ethernet:EthernetII">'
        f'<dstMac>{dst_mac_outer}</dstMac><srcMac>{src_mac_outer}</srcMac>'
        f'{vlan_xml}'
        f'<etherType>8847</etherType>'
        f'</pdu>'
        f'<pdu name="mpls1" pdu="mpls:Mpls">'
        f'<label>{mpls_label}</label><exp>000</exp><sBit>1</sBit><ttl>64</ttl>'
        f'</pdu>'
        f'<pdu name="cw1" pdu="custom:Custom"><pattern>{cw_pattern}</pattern></pdu>'
        f'<pdu name="eth_inner" pdu="ethernet:EthernetII">'
        f'<dstMac>{inner_dst_mac}</dstMac><srcMac>{inner_src_mac}</srcMac>'
        f'</pdu>'
        '</pdus></config></frame>'
    )

    stc.config(sb, FrameConfig=frame_xml, Load=str(rate_mbps),
               LoadUnit='MEGABITS_PER_SECOND')
    stc.apply()

    stream_info = {
        "name": stream_name,
        "handle": sb,
        "type": "vpls_pw",
        "outer_vlan": outer_vlan,
        "inner_vlan": inner_vlan,
        "mpls_label": mpls_label,
        "inner_src_mac": inner_src_mac,
        "inner_dst_mac": inner_dst_mac,
        "dst_mac_outer": dst_mac_outer,
        "rate": rate_mbps,
        "frame_size": frame_size,
        "control_word": cw_pattern,
        "created": datetime.utcnow().isoformat(),
    }
    sess.setdefault("streams", []).append(stream_info)
    save_session(sess)

    print(f"[OK] VPLS PW stream created: {stream_name}")
    print(f"  MPLS label: {mpls_label}")
    print(f"  Inner src MAC: {inner_src_mac} (this MAC will be learned on DUT)")
    print(f"  Q-in-Q: outer={outer_vlan} inner={inner_vlan}")
    print(f"  Rate: {rate_mbps} Mbps")


def cmd_start(args):
    """Start traffic generation.

    Without ``--stream-name``: preserves legacy behavior -- ``GeneratorStart``
    on the port, which transmits every StreamBlock whose ``Active`` flag is
    TRUE. Inactive streams stay silent.

    With ``--stream-name X``: scope the activation to stream ``X`` only.
    The flag on ``X`` is flipped to ``TRUE`` then ``GeneratorStart`` is issued
    so ``X`` transmits alongside any other already-active streams.

    Add ``--exclusive`` with ``--stream-name`` when the test requires hard
    isolation. In that mode, every other known StreamBlock is forced
    ``Active=FALSE`` before ``GeneratorStart``. This prevents a previous
    mobility-phase stream from continuing to transmit and masking the intended
    MAC source.
    """
    config = load_config()
    stc, sess = _require_ready(config)

    gen_handle = stc.get(sess["port_handle"], "children-Generator")
    if not gen_handle:
        print("ERROR: No generator found on port. Create a stream first.")
        sys.exit(1)

    stream_name = getattr(args, "stream_name", None)
    exclusive = getattr(args, "exclusive", False)
    if exclusive and not stream_name:
        print("ERROR: --exclusive requires --stream-name")
        sys.exit(1)
    if stream_name:
        streams = sess.get("streams", [])
        match = next((s for s in streams if s["name"] == stream_name), None)
        live_handles = (stc.get(sess["port_handle"], "children-StreamBlock") or "").split()
        live_match = None
        for handle in live_handles:
            try:
                if (stc.get(handle, "name") == stream_name or stc.get(handle, "Name") == stream_name):
                    live_match = handle
                    break
            except Exception:
                continue
        if live_match:
            if not match:
                match = {"name": stream_name}
                sess.setdefault("streams", []).append(match)
            elif match.get("handle") != live_match:
                print(f"[INFO] Stream '{stream_name}' cached handle {match.get('handle')} is stale; using live handle {live_match}")
            match["handle"] = live_match
            sess["streams"] = [
                s for s in sess.get("streams", [])
                if s is match or s.get("name") != stream_name
            ]
            if match not in sess["streams"]:
                sess["streams"].append(match)
        if not match or not match.get("handle"):
            print(f"ERROR: Stream '{stream_name}' not found. Run 'status' to list streams.")
            sys.exit(1)
        try:
            if exclusive:
                for handle in live_handles:
                    stc.config(handle, Active="TRUE" if handle == match["handle"] else "FALSE")
                if match["handle"] not in live_handles:
                    stc.config(match["handle"], Active="TRUE")
            else:
                stc.config(match["handle"], Active="TRUE")
            stc.apply()
        except Exception as exc:
            print(f"ERROR: Could not activate stream '{stream_name}': {exc}")
            sys.exit(1)
        if exclusive:
            for stream in streams:
                stream["active"] = "TRUE" if stream.get("handle") == match["handle"] else "FALSE"
        else:
            match["active"] = "TRUE"
        save_session(sess)
        if exclusive:
            print(f"Stream '{stream_name}' set Active=TRUE; all other streams set Active=FALSE")
        else:
            print(f"Stream '{stream_name}' set Active=TRUE (other streams untouched)")

    gen_config = stc.get(gen_handle, "children-GeneratorConfig")
    if gen_config:
        total_mbps = 0
        sbs = stc.get(sess["port_handle"], "children-StreamBlock")
        if sbs:
            for sb_h in sbs.split():
                try:
                    if (stc.get(sb_h, "Active") or "").upper() == "FALSE":
                        continue
                    sb_load = float(stc.get(sb_h, "Load") or 0)
                    sb_unit = (stc.get(sb_h, "LoadUnit") or "").upper()
                    if "MEGABITS" in sb_unit:
                        total_mbps += sb_load
                    elif "FRAMES" in sb_unit:
                        ffl = int(stc.get(sb_h, "FixedFrameLength") or 128)
                        total_mbps += (sb_load * ffl * 8) / 1e6
                    elif "PERCENT" in sb_unit:
                        total_mbps += sb_load * 1000
                    else:
                        total_mbps += max(sb_load, 1)
                except Exception:
                    total_mbps += 1
        total_mbps = max(total_mbps, 1)
        pct = (total_mbps / 100000.0) * 100.0
        pct = max(pct, 0.0001)
        stc.config(gen_config, SchedulingMode="PORT_BASED",
                   DurationMode="CONTINUOUS",
                   LoadMode="FIXED",
                   FixedLoad=str(pct),
                   LoadUnit="PERCENT_LINE_RATE")
        stc.apply()

    ana_handle = stc.get(sess["port_handle"], "children-Analyzer")
    if ana_handle:
        stc.perform("AnalyzerStart", AnalyzerList=ana_handle)

    stc.perform("GeneratorStart", GeneratorList=gen_handle)

    sess["traffic_running"] = True
    sess["traffic_started"] = datetime.utcnow().isoformat()
    save_session(sess)

    print(f"Traffic STARTED at {sess['traffic_started']}")
    active_count = sum(1 for s in sess.get("streams", []) if str(s.get("active", "")).upper() == "TRUE")
    print(f"Active streams: {active_count}")


def cmd_stop(args):
    """Stop traffic generation.

    Without ``--stream-name``: legacy behavior -- ``GeneratorStop`` halts all
    streams on the port. ``StreamBlock.Active`` flags are preserved, so the
    next ``start`` resumes whatever was active.

    With ``--stream-name X``: non-disruptive per-stream deactivation. Only
    stream ``X`` flips to ``Active=FALSE``; the generator keeps running and
    other streams keep transmitting. Use this when a scenario needs to
    remove one Spirent traffic source mid-test without blackholing the
    others (e.g. MAC move during EVPN GR window). Before this change the
    ``--stream-name`` flag was silently ignored -- every call stopped ALL
    traffic regardless of what was passed.
    """
    config = load_config()
    stc, sess = _require_ready(config)

    stream_name = getattr(args, "stream_name", None)
    if stream_name:
        streams = sess.get("streams", [])
        match = next((s for s in streams if s["name"] == stream_name), None)
        if not match or not match.get("handle"):
            print(f"ERROR: Stream '{stream_name}' not found. Run 'status' to list streams.")
            sys.exit(1)
        try:
            stc.config(match["handle"], Active="FALSE")
            stc.apply()
        except Exception as exc:
            print(f"ERROR: Could not deactivate stream '{stream_name}': {exc}")
            sys.exit(1)
        match["active"] = "FALSE"
        save_session(sess)
        print(f"Stream '{stream_name}' set Active=FALSE (generator keeps running, other streams unaffected)")
        return

    gen_handle = stc.get(sess["port_handle"], "children-Generator")
    if gen_handle:
        stc.perform("GeneratorStop", GeneratorList=gen_handle)

    sess["traffic_running"] = False
    sess["traffic_stopped"] = datetime.utcnow().isoformat()
    save_session(sess)

    print(f"Traffic STOPPED at {sess['traffic_stopped']}")


def _collect_per_stream_stats(stc, sess, project_handle, per_stream, stream_names=None):
    """Collect per-stream TX/RX stats using TxStreamBlockResults and RxStreamBlockResults."""
    streams_out = []
    stream_list = sess.get("streams", [])
    if not per_stream or not stream_list:
        return streams_out
    expected = {str(name) for name in (stream_names or []) if str(name).strip()}
    if expected:
        stream_list = [stream for stream in stream_list if str(stream.get("name") or "") in expected]
        if not stream_list:
            return streams_out

    subscription_warning = None
    try:
        stc.perform("ResultsSubscribe",
                     Parent=project_handle,
                     ConfigType="StreamBlock",
                     ResultType="TxStreamBlockResults",
                     RecordsPerPage=256)
        stc.perform("ResultsSubscribe",
                     Parent=project_handle,
                     ConfigType="StreamBlock",
                     ResultType="RxStreamBlockResults",
                     RecordsPerPage=256)
        time.sleep(2)
    except Exception as e:
        subscription_warning = str(e)

    for s in stream_list:
        handle = s.get("handle")
        if not handle:
            continue
        entry = {
            "name": s.get("name", "?"),
            "tx_frames": 0,
            "tx_rate_bps": 0,
            "rx_frames": 0,
            "rx_rate_bps": 0,
            "dropped": 0,
        }
        try:
            tx_res = stc.get(handle, "children-TxStreamBlockResults")
            if tx_res:
                tx_h = tx_res.split()[0] if isinstance(tx_res, str) else tx_res
                tx_stats = stc.get(tx_h)
                entry["tx_frames"] = int(tx_stats.get("FrameCount", tx_stats.get("GeneratorFrameCount", 0)) or 0)
                entry["tx_rate_bps"] = int(tx_stats.get("BitRate", tx_stats.get("GeneratorBitRate", 0)) or 0)
        except Exception:
            pass
        try:
            rx_res = stc.get(handle, "children-RxStreamBlockResults")
            if rx_res:
                rx_h = rx_res.split()[0] if isinstance(rx_res, str) else rx_res
                rx_stats = stc.get(rx_h)
                entry["rx_frames"] = int(rx_stats.get("SigFrameCount", rx_stats.get("TotalFrameCount", 0)) or 0)
                entry["rx_rate_bps"] = int(rx_stats.get("BitRate", rx_stats.get("TotalBitRate", 0)) or 0)
                entry["dropped"] = int(rx_stats.get("DroppedFrameCount", 0) or 0)
        except Exception:
            pass
        streams_out.append(entry)
    if subscription_warning:
        for entry in streams_out:
            entry.setdefault("warnings", []).append(
                "ResultsSubscribe failed; reused existing result children when available"
            )
    return streams_out


def cmd_stats(args):
    """Get traffic statistics from the port."""
    config = load_config()
    stc, sess = _require_ready(config)
    port_handle = sess["port_handle"]
    project_handle = sess.get("project_handle") or "project1"

    gen_results = stc.get(port_handle, "children-GeneratorPortResults")
    ana_results = stc.get(port_handle, "children-AnalyzerPortResults")

    if not gen_results or not ana_results:
        try:
            stc.perform("ResultsSubscribe",
                         Parent=project_handle,
                         ConfigType="Generator",
                         ResultType="GeneratorPortResults",
                         RecordsPerPage=256)
            stc.perform("ResultsSubscribe",
                         Parent=project_handle,
                         ConfigType="Analyzer",
                         ResultType="AnalyzerPortResults",
                         RecordsPerPage=256)
            time.sleep(3)
            gen_results = stc.get(port_handle, "children-GeneratorPortResults")
            ana_results = stc.get(port_handle, "children-AnalyzerPortResults")
        except Exception:
            pass

    if not gen_results or not ana_results:
        gen_handle = stc.get(port_handle, "children-Generator")
        ana_handle = stc.get(port_handle, "children-Analyzer")
        if gen_handle and not gen_results:
            alt = stc.get(gen_handle, "children-GeneratorPortResults")
            if alt:
                gen_results = alt.split()[-1]
        if ana_handle and not ana_results:
            alt = stc.get(ana_handle, "children-AnalyzerPortResults")
            if alt:
                ana_results = alt.split()[-1]

    if not gen_results and not ana_results:
        gen_handle = stc.get(port_handle, "children-Generator")
        gen_state = stc.get(gen_handle, "state") if gen_handle else "N/A"
        print(f"Note: Result objects not yet available. Generator state: {gen_state}")
        print("Try starting the analyzer first ('start' command auto-starts it).")

    stats_out = {"timestamp": datetime.utcnow().isoformat(), "port": config["port_location"]}

    if gen_results:
        gen_stats = stc.get(gen_results)
        stats_out["tx"] = {
            "total_frames": gen_stats.get("GeneratorFrameCount", "0"),
            "total_bytes": gen_stats.get("GeneratorOctetCount", "0"),
            "rate_fps": gen_stats.get("GeneratorFrameRate", "0"),
            "rate_bps": gen_stats.get("GeneratorBitRate", "0"),
            "sig_frames": gen_stats.get("GeneratorSigFrameCount", "0"),
        }

    if ana_results:
        ana_stats = stc.get(ana_results)
        stats_out["rx"] = {
            "total_frames": ana_stats.get("TotalFrameCount", "0"),
            "total_bytes": ana_stats.get("TotalOctetCount", "0"),
            "rate_fps": ana_stats.get("TotalFrameRate", "0"),
            "rate_bps": ana_stats.get("TotalBitRate", "0"),
            "sig_frames": ana_stats.get("SigFrameCount", "0"),
            "dropped_frames": ana_stats.get("DroppedFrameCount", "0"),
            "dropped_pct": ana_stats.get("DroppedFramePercent", "0"),
        }

    tx_frames = int(stats_out.get("tx", {}).get("total_frames", 0))
    rx_frames = int(stats_out.get("rx", {}).get("total_frames", 0))
    if tx_frames > 0:
        stats_out["loss"] = {
            "frames": tx_frames - rx_frames,
            "percent": round(((tx_frames - rx_frames) / tx_frames) * 100, 4) if tx_frames > 0 else 0,
        }

    per_stream = getattr(args, "per_stream", True)
    stream_names = []
    if getattr(args, "stream_name", None):
        stream_names = [name.strip() for name in str(args.stream_name).split(",") if name.strip()]
    streams_data = _collect_per_stream_stats(stc, sess, project_handle, per_stream, stream_names=stream_names)
    if streams_data:
        stats_out["streams"] = streams_data

    if args.json_output:
        print(json.dumps(stats_out, indent=2))
    else:
        print(f"=== Spirent Port Stats ({config['port_location']}) ===")
        print(f"Timestamp: {stats_out['timestamp']}")
        if "tx" in stats_out:
            tx = stats_out["tx"]
            print(f"\n  TX:")
            print(f"    Frames:  {tx['total_frames']}")
            print(f"    Rate:    {tx['rate_fps']} fps / {tx['rate_bps']} bps")
        if "rx" in stats_out:
            rx = stats_out["rx"]
            print(f"\n  RX:")
            print(f"    Frames:  {rx['total_frames']}")
            print(f"    Rate:    {rx['rate_fps']} fps / {rx['rate_bps']} bps")
            print(f"    Dropped: {rx['dropped_frames']} ({rx['dropped_pct']}%)")
        if "loss" in stats_out:
            loss = stats_out["loss"]
            print(f"\n  Loss: {loss['frames']} frames ({loss['percent']}%)")
        if "streams" in stats_out:
            print(f"\n  Per-stream:")
            for s in stats_out["streams"]:
                print(f"    {s['name']}: tx={s['tx_frames']} ({s['tx_rate_bps']} bps) rx={s['rx_frames']} ({s['rx_rate_bps']} bps) dropped={s['dropped']}")

    os.makedirs(STATS_DIR, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    stats_path = os.path.join(STATS_DIR, f"stats_{ts}.json")
    with open(stats_path, "w") as f:
        json.dump(stats_out, f, indent=2)


# ────────────────────────────────────────────
# BGP Protocol Emulation (Phase 1)
# ────────────────────────────────────────────

def cmd_create_device(args):
    """Create EmulatedDevice(s) with EthIIIf + IPv4/IPv6 stack (optional VlanIf).

    Supports STC Device Block multiplier: --device-count N creates N logical devices
    with auto-stepping IPv4 (--ip-step) and MAC (--mac-step). Single REST object,
    ~15 API calls regardless of N. IPv6 host creation is single-device today and
    is used by NDP fallback phases.
    """
    config = load_config()
    stc, sess = _require_ready(config)

    project = sess["project_handle"]
    port = sess["port_handle"]

    no_qinq = getattr(args, "no_qinq", False)
    excl_raw = getattr(args, "exclude_inner_vlans", None)
    excl_set = set(int(v) for v in excl_raw.split(",") if v.strip()) if excl_raw else None
    outer_vlan, inner_vlan_id = _resolve_qinq_vlans(
        config, sess, args.vlan, getattr(args, "inner_vlan", None), no_qinq=no_qinq, exclude_inner=excl_set
    )
    if inner_vlan_id is not None:
        print(f"[INFO] Auto Q-in-Q: outer={outer_vlan} inner={inner_vlan_id}")

    ipv4_addr = getattr(args, "ip", None)
    ipv4_gateway = getattr(args, "gateway", None)
    ipv6_addr = getattr(args, "ipv6", None)
    ipv6_gateway = getattr(args, "ipv6_gateway", None)
    if not ipv4_addr and not ipv6_addr:
        raise SystemExit("create-device requires either --ip/--gateway or --ipv6/--ipv6-gateway")
    if ipv4_addr and not ipv4_gateway:
        raise SystemExit("create-device requires --gateway when --ip is used")
    if ipv6_addr and not ipv6_gateway:
        raise SystemExit("create-device requires --ipv6-gateway when --ipv6 is used")

    dev_count = getattr(args, "device_count", 1) or 1
    if ipv6_addr and dev_count > 1:
        raise SystemExit("IPv6 create-device currently supports a single device; use --device-count 1")
    ip_step_raw = getattr(args, "ip_step", None)
    mac_step_raw = getattr(args, "mac_step", None)
    device_name = args.name or f"BGP_Peer_{len(sess.get('devices', []))}"
    prefix_len = int(args.prefix_len) if args.prefix_len else 24
    ipv6_prefix_len = int(getattr(args, "ipv6_prefix_len", 64) or 64)
    router_id = args.router_id or ipv4_addr or f"192.0.2.{(len(sess.get('devices', [])) % 250) + 1}"
    src_mac = args.mac or f"00:10:94:00:00:{len(sess.get('devices', [])) + 1:02d}"

    dev_attrs = {
        "Name": device_name,
        "EnablePingResponse": "TRUE",
        "RouterId": router_id,
    }
    if dev_count > 1:
        ip_step = _ip_step_str(ip_step_raw or 1)
        mac_step = _mac_step_str(mac_step_raw or 1)
        dev_attrs["DeviceCount"] = str(dev_count)
        dev_attrs["RouterIdStep"] = ip_step
        print(f"[INFO] Device Block: {dev_count} devices, IP step={ip_step}, MAC step={mac_step}")

    device = stc.create("EmulatedDevice", under=project, **dev_attrs)

    eth_attrs = {"SourceMac": src_mac}
    if dev_count > 1:
        eth_attrs["SrcMacStep"] = mac_step
    eth = stc.create("EthIIIf", under=device, **eth_attrs)

    if ipv6_addr:
        l3_attrs = {
            "Address": ipv6_addr,
            "Gateway": ipv6_gateway,
            "PrefixLength": str(ipv6_prefix_len),
        }
        l3_if = stc.create("Ipv6If", under=device, **l3_attrs)
    else:
        ipv4_attrs = {
            "Address": ipv4_addr,
            "Gateway": ipv4_gateway,
            "PrefixLength": str(prefix_len),
        }
        if dev_count > 1:
            ipv4_attrs["AddrStep"] = ip_step
            ipv4_attrs["GatewayStep"] = "0.0.0.0"
        l3_if = stc.create("Ipv4If", under=device, **ipv4_attrs)

    stc.config(device, **{"TopLevelIf-targets": [l3_if]})
    stc.config(device, **{"PrimaryIf-targets": [l3_if]})

    if outer_vlan is not None and inner_vlan_id is not None:
        inner_vlan_if = stc.create("VlanIf", under=device, VlanId=str(inner_vlan_id))
        outer_vlan_if = stc.create("VlanIf", under=device, VlanId=str(outer_vlan))
        stc.config(l3_if, **{"StackedOnEndpoint-targets": [inner_vlan_if]})
        stc.config(inner_vlan_if, **{"StackedOnEndpoint-targets": [outer_vlan_if]})
        stc.config(outer_vlan_if, **{"StackedOnEndpoint-targets": [eth]})
    elif outer_vlan is not None:
        vlan_if = stc.create("VlanIf", under=device, VlanId=str(outer_vlan))
        stc.config(l3_if, **{"StackedOnEndpoint-targets": [vlan_if]})
        stc.config(vlan_if, **{"StackedOnEndpoint-targets": [eth]})
    else:
        stc.config(l3_if, **{"StackedOnEndpoint-targets": [eth]})

    # B5: NEVER reset port-level AffiliationPort-sources when there is an
    # already-affiliated peer on the port -- that operation can flap ARP/ND
    # and bounce active or pending BGP/ISIS/LDP sessions on Lab Server.
    # Always prefer per-device AffiliationPort-targets when ANY valid device
    # exists, regardless of whether its protocols are currently active.
    # The port-level "rebuild from scratch" path is only used on the very
    # first device created in a session.
    existing_devices = [d["handle"] for d in sess.get("devices", []) if d.get("handle")]
    valid_existing = []
    protocol_active_devices = []
    for dh in existing_devices:
        try:
            stc.get(dh, "Name")
            valid_existing.append(dh)
            for child_attr, label in (
                ("children-BgpRouterConfig", "BGP"),
                ("children-IsisRouterConfig", "ISIS"),
                ("children-LdpRouterConfig", "LDP"),
                ("children-OspfRouterConfig", "OSPF"),
            ):
                try:
                    children = stc.get(dh, child_attr)
                    if children and children.strip():
                        protocol_active_devices.append(f"{stc.get(dh, 'Name')}({label})")
                        break
                except Exception:
                    pass
        except Exception:
            pass

    if valid_existing:
        if protocol_active_devices:
            print(f"[INFO] Existing protocol peers: {', '.join(protocol_active_devices)} -- "
                  "preserving via per-device affiliation")
        else:
            print(f"[INFO] {len(valid_existing)} existing device(s) on port -- "
                  "using per-device affiliation (no port-level reset)")
        try:
            stc.config(device, **{"AffiliationPort-targets": [port]})
        except Exception as e:
            print(f"Warning: AffiliationPort-targets failed: {e}")
            try:
                all_devices = valid_existing + [device]
                stc.config(port, **{"AffiliationPort-sources": all_devices})
            except Exception as e2:
                print(f"Warning: AffiliationPort-sources fallback also failed: {e2}")
    else:
        try:
            stc.config(port, **{"AffiliationPort-sources": [device]})
        except Exception as e:
            print(f"Warning: AffiliationPort-sources failed: {e}")
            try:
                stc.config(device, **{"AffiliationPort-targets": [port]})
            except Exception as e2:
                print(f"Warning: AffiliationPort-targets fallback also failed: {e2}")

    stc.apply()

    dev_info = {
        "name": device_name,
        "handle": device,
        "ip": ipv4_addr,
        "gateway": ipv4_gateway,
        "ipv6": ipv6_addr,
        "ipv6_gateway": ipv6_gateway,
        "vlan": outer_vlan,
        "inner_vlan": inner_vlan_id,
        "router_id": router_id,
        "device_count": dev_count,
        "created": datetime.utcnow().isoformat(),
    }
    if dev_count > 1:
        dev_info["ip_step"] = ip_step
        dev_info["mac"] = src_mac
        dev_info["mac_step"] = mac_step
    sess.setdefault("devices", []).append(dev_info)
    save_session(sess)

    if dev_count > 1:
        print(f"[OK] Device Block created: {device_name} x{dev_count} ({args.ip}, step {ip_step})")
    elif ipv6_addr:
        print(f"Device created: {device_name} ({ipv6_addr})")
    else:
        print(f"Device created: {device_name} ({ipv4_addr})")
    print(json.dumps(dev_info, indent=2))


def _configure_vpls_route(stc, route_cfg_handle, args):
    """Configure BgpIpv4VplsConfig with VPLS-specific attributes (RD, RT, VE-ID, label block).

    When --vpls-nexthop is set, overrides the BGP NEXT_HOP so PE uses an
    LDP-resolvable loopback (e.g. 3.3.3.3) rather than the connected IP.
    """
    vpls_attrs = {}
    vpls_rd = getattr(args, "vpls_rd", None)
    vpls_rt = getattr(args, "vpls_rt", None)
    vpls_ve_id = getattr(args, "vpls_ve_id", None)
    vpls_block_size = getattr(args, "vpls_block_size", None)
    vpls_mtu = getattr(args, "vpls_mtu", None)
    vpls_nexthop = getattr(args, "vpls_nexthop", None)

    if vpls_rd:
        vpls_attrs["RouteDistinguisher"] = vpls_rd
    if vpls_rt:
        parts = vpls_rt.split(":")
        if len(parts) == 2:
            vpls_attrs["ExtendedCommunity"] = f"0x00:0x02:{parts[0]}:{parts[1]}"
        else:
            vpls_attrs["ExtendedCommunity"] = vpls_rt
    vpls_offset = getattr(args, "vpls_offset", 1)
    if vpls_ve_id is not None:
        vpls_attrs["VeId"] = str(vpls_ve_id)
    vpls_attrs["BlkOffset"] = str(vpls_offset)
    if vpls_block_size is not None:
        vpls_attrs["BlkSize"] = str(vpls_block_size)
    if vpls_mtu is not None:
        vpls_attrs["MtuSize"] = str(vpls_mtu)
    vpls_attrs["EncapType"] = "VPLS"
    vpls_attrs["EnableFlooding"] = "TRUE"
    vpls_attrs["ControlFlag"] = "02"
    if vpls_nexthop:
        vpls_attrs["NextHop"] = vpls_nexthop
    if vpls_attrs:
        try:
            stc.config(route_cfg_handle, **vpls_attrs)
            nh_msg = f", NextHop={vpls_nexthop}" if vpls_nexthop else ""
            print(f"  [OK] VPLS config: RD={vpls_rd}, RT={vpls_rt}, VE-ID={vpls_ve_id}, BlkSize={vpls_block_size}{nh_msg}")
        except Exception as e:
            print(f"  [WARN] VPLS config failed: {e}")


def _configure_evpn_route(stc, route_cfg_handle, args):
    """Configure BgpEvpnMacAdvRouteConfig with EVPN RT-2 (MAC/IP Advertisement) attributes."""
    evpn_attrs = {}
    evpn_rd = getattr(args, "evpn_rd", None)
    evpn_rt = getattr(args, "evpn_rt", None)
    evpn_label = getattr(args, "evpn_label", None)
    evpn_mac = getattr(args, "evpn_mac", None)
    evpn_evi_rt = getattr(args, "evpn_evi_rt", None)
    evpn_nexthop = getattr(args, "evpn_nexthop", None)

    if evpn_rd:
        evpn_attrs["RouteDistinguisher"] = evpn_rd
    if evpn_rt:
        parts = evpn_rt.split(":")
        if len(parts) == 2:
            evpn_attrs["RouteTarget"] = evpn_rt
            evpn_attrs["ExtendedCommunity"] = f"0x00:0x02:{parts[0]}:{parts[1]}"
        else:
            evpn_attrs["RouteTarget"] = evpn_rt
    if evpn_evi_rt:
        evpn_attrs["ExtCommunityEviRouteTarget"] = evpn_evi_rt
    elif evpn_rt:
        evpn_attrs["ExtCommunityEviRouteTarget"] = evpn_rt
    evpn_attrs["DataPlaneEncap"] = "MPLS"
    if evpn_label is not None:
        evpn_attrs["MplsLabel"] = str(evpn_label)
    else:
        evpn_attrs["MplsLabel"] = "16000"
    evpn_attrs["EthernetTagId"] = "0"
    evpn_attrs["EviCount"] = "1"
    evpn_attrs["Origin"] = "IGP"
    evpn_attrs["IncludeMacMobility"] = "TRUE"
    evpn_attrs["SequenceNumber"] = "0"
    if evpn_nexthop:
        evpn_attrs["NextHop"] = evpn_nexthop

    if evpn_attrs:
        try:
            stc.config(route_cfg_handle, **evpn_attrs)
            mac_block = stc.get(route_cfg_handle, "children-MacBlock")
            if mac_block:
                mac = evpn_mac or "00:DE:AD:00:01:01"
                stc.config(mac_block.split()[0], StartMacList=mac, NetworkCount="1",
                           AddrIncrement="1")
            nh_msg = f", NextHop={evpn_nexthop}" if evpn_nexthop else ""
            print(f"  [OK] EVPN RT-2: RD={evpn_rd}, RT={evpn_rt}, Label={evpn_attrs['MplsLabel']}, MAC={evpn_mac or '00:DE:AD:00:01:01'}{nh_msg}")
        except Exception as e:
            print(f"  [WARN] EVPN RT-2 config failed: {e}")


def _fix_ipv6_flowspec_safi(stc, route_cfg_handle, bgp_router_handle):
    """BgpIpv6FlowSpecConfig defaults to SAFI 134 (FlowSpec-VPN).
    For plain IPv6 FlowSpec (SAFI 133), set SubAfi to FLOW_SPEC and fix
    the auto-created BgpCapabilityConfig SubAfi from 134 to 133."""
    try:
        stc.config(route_cfg_handle, SubAfi='FLOW_SPEC')
    except Exception:
        pass
    try:
        children = stc.get(bgp_router_handle, 'children').split()
        for child in children:
            if 'capabilityconfig' in child and 'nlri' not in child:
                try:
                    attrs = stc.get(child)
                    if attrs.get('Afi') == '2' and attrs.get('SubAfi') == '134':
                        stc.config(child, SubAfi='133')
                except Exception:
                    pass
    except Exception:
        pass


def cmd_bgp_peer(args):
    """Configure BGP on an emulated device and start the session."""
    config = load_config()
    stc, sess = _require_ready(config)

    device_handle, dev_match = _require_device(stc, sess, args.device_name)

    if not dev_match.get("bgp_handle"):
        _preflight_capacity_warn(config, sess, new_peer=True)
    port = sess["port_handle"]

    neighbor = args.neighbor or dev_match["gateway"]
    ip_version = "IPV6" if args.afi == "ipv6" else "IPV4"

    use_4byte = args.as_num > 65535 or args.dut_as > 65535
    bgp_attrs = {
        "DutIpv4Addr": neighbor,
        "UseGatewayAsDut": "FALSE",
        "IpVersion": ip_version,
        "HoldTimeInterval": str(args.hold_timer) if args.hold_timer else "90",
        "KeepAliveInterval": str(args.keepalive) if args.keepalive else "30",
    }
    if use_4byte:
        bgp_attrs["Enable4ByteAsNum"] = "TRUE"
        bgp_attrs["Enable4ByteDutAsNum"] = "TRUE"
        bgp_attrs["AsNum4Byte"] = str(args.as_num)
        bgp_attrs["DutAsNum4Byte"] = str(args.dut_as)
        bgp_attrs["AsNum"] = "23456"  # AS_TRANS per RFC 6793
        bgp_attrs["DutAsNum"] = "23456"
    else:
        bgp_attrs["AsNum"] = str(args.as_num)
        bgp_attrs["DutAsNum"] = str(args.dut_as)

    bgp = stc.create("BgpRouterConfig", under=device_handle, **bgp_attrs)

    ipv4_children = stc.get(device_handle, "children-Ipv4If")
    if ipv4_children:
        ipv4_handle = ipv4_children.split()[0]
        stc.config(bgp, **{"UsesIf-targets": [ipv4_handle]})

    # AFI/SAFI capability negotiation: create route config objects so Spirent
    # advertises the correct capabilities in OPEN. Without these, PE sees (NoNeg).
    negotiated_afis = []
    requested_afis = getattr(args, "negotiate_afi", None) or []
    if isinstance(requested_afis, str):
        requested_afis = [a.strip() for a in requested_afis.split(",")]

    afi_map = {
        "ipv4-unicast": ("BgpIpv4RouteConfig", {}),
        "ipv6-unicast": ("BgpIpv6RouteConfig", {}),
        "ipv4-flowspec": ("BgpFlowSpecConfig", {}),
        "ipv6-flowspec": ("BgpIpv6FlowSpecConfig", {}),
        "ipv4-vpn": ("BgpVpnRouteConfig", {}),
        "ipv6-vpn": ("BgpVpnRouteConfig", {"IpVersion": "IPV6"}),
        "l2vpn-vpls": ("BgpIpv4VplsConfig", {}),
        "l2vpn-evpn": ("BgpEvpnMacAdvRouteConfig", {"DataPlaneEncap": "MPLS"}),
    }

    for afi_name in requested_afis:
        afi_key = afi_name.lower().strip()
        if afi_key == "all":
            requested_afis = list(afi_map.keys())
            break

    is_ibgp = args.as_num == args.dut_as
    route_as_path = "" if is_ibgp else str(args.as_num)

    for afi_name in requested_afis:
        afi_key = afi_name.lower().strip()
        if afi_key not in afi_map:
            print(f"[WARN] Unknown AFI '{afi_key}', skipping. Valid: {', '.join(afi_map.keys())}")
            continue
        obj_type, extra_attrs = afi_map[afi_key]
        try:
            route_cfg = stc.create(obj_type, under=bgp, **extra_attrs)
            try:
                stc.config(route_cfg, AsPath=route_as_path)
            except Exception:
                pass
            if afi_key == "ipv6-flowspec":
                _fix_ipv6_flowspec_safi(stc, route_cfg, bgp)
            if afi_key == "l2vpn-vpls":
                _configure_vpls_route(stc, route_cfg, args)
            if afi_key == "l2vpn-evpn":
                _configure_evpn_route(stc, route_cfg, args)
            negotiated_afis.append(afi_key)
            print(f"  [OK] AFI capability: {afi_key} ({obj_type} -> {route_cfg})")
        except Exception as e:
            print(f"  [WARN] Failed to create {obj_type} for {afi_key}: {e}")

    if negotiated_afis:
        print(f"[OK] Will negotiate AFIs: {', '.join(negotiated_afis)}")
    elif not requested_afis:
        print("[INFO] No --negotiate-afi specified. PE may show (NoNeg) for some AFIs.")
        print("[INFO] Use --negotiate-afi ipv4-unicast,ipv4-flowspec to advertise capabilities.")

    stc.apply()

    dev_match["bgp_handle"] = bgp
    dev_match["as_num"] = args.as_num
    dev_match["dut_as"] = args.dut_as
    dev_match["negotiated_afis"] = negotiated_afis
    save_session(sess)

    if getattr(args, 'no_start', False):
        print("[OK] BGP configured (--no-start: protocols NOT started)")
        print("[INFO] Run 'protocol-start' to start protocols when all devices are ready.")
        return

    print("Starting ARP/ND and device protocols...")
    stc.perform("ArpNdStartCommand", HandleList=port)
    time.sleep(2)
    stc.perform("DeviceStartCommand", DeviceList=device_handle)
    stc.apply()

    wait_established = getattr(args, "wait_established", 0) or 0
    if wait_established <= 0:
        print("[OK] BGP start triggered.")
        print("[INFO] Skipping Spirent-side BGP wait by default; verify on DUT for ground truth.")
        print("[INFO] Use --wait-established <seconds> to poll Spirent-side results when needed.")
        return

    print(f"Waiting for BGP session (ESTABLISHED, timeout {wait_established}s)...")
    project_handle = sess.get("project_handle")
    if project_handle:
        try:
            stc.perform(
                "ResultsSubscribe",
                Parent=project_handle,
                ConfigType="BgpRouterConfig",
                ResultType="BgpRouterResults",
            )
        except Exception:
            pass

    if poll_until is not None:
        def _bgp_up_check():
            try:
                results_handle = stc.get(bgp, "children-BgpRouterResults")
                if not results_handle:
                    return False, {"state": "no_results_yet"}
                results = stc.get(results_handle.split()[0])
                state = results.get("SessionState", "UNKNOWN")
                return (state == "ESTABLISHED"), {"state": state}
            except Exception as exc:
                return False, {"error": f"{exc.__class__.__name__}: {exc}"}

        def _bgp_progress(elapsed, observed):
            state = observed.get("state", "?") if isinstance(observed, dict) else "?"
            print(f"  BGP state: {state}", flush=True)

        res = poll_until(_bgp_up_check, timeout_sec=float(wait_established), interval_sec=1.0,
                         on_progress=_bgp_progress, progress_every=1)
        if res.passed:
            print(f"BGP session ESTABLISHED with {neighbor} in {res.elapsed_sec:.1f}s")
            return
        print(f"WARNING: BGP session not ESTABLISHED within {wait_established}s ({res.reason}). "
              "Check DUT config and connectivity.")
    else:
        for _ in range(wait_established):
            time.sleep(1)
            try:
                results_handle = stc.get(bgp, "children-BgpRouterResults")
                if results_handle:
                    results = stc.get(results_handle.split()[0])
                    state = results.get("SessionState", "UNKNOWN")
                    print(f"  BGP state: {state}")
                    if state == "ESTABLISHED":
                        print(f"BGP session ESTABLISHED with {neighbor}")
                        return
            except Exception as e:
                print(f"  Polling... ({e})")
        print(f"WARNING: BGP session not ESTABLISHED within {wait_established}s. Check DUT config and connectivity.")


def cmd_add_afi(args):
    """Add AFI/SAFI route config objects to an existing BGP peer (triggers capability renegotiation)."""
    config = load_config()
    stc, sess = _require_ready(config)
    _, dev_match = _require_device(stc, sess, args.device_name)
    bgp_handle = dev_match.get("bgp_handle")
    if not bgp_handle:
        print(f"ERROR: Device '{args.device_name}' has no BGP config. Run 'bgp-peer' first.")
        sys.exit(1)

    afi_map = {
        "ipv4-unicast": ("BgpIpv4RouteConfig", {}),
        "ipv6-unicast": ("BgpIpv6RouteConfig", {}),
        "ipv4-flowspec": ("BgpFlowSpecConfig", {}),
        "ipv6-flowspec": ("BgpIpv6FlowSpecConfig", {}),
        "ipv4-vpn": ("BgpVpnRouteConfig", {}),
        "ipv6-vpn": ("BgpVpnRouteConfig", {"IpVersion": "IPV6"}),
        "l2vpn-vpls": ("BgpIpv4VplsConfig", {}),
        "l2vpn-evpn": ("BgpEvpnMacAdvRouteConfig", {"DataPlaneEncap": "MPLS"}),
    }

    requested = [a.strip().lower() for a in args.afis.split(",")]
    if "all" in requested:
        requested = list(afi_map.keys())

    added = []
    existing = dev_match.get("negotiated_afis", [])

    peer_as = dev_match.get("as_num", 65100)
    dut_as = dev_match.get("dut_as", 0)
    route_as_path = "" if peer_as == dut_as else str(peer_as)

    for afi_key in requested:
        if afi_key in existing:
            print(f"  [SKIP] {afi_key} already configured")
            continue
        if afi_key not in afi_map:
            print(f"  [WARN] Unknown AFI '{afi_key}'. Valid: {', '.join(afi_map.keys())}")
            continue
        obj_type, extra_attrs = afi_map[afi_key]
        try:
            route_cfg = stc.create(obj_type, under=bgp_handle, **extra_attrs)
            try:
                stc.config(route_cfg, AsPath=route_as_path)
            except Exception:
                pass
            if afi_key == "ipv6-flowspec":
                _fix_ipv6_flowspec_safi(stc, route_cfg, bgp_handle)
            if afi_key == "l2vpn-evpn":
                _configure_evpn_route(stc, route_cfg, args)
            added.append(afi_key)
            print(f"  [OK] Added AFI: {afi_key} ({obj_type} -> {route_cfg})")
        except Exception as e:
            print(f"  [WARN] Failed: {afi_key}: {e}")

    if added:
        stc.apply()
        dev_match.setdefault("negotiated_afis", []).extend(added)
        save_session(sess)

        print(f"\n[OK] Added {len(added)} AFI(s). Restarting BGP to renegotiate...")
        device_handle = dev_match["handle"]
        try:
            stc.perform("DeviceStopCommand", DeviceList=device_handle)
            time.sleep(2)
            stc.perform("DeviceStartCommand", DeviceList=device_handle)
            print("[OK] BGP session restarting -- PE should now negotiate the new AFIs.")
        except Exception as e:
            print(f"[WARN] Could not restart device: {e}")
            print("[INFO] Manually restart: spirent_tool.py protocol-stop && protocol-start")
    else:
        print("[INFO] No new AFIs added.")


def cmd_bgp_status(args):
    """Show BGP session state and route counts for emulated devices.
    STC BgpRouterResults is UNRELIABLE (always N/A). Use --verify-dut for ground truth."""
    config = load_config()
    stc, sess = _require_ready(config)

    devices = sess.get("devices", [])
    if not devices:
        print("No emulated devices in session. Run 'create-device' first.")
        return

    if args.device_name:
        devices = [d for d in devices if d["name"] == args.device_name]
        if not devices:
            print(f"Device '{args.device_name}' not found.")
            sys.exit(1)

    verify_dut = getattr(args, "verify_dut", False)
    idle_classify = getattr(args, "idle_classify", False)
    idle_threshold = int(getattr(args, "idle_threshold", 30) or 30)
    if idle_classify:
        verify_dut = True  # idle classification needs DUT-side ground truth
    dut_bgp_summary = {}      # peer_ip -> raw_state
    dut_bgp_idle = {}         # peer_ip -> idle_seconds (-1 = never)
    if verify_dut:
        dut_ip = getattr(args, "dut_ip", "") or config.get("dut_mgmt_ip", "")
        if dut_ip:
            try:
                from scaler.dnos_session import DNOSSession
                with DNOSSession(dut_ip, "dnroot", "dnroot") as ssh:
                    for afi_cmd in ["show bgp l2vpn evpn summary | no-more",
                                    "show bgp l2vpn vpls summary | no-more",
                                    "show bgp summary | no-more"]:
                        dut_out = ssh.send_command(afi_cmd)
                        for line in dut_out.splitlines():
                            for dev in devices:
                                peer_ip = dev.get("ip", "")
                                if peer_ip and peer_ip in line:
                                    cols = line.split()
                                    dut_state = cols[-1] if cols else "?"
                                    dut_bgp_summary[peer_ip] = dut_state
                                    if idle_classify:
                                        # Parse Up/Down column (HH:MM:SS, NdNh, NwNd, or 'never')
                                        idle = 0
                                        for c in cols:
                                            if re.match(r"^\d{1,2}:\d{2}:\d{2}$", c):
                                                h, mi, s = c.split(":")
                                                idle = int(h) * 3600 + int(mi) * 60 + int(s)
                                                break
                                            if re.match(r"^\d+d\d+h$", c):
                                                m = re.match(r"^(\d+)d(\d+)h$", c)
                                                idle = int(m.group(1)) * 86400 + int(m.group(2)) * 3600
                                                break
                                            if re.match(r"^\d+w\d+d$", c):
                                                m = re.match(r"^(\d+)w(\d+)d$", c)
                                                idle = int(m.group(1)) * 604800 + int(m.group(2)) * 86400
                                                break
                                            if c.lower() == "never":
                                                idle = -1
                                                break
                                        dut_bgp_idle[peer_ip] = idle
            except Exception as e:
                print(f"[WARN] DUT verification failed: {e}")

    out = []
    for dev in devices:
        bgp_handle = dev.get("bgp_handle")
        entry = {"device": dev["name"], "ip": dev.get("ip", "?")}

        if not bgp_handle:
            entry["bgp"] = "not configured"
            out.append(entry)
            continue

        try:
            results_handle = stc.get(bgp_handle, "children-BgpRouterResults")
            if results_handle:
                rh = results_handle.split()[0]
                results = stc.get(rh)
                entry["stc_state"] = results.get("SessionState", "N/A")
                entry["routes_advertised"] = results.get("RoutesAdvertised", "0")
                entry["routes_received"] = results.get("RoutesReceived", "0")
            else:
                entry["stc_state"] = "no results"
        except Exception as e:
            entry["stc_state_error"] = str(e)

        peer_ip = dev.get("ip", "")
        if peer_ip in dut_bgp_summary:
            entry["dut_state"] = dut_bgp_summary[peer_ip]
        elif verify_dut:
            entry["dut_state"] = "NOT_FOUND"

        if idle_classify and peer_ip in dut_bgp_summary:
            raw = dut_bgp_summary[peer_ip]
            idle = dut_bgp_idle.get(peer_ip, 0)
            entry["idle_sec"] = idle
            BAD = {"idle", "connect", "active", "opensent", "openconfirm", "down"}
            if raw.isdigit() or raw.lower() == "established":
                entry["classification"] = "ESTABLISHED"
                entry["is_dead"] = False
            elif idle == -1:
                entry["classification"] = "NEVER"
                entry["is_dead"] = True
            elif raw.lower() in BAD and idle >= idle_threshold:
                entry["classification"] = "DEAD"
                entry["is_dead"] = True
            elif raw.lower() in BAD:
                entry["classification"] = "STARTING"
                entry["is_dead"] = False
            else:
                entry["classification"] = "UNKNOWN"
                entry["is_dead"] = False

        stc_state = entry.get("stc_state", "N/A")
        if stc_state == "N/A" and not verify_dut:
            entry["note"] = "STC state unreliable -- use --verify-dut for ground truth"

        out.append(entry)

    if args.json_output:
        print(json.dumps(out, indent=2))
    else:
        print("=== BGP Session Status ===")
        if not verify_dut:
            print("  [NOTE] STC BgpRouterResults is unreliable. Add --verify-dut for DUT-side state.\n")
        for r in out:
            dev_name = r.get("device", "?")
            print(f"\n  {dev_name} ({r.get('ip', '?')}):")
            for k, v in r.items():
                if k not in ("device", "ip"):
                    print(f"    {k}: {v}")


# ────────────────────────────────────────────
# Phase 2: Route Scale Advertising
# ────────────────────────────────────────────

def cmd_add_routes(args):
    """Add route blocks to a BGP router (IPv4, IPv6, VPNv4, VPNv6)."""
    config = load_config()
    stc, sess = _require_ready(config)
    _, dev_match = _require_device(stc, sess, args.device_name)

    bgp_handle = dev_match.get("bgp_handle")
    if not bgp_handle:
        print(f"ERROR: Device '{args.device_name}' has no BGP config. Run 'bgp-peer' first.")
        sys.exit(1)
    next_hop = args.next_hop or dev_match["ip"]
    peer_as = dev_match.get("as_num", 65200)
    dut_as = dev_match.get("dut_as", 0)
    as_path = args.as_path or ("" if peer_as == dut_as else str(peer_as))

    if args.afi in ("ipv4", "ipv4-unicast"):
        route_cfg = stc.create(
            "BgpIpv4RouteConfig",
            under=bgp_handle,
            NextHop=next_hop,
            AsPath=as_path,
        )
        net_block = stc.get(route_cfg, "children-Ipv4NetworkBlock")
        if net_block:
            nb = net_block.split()[0]
            stc.config(
                nb,
                StartIpList=args.prefix,
                PrefixLength=str(args.prefix_length),
                NetworkCount=str(args.count),
                AddrIncrement="1",
            )
        stc.apply()
        print(f"Added {args.count} IPv4 routes: {args.prefix}/{args.prefix_length}")

    elif args.afi in ("ipv6", "ipv6-unicast"):
        route_cfg = stc.create(
            "BgpIpv6RouteConfig",
            under=bgp_handle,
            NextHop=next_hop,
            AsPath=as_path,
        )
        net_block = stc.get(route_cfg, "children-Ipv6NetworkBlock")
        if net_block:
            nb = net_block.split()[0]
            stc.config(
                nb,
                StartIpList=args.prefix,
                PrefixLength=str(args.prefix_length),
                NetworkCount=str(args.count),
                AddrIncrement="1",
            )
        stc.apply()
        print(f"Added {args.count} IPv6 routes: {args.prefix}/{args.prefix_length}")

    elif args.afi in ("vpnv4", "vpnv4-unicast"):
        if not args.rd or not args.rt:
            print("ERROR: VPN routes require --rd and --rt")
            sys.exit(1)
        route_cfg = stc.create(
            "BgpVpnRouteConfig",
            under=bgp_handle,
            NextHop=next_hop,
            AsPath=as_path,
            RouteDistinguisher=args.rd,
            RouteTarget=args.rt,
        )
        net_block = stc.get(route_cfg, "children-Ipv4NetworkBlock")
        if net_block:
            nb = net_block.split()[0]
            stc.config(
                nb,
                StartIpList=args.prefix,
                PrefixLength=str(args.prefix_length),
                NetworkCount=str(args.count),
                AddrIncrement="1",
            )
        stc.apply()
        print(f"Added {args.count} VPNv4 routes: {args.prefix}/{args.prefix_length} (RD={args.rd}, RT={args.rt})")

    elif args.afi in ("vpnv6", "vpnv6-unicast"):
        if not args.rd or not args.rt:
            print("ERROR: VPN routes require --rd and --rt")
            sys.exit(1)
        route_cfg = stc.create(
            "BgpVpnIpv6RouteConfig",
            under=bgp_handle,
            NextHop=next_hop,
            AsPath=as_path,
            RouteDistinguisher=args.rd,
            RouteTarget=args.rt,
        )
        net_block = stc.get(route_cfg, "children-Ipv6NetworkBlock")
        if net_block:
            nb = net_block.split()[0]
            stc.config(
                nb,
                StartIpList=args.prefix,
                PrefixLength=str(args.prefix_length),
                NetworkCount=str(args.count),
                AddrIncrement="1",
            )
        stc.apply()
        print(f"Added {args.count} VPNv6 routes: {args.prefix}/{args.prefix_length} (RD={args.rd}, RT={args.rt})")

    elif args.afi == "flowspec":
        base_prefix = args.dst_prefix or args.prefix
        dst_len = args.dst_prefix_length
        count = min(args.count, 500)  # Cap at 500 for safety
        try:
            # Parse base: e.g. 100.0.0.0 -> (100, 0, 0)
            parts = base_prefix.split(".")
            if len(parts) != 4:
                print("ERROR: FlowSpec prefix must be IPv4 (e.g. 100.0.0.0)")
                sys.exit(1)
            a, b, c, _ = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
            added = 0
            for i in range(count):
                dst_prefix = f"{a}.{b}.{c + i}.0"
                flowspec = stc.create(
                    "BgpFlowSpecConfig",
                    under=bgp_handle,
                    DestinationPrefix=dst_prefix,
                    DestinationPrefixLength=str(dst_len),
                )
                if args.action == "redirect-ip" and args.redirect_target:
                    stc.config(flowspec, RedirectIpNextHop=args.redirect_target)
                elif args.action == "drop":
                    stc.config(flowspec, TrafficRate="0")
                added += 1
            stc.apply()
            print(f"Added {added} FlowSpec rules: {base_prefix}/{dst_len} x{count} action={args.action}")
        except Exception as e:
            print(f"FlowSpec not supported in this STC version: {e}")
            print("Use ExaBGP or /BGP for FlowSpec injection.")
            raise

    else:
        print(f"ERROR: Unsupported AFI: {args.afi}")
        sys.exit(1)


# ────────────────────────────────────────────
# EVPN Route Injection (RT-2 MAC/IP Advertisement)
# ────────────────────────────────────────────


def cmd_evpn_routes(args):
    """Add EVPN RT-2 (MAC/IP Advertisement) routes to an existing BGP device."""
    config = load_config()
    stc, sess = _require_ready(config)

    _, dev_match = _require_device(stc, sess, args.device_name)
    bgp_handle = dev_match.get("bgp_handle")
    if not bgp_handle:
        print(f"ERROR: No BGP on '{args.device_name}'. Run 'bgp-peer' first.")
        sys.exit(1)

    rd = args.rd or "3.3.3.3:100"
    rt = args.rt or "100:100"
    mac = args.mac or "00:DE:AD:00:01:01"
    label = args.label or 16000
    mac_count = args.count or 1
    mac_step = args.mac_step or "00:00:00:00:00:01"
    eth_tag = args.ethernet_tag or 0
    seq = args.seq_num or 0
    include_mobility = not args.no_mac_mobility

    peer_as = dev_match.get("as_num", 65000)
    dut_as = dev_match.get("dut_as", 0)
    is_ibgp = peer_as == dut_as
    as_path = "" if is_ibgp else str(peer_as)

    sticky = getattr(args, 'sticky', False)

    evpn_attrs = {
        "RouteDistinguisher": rd,
        "RouteTarget": rt,
        "ExtCommunityEviRouteTarget": rt,
        "DataPlaneEncap": "MPLS",
        "MplsLabel": str(label),
        "EthernetTagId": str(eth_tag),
        "EviCount": "1",
        "Origin": "IGP",
        "IncludeMacMobility": "TRUE" if include_mobility else "FALSE",
        "SequenceNumber": str(seq),
        "IsStatic": "TRUE" if sticky else "FALSE",
        "AsPath": as_path,
    }

    nh = args.next_hop or dev_match.get("ip")
    if nh:
        evpn_attrs["NextHop"] = nh

    # Clean stale BgpEvpnMacAdvRouteConfig objects to prevent route accumulation.
    # Each previous evpn-routes call added a new config; bulk routes under one
    # BGP handle cause session disruption during stc.apply().
    existing_evpn_routes = dev_match.get("evpn_routes", [])
    for old_route in list(existing_evpn_routes):
        old_handle = old_route.get("handle", "")
        if not old_handle:
            continue
        try:
            stc.delete(old_handle)
            print(f"  [CLEANUP] Removed stale route config: {old_handle}")
        except Exception:
            pass
    dev_match["evpn_routes"] = []

    route_cfg = stc.create("BgpEvpnMacAdvRouteConfig", under=bgp_handle, **evpn_attrs)
    print(f"  [OK] Created BgpEvpnMacAdvRouteConfig: {route_cfg}")

    mac_block = stc.get(route_cfg, "children-MacBlock")
    if mac_block:
        mb = mac_block.split()[0]
        mac_step_int = mac_step
        if ":" in str(mac_step):
            mac_step_int = str(int(mac_step.replace(":", ""), 16))
        stc.config(mb, StartMacList=mac, NetworkCount=str(mac_count),
                   AddrIncrement=mac_step_int)
        print(f"  [OK] MacBlock: start={mac}, count={mac_count}, step={mac_step}")

    if args.ip:
        try:
            ip_block = stc.get(route_cfg, "children-Ipv4NetworkBlock")
            if ip_block:
                nb = ip_block.split()[0]
                stc.config(nb, StartIpList=args.ip, PrefixLength="32", NetworkCount=str(mac_count))
                print(f"  [OK] IPv4 binding: {args.ip}")
        except Exception as e:
            print(f"  [WARN] IPv4 binding failed: {e}")

    stc.apply()

    dev_match.setdefault("evpn_routes", []).append({
        "handle": route_cfg,
        "rd": rd, "rt": rt, "mac": mac, "label": label,
        "count": mac_count, "seq": seq, "mac_mobility": include_mobility,
        "sticky": sticky,
    })
    save_session(sess)

    restart = not args.no_restart
    if restart:
        device_handle = dev_match["handle"]
        print("Restarting device to advertise EVPN routes...")
        try:
            stc.perform("DeviceStopCommand", DeviceList=device_handle)
            time.sleep(2)
            stc.perform("DeviceStartCommand", DeviceList=device_handle)
            time.sleep(3)
            print("[OK] Device restarted. EVPN RT-2 routes should be advertised.")
        except Exception as e:
            print(f"[WARN] Restart failed: {e}. Try: protocol-stop && protocol-start")
    else:
        # Force BGP UPDATE for new routes. If BgpReadvertiseRouteCommand fails,
        # fall back to a brief device stop/start cycle.
        try:
            stc.perform("BgpReadvertiseRouteCommand", RouterList=bgp_handle)
            print("  [OK] Forced BGP re-advertisement (no-restart mode)")
        except Exception as e:
            print(f"  [WARN] BgpReadvertiseRouteCommand failed ({e}), falling back to device restart")
            try:
                device_handle = dev_match["handle"]
                stc.perform("DeviceStopCommand", DeviceList=device_handle)
                time.sleep(1)
                stc.perform("DeviceStartCommand", DeviceList=device_handle)
                time.sleep(3)
                print("  [OK] Device restarted as fallback for route advertisement")
            except Exception as e2:
                print(f"  [WARN] Fallback restart also failed: {e2}")

    print(f"\n[OK] EVPN RT-2 summary:")
    print(f"  RD={rd}  RT={rt}  Label={label}")
    print(f"  MAC={mac} x{mac_count}  EthTag={eth_tag}  SeqNum={seq}")
    print(f"  MAC Mobility={'enabled' if include_mobility else 'disabled'}  Sticky={'YES' if sticky else 'no'}")
    if nh:
        print(f"  NextHop={nh}")
    print(f"\nVerify on DUT: show evpn mac-table detail instance <name> | no-more")
    print(f"               show bgp l2vpn evpn | no-more")


def cmd_withdraw_routes(args):
    """Withdraw routes already advertised by an emulated BGP device.

    Selection rules (in order):
      1. --route-handle <H>  : withdraw exactly that BgpEvpnMacAdvRouteConfig handle
      2. --rd / --mac        : match against tracked routes in the session JSON
      3. --afi l2vpn-evpn    : withdraw ALL EVPN MAC routes from the device
      4. (no filter)         : withdraw ALL routes the session knows about

    Implementation detail: STC withdraws at the route-config object granularity
    via BgpWithdrawRouteCommand, not per-MAC. So when the route-config holds a
    MacBlock of N MACs, withdrawing it pulls all N. To withdraw a single MAC
    when multiple were created in one block, use evpn-routes again with a
    filtered MacBlock first, or rely on the protocol-stop fallback that the
    caller (mac_trigger.spirent_withdraw_evpn_mac_route) already implements.
    """
    config = load_config()
    stc, sess = _require_ready(config)

    _, dev_match = _require_device(stc, sess, args.device_name)

    bgp_handle = dev_match.get("bgp_handle")
    if not bgp_handle:
        print(f"ERROR: No BGP on '{args.device_name}'. Run 'bgp-peer' first.")
        sys.exit(1)

    routes = list(dev_match.get("evpn_routes", []))
    if not routes:
        print(f"[INFO] No tracked EVPN routes on '{args.device_name}' -- nothing to withdraw.")
        return

    selected: list = []
    if getattr(args, "route_handle", None):
        selected = [r for r in routes if r.get("handle") == args.route_handle]
        if not selected:
            print(f"ERROR: route-handle {args.route_handle} not found on device '{args.device_name}'")
            sys.exit(1)
    elif getattr(args, "rd", None) or getattr(args, "mac", None):
        for r in routes:
            if args.rd and (r.get("rd") or "").lower() != args.rd.lower():
                continue
            if args.mac and (r.get("mac") or "").lower() != args.mac.lower():
                continue
            selected.append(r)
        if not selected:
            print(f"[INFO] No tracked routes match rd={args.rd} mac={args.mac}; nothing to withdraw.")
            return
    else:
        selected = routes

    afi = (getattr(args, "afi", None) or "").strip().lower()
    if afi and afi not in ("", "l2vpn-evpn", "evpn"):
        print(f"[WARN] Unsupported --afi '{afi}'; only l2vpn-evpn is implemented. "
              f"Withdrawing the selected EVPN routes anyway.")

    withdrawn = []
    failed = []
    for r in selected:
        h = r.get("handle")
        if not h:
            continue
        try:
            stc.perform("BgpWithdrawRouteCommand", RouteList=h)
            withdrawn.append({"handle": h, "rd": r.get("rd"), "mac": r.get("mac"),
                              "count": r.get("count")})
            print(f"  [OK] Withdrew route {h} (rd={r.get('rd')}, mac={r.get('mac')})")
        except Exception as e:
            failed.append({"handle": h, "error": str(e)})
            print(f"  [WARN] BgpWithdrawRouteCommand failed for {h}: {e}")

    try:
        stc.apply()
    except Exception as e:
        print(f"  [WARN] stc.apply() after withdraw failed: {e}")

    keep = [r for r in routes if r not in selected]
    dev_match["evpn_routes"] = keep
    save_session(sess)

    if getattr(args, "json_output", False):
        print(json.dumps({
            "device": args.device_name,
            "withdrawn_count": len(withdrawn),
            "withdrawn": withdrawn,
            "failed": failed,
        }, indent=2))
    else:
        print(f"\n[OK] Withdraw summary for {args.device_name}:")
        print(f"  Withdrawn: {len(withdrawn)} route-config(s)")
        if failed:
            print(f"  Failed:    {len(failed)}")
        print(f"  Remaining tracked routes: {len(keep)}")


def cmd_evpn_rt1(args):
    """Inject EVPN RT-1 (Ethernet Auto-Discovery) route for MH testing."""
    config = load_config()
    stc, sess = _require_ready(config)

    _, dev_match = _require_device(stc, sess, args.device_name)
    bgp_handle = dev_match.get("bgp_handle")
    if not bgp_handle:
        print(f"ERROR: No BGP on '{args.device_name}'. Run 'bgp-peer' first.")
        sys.exit(1)

    rd = args.rd or f"{dev_match.get('ip', '10.99.99.1')}:100"
    rt = args.rt or "100:100"
    esi = args.esi
    label = args.label or 0
    sub_type = args.sub_type

    peer_as = dev_match.get("as_num", 65000)
    dut_as = dev_match.get("dut_as", 0)
    is_ibgp = peer_as == dut_as
    as_path = "" if is_ibgp else str(peer_as)

    eth_tag = args.evi if sub_type == "per_evi" else 0xFFFFFFFF
    ad_route_type = "PER_EVI" if sub_type == "per_evi" else "PER_ESI"

    rt1_attrs = {
        "RouteDistinguisher": rd,
        "RouteTarget": rt,
        "EthernetSegmentId": esi,
        "EthernetTagId": str(eth_tag),
        "EvpnADRouteType": ad_route_type,
        "Origin": "IGP",
        "AsPath": as_path,
    }
    if label > 0:
        rt1_attrs["MplsLabel"] = str(label)

    nh = dev_match.get("ip")
    if nh:
        rt1_attrs["NextHop"] = nh

    try:
        route_cfg = stc.create("BgpEvpnAdRouteConfig", under=bgp_handle, **rt1_attrs)
        print(f"  [OK] Created BgpEvpnAdRouteConfig ({sub_type}): {route_cfg}")
    except Exception as e:
        print(f"  [ERROR] Failed to create RT-1: {e}")
        print(f"  [INFO] Verify STC API version supports BgpEvpnAdRouteConfig.")
        sys.exit(1)

    stc.apply()

    dev_match.setdefault("evpn_rt1_routes", []).append({
        "handle": route_cfg,
        "esi": esi, "rd": rd, "rt": rt,
        "sub_type": sub_type, "eth_tag": eth_tag,
    })
    save_session(sess)

    restart = not args.no_restart
    if restart:
        device_handle = dev_match["handle"]
        print("Restarting device to advertise EVPN RT-1 route...")
        try:
            stc.perform("DeviceStopCommand", DeviceList=device_handle)
            time.sleep(2)
            stc.perform("DeviceStartCommand", DeviceList=device_handle)
            time.sleep(3)
            print("[OK] Device restarted. EVPN RT-1 route should be advertised.")
        except Exception as e:
            print(f"[WARN] Restart failed: {e}. Try: protocol-stop && protocol-start")

    print(f"\n[OK] EVPN RT-1 ({sub_type}) summary:")
    print(f"  ESI={esi}  RD={rd}  RT={rt}")
    print(f"  EthernetTag={'per-EVI: ' + str(args.evi) if sub_type == 'per_evi' else 'MAX (per-ES)'}")
    print(f"\nVerify on DUT: show evpn instance <name> ethernet-segments-info | no-more")
    print(f"               show bgp l2vpn evpn route-type ethernet-auto-discovery | no-more")


def cmd_evpn_rt4(args):
    """Inject EVPN RT-4 (Ethernet Segment) route for MH DF election."""
    config = load_config()
    stc, sess = _require_ready(config)

    _, dev_match = _require_device(stc, sess, args.device_name)
    bgp_handle = dev_match.get("bgp_handle")
    if not bgp_handle:
        print(f"ERROR: No BGP on '{args.device_name}'. Run 'bgp-peer' first.")
        sys.exit(1)

    rd = args.rd or f"{dev_match.get('ip', '10.99.99.1')}:100"
    rt = args.rt or "100:100"
    esi = args.esi
    originator_ip = args.originator_ip or dev_match.get("ip", "10.99.99.1")

    peer_as = dev_match.get("as_num", 65000)
    dut_as = dev_match.get("dut_as", 0)
    is_ibgp = peer_as == dut_as
    as_path = "" if is_ibgp else str(peer_as)

    rt4_attrs = {
        "RouteDistinguisher": rd,
        "RouteTarget": rt,
        "EthernetSegmentId": esi,
        "OriginatingRouterIpv4Addr": originator_ip,
        "Origin": "IGP",
        "AsPath": as_path,
    }

    nh = dev_match.get("ip")
    if nh:
        rt4_attrs["NextHop"] = nh

    try:
        route_cfg = stc.create("BgpEvpnEthernetSegmentRouteConfig", under=bgp_handle, **rt4_attrs)
        print(f"  [OK] Created BgpEvpnEthernetSegmentRouteConfig: {route_cfg}")
    except Exception as e:
        print(f"  [ERROR] Failed to create RT-4: {e}")
        print(f"  [INFO] This STC version may not support BgpEvpnEthernetSegmentRouteConfig.")
        print(f"  [INFO] Check STC API version and EVPN capabilities.")
        sys.exit(1)

    stc.apply()

    dev_match.setdefault("evpn_rt4_routes", []).append({
        "handle": route_cfg,
        "esi": esi, "rd": rd, "rt": rt,
        "originator_ip": originator_ip,
    })
    save_session(sess)

    restart = not args.no_restart
    if restart:
        device_handle = dev_match["handle"]
        print("Restarting device to advertise EVPN RT-4 route...")
        try:
            stc.perform("DeviceStopCommand", DeviceList=device_handle)
            time.sleep(2)
            stc.perform("DeviceStartCommand", DeviceList=device_handle)
            time.sleep(3)
            print("[OK] Device restarted. EVPN RT-4 (ES) route should be advertised.")
        except Exception as e:
            print(f"[WARN] Restart failed: {e}. Try: protocol-stop && protocol-start")

    print(f"\n[OK] EVPN RT-4 (ES Route) summary:")
    print(f"  ESI={esi}  RD={rd}  RT={rt}")
    print(f"  OriginatorIP={originator_ip}")
    print(f"\nVerify on DUT: show evpn instance <name> ethernet-segments-info | no-more")
    print(f"               show bgp l2vpn evpn route-type ethernet-segment | no-more")
    print(f"               show dnos-internal routing evpn instance <name> vpls-df-info | no-more")


# ────────────────────────────────────────────
# Phase 3: ECMP (Multiple BGP Peers)
# ────────────────────────────────────────────

def _ip_step_str(step):
    """Convert integer step to dotted-quad IP step string. e.g. 1->'0.0.0.1', 256->'0.0.1.0'."""
    if isinstance(step, str) and '.' in step:
        return step
    step = int(step)
    return f"{(step >> 24) & 0xFF}.{(step >> 16) & 0xFF}.{(step >> 8) & 0xFF}.{step & 0xFF}"


def _mac_step_str(step):
    """Convert integer step to MAC step string. e.g. 1->'00:00:00:00:00:01'."""
    if isinstance(step, str) and ':' in step:
        return step
    step = int(step)
    parts = []
    for _ in range(6):
        parts.append(f"{step & 0xFF:02x}")
        step >>= 8
    return ":".join(reversed(parts))


def _validate_subnet(base_ip, count, prefix_len=24):
    """Validate that count peers fit in the subnet starting at base_ip."""
    import ipaddress
    base = ipaddress.IPv4Address(base_ip)
    last = base + (count - 1)
    network = ipaddress.IPv4Network(f"{base_ip}/{prefix_len}", strict=False)
    if last not in network:
        raise ValueError(
            f"Subnet overflow: {count} peers from {base_ip}/{prefix_len} "
            f"would reach {last}, outside {network}. Reduce --count or use a larger subnet."
        )
    return str(last)


def _clean_stale_devices(stc, project, sess):
    """Remove only stale ECMP_Block devices, preserving all other emulated devices.
    Only targets devices whose name starts with 'ECMP_Block' to avoid destroying
    VRF CE peers or other independently created devices.
    """
    try:
        children = stc.get(project, "children-EmulatedDevice")
        if not children:
            return 0
        handles = children.split()
        removed = 0
        preserved = 0
        for h in handles:
            try:
                name = stc.get(h, "Name")
                if name.startswith("ECMP_Block"):
                    stc.delete(h)
                    removed += 1
                    print(f"  [CLEANUP] Removed stale ECMP device: {name} ({h})")
                    sess["devices"] = [
                        d for d in sess.get("devices", [])
                        if d.get("handle") != h and d.get("name") != name
                    ]
                else:
                    preserved += 1
                    print(f"  [KEEP] Preserved device: {name} ({h})")
            except Exception as e:
                print(f"  [WARN] Could not inspect {h}: {e}")
        if removed:
            save_session(sess)
            stc.apply()
        if preserved:
            print(f"  [OK] {preserved} non-ECMP device(s) preserved")
        return removed
    except Exception:
        return 0


def _gen_dnos_neighbor_group_config(base_ip, count, ip_step, as_num, dut_as, gateway):
    """Generate DNOS neighbor-group + neighbor config for DUT-side BGP.
    Returns the config string ready for validate_config / SSH apply.
    """
    import ipaddress
    lines = []
    lines.append("protocols")
    lines.append(f"  bgp {dut_as}")
    lines.append(f"    neighbor-group SPIRENT_ECMP")
    lines.append(f"      remote-as {as_num}")
    lines.append(f"      address-family ipv4-unicast")
    lines.append(f"        send-community community-type both")
    lines.append(f"        soft-reconfiguration inbound")
    lines.append(f"      !")
    lines.append(f"    !")

    step_int = sum(int(o) << (8 * (3 - i)) for i, o in enumerate(ip_step.split(".")))
    base = ipaddress.IPv4Address(base_ip)
    for i in range(count):
        peer_ip = str(base + (i * step_int))
        lines.append(f"    neighbor {peer_ip}")
        lines.append(f"      neighbor-group SPIRENT_ECMP")
        lines.append(f"    !")

    lines.append("  !")
    lines.append("!")
    return "\n".join(lines)


def _query_bgp_block_established(stc, device_handle, count):
    """One-shot BGP convergence query against STC. Returns (established_count, total)
    or (None, total) when the BGP block is not yet present (e.g. DeviceStartCommand
    still propagating).

    Pure read: no sleeps, no retries -- safe to call from poll_until.
    """
    bgp_children = stc.get(device_handle, "children-BgpRouterConfig")
    if not bgp_children:
        return None, count
    bgp_handle = bgp_children.split()[0]
    results = stc.get(bgp_handle)
    block_state = results.get("BlockState", "")
    established = 0

    if block_state == "ALL_ESTABLISHED" or block_state == "ESTABLISHED":
        established = count
    elif "BlockState" in results and ("MIXED" in block_state or "SOME" in block_state):
        try:
            result_child = stc.get(bgp_handle, "children-BgpRouterResults")
            if result_child:
                r = stc.get(result_child.split()[0])
                established = int(r.get("SessionsEstablished", 0))
        except Exception:
            pass

    if established == 0:
        try:
            result_child = stc.get(bgp_handle, "children-BgpRouterResults")
            if result_child:
                r = stc.get(result_child.split()[0])
                established = int(r.get("SessionsEstablished", 0))
        except Exception:
            pass

    return established, count


def _wait_bgp_convergence(stc, device_handle, count, timeout_sec, port):
    """Poll BGP session states until all are ESTABLISHED or timeout.
    Returns (established_count, total_count).
    Retries ARP every 15 seconds if sessions are stuck.

    Uses the canonical `poll_until` primitive from scaler.validators when
    available. Falls back to a legacy local poll loop only if the validators
    layer is not importable (e.g. very stripped-down environment).
    """
    if poll_until is None:
        return _wait_bgp_convergence_legacy(stc, device_handle, count, timeout_sec, port)

    poll_interval = 5
    arp_retry_interval = 15
    state = {"last_arp_at": time.time(), "best_established": 0}

    def _condition():
        try:
            established, total = _query_bgp_block_established(stc, device_handle, count)
        except Exception as exc:
            return False, {"error": f"{exc.__class__.__name__}: {exc}",
                           "established": state["best_established"], "total": count}
        if established is None:
            return False, {"established": 0, "total": count, "stage": "no_bgp_yet"}
        state["best_established"] = max(state["best_established"], established)
        return (established >= total), {"established": established, "total": total}

    def _on_progress(elapsed, observed):
        est = observed.get("established", "?") if isinstance(observed, dict) else "?"
        tot = observed.get("total", count) if isinstance(observed, dict) else count
        print(f"  [{int(elapsed)}s] BGP: {est}/{tot} established", flush=True)

        # ARP retry trigger -- preserves legacy 15s ARP nudge behavior.
        now = time.time()
        if (now - state["last_arp_at"]) >= arp_retry_interval:
            current = observed.get("established", 0) if isinstance(observed, dict) else 0
            if current < count:
                print(f"  [ARP] Retrying ARP/ND resolution...", flush=True)
                try:
                    stc.perform("ArpNdStartCommand", HandleList=port)
                except Exception:
                    pass
                state["last_arp_at"] = now

    res = poll_until(
        _condition,
        timeout_sec=timeout_sec,
        interval_sec=poll_interval,
        on_progress=_on_progress,
        progress_every=1,
    )
    elapsed = int(res.elapsed_sec)
    if res.passed:
        print(f"  [OK] All {count} BGP sessions ESTABLISHED in {elapsed}s")
        return count, count
    print(f"  [TIMEOUT] {state['best_established']}/{count} established after {elapsed}s")
    return state["best_established"], count


def _wait_bgp_convergence_legacy(stc, device_handle, count, timeout_sec, port):
    """Pre-validators implementation, kept as a safety fallback when
    scaler.validators is not importable. Identical semantics to the
    poll_until-based path.
    """
    start = time.time()
    poll_interval = 5
    arp_retry_interval = 15
    last_arp = start
    best_established = 0

    while (time.time() - start) < timeout_sec:
        try:
            established, total = _query_bgp_block_established(stc, device_handle, count)
            if established is None:
                time.sleep(poll_interval)
                continue
            best_established = max(best_established, established)
            elapsed = int(time.time() - start)
            print(f"  [{elapsed}s] BGP: {established}/{total} established", flush=True)
            if established >= total:
                print(f"  [OK] All {total} BGP sessions ESTABLISHED in {elapsed}s")
                return established, total
            now = time.time()
            if (now - last_arp) >= arp_retry_interval and established < total:
                print(f"  [ARP] Retrying ARP/ND resolution...", flush=True)
                try:
                    stc.perform("ArpNdStartCommand", HandleList=port)
                except Exception:
                    pass
                last_arp = now
        except Exception as e:
            print(f"  [WARN] Poll error: {e}")
        time.sleep(poll_interval)

    elapsed = int(time.time() - start)
    print(f"  [TIMEOUT] {best_established}/{count} established after {elapsed}s")
    return best_established, count


def cmd_ecmp(args):
    """Create N BGP peers via STC Device Block (DeviceCount + step values).

    Uses STC's multiplier architecture: ONE EmulatedDevice with DeviceCount=N.
    STC auto-expands to N logical peers using AddrStep/SrcMacStep/RouterIdStep.
    This produces ~15 REST calls total regardless of N, vs ~10*N with the loop approach.
    """
    config = load_config()
    stc, sess = _require_ready(config)
    project = sess["project_handle"]
    port = sess["port_handle"]

    base_ip = args.base_ip or "10.99.212.10"
    gateway = args.gateway or "10.99.212.2"
    ip_step = _ip_step_str(getattr(args, "ip_step", 1) or 1)
    mac_step = _mac_step_str(getattr(args, "mac_step", 1) or 1)
    base_mac = args.mac or "00:10:94:00:00:0a"
    count = args.count

    last_ip = _validate_subnet(base_ip, count)
    print(f"[OK] Subnet check: {count} peers from {base_ip} to {last_ip} fit in /24")

    if getattr(args, "clean_stale", True):
        removed = _clean_stale_devices(stc, project, sess)
        if removed:
            print(f"[OK] Cleaned {removed} stale device(s)")

    if getattr(args, "gen_dut_config", False):
        dut_cfg = _gen_dnos_neighbor_group_config(
            base_ip, count, ip_step, args.as_num, args.dut_as, gateway
        )
        print("\n--- DNOS DUT Config (copy/paste or apply via Network Mapper) ---")
        print(dut_cfg)
        print("--- End DUT Config ---\n")

    use_4byte = args.as_num > 65535 or args.dut_as > 65535

    device = stc.create(
        "EmulatedDevice",
        under=project,
        Name="ECMP_Block",
        DeviceCount=str(count),
        EnablePingResponse="TRUE",
        RouterId=base_ip,
        RouterIdStep=ip_step,
    )

    eth = stc.create("EthIIIf", under=device, SourceMac=base_mac, SrcMacStep=mac_step)

    ipv4 = stc.create(
        "Ipv4If",
        under=device,
        Address=base_ip,
        AddrStep=ip_step,
        Gateway=gateway,
        GatewayStep="0.0.0.0",
        PrefixLength="24",
    )

    stc.config(device, **{"TopLevelIf-targets": [ipv4]})
    stc.config(device, **{"PrimaryIf-targets": [ipv4]})

    if args.vlan:
        outer_vlan_if = stc.create("VlanIf", under=device, VlanId=str(args.vlan), IdStep="0")
        inner_vlan = getattr(args, "inner_vlan", None)
        if inner_vlan:
            inner_vlan_if = stc.create("VlanIf", under=device, VlanId=str(inner_vlan), IdStep="0")
            stc.config(ipv4, **{"StackedOnEndpoint-targets": [inner_vlan_if]})
            stc.config(inner_vlan_if, **{"StackedOnEndpoint-targets": [outer_vlan_if]})
            stc.config(outer_vlan_if, **{"StackedOnEndpoint-targets": [eth]})
        else:
            stc.config(ipv4, **{"StackedOnEndpoint-targets": [outer_vlan_if]})
            stc.config(outer_vlan_if, **{"StackedOnEndpoint-targets": [eth]})
    else:
        stc.config(ipv4, **{"StackedOnEndpoint-targets": [eth]})

    bgp_attrs = {
        "DutIpv4Addr": gateway,
        "UseGatewayAsDut": "TRUE",
    }
    if use_4byte:
        bgp_attrs["Enable4ByteAsNum"] = "TRUE"
        bgp_attrs["Enable4ByteDutAsNum"] = "TRUE"
        bgp_attrs["AsNum4Byte"] = str(args.as_num)
        bgp_attrs["DutAsNum4Byte"] = str(args.dut_as)
        bgp_attrs["AsNum"] = "23456"  # AS_TRANS per RFC 6793
        bgp_attrs["DutAsNum"] = "23456"
    else:
        bgp_attrs["AsNum"] = str(args.as_num)
        bgp_attrs["DutAsNum"] = str(args.dut_as)

    bgp_attrs["Initiate"] = "FALSE"
    bgp = stc.create("BgpRouterConfig", under=device, **bgp_attrs)

    if count > 1:
        # STC auto-creates per-BgpRouterConfig modifier children (typically an
        # AsNumModifier) to vary attributes across the N emulated peers.  For
        # an ECMP block we want all N peers to share the same AS/DUT-AS so the
        # DUT forms a single ECMP group, so every modifier's StepValue is
        # zeroed.  We log every handle we touch + the pre-reset value so that
        # if STC ever starts creating a modifier we DIDN'T anticipate (e.g.
        # something tied to RouterId / MED / LocalPref), the drift is visible
        # in the log instead of being silently overwritten.
        bgp_children = stc.get(bgp, "children")
        touched = []
        if bgp_children:
            for child_handle in bgp_children.split():
                if "modifier" not in child_handle.lower():
                    continue
                child_name = ""
                prev_step = ""
                try:
                    child_name = stc.get(child_handle, "Name") or ""
                except Exception as e:
                    _swallowed(e, f"cmd_ecmp modifier-name {child_handle}")
                try:
                    prev_step = stc.get(child_handle, "StepValue") or ""
                except Exception as e:
                    _swallowed(e, f"cmd_ecmp modifier-stepvalue {child_handle}")
                reset_ok = False
                try:
                    stc.config(child_handle, StepValue="0")
                    reset_ok = True
                except Exception as e_int:
                    _swallowed(e_int, f"cmd_ecmp modifier-int-step {child_handle}")
                    try:
                        stc.config(child_handle, StepValue="0.0.0.0")
                        reset_ok = True
                    except Exception as e_dot:
                        _swallowed(e_dot, f"cmd_ecmp modifier-dotted-step {child_handle}")
                label = child_name or child_handle.split("::")[0] if "::" in child_handle else (child_name or child_handle)
                touched.append((label, prev_step, "OK" if reset_ok else "FAIL"))
            if touched:
                print(f"  [OK] BGP modifier steps zeroed across {count} devices "
                      f"(constant AS/DUT):")
                for label, prev, status in touched:
                    print(f"        - {label} StepValue {prev!r} -> 0  [{status}]")
            else:
                print(f"  [INFO] No BGP modifier children present on BgpRouterConfig "
                      f"(count={count}); STC will use scalar defaults for all peers.")

    ipv4_children = stc.get(device, "children-Ipv4If")
    if ipv4_children:
        ipv4_handle = ipv4_children.split()[0]
        stc.config(bgp, **{"UsesIf-targets": [ipv4_handle]})

    negotiated_afis = []
    requested_afis = getattr(args, "negotiate_afi", None) or []
    if isinstance(requested_afis, str):
        requested_afis = [a.strip() for a in requested_afis.split(",")]

    afi_map = {
        "ipv4-unicast": ("BgpIpv4RouteConfig", {}),
        "ipv6-unicast": ("BgpIpv6RouteConfig", {}),
        "ipv4-flowspec": ("BgpFlowSpecConfig", {}),
        "ipv6-flowspec": ("BgpIpv6FlowSpecConfig", {}),
        "ipv4-vpn": ("BgpVpnRouteConfig", {}),
        "ipv6-vpn": ("BgpVpnRouteConfig", {"IpVersion": "IPV6"}),
        "l2vpn-vpls": ("BgpIpv4VplsConfig", {}),
        "l2vpn-evpn": ("BgpEvpnMacAdvRouteConfig", {"DataPlaneEncap": "MPLS"}),
    }

    for afi_name in requested_afis:
        if afi_name.lower().strip() == "all":
            requested_afis = list(afi_map.keys())
            break

    ecmp_is_ibgp = args.as_num == args.dut_as
    ecmp_as_path = "" if ecmp_is_ibgp else str(args.as_num)

    for afi_name in requested_afis:
        afi_key = afi_name.lower().strip()
        if afi_key not in afi_map:
            print(f"[WARN] Unknown AFI '{afi_key}', skipping.")
            continue
        obj_type, extra_attrs = afi_map[afi_key]
        try:
            route_cfg = stc.create(obj_type, under=bgp, **extra_attrs)
            stc.config(route_cfg, AsPath=ecmp_as_path)
            if afi_key == "ipv6-flowspec":
                _fix_ipv6_flowspec_safi(stc, route_cfg, bgp)
            negotiated_afis.append(afi_key)
            print(f"  [OK] AFI capability: {afi_key}")
        except Exception as e:
            print(f"  [WARN] Failed AFI {afi_key}: {e}")

    # Only advertise IPv4 unicast routes when ipv4-unicast is in the negotiated
    # set, OR when no AFIs were requested at all (legacy default = IPv4 unicast
    # ECMP). Previously this block was unconditional, so callers asking for
    # pure flowspec or EVPN also ended up advertising 100 extra v4 prefixes.
    should_advertise_v4_unicast = (
        not requested_afis
        or "ipv4-unicast" in negotiated_afis
    )
    if should_advertise_v4_unicast:
        route_cfg = stc.create(
            "BgpIpv4RouteConfig",
            under=bgp,
            NextHop=base_ip,
            AsPath=ecmp_as_path,
        )
        net_block = stc.get(route_cfg, "children-Ipv4NetworkBlock")
        if net_block:
            nb = net_block.split()[0]
            stc.config(
                nb,
                StartIpList=args.prefix,
                PrefixLength="24",
                NetworkCount=str(args.route_count),
                AddrIncrement="1",
            )
    else:
        print(
            f"  [INFO] ipv4-unicast not negotiated ({negotiated_afis}); "
            f"skipping default {args.route_count}-route v4 prefix advertisement."
        )

    stc.config(device, **{"AffiliationPort-targets": [port]})

    stc.apply()

    dev_info = {
        "name": "ECMP_Block",
        "handle": device,
        "ip": base_ip,
        "ip_step": ip_step,
        "mac": base_mac,
        "mac_step": mac_step,
        "device_count": count,
        "gateway": gateway,
        "vlan": args.vlan,
        "inner_vlan": getattr(args, "inner_vlan", None),
        "bgp_handle": bgp,
        "as_num": args.as_num,
        "dut_as": args.dut_as,
        "negotiated_afis": negotiated_afis,
        "route_prefix": args.prefix,
        "route_count": args.route_count,
        "created": datetime.utcnow().isoformat(),
    }
    sess.setdefault("devices", []).append(dev_info)
    save_session(sess)

    print(f"[OK] Created ECMP Device Block: {count} peers via STC multiplier")
    print(f"  Base IP:  {base_ip}  step: {ip_step}")
    print(f"  Base MAC: {base_mac}  step: {mac_step}")
    print(f"  Gateway:  {gateway}")
    print(f"  BGP AS:   {args.as_num} -> DUT AS: {args.dut_as}")
    if negotiated_afis:
        print(f"  AFIs:     {', '.join(negotiated_afis)}")
    print(f"  Routes:   {args.route_count} x {args.prefix}/24 per peer")
    print(f"  REST calls: ~15 (vs ~{count * 10} with loop)")
    print(json.dumps(dev_info, indent=2))

    print("\nStarting ARP and devices...")
    stc.perform("ArpNdStartCommand", HandleList=port)
    time.sleep(2)
    stc.perform("DeviceStartCommand", DeviceList=device)
    stc.apply()
    print(f"ECMP block started ({count} peers).")

    wait_sec = getattr(args, "wait_established", 120)
    if wait_sec > 0:
        print(f"\nWaiting for BGP convergence (timeout {wait_sec}s)...")
        established, total = _wait_bgp_convergence(stc, device, count, wait_sec, port)
        dev_info["established"] = established
        dev_info["convergence_time"] = wait_sec if established < total else None
        save_session(sess)
        if established < total:
            print(f"\n[WARN] Only {established}/{total} sessions established.")
            print("  Possible issues: DUT config missing, ARP failure, or firewall blocking.")
            print("  Use --gen-dut-config to get the DUT-side BGP config.")


def cmd_protocol_start(args):
    """Start protocols (ARP/ND + BGP) on emulated devices."""
    config = load_config()
    stc, sess = _require_ready(config)
    port = sess["port_handle"]
    devices = [d for d in sess.get("devices", []) if d.get("handle")]

    if args.device_name:
        devices = [d for d in devices if d["name"] == args.device_name]
    if not devices:
        print("No devices to start.")
        return

    if args.device_name:
        dev_handles = " ".join(d["handle"] for d in devices)
        stc.perform("ArpNdStartCommand", HandleList=dev_handles)
    else:
        stc.perform("ArpNdStartCommand", HandleList=port)
    time.sleep(2)
    for d in devices:
        stc.perform("DeviceStartCommand", DeviceList=d["handle"])
    stc.apply()
    print(f"Started protocols on {len(devices)} device(s).")


def cmd_protocol_stop(args):
    """Stop protocols on emulated devices."""
    config = load_config()
    stc, sess = _require_ready(config)
    devices = [d for d in sess.get("devices", []) if d.get("handle")]

    if args.device_name:
        devices = [d for d in devices if d["name"] == args.device_name]
    if not devices:
        print("No devices to stop.")
        return

    for d in devices:
        try:
            stc.perform("DeviceStopCommand", DeviceList=d["handle"])
        except Exception as e:
            print(f"Warning stopping {d['name']}: {e}")
    stc.apply()
    print(f"Stopped protocols on {len(devices)} device(s).")


def cmd_list_devices(args):
    """List all emulated devices in the session.

    --names-only:  print one device name per line (script-friendly)
    --json:        emit a JSON array of device records
    default:       human-readable summary
    """
    sess = load_session()
    if not sess:
        if getattr(args, "names_only", False):
            return
        if getattr(args, "json_output", False):
            print("[]")
            return
        print("ERROR: No active session.")
        sys.exit(1)

    devices = sess.get("devices", [])

    if getattr(args, "names_only", False):
        for d in devices:
            name = (d.get("name") or "").strip()
            if name:
                print(name)
        return

    if getattr(args, "json_output", False):
        out = []
        for d in devices:
            out.append({
                "name": d.get("name"),
                "ip": d.get("ip"),
                "gateway": d.get("gateway"),
                "vlan": d.get("vlan"),
                "inner_vlan": d.get("inner_vlan"),
                "mac": d.get("mac"),
                "bgp_configured": bool(d.get("bgp_handle")),
                "as_num": d.get("as_num"),
                "dut_as": d.get("dut_as"),
            })
        print(json.dumps(out, indent=2))
        return

    if not devices:
        print("No emulated devices in session.")
        return

    print("=== Emulated Devices ===")
    for d in devices:
        bgp = "BGP configured" if d.get("bgp_handle") else "no BGP"
        print(f"  {d['name']}: {d['ip']} (gw: {d['gateway']}) vlan={d.get('vlan', 'none')} [{bgp}]")


def cmd_set_stream_active(args):
    """Toggle StreamBlock.Active on one or more streams without destroying them.

    Use case: SC04_pw_to_sticky_ac (and similar mobility scenarios) need to drive
    the DUT with ONLY one Spirent stream at a time (e.g. VPLS PW path during PW
    learn phase, then AC L2 path during sticky re-learn phase). A global
    `start` starts all StreamBlocks in PORT_BASED mode, so mobility phases with
    competing streams race each other -- the PW stream wins in the NPU, MAC
    stays as VPLS, sticky AC never gets the MAC. `set-stream-active` flips the
    StreamBlock.Active flag so only the intended phase's stream transmits on
    the next `start`. Does NOT delete streams, does NOT create/remove devices,
    does NOT restart BGP/protocols -- only one `stc.apply()` per call that
    updates StreamBlock properties (sub-second, non-disruptive to BGP sessions).

    Accepts ``--name`` (single) or ``--names`` (comma-separated list). The
    ``--active`` flag takes ``true`` / ``false`` / ``TRUE`` / ``FALSE`` and is
    normalised before being sent to the BLL.
    """
    config = load_config()
    stc, sess = _require_ready(config)

    raw_active = (args.active or "").strip().lower()
    if raw_active in ("true", "1", "yes", "on"):
        active_value = "TRUE"
    elif raw_active in ("false", "0", "no", "off"):
        active_value = "FALSE"
    else:
        print(f"ERROR: --active must be true/false, got '{args.active}'")
        sys.exit(1)

    target_names: List[str] = []
    if args.names:
        target_names = [n.strip() for n in args.names.split(",") if n.strip()]
    if args.name:
        target_names.append(args.name.strip())
    target_names = [n for n in target_names if n]
    if not target_names:
        print("ERROR: Provide --name or --names (comma-separated)")
        sys.exit(1)

    streams = sess.get("streams", [])
    stream_by_name = {s["name"]: s for s in streams}

    updated: List[str] = []
    missing: List[str] = []
    for nm in target_names:
        match = stream_by_name.get(nm)
        if not match:
            missing.append(nm)
            continue
        handle = match.get("handle")
        if not handle:
            missing.append(nm)
            continue
        try:
            stc.config(handle, Active=active_value)
            updated.append(nm)
        except Exception as exc:
            print(f"WARN: failed to set Active={active_value} on '{nm}': {exc}")
    if updated:
        try:
            stc.apply()
        except Exception as exc:
            print(f"ERROR: stc.apply() failed after set-stream-active: {exc}")
            sys.exit(1)
        for nm in updated:
            stream_by_name[nm]["active"] = active_value
        save_session(sess)
    print(f"set-stream-active: Active={active_value} applied on {updated}")
    if missing:
        print(f"NOT FOUND: {missing}")
        if not updated:
            sys.exit(2)


def cmd_mac_mob_flap(args):
    """Flap a MAC between two existing streams -- operator helper for MAC mobility priming.

    Convenience wrapper that toggles ``Active`` on two existing StreamBlocks in
    alternation for N cycles, starting/stopping port traffic around each
    cycle. This mirrors the in-orchestrator ``rapid_flap`` helper used by the
    clear_operations test's setup_trigger phase, but is callable from the
    shell so operators can prime the DUT into suppression independently of a
    ``/TEST`` run (e.g. when debugging ``clear evpn mac-suppression`` by
    hand).

    The two streams must already exist in the persistent session. Use
    ``spirent_tool.py create-stream --name ...`` twice first, or rely on the
    orchestrator's scenario setup to have created them.

    Output:
      - Per-cycle line printed (1, 2, 3 ...) so long flaps show progress.
      - JSON report at the end with ``{cycles_completed, total_elapsed_sec,
        a_seen, b_seen}`` when ``--json-output`` is set.

    Not destructive: does not create or delete streams, does not modify BGP
    peers. Only ``stc.config()`` on StreamBlock.Active + ``stc.apply()``.
    Will NOT clear the DUT MAC table; run ``clear evpn mac-table`` on the DUT
    manually first if you need a clean priming baseline.
    """
    config = load_config()
    stc, sess = _require_ready(config)

    cycles = max(1, int(getattr(args, "cycles", 6) or 6))
    interval = max(0.05, float(getattr(args, "interval_sec", 0.5) or 0.5))
    start_first = bool(getattr(args, "start_first", False))

    streams = sess.get("streams", [])
    stream_by_name = {s["name"]: s for s in streams}
    a = stream_by_name.get(args.stream_a)
    b = stream_by_name.get(args.stream_b)
    missing = []
    if not a:
        missing.append(args.stream_a)
    if not b:
        missing.append(args.stream_b)
    if missing:
        print(f"ERROR: Streams not found in session: {missing}")
        print(f"INFO: Available streams: {sorted(stream_by_name.keys())[:12]}")
        sys.exit(2)

    ha = a.get("handle")
    hb = b.get("handle")
    if not ha or not hb:
        print("ERROR: one or both streams have no handle -- session state is stale; "
              "run 'spirent_tool.py heal' first")
        sys.exit(2)

    # Resolve the live generator handle from the port (sess['generator_handle']
    # is often unset for sessions created before this field existed). Mirrors
    # the same lookup that cmd_start uses.
    gen_handle = sess.get("generator_handle") or ""
    if not gen_handle:
        try:
            gen_handle = stc.get(sess["port_handle"], "children-Generator") or ""
        except Exception as exc:
            print(f"ERROR: could not resolve generator handle from port: {exc}")
            sys.exit(2)
        if gen_handle:
            sess["generator_handle"] = gen_handle
            try:
                save_session(sess)
            except Exception:
                pass
    if not gen_handle:
        print("ERROR: no Generator object on port; create a stream first or run 'start'")
        sys.exit(2)

    ana_handle = ""
    try:
        ana_handle = stc.get(sess["port_handle"], "children-Analyzer") or ""
    except Exception:
        ana_handle = ""

    # Start port traffic once up front when requested -- some PPX builds need
    # the generator to be running before Active toggles take effect on live
    # streams. When not set, we start/stop around each cycle (slower but the
    # safer default when the operator isn't sure what's running).
    def _start():
        try:
            if ana_handle:
                try:
                    stc.perform("AnalyzerStart", AnalyzerList=ana_handle)
                except Exception:
                    pass
            stc.perform("GeneratorStart", GeneratorList=gen_handle)
        except Exception as exc:
            print(f"WARN: GeneratorStart failed: {exc}")

    def _stop():
        try:
            stc.perform("GeneratorStop", GeneratorList=gen_handle)
        except Exception as exc:
            print(f"WARN: GeneratorStop failed: {exc}")

    import time as _t
    t0 = _t.time()
    if start_first:
        _start()

    cycles_done = 0
    try:
        for cyc in range(1, cycles + 1):
            # A on, B off
            stc.config(ha, Active="TRUE")
            stc.config(hb, Active="FALSE")
            stc.apply()
            if not start_first:
                _start()
            _t.sleep(interval)
            if not start_first:
                _stop()

            # B on, A off
            stc.config(ha, Active="FALSE")
            stc.config(hb, Active="TRUE")
            stc.apply()
            if not start_first:
                _start()
            _t.sleep(interval)
            if not start_first:
                _stop()

            cycles_done = cyc
            # Progress ping every 5 cycles so large flaps show movement.
            if cyc % 5 == 0 or cyc == cycles:
                print(f"mac-mob-flap cycle {cyc}/{cycles} (elapsed {_t.time()-t0:.1f}s)",
                      flush=True)
    finally:
        if start_first:
            _stop()
        # Leave both streams inactive so the session does not keep
        # transmitting after the operator's flap is done.
        try:
            stc.config(ha, Active="FALSE")
            stc.config(hb, Active="FALSE")
            stc.apply()
        except Exception:
            pass

    elapsed = _t.time() - t0
    if getattr(args, "json_output", False):
        import json as _j
        print(_j.dumps({
            "cycles_requested": cycles,
            "cycles_completed": cycles_done,
            "interval_sec": interval,
            "total_elapsed_sec": round(elapsed, 2),
            "stream_a": args.stream_a,
            "stream_b": args.stream_b,
            "start_first": start_first,
        }, indent=2))
    else:
        print(f"mac-mob-flap: {cycles_done}/{cycles} cycles completed in "
              f"{elapsed:.1f}s ({interval}s interval)")


def cmd_remove_stream(args):
    """Remove a stream from the session (within persistent session)."""
    config = load_config()
    stc, sess = _require_ready(config)

    streams = sess.get("streams", [])
    match = next((s for s in streams if s["name"] == args.name), None)
    if not match:
        print(f"ERROR: Stream '{args.name}' not found. Run 'status' to list streams.")
        sys.exit(1)

    if match.get("vlan") is not None and match.get("inner_vlan") is not None:
        _free_inner_vlan(sess, match["vlan"], match["inner_vlan"])
    try:
        stc.delete(match["handle"])
        stc.apply()
    except Exception as e:
        print(f"ERROR: Could not delete stream from STC: {e}")
        sys.exit(1)

    sess["streams"] = [s for s in streams if s["name"] != args.name]
    save_session(sess)
    print(f"Stream removed: {args.name}")


def cmd_remove_device(args):
    """Stop BGP and remove device from session (within persistent session)."""
    config = load_config()
    stc, sess = _require_ready(config)

    devices = sess.get("devices", [])
    match = next((d for d in devices if d["name"] == args.name), None)
    if not match:
        print(f"ERROR: Device '{args.name}' not found. Run 'list-devices' to see devices.")
        sys.exit(1)

    port = sess["port_handle"]
    dev_handle = match["handle"]

    if match.get("vlan") is not None and match.get("inner_vlan") is not None:
        _free_inner_vlan(sess, match["vlan"], match["inner_vlan"])

    try:
        stc.perform("DeviceStopCommand", DeviceList=dev_handle)
    except Exception as e:
        print(f"Warning stopping device: {e}")

    try:
        remaining = [d for d in devices if d["name"] != args.name]
        valid_remaining = []
        for d in remaining:
            try:
                stc.get(d["handle"], "Name")
                valid_remaining.append(d["handle"])
            except Exception:
                print(f"Warning: stale handle for '{d['name']}' -- excluding from affiliation")
        stc.config(port, **{"AffiliationPort-sources": valid_remaining})
        stc.delete(dev_handle)
        stc.apply()
    except Exception as e:
        print(f"ERROR: Could not remove device from STC: {e}")
        sys.exit(1)

    sess["devices"] = [d for d in devices if d["name"] != args.name]
    save_session(sess)
    print(f"Device removed: {args.name}")


def cmd_prune_test_scope(args):
    """Remove stale TEST-owned streams that do not belong to the current test."""
    if not getattr(args, "confirm", False):
        print("ERROR: --confirm is required for prune-test-scope")
        sys.exit(1)
    test_id = str(getattr(args, "test_id", "") or "").strip()
    if not test_id:
        print("ERROR: --test-id is required")
        sys.exit(1)
    config = load_config()
    stc, sess = _require_ready(config)
    dry_run = bool(getattr(args, "dry_run", False))
    remove_devices = bool(getattr(args, "include_devices", False))

    test_owned_prefixes = (
        "TEST_",
        "TEST-",
        "TC-",
        "HOST_TEST_",
        "HOST_TC_",
        "REPRO_",
        "SW228552_",
    )

    def is_test_owned(name):
        return str(name or "").startswith(test_owned_prefixes)

    stale_streams = [
        stream for stream in sess.get("streams", [])
        if is_test_owned(stream.get("name")) and test_id not in str(stream.get("name") or "")
    ]
    removed_streams = []
    errors = []
    for stream in stale_streams:
        name = stream.get("name")
        handle = stream.get("handle")
        if not dry_run and handle:
            try:
                stc.delete(handle)
            except Exception as exc:
                errors.append(f"stream {name}: {exc}")
                continue
        removed_streams.append(name)

    removed_devices = []
    if remove_devices:
        stale_devices = [
            device for device in sess.get("devices", [])
            if is_test_owned(device.get("name")) and test_id not in str(device.get("name") or "")
        ]
        for device in stale_devices:
            name = device.get("name")
            handle = device.get("handle")
            if not dry_run and handle:
                try:
                    stc.delete(handle)
                except Exception as exc:
                    errors.append(f"device {name}: {exc}")
                    continue
            removed_devices.append(name)

    if not dry_run:
        if removed_streams or removed_devices:
            try:
                stc.apply()
            except Exception as exc:
                errors.append(f"stc.apply: {exc}")
        removed_stream_set = set(removed_streams)
        removed_device_set = set(removed_devices)
        sess["streams"] = [s for s in sess.get("streams", []) if s.get("name") not in removed_stream_set]
        if remove_devices:
            sess["devices"] = [d for d in sess.get("devices", []) if d.get("name") not in removed_device_set]
        save_session(sess)

    result = {
        "test_id": test_id,
        "dry_run": dry_run,
        "removed_stream_count": len(removed_streams),
        "removed_streams": removed_streams,
        "removed_device_count": len(removed_devices),
        "removed_devices": removed_devices,
        "errors": errors,
    }
    print(json.dumps(result, indent=2))
    if errors:
        sys.exit(1)


def _format_cleanup_preview(sess, config):
    """Format session contents for cleanup confirmation."""
    lines = [
        f"Session: {sess.get('session_name', '?')} (active since {sess.get('created', '?')[:16]})",
        f"  Devices: {len(sess.get('devices', []))} ({', '.join(d['name'] for d in sess.get('devices', [])[:5])}{'...' if len(sess.get('devices', [])) > 5 else ''})",
        f"  Streams: {len(sess.get('streams', []))} ({', '.join(s['name'] for s in sess.get('streams', [])[:5])}{'...' if len(sess.get('streams', [])) > 5 else ''})",
        f"  Traffic: {'RUNNING' if sess.get('traffic_running') else 'STOPPED'}",
        f"  Port: {config.get('port_location', '?')} ({'RESERVED' if sess.get('port_reserved') else 'not reserved'})",
        "",
        "Run with --confirm to end this session.",
    ]
    return "\n".join(lines)


def _stop_port_generator(stc, port_handle):
    if not port_handle:
        return False
    gen_handle = stc.get(port_handle, "children-Generator")
    if not gen_handle:
        return False
    stc.perform("GeneratorStop", GeneratorList=gen_handle)
    return True


def _release_port_from_session(stc, port_handle):
    """Release a Spirent port without ending the Lab Server session.

    ``DetachPorts`` only disconnects the Port object from hardware in some STC
    builds; the Windows GUI can still show the port as owned by the automation
    session. ``ReleasePortCommand`` is the fast ownership release primitive.
    """
    if not port_handle:
        return []

    actions = []
    stc.perform("ReleasePortCommand", PortList=port_handle)
    actions.append("ReleasePortCommand")
    try:
        stc.perform("DetachPorts", portList=port_handle)
        actions.append("DetachPorts")
    except Exception as exc:
        actions.append(f"DetachPorts warning: {exc}")
    stc.apply()
    return actions


def cmd_release(args):
    """Stop traffic and release the port for manual Spirent GUI use.

    The Lab Server session is preserved. This is intentionally much faster and
    less destructive than ``cleanup --confirm``.
    """
    config = load_config()
    sess = load_session()
    if not sess or not sess.get("active"):
        print("No active Spirent session found; nothing to release.")
        return

    port_handle = sess.get("port_handle")
    if not port_handle:
        sess["port_reserved"] = False
        save_session(sess)
        print("No port object is tracked locally; session already has no reserved port.")
        return

    session_id = sess.get("session_id_on_server", "")
    stc = _stc_http(config)
    stc.join_session(session_id)

    stopped = False
    release_actions = []
    warnings = []
    try:
        stopped = _stop_port_generator(stc, port_handle)
    except Exception as exc:
        warnings.append(f"GeneratorStop warning: {exc}")

    try:
        release_actions = _release_port_from_session(stc, port_handle)
    except Exception as exc:
        warnings.append(f"ReleasePortCommand failed: {exc}")
        try:
            stc.perform("DetachPorts", portList=port_handle)
            stc.apply()
            release_actions = ["DetachPorts fallback"]
        except Exception as detach_exc:
            warnings.append(f"DetachPorts fallback failed: {detach_exc}")

    now = datetime.utcnow().isoformat()
    sess["traffic_running"] = False
    sess["traffic_stopped"] = now
    sess["port_reserved"] = False
    sess["port_released"] = now
    sess["port_release_actions"] = release_actions
    sess.setdefault("audit_log", []).append({
        "ts": now,
        "action": f"released port {config.get('port_location')} via {', '.join(release_actions) or 'no-op'}; session preserved",
    })
    save_session(sess)

    print(f"Session preserved: {sess.get('session_name')} ({session_id})")
    print(f"Traffic stopped: {stopped}")
    print(f"Port released: {bool(release_actions)} ({config.get('port_location')})")
    for warning in warnings:
        print(f"WARNING: {warning}")
    print("Manual Spirent GUI can now reserve/connect to the port.")


def cmd_detach(args):
    """Detach the automation client without destroying the Lab Server session."""
    sess = load_session()
    if not sess or not sess.get("active"):
        print("No active Spirent session found.")
        return
    sess["last_detached"] = datetime.utcnow().isoformat()
    sess.setdefault("audit_log", []).append({
        "ts": sess["last_detached"],
        "action": "automation client detached; session preserved",
    })
    save_session(sess)
    print(f"Detached from {sess.get('session_name')}. Session remains on Lab Server.")


def cmd_cleanup(args):
    """Release port, end session, clean up. Use --confirm after user approval."""
    config = load_config()
    sess = load_session() if args.session_name != "--all" else None

    if args.session_name == "--all":
        print("Cleaning ALL local dn_spirent sessions...")
        _clean_stale_local_sessions(config)
        try:
            stc_tmp = _stc_http(config)
            user = config.get("user_name", "dn_spirent")
            for s in list(stc_tmp.sessions()):
                if user in s:
                    _kill_zombie_session(config, s)
        except Exception as e:
            print(f"Warning listing server sessions: {e}")
        for sf in Path(SESSION_DIR).glob("*.json"):
            try:
                with open(sf) as f:
                    sd = json.load(f)
                sd["active"] = False
                sd["traffic_running"] = False
                sd["cleaned_up"] = datetime.utcnow().isoformat()
                sd["inner_vlan_allocations"] = {}
                with open(sf, "w") as f:
                    json.dump(sd, f, indent=2)
            except Exception as e:
                _swallowed(e, f"cmd_cleanup --all write {sf.name}")
        print("All sessions cleaned.")
        return

    if not sess:
        print("No active session to clean up.")
        return

    if not getattr(args, "confirm", False):
        print(_format_cleanup_preview(sess, config))
        return

    session_id = sess.get("session_id_on_server", "")
    joined = False

    try:
        stc = _stc_http(config)
        stc.join_session(session_id)
        joined = True
    except Exception:
        print(f"Could not join session '{session_id}' (may already be dead)")

    if joined:
        try:
            if sess.get("traffic_running") and sess.get("port_handle"):
                _stop_port_generator(stc, sess["port_handle"])
        except Exception as e:
            print(f"Warning stopping traffic: {e}")

        try:
            if sess.get("port_reserved") and sess.get("port_handle"):
                _release_port_from_session(stc, sess["port_handle"])
        except Exception as e:
            print(f"Warning detaching port: {e}")

        try:
            stc.end_session(end_tcsession=True)
            print(f"Server session ended: {session_id}")
        except Exception as e:
            print(f"Warning ending session: {e}")
            _kill_zombie_session(config, session_id)
    else:
        _kill_zombie_session(config, session_id)

    sess["active"] = False
    sess["traffic_running"] = False
    sess["cleaned_up"] = datetime.utcnow().isoformat()
    sess["inner_vlan_allocations"] = {}
    save_session(sess)

    print(f"Session ended, port released, cleanup complete.")


def cmd_reconcile(args):
    """Compare local session files vs Lab Server, mark stale, optionally kill orphan server sessions."""
    config = load_config()
    _clean_stale_local_sessions(config)
    try:
        stc_tmp = _stc_http(config)
        server_sessions = set(stc_tmp.sessions())
    except Exception as e:
        print(f"ERROR: Lab Server unreachable: {e}")
        sys.exit(1)

    local_sids = set()
    for sf in Path(SESSION_DIR).glob("*.json"):
        try:
            with open(sf) as f:
                sd = json.load(f)
            sid = sd.get("session_id_on_server")
            if sid:
                local_sids.add(sid)
                if sd.get("active") and sid not in server_sessions:
                    sd["active"] = False
                    sd["_stale_reason"] = "server session gone"
                    with open(sf, "w") as f:
                        json.dump(sd, f, indent=2)
                    print(f"  Marked inactive (server gone): {sf.stem}")
        except Exception:
            pass

    user = config.get("user_name", "dn_spirent")
    orphans = [s for s in server_sessions if user in s and s not in local_sids]
    if orphans:
        print(f"\nOrphan sessions on server (not in local files): {orphans}")
        if args.kill_orphans:
            for o in orphans:
                _kill_zombie_session(config, o)
            print("  Killed orphan sessions.")
        else:
            print("  Run with --kill-orphans to remove them.")

    print("Reconcile complete.")


def _heal_session(stc, sess, config=None):
    """Core heal logic -- rebuild ``sess`` from the live BLL state (F2).

    Shared by ``cmd_heal`` and ``cmd_connect`` (for auto-resync after a
    discover-via-server-scan join).  Mutates ``sess`` in place, saves it,
    and returns ``(before_snapshot, findings_list)``.
    """
    if config is None:
        config = load_config()
    before = {
        "port_handle": sess.get("port_handle"),
        "port_reserved": sess.get("port_reserved"),
        "project_handle": sess.get("project_handle"),
        "device_count": len(sess.get("devices", []) or []),
        "stream_count": len(sess.get("streams", []) or []),
    }
    findings = []
    _heal_apply(stc, sess, findings, config)
    save_session(sess)
    return before, findings


def cmd_heal(args):
    """Rebuild local session JSON from the live BLL state (F2).

    When the BLL subprocess is respawned (stcweb restart, session crash, or
    ``supervisorctl`` restart), the REST/HTTP tier keeps responding but the
    in-memory objects (port reservation, EmulatedDevice handles, BgpRouterConfig
    handles) are GONE.  Local JSON still lists them, which makes subsequent
    ``create-device`` / ``isis-peer`` / ``bgp-peer`` commands race on stale
    handles and produce confusing errors (`Device not found`, `Port not
    reserved`, `Lost network connection`).

    ``heal`` fixes this by:
      1. Probing the Lab Server and joining the existing session (no create).
      2. Enumerating STC objects under ``project1`` and rebuilding the
         ``devices`` / ``streams`` lists from LIVE data (authoritative).
      3. Re-binding ``port_handle`` and ``port_reserved`` by reading
         ``children-Port`` and its ``Online`` / ``Location`` attributes.
      4. Re-binding ``project_handle`` by reading ``system1 children-Project``.
      5. Dropping any JSON entry whose STC handle no longer exists.
      6. Saving the fresh session file.

    The command is SAFE and IDEMPOTENT -- it never creates, modifies, or
    deletes anything on the BLL.  It only re-discovers the truth and writes
    our view of it.  Run this whenever the ``/SPIRENT status`` output seems
    to disagree with what the BLL is doing (most common: after stcweb
    restart, crash recovery, or when the orchestrator hit a stale-handle
    traceback).
    """
    config = load_config()

    try:
        stc, sess = get_stc(config, force_new=False, allow_create=False)
    except SpirentSessionError as e:
        print(f"[ERROR] {e}")
        print()
        print("[INFO] heal needs a joinable session.  If stcweb is dead, run")
        print("       'spirent_tool.py recover --level stcweb' first.  If you")
        print("       really want to start fresh, run")
        print("       'spirent_tool.py connect --create-if-missing'.")
        sys.exit(2)

    before, findings = _heal_session(stc, sess, config)
    _print_heal_report(before, sess, findings)

    if getattr(args, "json", False):
        print()
        print(json.dumps({
            "session_name": sess.get("session_name"),
            "before": before,
            "after": {
                "port_handle": sess.get("port_handle"),
                "port_reserved": sess.get("port_reserved"),
                "project_handle": sess.get("project_handle"),
                "device_count": len(sess.get("devices") or []),
                "stream_count": len(sess.get("streams") or []),
                "traffic_running": sess.get("traffic_running", False),
            },
            "findings": findings,
        }, indent=2))


def _heal_apply(stc, sess, findings, config):
    """Apply the heal algorithm to ``sess`` using live BLL data.

    Mutates ``sess`` in place and appends human-readable change
    descriptions to ``findings``.  Does NOT save to disk (caller does).
    """

    # 1) Project handle
    try:
        proj_children = stc.get("system1", "children-Project") or ""
        projects = proj_children.split() if proj_children.strip() else []
    except Exception as e:
        print(f"[ERROR] BLL not responding to system1 query: {e}")
        sys.exit(1)

    if not projects:
        findings.append("no Project under system1 -- session is empty")
        sess["project_handle"] = None
        sess["port_handle"] = None
        sess["port_reserved"] = False
        sess["devices"] = []
        sess["streams"] = []
        sess["_healed_at"] = datetime.utcnow().isoformat()
        return

    # Prefer the cached project handle if it still exists, else take the first
    proj = sess.get("project_handle")
    if proj not in projects:
        if sess.get("project_handle"):
            findings.append(f"project_handle '{sess['project_handle']}' stale -> rebinding to '{projects[0]}'")
        proj = projects[0]
    sess["project_handle"] = proj

    # 2) Port handle + reservation state
    try:
        port_children = stc.get(proj, "children-Port") or ""
        ports = port_children.split() if port_children.strip() else []
    except Exception:
        ports = []

    configured_loc = config.get("port_location", "")
    matched_port = None
    reserved = False
    for ph in ports:
        try:
            loc = stc.get(ph, "Location") or ""
            online = (stc.get(ph, "Online") or "").lower() == "true"
            if loc == configured_loc:
                matched_port = ph
                reserved = online
                break
            if matched_port is None:
                matched_port = ph
                reserved = online
        except Exception:
            continue

    if matched_port:
        if sess.get("port_handle") != matched_port:
            findings.append(f"port_handle '{sess.get('port_handle')}' -> '{matched_port}'")
        sess["port_handle"] = matched_port
        if bool(sess.get("port_reserved")) != bool(reserved):
            findings.append(f"port_reserved {sess.get('port_reserved')} -> {reserved}")
        sess["port_reserved"] = bool(reserved)
    else:
        if sess.get("port_handle"):
            findings.append("no Port under project -> clearing port_handle / port_reserved")
        sess["port_handle"] = None
        sess["port_reserved"] = False

    # 3) Emulated devices -- rebuild from BLL
    try:
        dev_children = stc.get(proj, "children-EmulatedDevice") or ""
        dev_handles = dev_children.split() if dev_children.strip() else []
    except Exception:
        dev_handles = []

    live_names = set()
    live_devices = []
    for dh in dev_handles:
        try:
            name = stc.get(dh, "Name")
        except Exception:
            continue
        live_names.add(name)
        ip = gw = vlan = None
        try:
            ipv4 = (stc.get(dh, "children-Ipv4If") or "").split()
            if ipv4:
                ip = stc.get(ipv4[0], "Address")
                gw = stc.get(ipv4[0], "Gateway")
        except Exception:
            pass
        try:
            vif = (stc.get(dh, "children-VlanIf") or "").split()
            if vif:
                vlan = stc.get(vif[0], "VlanId")
        except Exception:
            pass
        bgp_handle = None
        try:
            bgp = (stc.get(dh, "children-BgpRouterConfig") or "").split()
            if bgp:
                bgp_handle = bgp[0]
        except Exception:
            pass
        existing_dev = next(
            (d for d in sess.get("devices", []) or [] if d.get("name") == name),
            {},
        )
        live_devices.append({
            **existing_dev,
            "name": name,
            "handle": dh,
            "ip": ip or existing_dev.get("ip"),
            "gateway": gw or existing_dev.get("gateway"),
            "vlan": vlan if vlan is not None else existing_dev.get("vlan"),
            "bgp_handle": bgp_handle,
            "_healed_at": datetime.utcnow().isoformat(),
        })

    dropped_devs = [
        d.get("name") for d in (sess.get("devices") or [])
        if d.get("name") and d.get("name") not in live_names
    ]
    if dropped_devs:
        findings.append(f"dropped {len(dropped_devs)} stale device JSON entries: {dropped_devs}")
    adopted_devs = [
        n for n in live_names
        if n not in {d.get("name") for d in (sess.get("devices") or [])}
    ]
    if adopted_devs:
        findings.append(f"adopted {len(adopted_devs)} orphan devices from BLL: {adopted_devs}")
    sess["devices"] = live_devices

    # 4) StreamBlocks -- rebuild from BLL
    live_streams = []
    live_stream_handles = set()
    for ph in ports:
        try:
            sb_children = stc.get(ph, "children-StreamBlock") or ""
            sb_handles = sb_children.split() if sb_children.strip() else []
        except Exception:
            sb_handles = []
        for sh in sb_handles:
            live_stream_handles.add(sh)
            try:
                sb_name = stc.get(sh, "Name")
            except Exception:
                continue
            existing_st = next(
                (s for s in sess.get("streams", []) or [] if s.get("handle") == sh or s.get("name") == sb_name),
                {},
            )
            live_streams.append({
                **existing_st,
                "name": sb_name,
                "handle": sh,
                "_healed_at": datetime.utcnow().isoformat(),
            })

    dropped_streams = [
        s.get("name") for s in (sess.get("streams") or [])
        if s.get("handle") and s.get("handle") not in live_stream_handles
    ]
    if dropped_streams:
        findings.append(f"dropped {len(dropped_streams)} stale stream JSON entries: {dropped_streams}")
    sess["streams"] = live_streams

    # 5) Traffic running -- probe Generator state if port is there
    traffic_running = False
    if matched_port:
        try:
            gens = (stc.get(matched_port, "children-Generator") or "").split()
            if gens:
                gen_state = stc.get(gens[0], "State") or ""
                traffic_running = gen_state.upper() == "RUNNING"
        except Exception:
            pass
    if bool(sess.get("traffic_running")) != bool(traffic_running):
        findings.append(f"traffic_running {sess.get('traffic_running')} -> {traffic_running}")
    sess["traffic_running"] = bool(traffic_running)

    sess["_healed_at"] = datetime.utcnow().isoformat()


def _print_heal_report(before, sess, findings):
    print(f"=== Heal report: session '{sess.get('session_name')}' ===")
    print(f"  project_handle : {before['project_handle']} -> {sess.get('project_handle')}")
    print(f"  port_handle    : {before['port_handle']} -> {sess.get('port_handle')}")
    print(f"  port_reserved  : {before['port_reserved']} -> {sess.get('port_reserved')}")
    print(f"  devices        : {before['device_count']} -> {len(sess.get('devices') or [])}")
    print(f"  streams        : {before['stream_count']} -> {len(sess.get('streams') or [])}")
    if findings:
        print()
        print("Changes:")
        for f in findings:
            print(f"  - {f}")
    else:
        print()
        print("  (no changes -- local JSON already in sync with BLL)")


def cmd_daemon(args):
    """Control / use the long-running ``spirent_daemon.py`` process (F5).

    The daemon keeps ONE ``StcHttp`` connection joined to the session so
    clustered CLI calls (orchestrator bursts, tight test loops) skip the
    per-invocation cold start.  See ``spirent_daemon.py`` for the protocol
    and rationale.
    """
    from spirent.daemon_cmd import cmd_daemon as _cmd_daemon

    return _cmd_daemon(args, session_dir=SESSION_DIR, tool_file=__file__)


def cmd_recover(args):
    """Diagnose and recover a crashed Lab Server (stcweb/testcenter-server)."""
    import base64
    config = load_config()
    ssh_cfg = config.get("lab_server_ssh", {})
    if not ssh_cfg.get("host"):
        print("[ERROR] No lab_server_ssh config in ~/.spirent_config.json")
        print("[INFO] Add: lab_server_ssh: {host, username, password_b64}")
        sys.exit(1)

    host = ssh_cfg["host"]
    username = ssh_cfg.get("username", "dn")
    password = base64.b64decode(ssh_cfg.get("password_b64", "")).decode()

    level = getattr(args, "level", "stcweb")

    ok, result = _health_probe(config)
    if ok:
        print(f"[OK] Lab Server health probe passed. {len(result)} sessions on server.")
        if level != "full":
            print("[INFO] Server appears healthy. Use --level full to force restart anyway.")
            return

    print(f"[WARN] Lab Server health probe {'PASSED but --level full requested' if ok else 'FAILED: ' + str(result)}")
    print(f"[INFO] Connecting to Lab Server at {host} via SSH...")

    try:
        import paramiko
    except ImportError:
        print("[ERROR] paramiko not installed. Run: pip install paramiko")
        sys.exit(1)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, username=username, password=password, timeout=10)
    except Exception as e:
        print(f"[ERROR] SSH to Lab Server failed: {e}")
        sys.exit(1)

    def _run(cmd):
        _, stdout, stderr = ssh.exec_command(cmd, timeout=30)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        return out, err

    container_name = "spirent-labserver"
    print(f"\n--- Diagnosing Lab Server ({host}) ---")

    out, _ = _run(f"docker ps --filter name={container_name} --format '{{{{.Status}}}}'")
    print(f"Container status: {out or '(not running)'}")

    if level == "stcweb":
        print("\n--- Restarting stcweb (light recovery) ---")
        out, err = _run(f"docker exec {container_name} supervisorctl restart stcweb")
        print(f"stcweb restart: {out} {err}")
        time.sleep(3)
    elif level == "engine":
        print("\n--- Restarting testcenter-server (medium recovery) ---")
        out, err = _run(f"docker exec {container_name} supervisorctl restart testcenter-server")
        print(f"testcenter-server restart: {out} {err}")
        time.sleep(5)
        out, err = _run(f"docker exec {container_name} supervisorctl restart stcweb")
        print(f"stcweb restart: {out} {err}")
        time.sleep(3)
    elif level == "full":
        print("\n--- Full container restart (nuclear) ---")
        out, err = _run(f"docker restart {container_name}")
        print(f"docker restart: {out} {err}")
        print("Waiting 15s for services to start...")
        time.sleep(15)
    else:
        print(f"[ERROR] Unknown level '{level}'. Use: stcweb, engine, full")
        ssh.close()
        sys.exit(1)

    ssh.close()

    print("\n--- Post-recovery health check ---")

    last_failure = {"result": None}

    if poll_until is not None:
        def _health_check():
            ok, result = _health_probe(config)
            if not ok:
                last_failure["result"] = result
            return ok, {"ok": ok, "session_count": len(result) if ok else 0,
                        "error": (None if ok else str(result)[:120])}

        def _health_progress(elapsed, observed):
            err = observed.get("error", "?") if isinstance(observed, dict) else "?"
            print(f"  Health check still failing at {elapsed:.0f}s: {err}", flush=True)

        # 6s budget mirrors the legacy 3 attempts * 2s sleep, but we exit ASAP.
        res = poll_until(_health_check, timeout_sec=6.0, interval_sec=2.0,
                         on_progress=_health_progress, progress_every=1)
        recovered = res.passed
        sessions_after = (res.last_value or {}).get("session_count", 0)
    else:
        recovered = False
        sessions_after = 0
        for attempt in range(3):
            time.sleep(2)
            ok, result = _health_probe(config)
            if ok:
                recovered = True
                sessions_after = len(result)
                break
            last_failure["result"] = result
            print(f"  Health check attempt {attempt+1}/3 failed: {result}")

    if recovered:
        print(f"[OK] Lab Server recovered. {sessions_after} sessions.")
        for sf in Path(SESSION_DIR).glob("*.json"):
            try:
                with open(sf) as f:
                    sd = json.load(f)
                if sd.get("active"):
                    sd["active"] = False
                    sd["_stale_reason"] = f"post-recovery invalidation ({level})"
                    with open(sf, "w") as f:
                        json.dump(sd, f, indent=2)
            except Exception as e:
                _swallowed(e, f"heal --deep invalidate {sf.name}")
        print("[INFO] All local sessions marked inactive. Run 'connect' to create fresh session.")
        return

    print(f"[ERROR] Lab Server did not recover after restart "
          f"(last error: {last_failure['result']!r}).")
    print("[INFO] Try: ssh dn@10.10.50.18 -> docker logs spirent-labserver --tail 50")


def cmd_list_sessions(args):
    """List all sessions on the Lab Server."""
    config = load_config()
    stc = _stc_http(config)
    sessions = stc.sessions()

    print(f"=== Lab Server Sessions ({config['lab_server']}:{config.get('lab_server_port', 80)}) ===")
    if not sessions:
        print("  (no active sessions)")
    else:
        for s in sessions:
            owner_mark = " <-- YOURS" if config.get("user_name", "") in s else ""
            print(f"  {s}{owner_mark}")

    local_sessions = sorted(Path(SESSION_DIR).glob("*.json"), key=os.path.getmtime, reverse=True)
    if local_sessions:
        print(f"\n=== Local Session Files ({SESSION_DIR}) ===")
        for sp in local_sessions:
            with open(sp) as f:
                sd = json.load(f)
            status = "ACTIVE" if sd.get("active") else "ENDED"
            traffic = "RUNNING" if sd.get("traffic_running") else "stopped"
            streams = len(sd.get("streams", []))
            print(f"  {sp.stem}: {status} | traffic: {traffic} | streams: {streams} | created: {sd.get('created', '?')}")


def _resolve_device_vlan_stack(stc, device_handle):
    """Trace the STC IfStack for an EmulatedDevice and return (outer_tag, inner_tag, all_tags).

    The WIRE order is: Ethernet -> outer VLAN -> inner VLAN -> IP payload.
    `children-VlanIf` list order is the creation order inside STC (often innermost first),
    which is NOT the wire order. This helper walks `StackedOnEndpoint-Targets` instead so
    the outer tag is unambiguously the VlanIf stacked directly on the EthII interface, and
    the inner tag is the VlanIf stacked on top of the outer VlanIf.

    Returns (outer_tag|None, inner_tag|None, [all_tags_in_wire_order]).
    """
    try:
        vifs = (stc.get(device_handle, "children-VlanIf") or "").split()
    except Exception:
        return (None, None, [])
    if not vifs:
        return (None, None, [])

    tag_map = {}
    stack_map = {}
    for vh in vifs:
        try:
            vid = int(stc.get(vh, "VlanId") or 0)
        except Exception:
            vid = 0
        tag_map[vh] = vid
        try:
            stacked = (stc.get(vh, "StackedOnEndpoint-Targets") or "").strip().split()
        except Exception:
            stacked = []
        stack_map[vh] = stacked[0] if stacked else ""

    eth_handles = set((stc.get(device_handle, "children-EthIIIf") or "").split())
    outer_handle = None
    for vh, base in stack_map.items():
        if base and (base in eth_handles or base.startswith("ethiiif")):
            outer_handle = vh
            break

    if outer_handle is None:
        ordered = []
        seen = set()
        for start in vifs:
            cur = start
            path = []
            while cur and cur not in seen and cur in tag_map:
                path.append(cur)
                seen.add(cur)
                cur = stack_map.get(cur, "")
            for h in reversed(path):
                if h not in ordered:
                    ordered.append(h)
        tags = [tag_map[h] for h in ordered if tag_map.get(h)]
        return (tags[0] if tags else None, tags[1] if len(tags) > 1 else None, tags)

    wire = [outer_handle]
    child_map = {base: vh for vh, base in stack_map.items() if base}
    cur = outer_handle
    while cur in child_map:
        nxt = child_map[cur]
        if nxt in wire:
            break
        wire.append(nxt)
        cur = nxt
    tags = [tag_map[h] for h in wire if tag_map.get(h)]
    return (tags[0] if tags else None, tags[1] if len(tags) > 1 else None, tags)


def _alloc_inner_vlan(sess, outer_vlan, name, item_type="stream", exclude=None):
    """Allocate next free inner VLAN for outer_vlan. Updates session inner_vlan_allocations. Returns inner_vlan.
    exclude: optional set/list of inner VLANs already used on the DUT (from get_device_interfaces discovery)."""
    sess.setdefault("inner_vlan_allocations", {})
    used = set(sess["inner_vlan_allocations"].get(str(outer_vlan), []))
    if isinstance(used, list):
        used = set(used)
    dut_used = set(exclude) if exclude else set()
    blocked = used | dut_used
    for iv in range(100, 4095):
        if iv not in blocked:
            used.add(iv)
            sess["inner_vlan_allocations"][str(outer_vlan)] = sorted(used)
            return iv
    raise RuntimeError(f"No free inner VLAN in pool for outer {outer_vlan}")


def _free_inner_vlan(sess, outer_vlan, inner_vlan):
    """Free inner VLAN from allocations. Call on remove-stream, remove-device, cleanup."""
    if not sess:
        return
    alloc = sess.get("inner_vlan_allocations", {})
    key = str(outer_vlan)
    if key not in alloc:
        return
    used = set(alloc[key]) if isinstance(alloc[key], list) else set(alloc[key])
    used.discard(inner_vlan)
    if used:
        sess["inner_vlan_allocations"][key] = sorted(used)
    else:
        del sess["inner_vlan_allocations"][key]


def _resolve_qinq_vlans(config, sess, vlan_arg, inner_arg, no_qinq=False, exclude_inner=None):
    """Resolve (outer_vlan, inner_vlan) for stream/device. None = single-tagged.
    Returns (outer_vlan, inner_vlan). inner_vlan is None for single-tagged.
    exclude_inner: optional set/list of DUT-used inner VLANs to avoid collision."""
    if no_qinq:
        return (vlan_arg, None)
    transport = config.get("transport_vlans", {})
    if vlan_arg is not None and inner_arg is not None:
        return (vlan_arg, inner_arg)
    if vlan_arg is not None and str(vlan_arg) in transport and transport[str(vlan_arg)].get("dnaas_status") == "READY":
        inner = _alloc_inner_vlan(sess, vlan_arg, "", "stream", exclude=exclude_inner)
        return (vlan_arg, inner)
    if vlan_arg is not None:
        return (vlan_arg, None)
    for ov_str, tv in transport.items():
        if tv.get("dnaas_status") == "READY":
            ov = int(ov_str)
            inner = _alloc_inner_vlan(sess, ov, "", "stream", exclude=exclude_inner)
            return (ov, inner)
    return (None, None)


def _preflight_capacity_warn(config, sess, stream_rate_gbps=None, new_peer=False):
    """Warn if adding stream/peer would approach capacity limits. Does not block."""
    if not sess:
        return
    cap_cfg = config.get("capacity", {})
    port_speed = float(cap_cfg.get("port_speed_gbps", 100))
    safety_pct = float(cap_cfg.get("safety_margin_pct", 10)) / 100.0
    max_streams = int(cap_cfg.get("max_streams", 64))
    max_peers = int(cap_cfg.get("max_bgp_peers", 32))
    cap = _compute_capacity(config, sess, live=False)
    if stream_rate_gbps is not None:
        new_total = cap["bandwidth_used_gbps"] + stream_rate_gbps
        threshold = port_speed * (1 - safety_pct)
        if new_total > threshold:
            print(f"[WARN] Adding this stream ({stream_rate_gbps:.3f} Gbps) would use {new_total:.2f}/{port_speed} Gbps ({100*new_total/port_speed:.1f}%) -- above {100*(1-safety_pct):.0f}% safety threshold")
    if new_peer:
        peers_after = cap["bgp_peers"]["used"] + 1
        if peers_after > max_peers:
            print(f"[WARN] Adding BGP peer would exceed limit: {peers_after} > {max_peers}")
    streams_after = cap["streams"]["used"] + (1 if stream_rate_gbps is not None else 0)
    if stream_rate_gbps is not None and streams_after > max_streams:
        print(f"[WARN] Adding stream would exceed limit: {streams_after} > {max_streams}")


def _compute_capacity(config, sess, live=False):
    """Compute capacity usage from config limits and session state.
    Returns dict: port_speed_gbps, bandwidth_used_gbps, bandwidth_remaining_gbps, bandwidth_pct,
    streams {used, max}, bgp_peers {used, max}, routes {used, max}, flowspec_tcam {used, max}."""
    cap_cfg = config.get("capacity", {})
    port_speed = float(cap_cfg.get("port_speed_gbps", 100))
    max_streams = int(cap_cfg.get("max_streams", 64))
    max_peers = int(cap_cfg.get("max_bgp_peers", 32))
    max_routes = int(cap_cfg.get("max_total_routes", 500000))
    max_tcam = int(cap_cfg.get("dut_flowspec_tcam", 1000))

    streams = sess.get("streams", []) if sess else []
    devices = sess.get("devices", []) if sess else []

    # Bandwidth: sum stream rates (Mbps or pps -> Gbps)
    bw_used_gbps = 0.0
    for st in streams:
        rate = float(st.get("rate", 0))
        unit = st.get("rate_unit", "MEGABITS_PER_SECOND")
        if unit == "MEGABITS_PER_SECOND":
            bw_used_gbps += rate / 1000.0
        else:
            # FRAMES_PER_SECOND: rate * frame_size * 8 / 1e9
            fsize = int(st.get("frame_size", 128))
            bw_used_gbps += (rate * fsize * 8) / 1e9

    bw_remaining = max(0, port_speed - bw_used_gbps)
    bw_pct = (bw_used_gbps / port_speed * 100) if port_speed > 0 else 0

    bgp_peers_used = sum(1 for d in devices if d.get("bgp_handle"))
    routes_used = 0
    flowspec_used = 0

    if live and sess and sess.get("port_reserved"):
        try:
            stc, _ = get_stc(config)
            for d in devices:
                bh = d.get("bgp_handle")
                if not bh:
                    continue
                try:
                    rh = stc.get(bh, "children-BgpRouterResults")
                    if rh:
                        r = stc.get(rh.split()[0])
                        routes_used += int(r.get("RoutesAdvertised", 0) or 0)
                except Exception:
                    pass
        except Exception:
            pass

    dut_ctx = (sess or {}).get("dut_context", {})
    if dut_ctx.get("flowspec_tcam_used") is not None:
        flowspec_used = int(dut_ctx["flowspec_tcam_used"])
    elif dut_ctx.get("flowspec"):
        import re
        for fs in dut_ctx["flowspec"]:
            # Parse "VRF X: 400 ipv4 + 200 ipv6" or "400 ipv4" etc
            for m in re.finditer(r"(\d+)\s*(?:ipv[46]|rules?)", str(fs), re.I):
                flowspec_used += int(m.group(1))

    return {
        "port_speed_gbps": port_speed,
        "bandwidth_used_gbps": round(bw_used_gbps, 3),
        "bandwidth_remaining_gbps": round(bw_remaining, 3),
        "bandwidth_pct": round(bw_pct, 2),
        "streams": {"used": len(streams), "max": max_streams},
        "bgp_peers": {"used": bgp_peers_used, "max": max_peers},
        "routes": {"used": routes_used, "max": max_routes},
        "flowspec_tcam": {"used": flowspec_used, "max": max_tcam},
    }


def cmd_capacity(args):
    """Show capacity usage: bandwidth, streams, BGP peers, routes, FlowSpec TCAM."""
    config = load_config()
    sess = load_session()
    cap = _compute_capacity(config, sess or {}, live=args.live)
    if args.json_output:
        print(json.dumps({"capacity": cap}, indent=2))
    else:
        port = cap["port_speed_gbps"]
        used = cap["bandwidth_used_gbps"]
        rem = cap["bandwidth_remaining_gbps"]
        pct = cap["bandwidth_pct"]
        bar_w = 20
        filled = int(bar_w * pct / 100) if port > 0 else 0
        bar = "=" * filled + " " * (bar_w - filled)
        print(f"Bandwidth: [{bar}] {used} / {port} Gbps ({pct}%)")
        s = cap["streams"]
        p = cap["bgp_peers"]
        r = cap["routes"]
        t = cap["flowspec_tcam"]
        r_used = r["used"]
        r_str = f"{r_used:,}" if r_used >= 1000 else str(r_used)
        print(f"Streams:   {s['used']} / {s['max']}  |  BGP Peers: {p['used']} / {p['max']}  |  Routes: {r_str} / {r['max']:,}")
        print(f"FlowSpec TCAM (DUT): {t['used']} / {t['max']} ({100*t['used']/t['max']:.0f}%)" if t["max"] > 0 else "FlowSpec TCAM: N/A")


def cmd_status(args):
    """Single comprehensive status: session, devices, BGP, streams, traffic, anomalies."""
    config = load_config()
    sess = load_session()
    anomalies = []
    output = {"config": {}, "session": None, "devices": [], "streams": [], "traffic": None, "anomalies": []}

    output["config"] = {
        "lab_server": f"{config['lab_server']}:{config.get('lab_server_port', 80)}",
        "chassis": f"{config['chassis_hostname']} ({config['chassis_ip']})",
        "port": config["port_location"],
        "dnaas_leaf": config.get("dnaas_leaf", "unknown"),
        "dnaas_port": config.get("dnaas_spirent_port", "unknown"),
    }

    if sess and sess.get("active"):
        port_reserved = sess.get("port_reserved", False)
        traffic_running = sess.get("traffic_running", False)
        streams = sess.get("streams", [])
        devices = sess.get("devices", [])

        output["session"] = {
            "name": sess["session_name"],
            "active": True,
            "port_reserved": port_reserved,
            "traffic_running": traffic_running,
            "stream_count": len(streams),
            "device_count": len(devices),
            "created": sess.get("created", "?"),
        }

        if not port_reserved:
            anomalies.append("PORT_NOT_RESERVED: Session active but port not reserved")

        for d in devices:
            dev_info = {
                "name": d["name"],
                "ip": d["ip"],
                "gateway": d["gateway"],
                "vlan": d.get("vlan"),
                "bgp": bool(d.get("bgp_handle")),
                "as_num": d.get("as_num"),
            }
            output["devices"].append(dev_info)
            if not d.get("bgp_handle"):
                anomalies.append(f"NO_BGP: Device '{d['name']}' has no BGP configuration")

        for i, st in enumerate(streams):
            s_info = {
                "index": i,
                "name": st["name"],
                "vlan": st.get("vlan"),
                "inner_vlan": st.get("inner_vlan"),
                "rate": f"{st.get('rate', 'N/A')} {st.get('rate_unit', '')}".strip(),
                "frame_size": st.get("frame_size"),
                "protocol": st.get("protocol", "L2"),
                "dst_ip": st.get("dst_ip"),
                "src_ip": st.get("src_ip"),
                "dst_mac": st.get("dst_mac"),
                "src_mac": st.get("src_mac"),
            }
            output["streams"].append(s_info)
            proto = str(st.get("protocol") or "").lower()
            dst_mac = str(st.get("dst_mac") or "").lower()
            dst_ip = str(st.get("dst_ip") or "").lower()
            if proto == "icmpv6-na":
                try:
                    load_value = float(st.get("rate") or 0)
                except (TypeError, ValueError):
                    load_value = 0.0
                load_unit = str(st.get("rate_unit") or "").upper()
                if ("MEGABITS" in load_unit and load_value >= 0.1) or ("FRAMES" in load_unit and load_value > 20):
                    anomalies.append(
                        f"HIGH_NDP_RATE: stream '{st['name']}' runs ICMPv6 NA at "
                        f"{load_value:g} {st.get('rate_unit')}; use <= {NDP_SAFE_RATE_PPS} fps "
                        "for teach/repro traffic to avoid DNOS CPRL NDP rate-limit warnings."
                    )
                if dst_mac == "ff:ff:ff:ff:ff:ff":
                    anomalies.append(
                        f"MALFORMED_ICMPV6_NA: stream '{st['name']}' uses L2 broadcast "
                        "dst_mac (invalid for IPv6); DNOS NDP punt will drop. "
                        "Use dst_ip=ff02::1 and let auto-multicast set dst_mac=33:33:00:00:00:01."
                    )
                elif dst_ip and not (dst_ip.startswith("ff") or dst_mac.startswith("33:33")):
                    anomalies.append(
                        f"SUSPECT_ICMPV6_NA: stream '{st['name']}' has unicast dst_ip "
                        f"{dst_ip!r} with non-multicast dst_mac {dst_mac!r}; an unsolicited "
                        "NA should target ff02::1 with 33:33:00:00:00:01."
                    )
        stream_names = [st["name"] for st in streams]
        for name in {n for n in stream_names if stream_names.count(n) > 1}:
            anomalies.append(f"DUPLICATE_STREAM_NAME: '{name}' appears multiple times in the session")

        device_names = [d["name"] for d in devices]
        for name in {n for n in device_names if device_names.count(n) > 1}:
            anomalies.append(f"DUPLICATE_DEVICE_NAME: '{name}' appears multiple times in the session")

        if traffic_running and len(streams) == 0:
            anomalies.append("NO_STREAMS: Traffic marked running but no streams defined")

        if devices and not any(d.get("bgp_handle") for d in devices):
            anomalies.append("ALL_DEVICES_NO_BGP: All emulated devices lack BGP config")

        created = sess.get("created")
        if created:
            try:
                age_h = (datetime.utcnow() - datetime.fromisoformat(created)).total_seconds() / 3600
                if age_h > 24:
                    anomalies.append(f"STALE_SESSION: Session created {age_h:.0f}h ago — consider cleanup")
            except Exception:
                pass

        if args.live and port_reserved:
            try:
                stc, _ = get_stc(config)
                port_handle = sess["port_handle"]

                for d in devices:
                    bgp_handle = d.get("bgp_handle")
                    if not bgp_handle:
                        continue
                    try:
                        rh = stc.get(bgp_handle, "children-BgpRouterResults")
                        if rh:
                            r = stc.get(rh.split()[0])
                            state = r.get("SessionState", "N/A")
                            adv = r.get("RoutesAdvertised", "0")
                            rcv = r.get("RoutesReceived", "0")
                            for di in output["devices"]:
                                if di["name"] == d["name"]:
                                    di["bgp_state"] = state
                                    di["routes_advertised"] = adv
                                    di["routes_received"] = rcv
                            if state != "ESTABLISHED":
                                anomalies.append(f"BGP_DOWN: {d['name']} state={state}")
                    except Exception:
                        pass

                gen_results = stc.get(port_handle, "children-GeneratorPortResults")
                ana_results = stc.get(port_handle, "children-AnalyzerPortResults")
                traffic = {}
                if gen_results:
                    gs = stc.get(gen_results)
                    traffic["tx_frames"] = gs.get("GeneratorFrameCount", "0")
                    traffic["tx_rate_bps"] = gs.get("GeneratorBitRate", "0")
                if ana_results:
                    an = stc.get(ana_results)
                    traffic["rx_frames"] = an.get("TotalFrameCount", "0")
                    traffic["rx_rate_bps"] = an.get("TotalBitRate", "0")
                    traffic["dropped_frames"] = an.get("DroppedFrameCount", "0")
                    traffic["dropped_pct"] = an.get("DroppedFramePercent", "0")

                if traffic:
                    output["traffic"] = traffic
                    tx = int(traffic.get("tx_frames", 0))
                    rx = int(traffic.get("rx_frames", 0))
                    dropped = int(traffic.get("dropped_frames", 0))
                    if tx > 0 and dropped > 0:
                        anomalies.append(f"TRAFFIC_LOSS: {dropped} frames dropped ({traffic.get('dropped_pct', '?')}%)")
                    if traffic_running and tx == 0:
                        anomalies.append("TX_ZERO: Traffic marked running but 0 TX frames")
                    if traffic_running and tx > 0 and rx == 0:
                        anomalies.append("RX_ZERO: TX active but 0 RX — check DNAAS path / DUT interface")
            except Exception as e:
                anomalies.append(f"LIVE_QUERY_FAILED: Could not reach STC API: {e}")
    else:
        output["session"] = {"active": False}
        local_sessions = sorted(Path(SESSION_DIR).glob("*.json"), key=os.path.getmtime, reverse=True)
        if local_sessions:
            for sp in local_sessions[:5]:
                with open(sp) as f:
                    sd = json.load(f)
                output.setdefault("recent_sessions", []).append({
                    "name": sp.stem,
                    "active": sd.get("active", False),
                    "streams": len(sd.get("streams", [])),
                    "devices": len(sd.get("devices", [])),
                    "created": sd.get("created", "?"),
                })

    if sess and sess.get("dut_context"):
        output["dut_context"] = sess["dut_context"]

    output["anomalies"] = anomalies

    # Capacity: always compute from session + config
    output["capacity"] = _compute_capacity(config, sess or {}, live=args.live)

    if args.json_output:
        print(json.dumps(output, indent=2))
    else:
        _print_status_table(output)


def _box_line(left, fill, mid, right, width):
    return f"{left}{fill * width}{right}"


def _box_row(left, content, right, width):
    return f"{left} {content:<{width - 2}} {right}"


def _print_status_table(output):
    """Print status with box-drawing, DUT context, and anomaly indicators."""
    W = 62
    B = "│"
    cfg = output["config"]

    print(_box_line("┌", "─", "─", "┐", W))
    title = "/SPIRENT Status"
    print(_box_row(B, f"{title:^{W - 2}}", B, W))
    print(_box_line("├", "─", "┬", "┤", W))

    print(_box_row(B, f"Lab Server  {cfg['lab_server']}", B, W))
    print(_box_row(B, f"Chassis     {cfg['chassis']}", B, W))

    s = output.get("session") or {}
    port_tag = "[RESERVED]" if s.get("port_reserved") else "[not reserved]"
    print(_box_row(B, f"Port        {cfg['port']}  {port_tag}", B, W))
    print(_box_row(B, f"DNAAS       {cfg['dnaas_leaf']} ({cfg['dnaas_port']})", B, W))

    print(_box_line("├", "─", "┼", "┤", W))

    if not s.get("active"):
        print(_box_row(B, "Session     NONE", B, W))
        recent = output.get("recent_sessions", [])
        if recent:
            print(_box_row(B, f"Recent ({len(recent)}):", B, W))
            for r in recent:
                st = "ACTIVE" if r["active"] else "ended"
                print(_box_row(B, f"  {r['name']}: {st} | {r['streams']}s {r['devices']}d", B, W))
    else:
        traf_tag = "[RUNNING]" if s.get("traffic_running") else "[stopped]"
        created = s.get("created", "?")[:16]
        print(_box_row(B, f"Session     {s['name']}  [ACTIVE]", B, W))
        print(_box_row(B, f"Created     {created}", B, W))
        age_str = ""
        try:
            age_h = (datetime.utcnow() - datetime.fromisoformat(s.get("created", ""))).total_seconds() / 3600
            age_str = f"{age_h:.1f}h ago"
        except Exception:
            pass
        summary = f"Traffic {traf_tag}  Streams: {s['stream_count']}  Devices: {s['device_count']}"
        if age_str:
            summary += f"  ({age_str})"
        print(_box_row(B, summary, B, W))

    cap = output.get("capacity", {})
    if cap:
        print(_box_line("├", "─", "┼", "┤", W))
        port = cap["port_speed_gbps"]
        used = cap["bandwidth_used_gbps"]
        pct = cap["bandwidth_pct"]
        bar_w = 20
        filled = min(bar_w, int(bar_w * pct / 100)) if port > 0 else 0
        bar = "=" * filled + " " * (bar_w - filled)
        print(_box_row(B, f"Bandwidth   [{bar}] {used} / {port} Gbps ({pct}%)", B, W))
        st_cap = cap["streams"]
        p_cap = cap["bgp_peers"]
        r_cap = cap["routes"]
        t_cap = cap["flowspec_tcam"]
        r_used = r_cap["used"]
        r_str = f"{r_used:,}" if r_used >= 1000 else str(r_used)
        line2 = f"Capacity    Streams: {st_cap['used']}/{st_cap['max']}  Peers: {p_cap['used']}/{p_cap['max']}  Routes: {r_str}/{r_cap['max']:,}"
        print(_box_row(B, line2, B, W))
        if t_cap["max"] > 0:
            tc_pct = 100 * t_cap["used"] / t_cap["max"]
            print(_box_row(B, f"FlowSpec TCAM (DUT)  {t_cap['used']}/{t_cap['max']} ({tc_pct:.0f}%)", B, W))

    devices = output.get("devices", [])
    if devices:
        print(_box_line("├", "─", "┼", "┤", W))
        print(_box_row(B, f"Emulated Devices ({len(devices)})", B, W))
        print(_box_row(B, "─" * (W - 2), B, W))
        for d in devices:
            name = d["name"][:16]
            ip_gw = f"{d['ip']} -> {d['gateway']}"
            vlan_s = f" v{d['vlan']}" if d.get("vlan") else ""
            line1 = f"  {name:<16} {ip_gw}{vlan_s}  AS {d.get('as_num', '?')}"
            print(_box_row(B, line1, B, W))
            if d.get("bgp"):
                state = d.get("bgp_state", "?")
                adv = d.get("routes_advertised", "?")
                rcv = d.get("routes_received", "?")
                state_indicator = "[OK]" if state == "ESTABLISHED" else "[!!]"
                line2 = f"  {'':16} BGP {state} {state_indicator}  adv={adv} rcv={rcv}"
                print(_box_row(B, line2, B, W))

    streams = output.get("streams", [])
    if streams:
        print(_box_line("├", "─", "┼", "┤", W))
        print(_box_row(B, f"Traffic Streams ({len(streams)})", B, W))
        print(_box_row(B, "─" * (W - 2), B, W))
        for st in streams:
            vlan_s = str(st.get("vlan", "-"))
            if st.get("inner_vlan"):
                vlan_s += f"+{st['inner_vlan']}"
            ip_s = f" {st.get('src_ip', '?')} -> {st['dst_ip']}" if st.get("dst_ip") else ""
            line = f"  [{st['index']}] {st['name']:<14} vlan={vlan_s:<6} {st['rate']:<12} {st['protocol']}"
            print(_box_row(B, line, B, W))
            if ip_s:
                print(_box_row(B, f"      {ip_s}  {st.get('frame_size', '?')}B", B, W))

    traffic = output.get("traffic")
    if traffic:
        print(_box_line("├", "─", "┼", "┤", W))
        print(_box_row(B, "Live Traffic Counters", B, W))
        print(_box_row(B, "─" * (W - 2), B, W))
        tx_rate = int(traffic.get("tx_rate_bps", 0))
        rx_rate = int(traffic.get("rx_rate_bps", 0))
        tx_mbps = f"{tx_rate / 1_000_000:.1f}" if tx_rate else "0"
        rx_mbps = f"{rx_rate / 1_000_000:.1f}" if rx_rate else "0"
        tx_frames = f"{int(traffic.get('tx_frames', 0)):,}"
        rx_frames = f"{int(traffic.get('rx_frames', 0)):,}"
        dropped = traffic.get("dropped_frames", "0")
        pct = traffic.get("dropped_pct", "0")
        print(_box_row(B, f"  TX   {tx_frames:>14} frames   {tx_mbps:>8} Mbps", B, W))
        print(_box_row(B, f"  RX   {rx_frames:>14} frames   {rx_mbps:>8} Mbps", B, W))
        loss_indicator = "[!!]" if int(dropped) > 0 else "[OK]"
        print(_box_row(B, f"  Drop {int(dropped):>14} frames   {pct:>7}%  {loss_indicator}", B, W))

    dut = output.get("dut_context")
    if dut:
        print(_box_line("├", "─", "┼", "┤", W))
        dut_name = dut.get("device", "?")
        print(_box_row(B, f"DUT Context: {dut_name}", B, W))
        print(_box_row(B, "─" * (W - 2), B, W))
        if dut.get("vrfs"):
            vrfs_str = ", ".join(dut["vrfs"][:6])
            if len(dut.get("vrfs", [])) > 6:
                vrfs_str += f" (+{len(dut['vrfs']) - 6} more)"
            print(_box_row(B, f"  VRFs        {vrfs_str}", B, W))
        if dut.get("bgp_as"):
            peers = dut.get("bgp_peers", 0)
            print(_box_row(B, f"  BGP         AS {dut['bgp_as']} | {peers} peers configured", B, W))
        if dut.get("flowspec"):
            for fs in dut["flowspec"][:3]:
                print(_box_row(B, f"  FlowSpec    {fs}", B, W))
        if dut.get("ready_subifs"):
            for si in dut["ready_subifs"][:5]:
                print(_box_row(B, f"  Ready IF    {si}", B, W))
        if dut.get("suggested_streams"):
            print(_box_row(B, "─" * (W - 2), B, W))
            print(_box_row(B, "  Auto-suggested streams:", B, W))
            for sg in dut["suggested_streams"][:4]:
                print(_box_row(B, f"    -> {sg}", B, W))

    anomalies = output.get("anomalies", [])
    print(_box_line("├", "─", "┼", "┤", W))
    if anomalies:
        print(_box_row(B, f"Anomalies ({len(anomalies)})", B, W))
        print(_box_row(B, "─" * (W - 2), B, W))
        for a in anomalies:
            tag, _, desc = a.partition(": ")
            print(_box_row(B, f"  [!!] {tag}", B, W))
            if desc:
                print(_box_row(B, f"       {desc}", B, W))
    else:
        print(_box_row(B, "No anomalies detected.  [OK]", B, W))
    print(_box_line("└", "─", "┴", "┘", W))


def cmd_store_dut_context(args):
    """Store DUT discovery context in session for auto-matching and status display."""
    sess = load_session()
    if not sess:
        print("ERROR: No active session.")
        sys.exit(1)

    if args.json_input:
        ctx = json.loads(args.json_input)
    elif args.json_file:
        with open(args.json_file) as f:
            ctx = json.load(f)
    else:
        ctx = {}
        if args.device:
            ctx["device"] = args.device
        if args.vrfs:
            ctx["vrfs"] = [v.strip() for v in args.vrfs.split(",")]
        if args.bgp_as:
            ctx["bgp_as"] = args.bgp_as
        if args.bgp_peers is not None:
            ctx["bgp_peers"] = args.bgp_peers
        if args.flowspec:
            ctx["flowspec"] = [f.strip() for f in args.flowspec.split("|")]
        if args.ready_subifs:
            ctx["ready_subifs"] = [s.strip() for s in args.ready_subifs.split(",")]
        if args.suggested_streams:
            ctx["suggested_streams"] = [s.strip() for s in args.suggested_streams.split("|")]

    ctx["updated"] = datetime.utcnow().isoformat()

    if args.merge and sess.get("dut_context"):
        existing = sess["dut_context"]
        existing.update({k: v for k, v in ctx.items() if v is not None})
        sess["dut_context"] = existing
    else:
        sess["dut_context"] = ctx

    save_session(sess)
    print(f"DUT context stored for '{ctx.get('device', '?')}'")
    print(json.dumps(sess["dut_context"], indent=2))


# ============================================================================
# DNAAS fabric diagnose/fix (Local Loop Detected Shutdown-AC + admin-state sticky)
# ----------------------------------------------------------------------------
# Signature library: maps show-interfaces output patterns to fault codes and
# the corresponding recovery action. Adding a new pattern = adding entries here.
# ============================================================================

_DNAAS_FAULT_SIGNATURES = [
    # (regex applied to `show interfaces <if>` output, fault_code, severity,
    #  recovery_action: 'delete_recreate' | 'no_shutdown' | 'manual')
    (re.compile(r"Reason for last down state:\s*Local Loop Detected Shutdown-AC", re.I),
     "LOCAL_LOOP_SHUTDOWN_STICKY", "high", "delete_recreate"),
    (re.compile(r"Reason for last down state:\s*admin-state disabled", re.I),
     "ADMIN_DISABLED_STICKY", "medium", "delete_recreate"),
    (re.compile(r"Reason for last down state:\s*link-down", re.I),
     "LINK_DOWN_STICKY", "high", "manual"),
    (re.compile(r"Admin state:\s*disabled", re.I),
     "ADMIN_CURRENTLY_DISABLED", "high", "no_shutdown"),
    (re.compile(r"Operational state:\s*down", re.I),
     "OPER_DOWN", "high", "manual"),
]

# Reasons that, when seen on an otherwise up/down mixed interface, are still
# worth surfacing even if no exact signature matched above. Prior bug: B-14
# ge100-0/0/15.214 had `Reason: link-down` but the tool said "all hops clean"
# because none of the signatures matched and the reason field was parsed-but-
# ignored. Anything in this table triggers a generic STICKY_DOWN_REASON fault.
_STICKY_REASON_SUBSTRINGS = (
    "link-down", "link down", "oper-down", "tx-fault", "rx-fault",
    "sfp", "los", "signal loss", "shutdown", "disabled",
    "suspended", "locked",
)


def _default_dnaas_topology(vlan):
    """Returns the canonical 4-hop DNAAS path for a Spirent-originated test VLAN.

    Shape: list[(hostname, ip, username, subifs:list, bd_name, role)]
    Falls back to topology hard-coded for the vlan-214 path (Spirent -> PE-1)
    documented in ~/.spirent_learning.json.

    Users can override via ~/.spirent_config.json -> transport_vlans.<vlan>.hops
    (future extension).
    """
    vlan = int(vlan)
    # Path inferred from transport_vlans + dnaas_leaves + vlan_mappings in config.
    # Canonical: Spirent -> B-14 -> SPINE-B09 -> SuperSpine-D04 -> SPINE-D14 -> D16 -> DUT
    # On DNAAS-SuperSpine-D04: bundle-60004 -> SPINE-B09, bundle-60007 -> SPINE-D14
    return [
        ("DNAAS-LEAF-B14",      "100.64.101.5",   "sisaev",
         [f"ge100-0/0/15.{vlan}", f"bundle-60000.{vlan}"], f"g_yor_v{vlan}_PE-1-evpn", "ingress-leaf"),
        ("SPINE-B09",           "100.64.100.12",  "sisaev",
         [f"bundle-60003.{vlan}", f"bundle-60000.{vlan}"], f"g_yor_v{vlan}", "ingress-spine"),
        ("DNAAS-SuperSpine-D04", "100.64.100.1",  "sisaev",
         [f"bundle-60004.{vlan}", f"bundle-60007.{vlan}"], f"g_yor_v{vlan}", "super-spine"),
        ("SPINE-D14",           "100.64.100.129", "sisaev",
         [f"bundle-60000.{vlan}", f"bundle-60004.{vlan}"], f"g_yor_v{vlan}", "egress-spine"),
        ("DNAAS-LEAF-D16",      "100.64.101.123", "sisaev",
         [f"bundle-60000.{vlan}", f"ge100-0/0/5.{vlan}"],  f"g_yor_v{vlan}", "egress-leaf"),
    ]


def _dnaas_ssh_creds(config):
    """Returns (password) from dnaas_credentials_b64 in spirent config."""
    import base64
    b64 = config.get("dnaas_credentials_b64", "")
    if not b64:
        raise RuntimeError("~/.spirent_config.json missing dnaas_credentials_b64")
    return base64.b64decode(b64).decode()


def _dnaas_shell_exec(hostname, ip, user, pw, commands, timeout_per_cmd=20,
                      idle_done_sec=1.2, initial_wait=0.4):
    """SSH to DNAAS device, open shell, run commands sequentially, return {cmd: output}.

    Uses an idle-timeout strategy: after sending a command, read until the
    receive buffer has been quiet for `idle_done_sec`, or timeout. This is
    the most reliable pattern on DNOS CLI -- command completion is signalled
    by the prompt returning + no further output. We avoid any marker/echo
    approach because DNOS echoes typed lines greedily, which caused
    premature exit on slow hops (e.g. DNAAS-SuperSpine-D04).
    """
    try:
        import paramiko
    except ImportError as e:
        raise RuntimeError(f"paramiko required: {e}")

    result = {}
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(ip, username=user, password=pw, timeout=15,
              look_for_keys=False, allow_agent=False)
    try:
        chan = c.invoke_shell(width=220, height=80)
        # Prime and drain initial banner until idle
        time.sleep(0.8)
        last_rx = time.time()
        dl = time.time() + 5.0
        while time.time() < dl:
            if chan.recv_ready():
                chan.recv(65536); last_rx = time.time(); time.sleep(0.1)
            else:
                if time.time() - last_rx > 0.8:
                    break
                time.sleep(0.1)

        for cmd in commands:
            chan.send(cmd + "\n")
            time.sleep(initial_wait)
            buf = b""
            last_rx = time.time()
            dl = time.time() + timeout_per_cmd
            while time.time() < dl:
                if chan.recv_ready():
                    buf += chan.recv(65536)
                    last_rx = time.time()
                    time.sleep(0.08)
                else:
                    if buf and (time.time() - last_rx > idle_done_sec):
                        break
                    time.sleep(0.1)
            raw = re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", buf.decode(errors="ignore"))
            result[cmd] = raw
    finally:
        try: chan.close()
        except Exception: pass
        c.close()
    return result


def _analyze_dnaas_output(show_output):
    """Apply fault signatures. Returns list[{code, severity, action, matched_line}]."""
    faults = []
    for rx, code, sev, action in _DNAAS_FAULT_SIGNATURES:
        m = rx.search(show_output)
        if m:
            # capture the matching line for context
            for line in show_output.split("\n"):
                if rx.search(line):
                    faults.append({
                        "code": code, "severity": sev, "action": action,
                        "matched_line": line.strip(),
                    })
                    break
    return faults


def _dnaas_diagnose_hop(hostname, ip, user, pw, subifs):
    """Probe a single hop: run show interfaces for each subif, analyze faults.
    Returns list[{subif, faults:[], oper_state, admin_state, reason}]."""
    cmds = [f"show interfaces {s} | no-more" for s in subifs]
    try:
        outs = _dnaas_shell_exec(hostname, ip, user, pw, cmds)
    except Exception as e:
        return [{"subif": s, "faults": [], "error": str(e),
                 "oper_state": None, "admin_state": None, "reason": None} for s in subifs]

    results = []
    for s in subifs:
        txt = outs.get(f"show interfaces {s} | no-more", "")
        oper = admin = reason = None
        last_changed = None
        state_trans = None
        for line in txt.split("\n"):
            m = re.search(r"Admin state:\s*(\S+)", line)
            if m: admin = m.group(1).rstrip(",")
            m = re.search(r"Operational state:\s*(\S+)", line)
            if m: oper = m.group(1).rstrip(",")
            m = re.search(r"Reason for last down state:\s*(.*)", line)
            if m: reason = m.group(1).strip()
            m = re.search(r"Last state change\s*:?\s*(.*?)\s*$", line, re.I)
            if m: last_changed = m.group(1).strip()
            m = re.search(r"(?:Oper(?:ational)? state )?transitions\s*:?\s*(\d+)", line, re.I)
            if m:
                try: state_trans = int(m.group(1))
                except ValueError: pass
        faults = _analyze_dnaas_output(txt)

        # Safety-net: if a non-trivial 'Reason' was captured and no matching
        # signature fired yet, surface it as STICKY_DOWN_REASON so the tool
        # never lies about "all hops clean" when the device itself is
        # reporting a down reason. This is the core /SPIRENT dnaas-diagnose
        # fix for the 'silent link-down' class of failures.
        if reason and reason.lower() not in ("none", "n/a", ""):
            rlow = reason.lower()
            if any(sub in rlow for sub in _STICKY_REASON_SUBSTRINGS):
                already = any(f.get("code") in (
                    "LINK_DOWN_STICKY", "LOCAL_LOOP_SHUTDOWN_STICKY",
                    "ADMIN_DISABLED_STICKY", "ADMIN_CURRENTLY_DISABLED",
                    "OPER_DOWN") for f in faults)
                if not already:
                    faults.append({
                        "code": "STICKY_DOWN_REASON",
                        "severity": "high" if oper and oper.lower() != "up" else "medium",
                        "action": "manual",
                        "matched_line": f"Reason for last down state: {reason}",
                    })

        # Flap evidence: if we captured state-transition count, warn above a
        # threshold even when port is currently up -- a flapping Spirent-
        # facing port is the #1 cause of GatewayMacResolveState=RESOLVE_FAILED.
        if state_trans is not None and state_trans > 50:
            faults.append({
                "code": "PORT_FLAP_HIGH",
                "severity": "medium",
                "action": "manual",
                "matched_line": f"Oper state transitions: {state_trans}",
            })

        results.append({
            "subif": s, "faults": faults,
            "oper_state": oper, "admin_state": admin, "reason": reason,
            "last_changed": last_changed, "state_transitions": state_trans,
        })
    return results


def _dnaas_snapshot_subif(hostname, ip, user, pw, subif):
    """Read current `show config interfaces <subif>` and extract description
    and any vlan-manipulation/other knobs we want to preserve on restore.
    Returns dict with at minimum {description, raw}."""
    try:
        out = _dnaas_shell_exec(hostname, ip, user, pw,
                                [f"show config interfaces {subif} | no-more"],
                                timeout_per_cmd=15, idle_done_sec=1.0)
        raw = out.get(f"show config interfaces {subif} | no-more", "")
    except Exception:
        return {"description": None, "raw": ""}
    desc = None
    for line in raw.split("\n"):
        m = re.search(r"^\s*description\s+(.*?)\s*$", line)
        if m:
            desc = m.group(1).strip('"').strip()
            break
    return {"description": desc, "raw": raw}


def _dnaas_spirent_fabric_desc(vlan, prior_desc=None):
    """Format a canonical SPIRENT fabric description for a sub-interface
    participating in a Spirent transport VLAN. Preserves prior description
    when present by prefixing it.
    """
    tag = f"SPIRENT-fabric-v{vlan}"
    if prior_desc and tag not in prior_desc:
        return f"{prior_desc} | {tag}"
    return prior_desc or tag


def _dnaas_recover_subifs(hostname, ip, user, pw, subifs, bd_name, vlan,
                         dry_run=False, verbose=True, tag_spirent=True):
    """Delete-and-recreate all <subifs> under <bd_name>, with 'top' CLI context
    resets between commands (DNOS hierarchical CLI requirement).

    When tag_spirent=True (default), pre-reads each sub-interface's current
    description and restores it on recreate with the `SPIRENT-fabric-v<vlan>`
    tag appended -- this marks every fabric sub-interface used by a Spirent
    transport VLAN so operators can `show config | include SPIRENT` and
    instantly see the path.

    Returns {phase_results:{...}, ok:bool, descriptions:{...}}.
    """
    # Snapshot current descriptions so we can restore + tag them
    descriptions = {}
    if tag_spirent:
        for s in subifs:
            snap = _dnaas_snapshot_subif(hostname, ip, user, pw, s)
            descriptions[s] = _dnaas_spirent_fabric_desc(vlan, snap.get("description"))
            if verbose:
                prior = snap.get("description") or "<none>"
                print(f"[{hostname}] snapshot {s}: prior_description={prior!r} -> "
                      f"will set {descriptions[s]!r}", flush=True)

    # Build remove block
    remove_block = ["configure", f"network-services bridge-domain instance {bd_name}"]
    for idx, s in enumerate(subifs):
        if idx > 0:
            remove_block.append("top")
            remove_block.append(f"network-services bridge-domain instance {bd_name}")
        remove_block.append(f"no interface {s}")
    remove_block.append("top")
    for idx, s in enumerate(subifs):
        if idx > 0:
            remove_block.append("top")
        remove_block.append(f"no interfaces {s}")

    # Build add block (preserve + tag descriptions)
    add_block = ["configure"]
    for idx, s in enumerate(subifs):
        if idx > 0:
            add_block.append("top")
        add_block.append(f"interfaces {s} admin-state enabled l2-service enabled vlan-id {vlan}")
        if tag_spirent and descriptions.get(s):
            add_block.append(f'interfaces {s} description "{descriptions[s]}"')
    add_block.append("top")
    add_block.append(f"network-services bridge-domain instance {bd_name}")
    for idx, s in enumerate(subifs):
        if idx > 0:
            add_block.append("top")
            add_block.append(f"network-services bridge-domain instance {bd_name}")
        add_block.append(f"interface {s}")
    add_block.append("top")

    commit_cmd = "commit check" if dry_run else "commit"
    phases = {"phase1_remove": [], "phase2_add": []}

    try:
        import paramiko
    except ImportError as e:
        return {"ok": False, "error": f"paramiko required: {e}", "phase_results": phases}

    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        c.connect(ip, username=user, password=pw, timeout=15,
                  look_for_keys=False, allow_agent=False)
        chan = c.invoke_shell(width=220, height=80)
        time.sleep(1.5)
        if chan.recv_ready(): chan.recv(65536)

        def _send(cmd, wait=1.2, timeout=12):
            chan.send(cmd + "\n")
            time.sleep(wait)
            buf = b""
            dl = time.time() + timeout
            while time.time() < dl:
                if chan.recv_ready():
                    buf += chan.recv(65536); time.sleep(0.2)
                else:
                    time.sleep(0.1)
                    if chan.recv_ready(): continue
                    break
            return re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", buf.decode(errors="ignore"))

        for phase_idx, (phase_key, block) in enumerate([("phase1_remove", remove_block),
                                                         ("phase2_add", add_block)]):
            # Exit config mode before phase 2 (phase 1's commit leaves us in config mode)
            if phase_idx > 0:
                _send("end", wait=1.0, timeout=5)

            for line in block:
                out = _send(line)
                phases[phase_key].append({"cmd": line, "out": out.strip()[-400:]})
                if verbose: print(f"[{hostname}] >>> {line}", flush=True)
                if "ERROR" in out or "Invalid word" in out or "rejected" in out.lower():
                    if verbose:
                        for ol in out.split("\n"):
                            if ol.strip() and ("ERROR" in ol or "Invalid" in ol or "rejected" in ol.lower()):
                                print(f"[{hostname}]     [!!] {ol.strip()}", flush=True)

            out = _send(commit_cmd, wait=3.0, timeout=30)
            phases[phase_key].append({"cmd": commit_cmd, "out": out.strip()[-800:]})
            committed_ok = ("succeeded" in out.lower()
                           and "ERROR" not in out
                           and "rejected" not in out.lower())
            if verbose:
                for ol in out.split("\n"):
                    if ol.strip() and any(k in ol for k in ("succeeded", "ERROR", "rejected", "failed", "Commit")):
                        print(f"[{hostname}]     [{commit_cmd}] {ol.strip()}", flush=True)

            if dry_run:
                out = _send("rollback 0", wait=1.5, timeout=8)
                phases[phase_key].append({"cmd": "rollback 0", "out": out.strip()[-200:]})

        _send("end", wait=1.0, timeout=5)

        chan.close()
        return {"ok": True, "phase_results": phases, "dry_run": dry_run,
                "descriptions": descriptions}
    except Exception as e:
        return {"ok": False, "error": str(e), "phase_results": phases,
                "descriptions": descriptions}
    finally:
        try: c.close()
        except Exception: pass


def cmd_dnaas_diagnose(args):
    """Walk all DNAAS hops for a VLAN and report any sticky/live faults."""
    config = load_config()
    try:
        pw = _dnaas_ssh_creds(config)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(2)

    vlan = int(args.vlan)
    hops = _default_dnaas_topology(vlan)

    report = {"vlan": vlan, "hops": [], "any_faults": False}
    print(f"\n=== DNAAS Diagnose VLAN {vlan} ({len(hops)} hops) ===\n", flush=True)

    for hostname, ip, user, subifs, bd_name, role in hops:
        print(f"--- {hostname} ({ip}) [{role}] ---", flush=True)
        hop_result = {
            "hostname": hostname, "ip": ip, "role": role, "bd": bd_name,
            "subifs": _dnaas_diagnose_hop(hostname, ip, user, pw, subifs),
        }
        for s in hop_result["subifs"]:
            if s.get("error"):
                print(f"  [ERR] {s['subif']}: {s['error']}", flush=True)
                continue
            tag = " [!!]" if s["faults"] else "     "
            admin = (s.get("admin_state") or "?").ljust(8)
            oper  = (s.get("oper_state")  or "?").ljust(4)
            reason = (s.get("reason") or "")[:40]
            trans = s.get("state_transitions")
            trans_str = f" trans={trans}" if trans is not None else ""
            print(f"  {tag} {s['subif']:30s} admin={admin} oper={oper} "
                  f"reason='{reason}'{trans_str}", flush=True)
            for f in s["faults"]:
                print(f"       FAULT: {f['code']} ({f['severity']}) "
                      f"-> recovery={f['action']}", flush=True)
                if f.get("matched_line"):
                    print(f"              evidence: {f['matched_line'][:120]}", flush=True)
                report["any_faults"] = True
        report["hops"].append(hop_result)

    if getattr(args, "json_output", False):
        print("\n=== JSON ===")
        print(json.dumps(report, indent=2, default=str))

    if report["any_faults"]:
        print(f"\n[SUMMARY] VLAN {vlan}: faults detected. Run `dnaas-fix --vlan {vlan}` to remediate.", flush=True)
        sys.exit(1)
    else:
        print(f"\n[SUMMARY] VLAN {vlan}: all hops clean.", flush=True)


def cmd_arp_check(args):
    """Report ARP/GatewayMac resolution state for Spirent emulated devices.

    This is the early-abort gate for /TEST: when an EmulatedDevice cannot
    resolve its gateway MAC, it means L2 never reaches the DUT (broken
    DNAAS path, flapping Spirent-facing port, DUT AC down, etc.) and ALL
    subsequent BGP/traffic scenarios will fail. Failing here saves ~10min
    of wasted scenario runs per test.

    Filters:
      --vlan <V>          : only devices whose outer VLAN matches V
      --inner-vlan <IV>   : additionally match inner VLAN
      --name <regex>      : match device name (regex)

    Exit codes:
       0 -> all inspected devices have resolved gateway (or no devices match)
       3 -> at least one device reports RESOLVE_FAILED / NOT_STARTED / etc.
       2 -> session unavailable
    """
    config = load_config()
    try:
        stc, sess = _require_ready(config)
    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(2)

    vlan = int(args.vlan) if args.vlan is not None else None
    inner = int(args.inner_vlan) if args.inner_vlan is not None else None
    name_rx = re.compile(args.name) if args.name else None

    project = sess.get("project_handle")
    try:
        dev_children = stc.get(project, "children-EmulatedDevice") or ""
        dev_handles = dev_children.split() if dev_children.strip() else []
    except Exception as e:
        print(f"ERROR: listing EmulatedDevices from BLL failed: {e}")
        sys.exit(2)

    report = {"vlan": vlan, "inner_vlan": inner, "devices": [],
              "any_failed": False, "total_matched": 0}

    for dh in dev_handles:
        try:
            name = stc.get(dh, "Name") or ""
        except Exception:
            continue
        if name_rx and not name_rx.search(name):
            continue

        # Resolve VLAN stack in WIRE order via the STC IfStack (outer =
        # VlanIf stacked directly on EthIIIf). children-VlanIf list order is
        # creation order, which is the reverse of the wire. See
        # _resolve_device_vlan_stack().
        outer_vlan, inner_vlan, all_vlan_tags = _resolve_device_vlan_stack(stc, dh)

        # Match by set-membership, not positional -- device Q-in-Q'd as 214/5
        # must match `--vlan 214` AND `--vlan 5` equally.
        if vlan is not None and vlan not in all_vlan_tags:
            continue
        if inner is not None and inner not in all_vlan_tags:
            continue

        ip_addr = gateway = None
        resolve_state = None
        gw_mac = None
        try:
            ipv4 = (stc.get(dh, "children-Ipv4If") or "").split()
            if ipv4:
                ip_addr = stc.get(ipv4[0], "Address")
                gateway = stc.get(ipv4[0], "Gateway")
                # GatewayMacResolveState is the STC attribute that flips to
                # RESOLVE_FAILED when ARP to the gateway times out.
                try:
                    resolve_state = stc.get(ipv4[0], "GatewayMacResolveState")
                except Exception:
                    resolve_state = None
                try:
                    gw_mac = stc.get(ipv4[0], "GatewayMac")
                except Exception:
                    gw_mac = None
        except Exception:
            pass

        failed = bool(resolve_state) and str(resolve_state).upper() not in (
            "SUCCEEDED", "RESOLVED", "RESOLVE_SUCCEEDED", "RESOLVE_DONE",
            "ARP_NOT_NEEDED",
        )
        report["devices"].append({
            "name": name, "handle": dh,
            "ip": ip_addr, "gateway": gateway,
            "outer_vlan": outer_vlan, "inner_vlan": inner_vlan,
            "all_vlan_tags": all_vlan_tags,
            "resolve_state": resolve_state,
            "resolved_gateway_mac": gw_mac,
            "failed": failed,
        })
        report["total_matched"] += 1
        if failed:
            report["any_failed"] = True

    if getattr(args, "json_output", False):
        print(json.dumps(report, indent=2, default=str))
    else:
        print(f"\n=== ARP / Gateway MAC Resolve Check "
              f"(vlan={vlan}, inner={inner}, matched={report['total_matched']}) ===\n",
              flush=True)
        for d in report["devices"]:
            tag = " [!!]" if d["failed"] else "     "
            vstr = f"o={d['outer_vlan']}" + (f" i={d['inner_vlan']}" if d['inner_vlan'] else "")
            print(f"  {tag} {d['name']:32s} {vstr:15s} "
                  f"ip={d['ip']} gw={d['gateway']} "
                  f"state={d['resolve_state']} gwMac={d['resolved_gateway_mac']}",
                  flush=True)
        if report["any_failed"]:
            print(f"\n[ARP FAIL] At least one device cannot resolve its gateway. "
                  f"L2 path from Spirent to DUT is broken. Check:\n"
                  f"   - DNAAS leaf Spirent-facing port (show interfaces, flap count)\n"
                  f"   - DNAAS BD membership on all hops (spirent_tool.py dnaas-diagnose --vlan N)\n"
                  f"   - DUT AC admin-state + oper-state\n",
                  flush=True)

    if report["any_failed"]:
        sys.exit(3)


def cmd_dnaas_fix(args):
    """Apply delete+recreate recovery on hops with sticky faults."""
    config = load_config()
    try:
        pw = _dnaas_ssh_creds(config)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(2)

    vlan = int(args.vlan)
    dry_run = bool(getattr(args, "dry_run", False))
    force_all = bool(getattr(args, "force_all", False))
    hops = _default_dnaas_topology(vlan)

    print(f"\n=== DNAAS Fix VLAN {vlan} ({'DRY-RUN' if dry_run else 'APPLY'}) ===\n", flush=True)

    fixed_hops = []
    clean_hops = []
    # --surgical (default True): only delete+recreate the SPECIFIC subifs
    # that have faults. Avoids bouncing clean fabric uplinks that share a
    # hop with a faulted access subif. Example: on B-14, ge100-0/0/15.214
    # is faulted but bundle-60000.214 (fabric uplink to SPINE-B09) is clean
    # -- we should only touch the access port, never the uplink.
    surgical = not bool(getattr(args, "all_subifs", False))
    for hostname, ip, user, subifs, bd_name, role in hops:
        probe = _dnaas_diagnose_hop(hostname, ip, user, pw, subifs)
        has_fault = any(s.get("faults") for s in probe)
        if not has_fault and not force_all:
            print(f"[SKIP] {hostname}: no faults detected.", flush=True)
            clean_hops.append(hostname)
            continue

        if surgical:
            faulted_subifs = [s["subif"] for s in probe if s.get("faults")]
            if not faulted_subifs and force_all:
                faulted_subifs = subifs
            target_subifs = faulted_subifs or subifs
            if target_subifs != subifs:
                print(f"\n[SURGICAL] {hostname}: only recreating faulted "
                      f"subif(s) {target_subifs}, leaving clean "
                      f"{[s for s in subifs if s not in target_subifs]} alone.",
                      flush=True)
        else:
            target_subifs = subifs

        print(f"\n--- RECOVERING {hostname} ({ip}) subifs={target_subifs} BD={bd_name} ---", flush=True)
        res = _dnaas_recover_subifs(hostname, ip, user, pw, target_subifs, bd_name, vlan,
                                    dry_run=dry_run, verbose=True)
        fixed_hops.append({"hostname": hostname, "result": res})

        if not dry_run and res.get("ok"):
            time.sleep(3)
            post = _dnaas_diagnose_hop(hostname, ip, user, pw, target_subifs)
            any_left = any(s.get("faults") for s in post)
            print(f"\n[POST] {hostname}: {'CLEAN' if not any_left else 'STILL HAS FAULTS'}", flush=True)
            for s in post:
                if s.get("faults"):
                    for f in s["faults"]:
                        print(f"       REMAINING: {s['subif']} {f['code']}", flush=True)

    print(f"\n=== SUMMARY ===\nClean hops: {clean_hops}\nFixed hops: {[h['hostname'] for h in fixed_hops]}", flush=True)


# ============================================================================
# dnaas-stabilize -- Prevent DNAAS AC flaps that kill ARP resolution & tests.
# Applies three layers of live-validated syntax (commit-check PASSED on B-14
# 2026-04-21):
#   1. Interface dampening on the leaf ACCESS physical port (Spirent/DUT-facing)
#      -- suppresses chronic flapping over seconds/minutes via penalty decay.
#      Syntax RELIES on physical ethernet port, NOT bundle (DNOS rejects
#      `interfaces bundle-60000 dampening ...` -> "Unknown word: 'dampening'").
#   2. Carrier-delay up/down on the same physical port -- absorbs O(ms)
#      transient flaps before they reach the control plane / LLP counter.
#   3. BD Local-Loop-Prevention tuning (restore-timer=60s, restore-max-cycles=
#      infinite) + clear any stuck ac-suppression / ac-history / mac-history.
#      LLP threshold must stay 2-30 (30=max, already configured) -- DNOS rejects
#      values >30 as "Invalid value".
# Spine / super-spine hops are bundle-only and skip physical dampening; they
# still get BD LLP tuning + clears.
# Evidence: Confluence page 6311346740 (carrier-delay-and-dampening), page
# 4943773697 (v25.1 BD LLP), page 5252677674 (DNAAS POC recommended values).
# ============================================================================

def _dnaas_physical_port(subif):
    """Map 'ge100-0/0/15.214' -> 'ge100-0/0/15'. Returns None for bundle
    sub-interfaces (dampening rejected on DNAAS bundle-60000) so callers
    skip physical dampening on spine hops.
    """
    if subif.startswith("bundle-"):
        return None
    if "." in subif:
        return subif.rsplit(".", 1)[0]
    return subif


def _dnaas_build_stabilize_cfg(physical, bd_name, disable_llp=False,
                               dampening=True, carrier_delay=True, tune_llp=True):
    """Return list of DNOS config lines to stabilize one leaf hop.
    All lines have been commit-check VALIDATED on DNAAS-LEAF-B14 2026-04-21.
    """
    lines = []
    if dampening and physical and not physical.startswith("bundle-"):
        lines += [
            f"interfaces {physical} dampening admin-state enabled",
            f"interfaces {physical} dampening half-life 300",
            f"interfaces {physical} dampening reuse-threshold 1000",
            f"interfaces {physical} dampening suppress-threshold 5000",
            f"interfaces {physical} dampening max-suppress 1800",
        ]
    if carrier_delay and physical and not physical.startswith("bundle-"):
        lines += [
            f"interfaces {physical} carrier-delay up 500",
            f"interfaces {physical} carrier-delay down 2000",
        ]
    if tune_llp and bd_name:
        lines += [
            f"network-services bridge-domain instance {bd_name} "
            f"mac-handling loop-prevention local-loop-prevention restore-timer 60",
            f"network-services bridge-domain instance {bd_name} "
            f"mac-handling loop-prevention local-loop-prevention restore-max-cycles infinite",
        ]
    if disable_llp and bd_name:
        # Only used with --disable-llp (for controlled test runs). Dangerous in prod.
        lines += [
            f"network-services bridge-domain instance {bd_name} "
            f"mac-handling loop-prevention local-loop-prevention admin-state disabled",
        ]
    return lines


def _dnaas_build_clear_cmds(bd_name):
    """Operator-mode clears to reset any stuck AC/MAC suppression state. Safe to
    run anytime. Clears do NOT require config mode.
    """
    return [
        f"clear bridge-domain instance {bd_name} ac-suppression",
        f"clear bridge-domain instance {bd_name} ac-history",
        f"clear bridge-domain instance {bd_name} ac-restore-cycles",
        f"clear bridge-domain instance {bd_name} mac-suppression",
        f"clear bridge-domain instance {bd_name} mac-history",
    ]


def _dnaas_stabilize_check_hop(hostname, ip, user, pw, physical, bd_name):
    """Read-only state check on one hop. Returns dict with current dampening,
    carrier-delay, LLP config + any active shutdown interfaces.
    """
    cmds = []
    if physical:
        cmds += [
            f"show config interfaces {physical} dampening | no-more",
            f"show config interfaces {physical} carrier-delay | no-more",
            f"show interfaces dampening {physical} | no-more",
        ]
    if bd_name:
        cmds += [
            f"show bridge-domain instance {bd_name} loop-prevention | no-more",
            f"show bridge-domain instance {bd_name} loop-prevention interface | no-more",
        ]
    try:
        outs = _dnaas_shell_exec(hostname, ip, user, pw, cmds,
                                 timeout_per_cmd=15, idle_done_sec=1.0)
    except Exception as e:
        return {"error": str(e), "hostname": hostname}
    state = {"hostname": hostname, "physical": physical, "bd": bd_name}
    if physical:
        damp_cfg = outs.get(f"show config interfaces {physical} dampening | no-more", "")
        cd_cfg = outs.get(f"show config interfaces {physical} carrier-delay | no-more", "")
        damp_show = outs.get(f"show interfaces dampening {physical} | no-more", "")
        state["dampening_configured"] = "admin-state enabled" in damp_cfg
        state["carrier_delay_configured"] = bool(re.search(r"carrier-delay\s+(up|down)\s+\d+", cd_cfg))
        m = re.search(r"Current penalty counter:\s*(\S+)", damp_show)
        state["current_penalty"] = m.group(1) if m else None
        m = re.search(r"Interface state changes due to dampening event:\s*(\d+)",
                      damp_show)
        state["damp_events"] = int(m.group(1)) if m else 0
    if bd_name:
        lp = outs.get(f"show bridge-domain instance {bd_name} loop-prevention | no-more", "")
        m = re.search(r"Loop Prevention\s*\|\s*(\S+)", lp)
        state["llp_admin_state"] = m.group(1) if m else None
        m = re.search(r"Restore Timer\s*\|\s*(\S+)", lp)
        state["llp_restore_timer"] = m.group(1) if m else None
        m = re.search(r"Restore Max Cycles\s*\|\s*(\S+)", lp)
        state["llp_restore_max_cycles"] = m.group(1) if m else None
        m = re.search(r"Number of Shutdown Interfaces\s*\|\s*(\d+)", lp)
        state["llp_shutdown_interfaces"] = int(m.group(1)) if m else 0
    return state


def _dnaas_stabilize_apply_hop(hostname, ip, user, pw, physical, bd_name,
                              dry_run=True, disable_llp=False, verbose=True):
    """Apply the stabilize config block on one hop. Uses commit-check first,
    then either commit or rollback 0 depending on dry_run. Clears run in
    operator mode AFTER config commits (clears do not live in candidate).
    """
    cfg_lines = _dnaas_build_stabilize_cfg(physical, bd_name, disable_llp=disable_llp)
    if not cfg_lines:
        return {"hostname": hostname, "ok": True, "skipped": "no applicable config (spine bundle-only hop with no access port)",
                "physical": physical, "bd": bd_name, "applied_lines": []}
    clear_cmds = _dnaas_build_clear_cmds(bd_name) if bd_name else []

    # Build the config-mode block
    seq = ["configure"] + cfg_lines
    # Always commit-check first
    seq.append("commit check")
    if dry_run:
        seq += ["rollback 0", "end"]
    else:
        seq += ["commit", "top", "end"] + clear_cmds

    try:
        outs = _dnaas_shell_exec(hostname, ip, user, pw, seq,
                                 timeout_per_cmd=25, idle_done_sec=1.2)
    except Exception as e:
        return {"hostname": hostname, "ok": False, "error": str(e),
                "physical": physical, "bd": bd_name}

    errors = []
    commit_check_ok = False
    commit_ok = False
    for cmd, out in outs.items():
        if re.search(r"ERROR:|Invalid value|Unknown word|Commit check failed|Commit failed",
                     out, re.I):
            errors.append({"cmd": cmd[:90], "detail": out[-300:].strip()})
        if cmd == "commit check" and re.search(r"Commit check passed|not applicable",
                                                out, re.I):
            commit_check_ok = True
        if cmd == "commit" and re.search(r"Commit succeeded|not applicable", out, re.I):
            commit_ok = True
    ok = not errors and (commit_check_ok or commit_ok)
    return {
        "hostname": hostname, "ok": ok, "errors": errors,
        "physical": physical, "bd": bd_name,
        "dry_run": dry_run, "disable_llp": disable_llp,
        "applied_lines": cfg_lines,
        "cleared": clear_cmds if not dry_run else [],
        "commit_check_ok": commit_check_ok, "commit_ok": commit_ok,
    }


def cmd_dnaas_stabilize(args):
    """Apply AC-flap-prevention stack across all DNAAS hops for a VLAN.

    Layers (all syntax live-validated via commit-check):
      - Interface dampening on leaf access port (ge100-0/0/15 on B-14,
        ge100-0/0/5 on D-16 for VLAN 214)
      - Carrier-delay up 500ms / down 2000ms on same ports
      - BD LLP tuning (restore-timer 60s, restore-max-cycles infinite)
      - Clear any stuck ac-suppression / ac-history / mac-history

    Spine/super-spine hops (bundle-only) skip physical dampening; they still
    get BD LLP tuning + clears.

    Default is --check (read current state only). Use --dry-run for
    commit-check + rollback 0. Use --apply to commit.
    """
    config = load_config()
    try:
        pw = _dnaas_ssh_creds(config)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(2)

    vlan = int(args.vlan)
    mode = "apply" if args.apply else ("dry-run" if args.dry_run else "check")
    disable_llp = bool(getattr(args, "disable_llp", False))
    hops = _default_dnaas_topology(vlan)

    print(f"\n=== DNAAS Stabilize VLAN {vlan} [mode={mode}] ===", flush=True)
    if mode == "check":
        print("Reading current flap-protection state (dampening, carrier-delay, LLP)...\n", flush=True)
    else:
        print("Target: prevent AC flaps that break ARP resolution / traffic.\n", flush=True)

    results = []
    for hostname, ip, user, subifs, bd_name, role in hops:
        # Find the access physical port (non-bundle subif)
        physical = None
        for s in subifs:
            pp = _dnaas_physical_port(s)
            if pp and not pp.startswith("bundle-"):
                physical = pp
                break
        print(f"--- {hostname} ({ip}) [{role}] "
              f"port={physical or '(bundle-only)'} bd={bd_name} ---", flush=True)

        if mode == "check":
            st = _dnaas_stabilize_check_hop(hostname, ip, user, pw, physical, bd_name)
            if st.get("error"):
                print(f"  [ERR] {st['error']}", flush=True)
            else:
                if physical:
                    dmp = "ON " if st.get("dampening_configured") else "OFF"
                    cd = "ON " if st.get("carrier_delay_configured") else "OFF"
                    pen = st.get("current_penalty", "?")
                    evs = st.get("damp_events", 0)
                    print(f"  dampening={dmp}  carrier-delay={cd}  penalty={pen}  damp_events={evs}",
                          flush=True)
                if bd_name:
                    print(f"  LLP admin={st.get('llp_admin_state')}  "
                          f"restore_timer={st.get('llp_restore_timer')}  "
                          f"max_cycles={st.get('llp_restore_max_cycles')}  "
                          f"shutdown_ifs={st.get('llp_shutdown_interfaces')}",
                          flush=True)
            results.append(st)
        else:
            res = _dnaas_stabilize_apply_hop(hostname, ip, user, pw, physical, bd_name,
                                             dry_run=(mode == "dry-run"),
                                             disable_llp=disable_llp)
            if res.get("skipped"):
                print(f"  [SKIP] {res['skipped']}", flush=True)
            else:
                print(f"  lines: {len(res.get('applied_lines', []))}", flush=True)
                for ln in res.get("applied_lines", [])[:4]:
                    print(f"     + {ln}", flush=True)
                if len(res.get("applied_lines", [])) > 4:
                    print(f"     + ... ({len(res['applied_lines']) - 4} more)", flush=True)
                if res.get("cleared"):
                    print(f"  cleared: {len(res['cleared'])} operator-mode state resets",
                          flush=True)
                if res.get("errors"):
                    print(f"  [!!] errors: {len(res['errors'])}", flush=True)
                    for e in res["errors"][:3]:
                        print(f"       {e['cmd']}: {e['detail'][:160]}", flush=True)
                elif mode == "apply":
                    tag = "[OK]" if res.get("commit_ok") else "[PARTIAL]"
                    print(f"  {tag} commit={res.get('commit_ok')}  "
                          f"check={res.get('commit_check_ok')}", flush=True)
                else:
                    tag = "[OK]" if res.get("commit_check_ok") else "[FAIL]"
                    print(f"  {tag} commit-check={res.get('commit_check_ok')}", flush=True)
            results.append(res)

    any_fail = any(not r.get("ok", False) and not r.get("skipped") for r in results)

    if getattr(args, "json_output", False):
        print("\n=== JSON ===")
        print(json.dumps({"vlan": vlan, "mode": mode, "results": results},
                         indent=2, default=str))

    print(f"\n=== SUMMARY === VLAN {vlan} mode={mode}", flush=True)
    for r in results:
        if r.get("error"):
            print(f"  [ERR]  {r.get('hostname')}: {r['error']}", flush=True)
        elif r.get("skipped"):
            print(f"  [SKIP] {r.get('hostname')}: {r['skipped']}", flush=True)
        elif mode == "check":
            dmp = "DAMP=ON " if r.get("dampening_configured") else "DAMP=off"
            llp_sh = r.get("llp_shutdown_interfaces", 0) or 0
            tag = "[OK]" if llp_sh == 0 and r.get("dampening_configured") else "[TUNE]"
            print(f"  {tag} {r.get('hostname'):22s} {dmp} "
                  f"shutdown_ifs={llp_sh} bd={r.get('bd')}", flush=True)
        else:
            tag = "[OK]" if r.get("ok") else "[FAIL]"
            print(f"  {tag} {r.get('hostname'):22s} "
                  f"port={r.get('physical')} bd={r.get('bd')}", flush=True)

    if mode == "check" and not any_fail:
        any_untuned = any(
            r.get("physical") and not r.get("dampening_configured") for r in results
        )
        if any_untuned:
            print("\n[HINT] Some leaves lack dampening. Run with --apply to deploy.",
                  flush=True)
    sys.exit(1 if any_fail else 0)


# ============================================================================
# dut-match -- Verify every Spirent EmulatedDevice maps to a real DUT sub-
# interface with matching VLAN tag(s) + IP + VRF. Smart DNOS-syntax search per
# user directive: "smart search via dnos syntax the correct matching on the
# DUT appon they are created". Runs after /SPIRENT create-device / bgp-peer /
# l2 to catch VLAN/IP mismatches immediately instead of during traffic start.
# ============================================================================

def _dut_pull_subif_index(dut_ip, dut_user, dut_pw):
    """SSH to DUT and pull full sub-interface index from `show config
    interfaces | no-more`. Returns list of dicts with parsed attrs.
    """
    try:
        import paramiko
    except Exception as e:
        return {"error": f"paramiko unavailable: {e}", "subifs": []}
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(dut_ip, username=dut_user, password=dut_pw, timeout=15,
                  allow_agent=False, look_for_keys=False)
    except Exception as e:
        return {"error": f"SSH to {dut_ip} failed: {e}", "subifs": []}
    try:
        chan = c.invoke_shell(width=220, height=80)
        time.sleep(1.2)
        while chan.recv_ready(): chan.recv(999999)

        def send(cmd, wait=1.2, tmo=25):
            chan.send(cmd + "\n")
            time.sleep(wait)
            buf = ""
            dl = time.time() + tmo
            last = time.time()
            while time.time() < dl:
                if chan.recv_ready():
                    buf += chan.recv(999999).decode(errors="ignore")
                    last = time.time()
                else:
                    if buf and (time.time() - last) > 1.0:
                        break
                    time.sleep(0.15)
            return re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", buf)

        send("no-paging")
        cfg = send("show config interfaces | no-more", wait=2.0, tmo=60)
    except Exception as e:
        c.close()
        return {"error": f"CLI read failed: {e}", "subifs": []}
    finally:
        try: c.close()
        except Exception: pass

    # Parse: an interface block starts with a line like "  ge400-0/0/5.1" at
    # some indentation, followed by indented attribute lines, ending with "!".
    subifs = []
    current = None
    for raw in cfg.split("\n"):
        line = raw.rstrip()
        m = re.match(r"^\s+(ge\S+\.\d+|bundle-\S+\.\d+|ge\S+|bundle-\S+)\s*$", line)
        if m and ("." in m.group(1)):
            if current:
                subifs.append(current)
            current = {"name": m.group(1)}
            continue
        if current is None:
            continue
        if re.match(r"^\s*!\s*$", line):
            subifs.append(current)
            current = None
            continue
        s = line.strip()
        m = re.match(r"^vlan-tags outer-tag (\d+) inner-tag (\d+)", s)
        if m:
            current["vlan_outer"] = int(m.group(1))
            current["vlan_inner"] = int(m.group(2))
            continue
        m = re.match(r"^vlan-id (\d+)", s)
        if m:
            current["vlan_id"] = int(m.group(1))
            continue
        m = re.match(r"^ipv4-address\s+(\S+)", s)
        if m:
            current["ipv4"] = m.group(1)
            continue
        m = re.match(r"^l2-service\s+(\S+)", s)
        if m:
            current["l2_service"] = m.group(1)
            continue
        m = re.match(r"^admin-state\s+(\S+)", s)
        if m:
            current["admin"] = m.group(1)
            continue
    if current:
        subifs.append(current)
    return {"subifs": subifs, "dut_ip": dut_ip}


def _score_subif_match(attrs, outer, inner, device_ip, gateway_ip):
    """Return (score, reasons) for how well a DUT sub-if matches the
    Spirent device's VLAN + IP profile. 100 = perfect match.
    """
    score = 0
    reasons = []
    a_outer = attrs.get("vlan_outer")
    a_inner = attrs.get("vlan_inner")
    a_vid = attrs.get("vlan_id")

    if outer and inner:
        if a_outer == outer and a_inner == inner:
            score += 60
            reasons.append(f"qinq outer={outer} inner={inner} EXACT")
        elif a_outer == outer:
            score += 20
            reasons.append(f"outer={outer} matches but inner differs ({a_inner})")
        elif a_vid == inner:
            score += 15
            reasons.append(f"vlan-id={inner} (inner-only, no outer tag on DUT)")
    elif outer:
        if a_vid == outer:
            score += 55
            reasons.append(f"vlan-id={outer} single-tagged EXACT")
        elif a_outer == outer:
            score += 30
            reasons.append(f"outer={outer} matches but this subif is Q-in-Q")

    if gateway_ip and attrs.get("ipv4"):
        a_ip = attrs["ipv4"].split("/")[0]
        if a_ip == gateway_ip.split("/")[0]:
            score += 35
            reasons.append(f"ipv4={attrs['ipv4']} matches Spirent gateway")
        elif device_ip and a_ip.rsplit(".", 1)[0] == device_ip.split("/")[0].rsplit(".", 1)[0]:
            score += 10
            reasons.append(f"ipv4={attrs['ipv4']} same /24 as Spirent device")

    if attrs.get("admin") == "enabled":
        score += 5
        reasons.append("admin-state=enabled")
    return score, reasons


def cmd_dut_match(args):
    """Cross-check each Spirent EmulatedDevice against DUT sub-interfaces.

    For every device (optionally filtered by --vlan/--name), search DUT
    config for the sub-interface that should receive its traffic. Reports
    MATCH (score >= 70), PARTIAL (score 30-69), or MISS (score < 30 / none).

    Fails with exit code 1 if any device has no MATCH -- /TEST uses this as
    a prerequisite gate.
    """
    config = load_config()
    try:
        stc, sess = _require_ready(config)
    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(2)

    vlan = int(args.vlan) if args.vlan else None
    name_rx = re.compile(args.name) if args.name else None
    dut_raw = getattr(args, "dut", None) or args.dut_ip
    resolved = _resolve_dut_mgmt_ip(dut_raw)
    dut_ip = resolved or dut_raw
    dut_user = args.user or "dnroot"
    dut_pw = args.password or os.environ.get("DNOS_DUT_PW") or "dnroot"

    print(f"\n=== DUT Match Check: DUT={dut_raw} "
          f"(ssh={dut_ip}) vlan_filter={vlan} ===", flush=True)
    if resolved and resolved != dut_raw:
        print(f"    resolved alias {dut_raw!r} -> {resolved}", flush=True)
    print(f"Pulling DUT sub-interface index from {dut_ip}...", flush=True)
    idx = _dut_pull_subif_index(dut_ip, dut_user, dut_pw)
    if idx.get("error"):
        print(f"[!!] {idx['error']}", flush=True)
        sys.exit(2)
    dut_subifs = idx["subifs"]
    print(f"[OK] Parsed {len(dut_subifs)} DUT sub-interfaces.\n", flush=True)

    project = sess.get("project_handle")
    dev_handles = (stc.get(project, "children-EmulatedDevice") or "").split()

    report = {"dut_ip": dut_ip, "vlan_filter": vlan, "devices": [],
              "any_miss": False, "total_matched": 0}
    for dh in dev_handles:
        try:
            name = stc.get(dh, "Name") or ""
            if name_rx and not name_rx.search(name):
                continue
            outer, inner, tags = _resolve_device_vlan_stack(stc, dh)
            if vlan is not None and vlan not in tags:
                continue
            ipvs = (stc.get(dh, "children-Ipv4If") or "").split()
            dev_ip = gw = None
            if ipvs:
                try: dev_ip = stc.get(ipvs[0], "Address")
                except Exception: pass
                try: gw = stc.get(ipvs[0], "Gateway")
                except Exception: pass
        except Exception:
            continue

        scored = []
        for s in dut_subifs:
            sc, reasons = _score_subif_match(s, outer, inner, dev_ip, gw)
            if sc > 0:
                scored.append({"subif": s["name"], "score": sc,
                               "reasons": reasons, "attrs": s})
        scored.sort(key=lambda x: -x["score"])
        best = scored[0] if scored else None

        if best and best["score"] >= 70:
            verdict = "MATCH"
        elif best and best["score"] >= 30:
            verdict = "PARTIAL"
        else:
            verdict = "MISS"
            report["any_miss"] = True
        report["devices"].append({
            "name": name, "outer": outer, "inner": inner,
            "device_ip": dev_ip, "gateway": gw,
            "verdict": verdict, "best": best, "top3": scored[:3],
        })
        report["total_matched"] += 1

        tag_map = {"MATCH": "[OK]", "PARTIAL": "[?]", "MISS": "[!!]"}
        print(f"{tag_map[verdict]} {name:30s} outer={outer} inner={inner} "
              f"ip={dev_ip} gw={gw}", flush=True)
        if best:
            print(f"     best: {best['subif']} (score={best['score']})",
                  flush=True)
            for r in best["reasons"]:
                print(f"       - {r}", flush=True)
        else:
            print(f"     [MISS] No DUT sub-interface tags match.", flush=True)

    if getattr(args, "json_output", False):
        print("\n=== JSON ===")
        print(json.dumps(report, indent=2, default=str))

    print(f"\n=== SUMMARY === matched={report['total_matched']} "
          f"miss={'YES' if report['any_miss'] else 'no'}", flush=True)
    sys.exit(1 if report["any_miss"] else 0)


# ============================================================================
# mark-dnos -- Tag DNOS objects (sub-interfaces, BGP neighbors, fabric BDs)
# with SPIRENT:<session>/<device>/v<vlan> descriptions for fast debugging.
# Per user directive: /SPIRENT must mark every Spirent-owned DNOS object with
# a description so `show config | include SPIRENT` shows the full Spirent
# footprint on any device. Runs on: DUT sub-ifs, DUT BGP neighbors (default +
# per-VRF), and fabric BD ACs for transport VLANs.
# ============================================================================

_DNOS_SUBIF_ATTR_RX = re.compile(
    r"^\s*(ipv4-address|vlan-id|vlan-tags.*)\s+(.*?)\s*$"
)


def _dnos_fetch_subif_map(dnos_ssh):
    """Query DUT for all sub-interfaces, return map:
    { subif_name: {vlan_outer, vlan_inner, vlan_id, ipv4, description} }.
    Uses `show config interfaces | no-more` as one fetch.
    """
    cfg = dnos_ssh.send_command("show config interfaces | no-more", timeout=30)
    current = None
    out = {}
    for line in cfg.split("\n"):
        line = line.rstrip()
        m = re.match(r"^\s*(ge\S+|bundle-\S+)\s*$", line)
        if m and (("." in m.group(1)) or "bundle-" in m.group(1)):
            current = m.group(1)
            out.setdefault(current, {})
            continue
        if current is None:
            continue
        if re.match(r"^\s*!\s*$", line):
            current = None
            continue
        md = re.match(r"^\s*description\s+(.*?)\s*$", line)
        if md:
            out[current]["description"] = md.group(1).strip('"').strip()
            continue
        mv = re.match(r"^\s*vlan-id\s+(\d+)", line)
        if mv:
            out[current]["vlan_id"] = int(mv.group(1))
            continue
        mvt = re.match(r"^\s*vlan-tags\s+outer-tag\s+(\d+)\s+inner-tag\s+(\d+)", line)
        if mvt:
            out[current]["vlan_outer"] = int(mvt.group(1))
            out[current]["vlan_inner"] = int(mvt.group(2))
            continue
        mi = re.match(r"^\s*ipv4-address\s+([\d.]+)/(\d+)", line)
        if mi:
            out[current]["ipv4"] = mi.group(1)
            out[current]["ipv4_prefix"] = int(mi.group(2))
            continue
    return out


def _dnos_fetch_bgp_neighbors(dnos_ssh):
    """Parse `show config | no-more` and walk the indented tree to find every
    BGP neighbor node along with its parent scope chain. Captures:
      - scope: 'default' or 'vrf'
      - vrf:   VRF name or None
      - bgp_as: BGP AS number (required for per-neighbor config path)
      - neighbor, description, remote_as
    """
    cfg = dnos_ssh.send_command("show config | no-more", timeout=60)
    lines = cfg.split("\n")

    def indent(s): return len(s) - len(s.lstrip())

    results = []
    # Use a stack of (indent, header_tokens) to track parents
    stack = []  # list of (indent, header_text)
    current_nbr = None
    current_nbr_indent = None

    for ln in lines:
        if not ln.strip() or ln.strip() == "!":
            # end of a block
            if current_nbr is not None and ln.strip() == "!":
                # neighbor block ends when we dedent past its indent
                pass
            continue
        ind = indent(ln)
        # Pop stack entries whose indent is >= current line's indent
        while stack and stack[-1][0] >= ind:
            stack.pop()

        # Close current neighbor if we've dedented past it
        if current_nbr and ind <= current_nbr_indent:
            results.append(current_nbr)
            current_nbr = None
            current_nbr_indent = None

        stripped = ln.strip()

        if current_nbr is not None:
            # Attribute lines inside a neighbor block
            md = re.match(r"^description\s+(.*?)\s*$", stripped)
            if md:
                current_nbr["description"] = md.group(1).strip('"').strip()
            mr = re.match(r"^remote-as\s+(\d+)", stripped)
            if mr:
                current_nbr["remote_as"] = int(mr.group(1))

        # Detect a neighbor start
        mn = re.match(r"^neighbor\s+(\S+)", stripped)
        if mn:
            # Determine scope from the stack
            scope = "default"
            vrf = None
            bgp_as = None
            for _, hdr in stack:
                mi = re.match(r"^instance\s+(\S+)", hdr)
                if mi and vrf is None:
                    vrf = mi.group(1)
                    scope = "vrf"
                mb = re.match(r"^bgp\s+(\d+)", hdr)
                if mb:
                    bgp_as = int(mb.group(1))
            current_nbr = {
                "scope": scope, "vrf": vrf, "bgp_as": bgp_as,
                "neighbor": mn.group(1),
                "description": None, "remote_as": None,
            }
            current_nbr_indent = ind
            # Push the neighbor onto the stack as well so indent tracking works
            stack.append((ind, stripped))
            continue

        # Push container headers onto the stack
        stack.append((ind, stripped))

    if current_nbr is not None:
        results.append(current_nbr)

    return results


def _resolve_dut_mgmt_ip(name_or_ip):
    """Resolve a DUT alias (e.g. YOR_PE-1) to its mgmt IP via SCALER devices.json.

    Returns the resolved IP string, or None if the input already looks like an
    IP, is unresolvable, or devices.json is missing. Checks name/hostname/alias
    AND the plural ``aliases`` list. Intended for use by commands that only need
    an SSH target; falls back to the caller's original input when unresolvable.
    """
    if not name_or_ip:
        return None
    # Already an IPv4 literal? Return None so caller keeps the original string.
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", str(name_or_ip)):
        return None
    try:
        db_path = os.path.expanduser("~/SCALER/db/devices.json")
        if not os.path.exists(db_path):
            return None
        with open(db_path) as fh:
            raw = json.load(fh)
        entries = []
        if isinstance(raw, list):
            entries = [d for d in raw if isinstance(d, dict)]
        elif isinstance(raw, dict):
            if isinstance(raw.get("devices"), list):
                entries = [d for d in raw["devices"] if isinstance(d, dict)]
            else:
                for k, v in raw.items():
                    if isinstance(v, dict):
                        v.setdefault("name", k)
                        entries.append(v)
        target = str(name_or_ip).strip()
        for dev in entries:
            matched = False
            for field in ("name", "hostname", "alias"):
                if str(dev.get(field) or "").strip() == target:
                    matched = True
                    break
            if not matched:
                aliases = dev.get("aliases")
                if isinstance(aliases, list) and target in (str(a).strip() for a in aliases):
                    matched = True
                elif isinstance(aliases, str) and target == aliases.strip():
                    matched = True
            if matched:
                for k in ("mgmt_ip", "ip", "address"):
                    ip = dev.get(k)
                    if ip and str(ip) not in ("?", "None", ""):
                        return str(ip)
    except Exception:
        pass
    return None


def _compose_spirent_tag(session_name, device_name, vlan, inner_vlan=None,
                        role="peer", extra=None):
    """Canonical SPIRENT tag for descriptions.
    Format: SPIRENT:<session>/<device>/v<vlan>[+<inner>]/<role>[/<extra>]
    """
    v = f"v{vlan}"
    if inner_vlan is not None:
        v = f"v{vlan}+{inner_vlan}"
    parts = [f"SPIRENT:{session_name}", device_name, v, role]
    if extra:
        parts.append(extra)
    return "/".join(str(p) for p in parts)


def _merge_spirent_desc(existing, new_tag):
    """Return merged description preserving existing non-SPIRENT content."""
    if not existing:
        return new_tag
    if new_tag in existing:
        return existing
    # Strip any previous SPIRENT:... segment then append the new one
    cleaned = re.sub(r"\s*\|\s*SPIRENT:[^\s|]+(\s*\|\s*)?", " | ", existing).strip(" |")
    cleaned = re.sub(r"^SPIRENT:[^\s|]+(\s*\|\s*)?", "", cleaned).strip(" |")
    return f"{cleaned} | {new_tag}" if cleaned else new_tag


def _mark_dnos_build_plan(session, subif_map, bgp_list):
    """Given a loaded Spirent session + current DUT state, compute a list
    of description patches to apply on DUT.

    Returns list[{object_type, path, current_desc, new_desc, commands}].
    """
    session_name = session.get("session_name") or "dn_spirent_main"
    plan = []

    for d in session.get("devices", []):
        dev_name = d.get("name", "spirent-dev")
        vlan = d.get("vlan")
        inner = d.get("inner_vlan")
        spirent_ip = d.get("ip")
        gateway_ip = d.get("gateway")  # DUT-facing IP
        if not vlan:
            continue

        # Match sub-interface: prefer (outer,inner) match, else vlan-id, else
        # gateway IP match. This handles single-tagged, Q-in-Q, and irregular
        # configs.
        matched_subif = None
        for subif, attrs in subif_map.items():
            if inner is not None:
                if attrs.get("vlan_outer") == vlan and attrs.get("vlan_inner") == inner:
                    matched_subif = subif; break
            else:
                if attrs.get("vlan_id") == vlan or attrs.get("vlan_outer") == vlan:
                    matched_subif = subif; break
        if matched_subif is None and gateway_ip:
            for subif, attrs in subif_map.items():
                if attrs.get("ipv4") == gateway_ip:
                    matched_subif = subif; break

        if matched_subif:
            role = "bgp-peer" if (d.get("peer_as") or d.get("neighbor")) else "device"
            new_tag = _compose_spirent_tag(session_name, dev_name, vlan, inner, role=role)
            cur_desc = subif_map[matched_subif].get("description")
            merged = _merge_spirent_desc(cur_desc, new_tag)
            if merged != cur_desc:
                plan.append({
                    "object_type": "subif",
                    "path": matched_subif,
                    "current_desc": cur_desc,
                    "new_desc": merged,
                    "commands": [f'interfaces {matched_subif} description "{merged}"'],
                })

        # Match BGP neighbor (Spirent peer IP == DUT neighbor address)
        if spirent_ip:
            for bn in bgp_list:
                if bn.get("neighbor") != spirent_ip:
                    continue
                new_tag = _compose_spirent_tag(
                    session_name, dev_name, vlan, inner,
                    role="bgp-peer",
                    extra=f"as{d.get('peer_as') or bn.get('remote_as') or '?'}")
                merged = _merge_spirent_desc(bn.get("description"), new_tag)
                if merged == bn.get("description"):
                    continue
                bgp_as = bn.get("bgp_as")
                if bn["scope"] == "default" and bgp_as:
                    cmd = (f'protocols bgp {bgp_as} neighbor {spirent_ip} '
                           f'description "{merged}"')
                elif bn["scope"] == "vrf" and bgp_as:
                    cmd = (f'network-services vrf instance {bn["vrf"]} '
                           f'protocols bgp {bgp_as} neighbor {spirent_ip} '
                           f'description "{merged}"')
                else:
                    # Missing AS -- cannot form a valid patch; skip and warn
                    plan.append({
                        "object_type": "bgp_neighbor_SKIPPED",
                        "path": f"{bn.get('vrf') or 'default'}:{spirent_ip}",
                        "current_desc": bn.get("description"),
                        "new_desc": merged,
                        "commands": ["! missing bgp_as in parsed config, skipped"],
                    })
                    continue
                plan.append({
                    "object_type": "bgp_neighbor",
                    "path": f"{bn.get('vrf') or 'default'}(AS{bgp_as}):{spirent_ip}",
                    "current_desc": bn.get("description"),
                    "new_desc": merged,
                    "commands": [cmd],
                })
    return plan


def _mark_fabric_hops_plan(vlan, user, pw, session_name):
    """Build per-hop description plans for every sub-interface in the
    _default_dnaas_topology(vlan). Returns list of:
      {hostname, ip, user, pw, patches:[{subif, current_desc, new_desc}]}
    """
    plans = []
    for hostname, ip, usr, subifs, bd_name, role in _default_dnaas_topology(vlan):
        hop_plan = {"hostname": hostname, "ip": ip, "user": usr,
                    "bd": bd_name, "role": role, "patches": []}
        try:
            out = _dnaas_shell_exec(
                hostname, ip, usr, pw,
                [f"show config interfaces {s} | no-more" for s in subifs],
                timeout_per_cmd=15, idle_done_sec=1.0)
        except Exception as e:
            hop_plan["error"] = str(e)
            plans.append(hop_plan); continue
        for s in subifs:
            raw = out.get(f"show config interfaces {s} | no-more", "")
            cur = None
            for line in raw.split("\n"):
                m = re.search(r"^\s*description\s+(.*?)\s*$", line)
                if m:
                    cur = m.group(1).strip('"').strip()
                    break
            tag = f"SPIRENT-fabric-v{vlan}/{session_name}/{role}"
            merged = _merge_spirent_desc(cur, tag)
            if merged != cur:
                hop_plan["patches"].append({
                    "subif": s, "current_desc": cur, "new_desc": merged,
                })
        plans.append(hop_plan)
    return plans


def _apply_fabric_hop_patches(hop_plan, user, pw, dry_run=False):
    """Apply description patches to a single fabric hop via commit-check(+commit)."""
    try:
        import paramiko
    except Exception as e:
        return {"ok": False, "error": f"paramiko: {e}"}
    if not hop_plan.get("patches"):
        return {"ok": True, "skipped": True}

    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        c.connect(hop_plan["ip"], username=user, password=pw,
                  timeout=15, look_for_keys=False, allow_agent=False)
        chan = c.invoke_shell(width=220, height=80)
        time.sleep(1.2)
        if chan.recv_ready(): chan.recv(65536)

        def _send(cmd, wait=0.8, timeout=15):
            chan.send(cmd + "\n"); time.sleep(wait)
            buf = b""; dl = time.time() + timeout
            last_rx = time.time()
            while time.time() < dl:
                if chan.recv_ready():
                    buf += chan.recv(65536); last_rx = time.time(); time.sleep(0.1)
                else:
                    if buf and (time.time() - last_rx > 1.0): break
                    time.sleep(0.1)
            return re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", buf.decode(errors="ignore"))

        _send("configure")
        for p in hop_plan["patches"]:
            _send(f'interfaces {p["subif"]} description "{p["new_desc"]}"')
            _send("top")
        chk = _send("commit check", wait=2.0, timeout=25)
        if "passed" not in chk.lower():
            _send("rollback 0")
            _send("end")
            chan.close()
            return {"ok": False, "error": "commit check failed",
                    "detail": chk.strip()[-500:]}
        if dry_run:
            _send("rollback 0"); _send("end"); chan.close()
            return {"ok": True, "dry_run": True}
        committed = _send("commit", wait=2.0, timeout=25)
        _send("end")
        chan.close()
        if "succeeded" not in committed.lower():
            return {"ok": False, "error": "commit did not succeed",
                    "detail": committed.strip()[-500:]}
        return {"ok": True, "commit": committed.strip()[-200:]}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        try: c.close()
        except Exception: pass


# ---------------------------------------------------------------------------
# footprint -- smart search: list every SPIRENT:* / TEST:* tagged DUT object
# in seconds via `show config | flatten | include <tag>`.
#
# Why this exists: BGP / VPLS / EVPN debugging on a busy DUT takes minutes
# because ``show config`` for the whole router is huge. With canonical
# descriptions applied by /SPIRENT (mark-dnos) and /TEST (provisioner), a
# single flatten|include pass returns only the lines the test framework owns
# -- zero noise, pinpoint ownership, instant state cross-check.
# ---------------------------------------------------------------------------
# Expected line shapes (flatten format, one config leaf per line):
#   interfaces ge400-0/0/5.5 description SPIRENT:dn_spirent_main/...
#   protocols bgp 1234567 neighbor 19.19.19.2 description SPIRENT:...
#   network-services evpn instance HA_TEST_ELAN description TEST:...
#   interfaces ge400-0/0/4.1000 description TEST:mac_mobility/evpn-ac/si
_FOOTPRINT_LINE_RE = re.compile(
    r"""^
    (?P<path>.+?)\s+            # config path up to last segment
    description\s+
    (?:"(?P<qdesc>[^"]*)"|(?P<udesc>\S+))
    \s*$""",
    re.VERBOSE,
)


def _footprint_classify(path, desc):
    """Return (owner, session_or_test, device_or_role, object_type, identity)
    for a description tag. owner in {SPIRENT, TEST, OTHER}."""
    d = desc.strip()
    if d.startswith("SPIRENT:"):
        parts = d[len("SPIRENT:"):].split("/")
        session = parts[0] if parts else "?"
        device = parts[1] if len(parts) > 1 else "?"
        role = parts[3] if len(parts) > 3 else (parts[2] if len(parts) > 2 else "?")
        owner = "SPIRENT"
        handle = f"{session}/{device}"
    elif d.startswith("SPIRENT-fabric-"):
        m = re.match(r"SPIRENT-fabric-v(\d+)/(\S+?)(?:/(\S+))?$", d)
        session = m.group(2) if m else "?"
        device = f"fabric-v{m.group(1)}" if m else d
        role = m.group(3) if m and m.group(3) else "fabric-hop"
        owner = "SPIRENT"
        handle = f"{session}/{device}"
    elif d.startswith("TEST:"):
        parts = d[len("TEST:"):].split("/")
        session = parts[0] if parts else "?"
        device = parts[1] if len(parts) > 1 else "?"
        role = parts[2] if len(parts) > 2 else (parts[1] if len(parts) > 1 else "?")
        owner = "TEST"
        handle = f"{session}/{device}"
    else:
        owner = "OTHER"
        handle = "-"
        role = "-"

    if path.startswith("interfaces "):
        otype = "interface"
        ident = path[len("interfaces "):]
    elif path.startswith("network-services evpn instance "):
        otype = "evpn-inst"
        ident = path[len("network-services evpn instance "):].split(" ", 1)[0]
    elif path.startswith("network-services bridge-domain "):
        otype = "bridge-domain"
        ident = path[len("network-services bridge-domain "):].split(" ", 1)[0]
    elif path.startswith("protocols bgp "):
        m = re.search(r"neighbor\s+(\S+)", path)
        if m:
            otype = "bgp-neighbor"
            ident = m.group(1)
        else:
            otype = "bgp-config"
            ident = path
    elif path.startswith("protocols isis"):
        otype = "isis"
        ident = path
    elif path.startswith("routing-options "):
        otype = "routing-options"
        ident = path
    else:
        otype = "other"
        ident = path

    return owner, handle, role, otype, ident


def _footprint_parse(text):
    """Parse `show config | flatten | include description` output.

    Returns list[{owner, handle, role, object_type, identity, path, desc}].
    Skips lines that don't match the flatten description pattern.
    """
    out = []
    for line in text.split("\n"):
        line = line.strip()
        if not line or "description " not in line:
            continue
        m = _FOOTPRINT_LINE_RE.match(line)
        if not m:
            continue
        path = m.group("path").strip()
        desc = (m.group("qdesc") or m.group("udesc") or "").strip()
        if not desc:
            continue
        owner, handle, role, otype, ident = _footprint_classify(path, desc)
        if owner == "OTHER":
            continue
        out.append({
            "owner": owner,
            "handle": handle,
            "role": role,
            "object_type": otype,
            "identity": ident,
            "path": path,
            "description": desc,
        })
    return out


def _footprint_fetch_bgp_state(ssh):
    """Return {neighbor_ip: {'state': ..., 'remote_as': ...}} parsed from
    `show bgp l2vpn evpn summary` + `show bgp l2vpn vpls summary`."""
    state = {}
    for cmd in (
        "show bgp l2vpn evpn summary | no-more",
        "show bgp l2vpn vpls summary | no-more",
        "show bgp summary | no-more",
    ):
        try:
            out = ssh.send_command(cmd)
        except Exception:
            continue
        for line in out.split("\n"):
            # `  19.19.19.2      4    1234567     394242  ...  Connect `
            m = re.match(
                r"^\s*([0-9a-fA-F\.:]+)\s+\d+\s+(\d+)\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\S+\s+(\S+)",
                line,
            )
            if not m:
                continue
            ip, remote_as, st = m.group(1), m.group(2), m.group(3)
            prev = state.get(ip)
            # Keep Established state if any summary shows it up
            if prev and prev.get("state") == "Established":
                continue
            state[ip] = {"state": st, "remote_as": remote_as}
    return state


def cmd_footprint(args):
    """Smart search: list every SPIRENT:* / TEST:* tagged DUT object
    using `show config | flatten | include <tag>`.

    Output:
      - Grouped by owner (SPIRENT / TEST), sorted by handle
      - Per-object: path, type, identity, description, state (for BGP + interface)
      - Summary footer: totals, any DOWN Spirent peers highlighted
    """
    try:
        sys.path.insert(0, os.path.expanduser("~/SCALER/scaler"))
        from scaler.dnos_session import DNOSSession  # type: ignore
    except Exception as e:
        print(f"ERROR: cannot import DNOSSession ({e})")
        sys.exit(2)

    dut_host = _resolve_dut_mgmt_ip(args.dut) or args.dut
    user = args.user
    pw = args.password or os.environ.get("DNOS_DUT_PW", "dnroot")

    with DNOSSession(dut_host, user, pw) as ssh:
        # ONE flatten|include pass covers both SPIRENT and TEST tags.
        # Using a broad regex-friendly include so we catch every tag variant
        # in a single SSH round-trip.
        cfg_out = ssh.send_command(
            'show config | flatten | include "description" | no-more'
        )
        entries = _footprint_parse(cfg_out)
        if args.owner:
            entries = [e for e in entries if e["owner"] == args.owner.upper()]
        if args.handle:
            entries = [e for e in entries if args.handle in e["handle"]]

        bgp_state = _footprint_fetch_bgp_state(ssh) if args.with_state else {}

        # Optional: interface admin/oper state lookup for tagged interfaces
        iface_state = {}
        if args.with_state:
            tagged_ifaces = sorted({
                e["identity"] for e in entries if e["object_type"] == "interface"
            })
            for iname in tagged_ifaces:
                try:
                    detail = ssh.send_command(f"show interfaces {iname} | no-more")
                except Exception:
                    continue
                adm = "?"; oper = "?"
                for ln in detail.split("\n"):
                    m = re.search(
                        r"Admin state:\s*(\S+),\s*Operational state:\s*(\S+)", ln
                    )
                    if m:
                        adm = m.group(1).rstrip(",")
                        oper = m.group(2).rstrip(",")
                        break
                iface_state[iname] = {"admin": adm, "oper": oper}

    # ---------------- present ----------------
    if args.json_output:
        payload = {
            "dut": dut_host,
            "entries": entries,
            "bgp_state": bgp_state,
            "iface_state": iface_state,
        }
        print(json.dumps(payload, indent=2, default=str))
        return

    by_owner = {}
    for e in entries:
        by_owner.setdefault(e["owner"], []).append(e)

    print(f"\n=== /SPIRENT + /TEST footprint on {dut_host} "
          f"({len(entries)} tagged objects) ===\n", flush=True)

    if not entries:
        print("No SPIRENT: or TEST: tagged objects found. "
              "Run `mark-dnos --dut <ip>` from /SPIRENT to tag peers, "
              "or ensure /TEST provisioner added TEST: descriptions.")
        return

    down_peers = []
    for owner in ("SPIRENT", "TEST"):
        items = by_owner.get(owner, [])
        if not items:
            continue
        items.sort(key=lambda x: (x["handle"], x["object_type"], x["identity"]))
        print(f"--- {owner} ({len(items)} objects) ---")
        print(f"{'HANDLE':<44}  {'TYPE':<14}  {'IDENTITY':<34}  {'ROLE':<18}  STATE")
        for e in items:
            st = "-"
            if e["object_type"] == "bgp-neighbor" and e["identity"] in bgp_state:
                st = bgp_state[e["identity"]]["state"]
                if owner == "SPIRENT" and st != "Established":
                    down_peers.append((e["handle"], e["identity"], st))
            elif e["object_type"] == "interface" and e["identity"] in iface_state:
                s = iface_state[e["identity"]]
                st = f"{s['admin']}/{s['oper']}"
            print(f"{e['handle']:<44}  {e['object_type']:<14}  "
                  f"{e['identity']:<34}  {e['role']:<18}  {st}")
        print()

    if down_peers:
        print("!! SPIRENT BGP peers NOT established:")
        for h, ip, st in down_peers:
            print(f"   - {h}  neighbor {ip}  state={st}")
        print()


def cmd_mark_dnos(args):
    """Audit + push SPIRENT:* descriptions on DUT sub-ifs, BGP neighbors,
    and (optional) DNAAS fabric hops for a transport VLAN."""
    try:
        sys.path.insert(0, os.path.expanduser("~/SCALER/scaler"))
        from scaler.dnos_session import DNOSSession  # type: ignore
    except Exception as e:
        print(f"ERROR: cannot import DNOSSession ({e}). Ensure SCALER repo is present.")
        sys.exit(2)

    sess = load_session()
    if not sess:
        print("ERROR: no Spirent session loaded. Run `connect` first.")
        sys.exit(2)

    # ---- Fabric-only mode ----
    fabric_vlan = getattr(args, "fabric_vlan", None)
    if fabric_vlan is not None and not args.dut:
        config = load_config()
        try:
            fabric_pw = _dnaas_ssh_creds(config)
        except Exception as e:
            print(f"ERROR: cannot resolve DNAAS creds: {e}"); sys.exit(2)
        session_name = sess.get("session_name") or "dn_spirent_main"
        plans = _mark_fabric_hops_plan(int(fabric_vlan), args.user, fabric_pw, session_name)
        total = sum(len(p.get("patches", [])) for p in plans)
        print(f"\n=== mark-dnos fabric v{fabric_vlan} "
              f"({len(plans)} hops, {total} patches) ===\n", flush=True)
        for hp in plans:
            print(f"--- {hp['hostname']} ({hp['ip']}) role={hp['role']} ---")
            if hp.get("error"):
                print(f"  [ERR] {hp['error']}"); continue
            if not hp["patches"]:
                print("  [SKIP] already tagged"); continue
            for p in hp["patches"]:
                print(f"  {p['subif']:30s}  {p['current_desc'] or '<none>'}  ->  {p['new_desc']}")
        if total == 0:
            print("\nNo patches required."); return
        if args.dry_run:
            print(f"\n[DRY-RUN] {total} patches would be applied."); return
        print(f"\n[APPLY] committing descriptions on {len(plans)} fabric hops...\n")
        for hp in plans:
            if not hp.get("patches"): continue
            r = _apply_fabric_hop_patches(hp, args.user, fabric_pw, dry_run=False)
            if r.get("ok"):
                print(f"  [ok] {hp['hostname']}")
            else:
                print(f"  [FAIL] {hp['hostname']}: {r.get('error')}")
        print("\n[DONE] Fabric descriptions applied.")
        return

    # ---- DUT mode (original) ----
    dut_host = args.dut
    dut_user = args.user
    dut_pw = args.password or os.environ.get("DNOS_DUT_PW", "dnroot")

    session_devices = sess.get("devices", []) or []
    print(f"\n=== mark-dnos on {dut_host} "
          f"(session={sess.get('session_name')}, "
          f"devices={len(session_devices)}) ===\n", flush=True)

    if not session_devices:
        print(
            "Spirent session has no emulated devices yet; nothing to tag on DUT.\n"
            "No patches required.",
            flush=True,
        )
        return

    dut_host_resolved = _resolve_dut_mgmt_ip(dut_host) or dut_host
    if dut_host_resolved != dut_host:
        print(f"      -> resolved DUT alias {dut_host!r} -> {dut_host_resolved}", flush=True)

    with DNOSSession(dut_host_resolved, dut_user, dut_pw) as ssh:
        print("[1/3] Fetching current sub-interface config...", flush=True)
        subif_map = _dnos_fetch_subif_map(ssh)
        print(f"      -> {len(subif_map)} sub-interfaces discovered", flush=True)

        print("[2/3] Fetching current BGP neighbor config...", flush=True)
        bgp_list = _dnos_fetch_bgp_neighbors(ssh)
        print(f"      -> {len(bgp_list)} BGP neighbors discovered", flush=True)

        print("[3/3] Building description patch plan...", flush=True)
        plan = _mark_dnos_build_plan(sess, subif_map, bgp_list)

    print(f"\n=== Plan: {len(plan)} description patches ===")
    for i, p in enumerate(plan, 1):
        print(f"\n[{i}] {p['object_type']:14s} {p['path']}")
        print(f"    current:  {p['current_desc'] or '<none>'}")
        print(f"    proposed: {p['new_desc']}")
        for c in p["commands"]:
            print(f"    cmd:      {c}")

    if not plan:
        print("\nNo patches required -- all Spirent-owned DNOS objects already tagged.")
        return

    if args.json_output:
        print("\n=== JSON ===")
        print(json.dumps(plan, indent=2, default=str))

    if args.dry_run:
        print(f"\n[DRY-RUN] {len(plan)} patches would be applied. Run without --dry-run to commit.")
        return

    # Live apply
    print(f"\n[APPLY] committing {len(plan)} description patches on {dut_host}...", flush=True)
    with DNOSSession(dut_host, dut_user, dut_pw) as ssh:
        with ssh.config_mode():
            for p in plan:
                for c in p["commands"]:
                    try:
                        out = ssh.send_command(c, auto_no_more=False)
                        low = out.lower()
                        if "error" in low or "invalid" in low or "rejected" in low:
                            print(f"  [!!] {p['path']}: {c}\n        {out.strip()[:300]}",
                                  flush=True)
                        else:
                            print(f"  [ok] {p['path']}", flush=True)
                    except Exception as e:
                        print(f"  [!!] {p['path']}: {e}", flush=True)
                    ssh.send_command("top", auto_no_more=False)
            ok_chk, chk_out = ssh.commit(check_only=True)
            if not ok_chk or "passed" not in chk_out.lower():
                print(f"[FAIL] commit check:\n{chk_out.strip()[-600:]}")
                ssh.rollback(0)
                sys.exit(1)
            ok_c, c_out = ssh.commit()
            print(f"[commit] ok={ok_c}: {c_out.strip()[-200:]}")

    print(f"\n[DONE] {len(plan)} descriptions applied on {dut_host}.", flush=True)


# ============================================================================
# Multicast / IGMP / MLD support  (EVPN IGMP-Proxy testing, epic SW-211037)
# ----------------------------------------------------------------------------
# The DUT (PE) is the IGMP proxy / querier. Spirent emulates:
#   * multicast SOURCES  -> data StreamBlock to a group address (auto group MAC)
#   * multicast RECEIVERS -> stateless IGMP/MLD membership reports (joins/leaves)
#   * external mrouter   -> stateless IGMP/MLD General/Group queries (src != 0)
#   * stateful host      -> IgmpHostConfig stack that auto-replies to queries
# Stateless StreamBlock objects (igmp:Igmpv2Report / igmp:Igmpv3Report+grpRecords
# +GroupRecord / igmp:Igmpv1, and the mld:* peers) are verified STC object types.
# The stateful host model (IgmpHostConfig / IgmpGroupMembership / Ipv4Group) and a
# few v3 source-list / query attributes are marked [VALIDATE-LIVE]: confirm the
# exact STC attribute names against the Lab Server on first live /TEST run.
# ============================================================================

# RFC well-known control destinations (group address / L2 MAC).
IGMP_ALL_ROUTERS_IP = "224.0.0.2"        # v2 Leave destination
IGMP_ALL_ROUTERS_MAC = "01:00:5e:00:00:02"
IGMP_V3_REPORT_IP = "224.0.0.22"         # v3 report destination (all IGMPv3 routers)
IGMP_V3_REPORT_MAC = "01:00:5e:00:00:16"
IGMP_ALL_HOSTS_IP = "224.0.0.1"          # general query destination
IGMP_ALL_HOSTS_MAC = "01:00:5e:00:00:01"
MLD_ALL_ROUTERS_IP = "ff02::2"           # MLDv1 Done destination
MLD_V2_REPORT_IP = "ff02::16"            # MLDv2 report destination
MLD_ALL_NODES_IP = "ff02::1"             # MLD general query destination

# IGMPv3 / MLDv2 GroupRecord types (RFC 3376 / RFC 3810; STC enum names).
_V3_RECORD_TYPES = {
    "mode_is_include": "MODE_IS_INCLUDE",
    "mode_is_exclude": "MODE_IS_EXCLUDE",
    "change_to_include": "CHANGE_TO_INCLUDE_MODE",
    "change_to_exclude": "CHANGE_TO_EXCLUDE_MODE",
    "allow_new_sources": "ALLOW_NEW_SOURCES",
    "block_old_sources": "BLOCK_OLD_SOURCES",
}


def _ipv4_mcast_mac(group_ip):
    """RFC 1112: IPv4 multicast group -> 01:00:5e + low 23 bits of the group."""
    octs = [int(x) for x in str(group_ip).split(".")]
    if len(octs) != 4 or not (224 <= octs[0] <= 239):
        raise ValueError(f"{group_ip} is not an IPv4 multicast group (224.0.0.0/4)")
    return "01:00:5e:%02x:%02x:%02x" % (octs[1] & 0x7f, octs[2], octs[3])


def _ipv6_mcast_mac(group_ip):
    """RFC 2464: IPv6 multicast group -> 33:33 + low 32 bits of the group."""
    packed = ipaddress.IPv6Address(str(group_ip)).packed
    return "33:33:%02x:%02x:%02x:%02x" % (packed[12], packed[13], packed[14], packed[15])


def _is_ipv4_mcast(ip):
    try:
        return ipaddress.IPv4Address(str(ip)).is_multicast
    except Exception:
        return False


def _is_ipv6_mcast(ip):
    try:
        return ipaddress.IPv6Address(str(ip)).is_multicast
    except Exception:
        return False


def _mcast_l2_for_ip(ip):
    """Return the derived multicast L2 MAC for an IPv4 or IPv6 group, or None."""
    if _is_ipv4_mcast(ip):
        return _ipv4_mcast_mac(ip)
    if _is_ipv6_mcast(ip):
        return _ipv6_mcast_mac(ip)
    return None


def _v3_record_type(*, leave, filter_mode, sources, override):
    """Pick the IGMPv3/MLDv2 GroupRecord type for the requested action.

    join  + include + S  -> CHANGE_TO_INCLUDE_MODE  (S,G) join
    join  + exclude      -> CHANGE_TO_EXCLUDE_MODE  (*,G) join
    leave + S            -> BLOCK_OLD_SOURCES       (S,G) leave
    leave (no source)    -> CHANGE_TO_INCLUDE_MODE  (*,G) leave (to empty INCLUDE)
    """
    if override:
        key = str(override).strip().lower()
        return _V3_RECORD_TYPES.get(key, override)
    if leave:
        return "BLOCK_OLD_SOURCES" if sources else "CHANGE_TO_INCLUDE_MODE"
    fm = (filter_mode or ("include" if sources else "exclude")).lower()
    return "CHANGE_TO_INCLUDE_MODE" if fm == "include" else "CHANGE_TO_EXCLUDE_MODE"


def _mcast_build_l2(stc, sb, src_mac, dst_mac, outer_vlan, inner_vlan_id):
    """Build EthernetII (+ optional VLAN tags) on a fresh StreamBlock."""
    eth = stc.get(sb, "children-ethernet:EthernetII")
    if eth:
        stc.config(eth, srcMac=src_mac, dstMac=dst_mac)
    else:
        eth = stc.create("ethernet:EthernetII", under=sb, srcMac=src_mac, dstMac=dst_mac)
    if outer_vlan is not None:
        vlans = stc.create("vlans", under=eth)
        stc.create("Vlan", under=vlans, id=str(outer_vlan), pri="0", cfi="0")
        if inner_vlan_id is not None:
            stc.create("Vlan", under=vlans, id=str(inner_vlan_id), pri="0", cfi="0")
    return eth


def _add_igmp_v3_records(stc, report_handle, *, group, sources, record_type):
    """Attach grpRecords/GroupRecord (+ best-effort source list) to a v3/MLDv2 report."""
    grp_records = stc.create("grpRecords", under=report_handle)
    record = stc.create(
        "GroupRecord", under=grp_records,
        mcastAddr=str(group), recordType=record_type, numSource=str(len(sources)),
    )
    if sources:
        # [VALIDATE-LIVE] confirm the GroupRecord source-list child/attr name on
        # the Lab Server. Tried (in order) common STC encodings; degrade quietly.
        applied = False
        for attr in ("srcList", "sourceList", "SrcList"):
            try:
                stc.config(record, **{attr: " ".join(str(s) for s in sources)})
                applied = True
                break
            except Exception:
                continue
        if not applied:
            try:
                for s in sources:
                    stc.create("SourceAddr", under=record, address=str(s))
                applied = True
            except Exception:
                applied = False
        if not applied:
            print(f"[WARN] v3 source list {sources} could not be set "
                  "(STC source-record attr name needs live validation [VALIDATE-LIVE])")
    return record


def _mcast_membership_stream(args, *, leave):
    """Create a stateless IGMP/MLD membership report (join) or leave StreamBlock.

    Builds Eth -> VLAN(s) -> IPv4/IPv6 (ttl/hop-limit 1) -> IGMP/MLD PDU.
    family=ipv4 -> IGMP v1/v2/v3 ; family=ipv6 -> MLD v1/v2.
    """
    config = load_config()
    stc, sess = _require_ready(config)
    port_handle = sess["port_handle"]

    family = (getattr(args, "family", None) or "ipv4").lower()
    version = str(getattr(args, "version", None) or ("2" if family == "ipv4" else "1"))
    group = args.group
    sources = [s.strip() for s in (getattr(args, "source", None) or "").split(",") if s.strip()]
    filter_mode = getattr(args, "filter_mode", None)
    record_override = getattr(args, "record_type", None)
    action = "leave" if leave else "join"

    default_name = f"mcast_{family}_v{version}_{action}_{len(sess.get('streams', []))}"
    stream_name = args.name or default_name
    host_mac = args.src_mac or "00:10:94:00:00:02"
    if family == "ipv6":
        host_ip = args.src_ip or "fe80::1094:1"
    else:
        host_ip = args.src_ip or "10.0.0.2"

    frame_size = int(args.frame_size) if getattr(args, "frame_size", None) else 64
    rate_pps = float(args.rate_pps) if getattr(args, "rate_pps", None) else 1.0

    outer_vlan, inner_vlan_id = _resolve_qinq_vlans(
        config, sess, getattr(args, "vlan", None), getattr(args, "inner_vlan", None),
        no_qinq=getattr(args, "no_qinq", False),
    )

    # Decide L2/L3 control destination + PDU class per family/version/action.
    record_type = None
    if family == "ipv6":
        if version == "2":
            dst_ip = MLD_V2_REPORT_IP
            record_type = _v3_record_type(leave=leave, filter_mode=filter_mode,
                                          sources=sources, override=record_override)
        elif leave:
            dst_ip = MLD_ALL_ROUTERS_IP            # MLDv1 Done
        else:
            dst_ip = str(group)                    # MLDv1 Report -> group
        dst_mac = _ipv6_mcast_mac(dst_ip)
    else:
        if version == "3":
            dst_ip = IGMP_V3_REPORT_IP
            dst_mac = IGMP_V3_REPORT_MAC
            record_type = _v3_record_type(leave=leave, filter_mode=filter_mode,
                                          sources=sources, override=record_override)
        elif version == "2" and leave:
            dst_ip = IGMP_ALL_ROUTERS_IP           # v2 Leave -> all-routers
            dst_mac = IGMP_ALL_ROUTERS_MAC
        else:
            dst_ip = str(group)                    # v1/v2 Report -> group
            dst_mac = _ipv4_mcast_mac(group)

    sb = stc.create("streamBlock", under=port_handle, insertSig="false",
                    frameLengthMode="FIXED", FixedFrameLength=str(frame_size),
                    load=str(rate_pps), loadUnit="FRAMES_PER_SECOND", name=stream_name)
    _mcast_build_l2(stc, sb, host_mac, dst_mac, outer_vlan, inner_vlan_id)

    if family == "ipv6":
        stc.create("ipv6:IPv6", under=sb, sourceAddr=host_ip, destAddr=dst_ip, hopLimit="1")
        if version == "2":
            rpt = stc.create("mld:Mldv2Report", under=sb)      # [VALIDATE-LIVE]
            _add_igmp_v3_records(stc, rpt, group=group, sources=sources, record_type=record_type)
        elif leave:
            stc.create("mld:MldDone", under=sb, groupAddress=str(group))   # [VALIDATE-LIVE]
        else:
            stc.create("mld:Mldv1Report", under=sb, groupAddress=str(group))  # [VALIDATE-LIVE]
    else:
        stc.create("ipv4:IPv4", under=sb, sourceAddr=host_ip, destAddr=dst_ip, ttl="1")
        if version == "3":
            rpt = stc.create("igmp:Igmpv3Report", under=sb)
            _add_igmp_v3_records(stc, rpt, group=group, sources=sources, record_type=record_type)
        elif version == "2" and leave:
            stc.create("igmp:Igmpv2Leave", under=sb, groupAddress=str(group))
        elif version == "2":
            stc.create("igmp:Igmpv2Report", under=sb, groupAddress=str(group))
        else:  # v1 (join only; v1 has no Leave message)
            stc.create("igmp:Igmpv1", under=sb, groupAddress=str(group))

    stc.apply()

    info = {
        "name": stream_name, "handle": sb, "kind": f"mcast-{action}",
        "family": family, "igmp_version": version, "group": group,
        "sources": sources, "filter_mode": filter_mode, "record_type": record_type,
        "src_ip": host_ip, "src_mac": host_mac, "dst_ip": dst_ip, "dst_mac": dst_mac,
        "vlan": outer_vlan, "inner_vlan": inner_vlan_id,
        "rate": rate_pps, "rate_unit": "FRAMES_PER_SECOND", "frame_size": frame_size,
        "protocol": f"{'mld' if family == 'ipv6' else 'igmp'}-v{version}-{action}",
        "created": datetime.utcnow().isoformat(),
    }
    sess["streams"] = [s for s in sess.get("streams", []) if s.get("name") != stream_name]
    sess.setdefault("streams", []).append(info)
    save_session(sess)
    print(f"Multicast {action} stream created: {stream_name} "
          f"({'MLD' if family == 'ipv6' else 'IGMP'}v{version} group {group}"
          f"{(' src ' + ','.join(sources)) if sources else ''})")
    print(json.dumps(info, indent=2))


def cmd_create_mcast_source(args):
    """Create a multicast data SOURCE StreamBlock (auto group L2 MAC).

    src_ip is the multicast source S; group is the destination group G. The
    Ethernet destination is derived per RFC 1112 (IPv4) / RFC 2464 (IPv6).
    """
    config = load_config()
    stc, sess = _require_ready(config)
    port_handle = sess["port_handle"]

    family = (getattr(args, "family", None) or "ipv4").lower()
    group = args.group
    if family == "ipv6":
        if not _is_ipv6_mcast(group):
            raise SystemExit(f"--group {group} is not an IPv6 multicast address (ff00::/8)")
        dst_mac = _ipv6_mcast_mac(group)
        src_ip = args.source or args.src_ip or "2001:db8::1"
    else:
        if not _is_ipv4_mcast(group):
            raise SystemExit(f"--group {group} is not an IPv4 multicast group (224.0.0.0/4)")
        dst_mac = _ipv4_mcast_mac(group)
        src_ip = args.source or args.src_ip or "10.0.0.1"

    stream_name = args.name or f"mcast_src_{len(sess.get('streams', []))}"
    src_mac = args.src_mac or "00:10:94:00:00:01"
    frame_size = int(args.frame_size) if getattr(args, "frame_size", None) else 128

    load_unit = "MEGABITS_PER_SECOND"
    rate = float(args.rate_mbps) if getattr(args, "rate_mbps", None) else 1.0
    if getattr(args, "rate_pps", None):
        load_unit = "FRAMES_PER_SECOND"
        rate = float(args.rate_pps)

    outer_vlan, inner_vlan_id = _resolve_qinq_vlans(
        config, sess, getattr(args, "vlan", None), getattr(args, "inner_vlan", None),
        no_qinq=getattr(args, "no_qinq", False),
    )

    sb = stc.create("streamBlock", under=port_handle, insertSig="true",
                    frameLengthMode="FIXED", FixedFrameLength=str(frame_size),
                    load=str(rate), loadUnit=load_unit, name=stream_name)
    _mcast_build_l2(stc, sb, src_mac, dst_mac, outer_vlan, inner_vlan_id)
    if family == "ipv6":
        stc.create("ipv6:IPv6", under=sb, sourceAddr=src_ip, destAddr=str(group))
    else:
        existing_ip = stc.get(sb, "children-ipv4:IPv4")
        if existing_ip:
            stc.config(existing_ip, sourceAddr=src_ip, destAddr=str(group))
        else:
            stc.create("ipv4:IPv4", under=sb, sourceAddr=src_ip, destAddr=str(group))
    stc.apply()

    info = {
        "name": stream_name, "handle": sb, "kind": "mcast-source",
        "family": family, "group": group, "src_ip": src_ip,
        "src_mac": src_mac, "dst_mac": dst_mac,
        "vlan": outer_vlan, "inner_vlan": inner_vlan_id,
        "rate": rate, "rate_unit": load_unit, "frame_size": frame_size,
        "protocol": "mcast-source-" + family,
        "created": datetime.utcnow().isoformat(),
    }
    sess["streams"] = [s for s in sess.get("streams", []) if s.get("name") != stream_name]
    sess.setdefault("streams", []).append(info)
    save_session(sess)
    print(f"Multicast source stream created: {stream_name} "
          f"(S={src_ip} -> G={group}, dst_mac={dst_mac})")
    print(json.dumps(info, indent=2))


def cmd_create_mcast_receiver(args):
    """Create a stateless IGMP/MLD membership report (join) StreamBlock."""
    return _mcast_membership_stream(args, leave=False)


def cmd_mcast_leave(args):
    """Create a stateless IGMP/MLD leave/done StreamBlock."""
    return _mcast_membership_stream(args, leave=True)


def cmd_mcast_querier(args):
    """Emulate an external mrouter: send a stateless IGMP/MLD query.

    A query with source != 0.0.0.0 (RFC 4541) makes the DUT mark the Spirent
    port as an mrouter port. --group empty => General Query; --group set =>
    Group-Specific Query.
    """
    config = load_config()
    stc, sess = _require_ready(config)
    port_handle = sess["port_handle"]

    family = (getattr(args, "family", None) or "ipv4").lower()
    version = str(getattr(args, "version", None) or ("2" if family == "ipv4" else "1"))
    group = getattr(args, "group", None)
    general = not group
    querier_ip = args.src_ip or ("fe80::1094:fe" if family == "ipv6" else "10.0.0.254")
    querier_mac = args.src_mac or "00:10:94:00:00:fe"
    stream_name = args.name or f"mcast_{family}_v{version}_query_{len(sess.get('streams', []))}"
    frame_size = int(args.frame_size) if getattr(args, "frame_size", None) else 64
    rate_pps = float(args.rate_pps) if getattr(args, "rate_pps", None) else 1.0

    outer_vlan, inner_vlan_id = _resolve_qinq_vlans(
        config, sess, getattr(args, "vlan", None), getattr(args, "inner_vlan", None),
        no_qinq=getattr(args, "no_qinq", False),
    )

    if family == "ipv6":
        dst_ip = MLD_ALL_NODES_IP if general else str(group)
        dst_mac = _ipv6_mcast_mac(dst_ip)
    else:
        dst_ip = IGMP_ALL_HOSTS_IP if general else str(group)
        dst_mac = IGMP_ALL_HOSTS_MAC if general else _ipv4_mcast_mac(group)

    sb = stc.create("streamBlock", under=port_handle, insertSig="false",
                    frameLengthMode="FIXED", FixedFrameLength=str(frame_size),
                    load=str(rate_pps), loadUnit="FRAMES_PER_SECOND", name=stream_name)
    _mcast_build_l2(stc, sb, querier_mac, dst_mac, outer_vlan, inner_vlan_id)

    group_addr = "0.0.0.0" if (general and family == "ipv4") else ("::" if general else str(group))
    if family == "ipv6":
        stc.create("ipv6:IPv6", under=sb, sourceAddr=querier_ip, destAddr=dst_ip, hopLimit="1")
        # [VALIDATE-LIVE] MLD query object names.
        mld_query = "mld:Mldv2Query" if version == "2" else "mld:Mldv1Query"
        stc.create(mld_query, under=sb, groupAddress=group_addr)
    else:
        stc.create("ipv4:IPv4", under=sb, sourceAddr=querier_ip, destAddr=dst_ip, ttl="1")
        # [VALIDATE-LIVE] IGMP query object names (v2/v3).
        igmp_query = "igmp:Igmpv3Query" if version == "3" else "igmp:Igmpv2Query"
        stc.create(igmp_query, under=sb, groupAddress=group_addr)
    stc.apply()

    info = {
        "name": stream_name, "handle": sb, "kind": "mcast-querier",
        "family": family, "igmp_version": version,
        "query_type": "general" if general else "group-specific",
        "group": None if general else group, "querier_ip": querier_ip,
        "src_mac": querier_mac, "dst_ip": dst_ip, "dst_mac": dst_mac,
        "vlan": outer_vlan, "inner_vlan": inner_vlan_id,
        "rate": rate_pps, "rate_unit": "FRAMES_PER_SECOND", "frame_size": frame_size,
        "protocol": f"{'mld' if family == 'ipv6' else 'igmp'}-v{version}-query",
        "created": datetime.utcnow().isoformat(),
    }
    sess["streams"] = [s for s in sess.get("streams", []) if s.get("name") != stream_name]
    sess.setdefault("streams", []).append(info)
    save_session(sess)
    print(f"Multicast querier stream created: {stream_name} "
          f"({'general' if general else 'group-specific'} {('MLD' if family == 'ipv6' else 'IGMP')}v{version} query, "
          f"src {querier_ip})")
    print(json.dumps(info, indent=2))


def cmd_igmp_host(args):
    """Configure a STATEFUL IGMP host stack (IgmpHostConfig) on an existing device.

    A stateful host auto-replies to membership queries from the DUT. It must be
    attached to an existing EmulatedDevice (created via create-device) that has an
    IPv4 stack. [VALIDATE-LIVE]: the IgmpHostConfig / IgmpGroupMembership /
    Ipv4Group object + relation names are confirmed against the Lab Server on the
    first live /TEST run; this builder degrades gracefully on a name mismatch.
    """
    config = load_config()
    stc, sess = _require_ready(config)
    project = sess["project_handle"]

    dev_name = getattr(args, "device_name", None)
    devices = [d for d in sess.get("devices", []) if d.get("handle")]
    if dev_name:
        devices = [d for d in devices if d.get("name") == dev_name]
    if not devices:
        raise SystemExit("igmp-host requires an existing emulated device "
                         "(create-device first); use --device-name to select it")
    device = devices[0]
    device_handle = device["handle"]

    version = str(getattr(args, "version", None) or "3")
    stc_version = {"1": "IGMP_V1", "2": "IGMP_V2", "3": "IGMP_V3"}.get(version, "IGMP_V3")
    group = args.group
    group_count = int(getattr(args, "group_count", None) or 1)
    sources = [s.strip() for s in (getattr(args, "source", None) or "").split(",") if s.strip()]
    filter_mode = (getattr(args, "filter_mode", None) or ("INCLUDE" if sources else "EXCLUDE")).upper()

    warnings = []
    try:
        igmp = stc.create("IgmpHostConfig", under=device_handle, Version=stc_version)
    except Exception as exc:
        raise SystemExit(f"[VALIDATE-LIVE] IgmpHostConfig create failed: {exc}. "
                         "Confirm the stateful host object name against the Lab Server.")

    # Multicast group pool object (Ipv4Group + Ipv4NetworkBlock).
    grp_handle = None
    try:
        grp_handle = stc.create("Ipv4Group", under=project)
        stc.create("Ipv4NetworkBlock", under=grp_handle,
                   StartIpList=str(group), NetworkCount=str(group_count), PrefixLength="32")
    except Exception as exc:
        warnings.append(f"[VALIDATE-LIVE] Ipv4Group/Ipv4NetworkBlock failed: {exc}")

    member = None
    try:
        member = stc.create("IgmpGroupMembership", under=igmp,
                            DeviceGroupMapping="MANY_TO_MANY", FilterMode=filter_mode)
        if grp_handle:
            stc.config(member, **{"MulticastGroup-targets": [grp_handle]})
    except Exception as exc:
        warnings.append(f"[VALIDATE-LIVE] IgmpGroupMembership failed: {exc}")

    if sources and member:
        try:
            src_grp = stc.create("Ipv4Group", under=project)
            stc.create("Ipv4NetworkBlock", under=src_grp,
                       StartIpList=str(sources[0]), NetworkCount=str(len(sources)), PrefixLength="32")
            stc.config(member, **{"SrcListBlk-targets": [src_grp]})
        except Exception as exc:
            warnings.append(f"[VALIDATE-LIVE] v3 source block failed: {exc}")

    try:
        stc.apply()
    except Exception as exc:
        warnings.append(f"apply failed: {exc}")

    device.setdefault("igmp_hosts", []).append({
        "handle": igmp, "version": version, "group": group,
        "group_count": group_count, "sources": sources, "filter_mode": filter_mode,
    })
    save_session(sess)
    print(f"IGMP host (stateful) configured on {device['name']}: "
          f"IGMPv{version} {filter_mode} group {group} x{group_count}"
          f"{(' src ' + ','.join(sources)) if sources else ''}")
    for w in warnings:
        print(w)
    print(json.dumps({
        "device": device["name"], "igmp_handle": igmp, "version": version,
        "group": group, "group_count": group_count, "sources": sources,
        "filter_mode": filter_mode, "warnings": warnings,
        "note": "Start with protocol-start; [VALIDATE-LIVE] object names on first live run.",
    }, indent=2))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Spirent TestCenter CLI tool")
    sub = parser.add_subparsers(dest="command")

    p_conn = sub.add_parser("connect", help="Connect to Lab Server (JOIN-only by default; see --create-if-missing)")
    p_conn.add_argument("--force-new", action="store_true", help="Kill existing session and create fresh (destructive)")
    p_conn.add_argument("--create-if-missing", action="store_true",
                        help="Create a new BLL session only when no joinable one exists (opt-in; default is JOIN-only)")

    p_res = sub.add_parser("reserve", help="Reserve the configured port")

    p_stream = sub.add_parser("create-stream", help="Create a traffic stream")
    p_stream.add_argument("--vlan", type=int, default=None, help="Outer VLAN (optional if transport_vlans READY)")
    p_stream.add_argument("--dst-mac", default=None)
    p_stream.add_argument("--src-mac", default=None)
    p_stream.add_argument("--dst-ip", default=None)
    p_stream.add_argument("--src-ip", default=None)
    p_stream.add_argument("--rate-mbps", default=None, help="Rate in Mbps")
    p_stream.add_argument("--rate-pps", default=None, help="Rate in frames/sec (overrides --rate-mbps)")
    p_stream.add_argument("--frame-size", default=None, help="Frame size in bytes (default 128)")
    p_stream.add_argument("--name", default=None, help="Stream name")
    p_stream.add_argument("--inner-vlan", type=int, default=None, help="Inner VLAN ID for Q-in-Q (auto-allocated if not set)")
    p_stream.add_argument("--no-qinq", action="store_true", help="Force single-tagged (no auto Q-in-Q)")
    p_stream.add_argument("--exclude-inner-vlans", default=None, help="Comma-separated inner VLANs already used on DUT (skipped during auto-alloc)")
    p_stream.add_argument("--protocol", default="ipv4", choices=["ipv4", "ipv6", "l2", "icmpv6-na"],
                          help="L3 payload type. icmpv6-na emits an explicit Neighbor Advertisement")
    p_stream.add_argument("--target-ipv6", default=None, help="ICMPv6 NA target IPv6 address (defaults to --src-ip)")
    p_stream.add_argument("--target-mac", default=None, help="ICMPv6 NA Target Link-Layer Address option (defaults to --src-mac)")
    p_stream.add_argument("--icmpv6-na-router", action="store_true", help="Set ICMPv6 NA Router flag")
    p_stream.add_argument(
        "--icmpv6-na-solicited",
        action="store_true",
        help="Set ICMPv6 NA Solicited flag; requires unicast --dst-ip and requester --dst-mac",
    )
    p_stream.add_argument("--icmpv6-na-override", action=argparse.BooleanOptionalAction, default=True,
                          help="Set ICMPv6 NA Override flag (default true)")
    p_stream.add_argument(
        "--reuse-policy",
        choices=["error", "reuse", "replace"],
        default="error",
        help="When a StreamBlock with the same name already exists on the reserved port: "
             "'error' (default, refuse so callers do not silently inherit stale encoding), "
             "'reuse' (keep the existing block as-is), 'replace' (delete + recreate with new args).",
    )

    p_mod_stream = sub.add_parser(
        "create-modifier-stream",
        help="Create one L2 Q-in-Q StreamBlock with synchronized VLAN/MAC RangeModifiers",
    )
    p_mod_stream.add_argument("--name", required=True, help="StreamBlock name")
    p_mod_stream.add_argument("--outer-vlan", type=int, required=True, help="Fixed outer VLAN ID")
    p_mod_stream.add_argument("--inner-vlan-start", type=int, required=True, help="First inner VLAN ID")
    p_mod_stream.add_argument("--inner-vlan-step", type=int, default=1, help="Inner VLAN increment (default 1)")
    p_mod_stream.add_argument("--count", type=int, required=True, help="Number of modified frames/flows")
    p_mod_stream.add_argument("--src-mac", required=True, help="First source MAC")
    p_mod_stream.add_argument("--src-mac-step", default="00:00:00:00:00:01", help="Source MAC increment")
    p_mod_stream.add_argument("--dst-mac", required=True, help="First destination MAC")
    p_mod_stream.add_argument("--dst-mac-step", default="00:00:00:00:00:01", help="Destination MAC increment")
    p_mod_stream.add_argument("--rate-mbps", default=None, help="Total StreamBlock rate in Mbps")
    p_mod_stream.add_argument("--rate-pps", default=None, help="Total StreamBlock rate in frames/sec (overrides --rate-mbps)")
    p_mod_stream.add_argument("--frame-size", default=None, help="Frame size in bytes (default 128)")
    p_mod_stream.add_argument(
        "--enable-flow-stats",
        action="store_true",
        help="Enable per-modified-flow result tracking (off by default to avoid scale limits)",
    )

    p_start = sub.add_parser("start", help="Start traffic generation")
    p_start.add_argument("--stream-name", default=None)
    p_start.add_argument("--exclusive", action="store_true",
                         help="With --stream-name, disable every other stream before starting")

    p_stop = sub.add_parser("stop", help="Stop traffic generation")
    p_stop.add_argument("--stream-name", default=None)

    p_release = sub.add_parser("release", help="Stop traffic and release the port for manual GUI use; keep session alive")

    p_detach = sub.add_parser("detach", help="Detach automation client; keep Lab Server session alive")

    p_stats = sub.add_parser("stats", help="Get traffic statistics")
    p_stats.add_argument("--json", dest="json_output", action="store_true")
    p_stats.add_argument("--no-per-stream", dest="per_stream", action="store_false", default=True,
                         help="Skip per-stream stats (faster, port-level only)")
    p_stats.add_argument("--stream-name", default=None,
                         help="Collect per-stream stats only for this StreamBlock name (comma-separated allowed)")

    p_clean = sub.add_parser("cleanup", help="Release port and end session (use --confirm after user approval)")
    p_clean.add_argument("--session-name", default=None, help="'--all' to clean all dn_spirent sessions")
    p_clean.add_argument("--confirm", action="store_true", help="User confirmed; proceed with cleanup")

    p_reconcile = sub.add_parser("reconcile", help="Compare local vs server sessions, mark stale, optionally kill orphans")
    p_reconcile.add_argument("--kill-orphans", action="store_true", help="Kill orphan server sessions not in local files")

    p_recover = sub.add_parser("recover", help="Diagnose and recover crashed Lab Server (SSH restart stcweb/engine/container)")
    p_recover.add_argument("--level", default="stcweb", choices=["stcweb", "engine", "full"],
                           help="Recovery level: stcweb (light), engine (medium), full (docker restart)")

    p_heal = sub.add_parser("heal",
        help="Rebuild local session JSON from live BLL state (safe/idempotent; no create/modify on server)")
    p_heal.add_argument("--json", action="store_true",
                        help="Also print a machine-readable heal report on stdout")

    p_list = sub.add_parser("list-sessions", help="List Lab Server sessions")

    p_status = sub.add_parser("status", help="Show current status (fast from session file, --live for STC query)")
    p_status.add_argument("--live", action="store_true", help="Query live STC API for BGP state and traffic stats")
    p_status.add_argument("--json", dest="json_output", action="store_true", help="Output as JSON")

    p_capacity = sub.add_parser("capacity", help="Show capacity usage: bandwidth, streams, BGP peers, routes, FlowSpec TCAM")
    p_capacity.add_argument("--live", action="store_true", help="Query STC API for route counts")
    p_capacity.add_argument("--json", dest="json_output", action="store_true", help="Output as JSON")

    p_create_dev = sub.add_parser("create-device", help="Create emulated device(s) with IP stack (supports multiplier)")
    p_create_dev.add_argument("--ip", default=None, help="IPv4 device address (base IP if --device-count > 1)")
    p_create_dev.add_argument("--gateway", default=None, help="IPv4 gateway (DUT) address")
    p_create_dev.add_argument("--prefix-len", default="24", help="Prefix length (default 24)")
    p_create_dev.add_argument("--ipv6", default=None, help="IPv6 device address")
    p_create_dev.add_argument("--ipv6-gateway", default=None, help="IPv6 gateway (DUT) address")
    p_create_dev.add_argument("--ipv6-prefix-len", default="64", help="IPv6 prefix length (default 64)")
    p_create_dev.add_argument("--vlan", type=int, default=None, help="VLAN ID for tagged traffic")
    p_create_dev.add_argument("--mac", default=None, help="Source MAC address (base MAC if --device-count > 1)")
    p_create_dev.add_argument("--name", default=None, help="Device name")
    p_create_dev.add_argument("--router-id", default=None, help="BGP Router ID (default: --ip)")
    p_create_dev.add_argument("--inner-vlan", type=int, default=None, help="Inner VLAN for Q-in-Q (auto-allocated if not set)")
    p_create_dev.add_argument("--no-qinq", action="store_true", help="Force single-tagged (no auto Q-in-Q)")
    p_create_dev.add_argument("--exclude-inner-vlans", default=None, help="Comma-separated inner VLANs already used on DUT (skipped during auto-alloc)")
    p_create_dev.add_argument("--device-count", type=int, default=1, help="STC Device Block: create N devices with stepping (default 1)")
    p_create_dev.add_argument("--ip-step", default=None, help="IP increment per device (int or dotted: 1 = 0.0.0.1)")
    p_create_dev.add_argument("--mac-step", default=None, help="MAC increment per device (int or colon-hex: 1 = 00:00:00:00:00:01)")

    p_bgp_peer = sub.add_parser("bgp-peer", help="Configure BGP on device and start session")
    p_bgp_peer.add_argument("--device-name", required=True, help="Emulated device name")
    p_bgp_peer.add_argument("--as", dest="as_num", type=int, required=True, help="Local AS number")
    p_bgp_peer.add_argument("--dut-as", type=int, required=True, help="DUT AS number")
    p_bgp_peer.add_argument("--neighbor", default=None, help="BGP neighbor IP (default: gateway)")
    p_bgp_peer.add_argument("--hold-timer", type=int, default=None)
    p_bgp_peer.add_argument("--keepalive", type=int, default=None)
    p_bgp_peer.add_argument("--afi", default="ipv4", choices=["ipv4", "ipv6"])
    p_bgp_peer.add_argument("--negotiate-afi", dest="negotiate_afi", default=None,
                            help="Comma-separated AFIs to negotiate: ipv4-unicast,ipv4-flowspec,ipv6-unicast,ipv6-flowspec,ipv4-vpn,ipv6-vpn,l2vpn-vpls,l2vpn-evpn,all")
    p_bgp_peer.add_argument("--vpls-rd", dest="vpls_rd", default=None,
                            help="VPLS route distinguisher (e.g. 18.18.18.2:500)")
    p_bgp_peer.add_argument("--vpls-rt", dest="vpls_rt", default=None,
                            help="VPLS route target (e.g. 100:100)")
    p_bgp_peer.add_argument("--vpls-ve-id", dest="vpls_ve_id", type=int, default=None,
                            help="VPLS VE-ID in the wire NLRI (must differ from DUT site-id)")
    p_bgp_peer.add_argument("--vpls-offset", dest="vpls_offset", type=int, default=1,
                            help="VPLS label block offset (default 1)")
    p_bgp_peer.add_argument("--vpls-block-size", dest="vpls_block_size", type=int, default=8,
                            help="VPLS label block size (default 8, must cover DUT site-id)")
    p_bgp_peer.add_argument("--vpls-mtu", dest="vpls_mtu", type=int, default=None,
                            help="VPLS MTU size in bytes (default 1500)")
    p_bgp_peer.add_argument("--vpls-nexthop", dest="vpls_nexthop", default=None,
                            help="Override BGP NEXT_HOP for VPLS routes (e.g. loopback IP for LDP tunnel)")
    p_bgp_peer.add_argument("--evpn-rd", dest="evpn_rd", default=None,
                            help="EVPN route distinguisher (e.g. 3.3.3.3:100)")
    p_bgp_peer.add_argument("--evpn-rt", dest="evpn_rt", default=None,
                            help="EVPN route target (e.g. 100:100)")
    p_bgp_peer.add_argument("--evpn-evi-rt", dest="evpn_evi_rt", default=None,
                            help="EVPN EVI route target (defaults to --evpn-rt)")
    p_bgp_peer.add_argument("--evpn-label", dest="evpn_label", type=int, default=None,
                            help="EVPN MPLS label (default 16000)")
    p_bgp_peer.add_argument("--evpn-mac", dest="evpn_mac", default=None,
                            help="EVPN MAC to advertise in RT-2 (default 00:DE:AD:00:01:01)")
    p_bgp_peer.add_argument("--evpn-nexthop", dest="evpn_nexthop", default=None,
                            help="Override BGP NEXT_HOP for EVPN routes (e.g. loopback IP for LDP tunnel)")
    p_bgp_peer.add_argument("--no-start", dest="no_start", action="store_true",
                            help="Configure BGP but do not start protocols (avoids stc.apply hang with ISIS+LDP)")
    p_bgp_peer.add_argument("--wait-established", type=int, default=0,
                            help="Seconds to poll Spirent-side BGP results after start (0=skip; default 0 because DUT verification is more reliable)")

    p_bgp_status = sub.add_parser("bgp-status", help="Show BGP session state")
    p_bgp_status.add_argument("--device-name", default=None, help="Filter by device")
    p_bgp_status.add_argument("--json", dest="json_output", action="store_true")
    p_bgp_status.add_argument("--verify-dut", dest="verify_dut", action="store_true",
                              help="Verify BGP state on DUT (ground truth, STC state is unreliable)")
    p_bgp_status.add_argument("--dut-ip", default=None,
                              help="DUT management IP for --verify-dut (default: from config)")
    p_bgp_status.add_argument("--idle-classify", dest="idle_classify", action="store_true",
                              help="Classify each peer as ESTABLISHED/DEAD/STARTING/NEVER based on Up/Down idle time (implies --verify-dut)")
    p_bgp_status.add_argument("--idle-threshold", dest="idle_threshold", type=int, default=30,
                              help="Idle seconds before non-ESTABLISHED peer is classified DEAD (default: 30)")

    p_add_afi = sub.add_parser("add-afi", help="Add AFI capabilities to existing BGP peer (renegotiates session)")
    p_add_afi.add_argument("--device-name", required=True, help="Emulated device name")
    p_add_afi.add_argument("--afis", required=True,
                           help="Comma-separated: ipv4-unicast,ipv4-flowspec,ipv6-unicast,ipv6-flowspec,ipv4-vpn,ipv6-vpn,all")

    p_list_dev = sub.add_parser("list-devices", help="List emulated devices")
    p_list_dev.add_argument("--names-only", dest="names_only", action="store_true",
                            help="Print only device names, one per line (script-friendly)")
    p_list_dev.add_argument("--json", dest="json_output", action="store_true",
                            help="Emit a JSON array of device records")

    p_remove_stream = sub.add_parser("remove-stream", help="Remove a stream from the session")
    p_remove_stream.add_argument("--name", required=True, help="Stream name to remove")

    p_set_active = sub.add_parser(
        "set-stream-active",
        help="Toggle StreamBlock.Active (TRUE/FALSE) without destroying streams -- non-disruptive to BGP",
    )
    p_set_active.add_argument("--name", default=None, help="Single stream name")
    p_set_active.add_argument("--names", default=None, help="Comma-separated stream names")
    p_set_active.add_argument("--active", required=True, help="true|false -- set StreamBlock.Active")

    p_remove_device = sub.add_parser("remove-device", help="Remove device from session (stops BGP first)")
    p_remove_device.add_argument("--name", required=True, help="Device name to remove")

    p_prune = sub.add_parser("prune-test-scope", help="Remove stale TEST-owned streams outside the current test id")
    p_prune.add_argument("--test-id", required=True, help="Current TEST id; matching streams are preserved")
    p_prune.add_argument("--include-devices", action="store_true", help="Also remove stale TEST-owned emulated devices")
    p_prune.add_argument("--dry-run", action="store_true", help="Preview removals without deleting")
    p_prune.add_argument("--confirm", action="store_true", help="Required to delete objects")

    p_add_routes = sub.add_parser("add-routes", help="Add route blocks to BGP router")
    p_add_routes.add_argument("--device-name", required=True, help="Emulated device name")
    p_add_routes.add_argument("--afi", required=True, help="ipv4, ipv6, vpnv4, vpnv6, flowspec")
    p_add_routes.add_argument("--prefix", default="192.168.1.0", help="Starting network (e.g. 100.0.0.0)")
    p_add_routes.add_argument("--prefix-length", type=int, default=24)
    p_add_routes.add_argument("--count", type=int, default=1000)
    p_add_routes.add_argument("--as-path", default=None)
    p_add_routes.add_argument("--next-hop", default=None)
    p_add_routes.add_argument("--rd", default=None, help="Route distinguisher for VPN (e.g. 65200:100)")
    p_add_routes.add_argument("--rt", default=None, help="Route target for VPN (e.g. target:1234567:100)")
    p_add_routes.add_argument("--dst-prefix", default=None, help="FlowSpec: destination prefix")
    p_add_routes.add_argument("--dst-prefix-length", type=int, default=24, help="FlowSpec: prefix length")
    p_add_routes.add_argument("--action", default="redirect-ip", help="FlowSpec: redirect-ip or drop")
    p_add_routes.add_argument("--redirect-target", default=None, help="FlowSpec: redirect-ip next-hop")

    p_evpn_routes = sub.add_parser("evpn-routes", help="Add EVPN RT-2 (MAC/IP Advertisement) routes to BGP device")
    p_evpn_routes.add_argument("--device-name", required=True, help="Emulated device name with BGP")
    p_evpn_routes.add_argument("--rd", default=None, help="Route distinguisher (e.g. 3.3.3.3:100)")
    p_evpn_routes.add_argument("--rt", default=None, help="Route target (e.g. 100:100)")
    p_evpn_routes.add_argument("--mac", default=None, help="Start MAC address (default 00:DE:AD:00:01:01)")
    p_evpn_routes.add_argument("--mac-step", default=None, help="MAC step per route (default 00:00:00:00:00:01)")
    p_evpn_routes.add_argument("--count", type=int, default=1, help="Number of MAC routes (default 1)")
    p_evpn_routes.add_argument("--label", type=int, default=None, help="MPLS label (default 16000)")
    p_evpn_routes.add_argument("--ethernet-tag", type=int, default=None, help="Ethernet tag ID (default 0)")
    p_evpn_routes.add_argument("--seq-num", type=int, default=None, help="MAC mobility sequence number (default 0)")
    p_evpn_routes.add_argument("--ip", default=None, help="Optional IPv4 binding for MAC/IP route")
    p_evpn_routes.add_argument("--next-hop", default=None, help="BGP next-hop (default: device IP)")
    p_evpn_routes.add_argument("--no-mac-mobility", action="store_true", help="Disable MAC Mobility extended community")
    p_evpn_routes.add_argument("--sticky", action="store_true", help="Set IsStatic (sticky/static) flag in MAC Mobility extended community")
    p_evpn_routes.add_argument("--no-restart", action="store_true", help="Do not restart device after adding routes")

    p_withdraw = sub.add_parser("withdraw-routes",
                                help="Withdraw routes already advertised by an emulated BGP device")
    p_withdraw.add_argument("--device-name", required=True, help="Emulated device name with BGP")
    p_withdraw.add_argument("--afi", default="l2vpn-evpn",
                            help="AFI to withdraw (only 'l2vpn-evpn' implemented)")
    p_withdraw.add_argument("--rd", default=None, help="Match route distinguisher (e.g. 3.3.3.3:100)")
    p_withdraw.add_argument("--mac", default=None, help="Match start MAC address")
    p_withdraw.add_argument("--ip", default=None,
                            help="Optional IPv4 binding (currently informational; selection uses RD/MAC)")
    p_withdraw.add_argument("--route-handle", default=None,
                            help="STC route-config handle to withdraw (overrides --rd/--mac)")
    p_withdraw.add_argument("--json", dest="json_output", action="store_true",
                            help="Emit a JSON summary of the withdraw result")

    p_evpn_rt1 = sub.add_parser("evpn-rt1", help="Inject EVPN RT-1 (Ethernet Auto-Discovery) route for MH testing")
    p_evpn_rt1.add_argument("--device-name", required=True, help="Emulated device name with BGP")
    p_evpn_rt1.add_argument("--esi", required=True, help="Ethernet Segment Identifier, 9 hex-byte STC format (e.g. 00:AA:BB:CC:DD:EE:FF:00:01)")
    p_evpn_rt1.add_argument("--sub-type", default="per_evi", choices=["per_evi", "per_es"],
                            help="AD route sub-type: per_evi (aliasing) or per_es (mass-withdraw)")
    p_evpn_rt1.add_argument("--evi", type=int, default=0, help="EVI (required for per_evi sub-type)")
    p_evpn_rt1.add_argument("--rd", default=None, help="Route distinguisher")
    p_evpn_rt1.add_argument("--rt", default=None, help="Route target")
    p_evpn_rt1.add_argument("--label", type=int, default=0, help="MPLS label")
    p_evpn_rt1.add_argument("--no-restart", action="store_true", help="Do not restart device after adding route")

    p_evpn_rt4 = sub.add_parser("evpn-rt4", help="Inject EVPN RT-4 (Ethernet Segment) route for MH DF election")
    p_evpn_rt4.add_argument("--device-name", required=True, help="Emulated device name with BGP")
    p_evpn_rt4.add_argument("--esi", required=True, help="Ethernet Segment Identifier, 9 hex-byte STC format (e.g. 00:AA:BB:CC:DD:EE:FF:00:01)")
    p_evpn_rt4.add_argument("--rd", default=None, help="Route distinguisher")
    p_evpn_rt4.add_argument("--rt", default=None, help="Route target")
    p_evpn_rt4.add_argument("--originator-ip", default=None, help="Originator IP (default: device IP)")
    p_evpn_rt4.add_argument("--no-restart", action="store_true", help="Do not restart device after adding route")

    p_ecmp = sub.add_parser("ecmp", help="Create N BGP peers via STC Device Block (multiplier)")
    p_ecmp.add_argument("--count", type=int, default=4, help="Number of peers (default 4)")
    p_ecmp.add_argument("--vlan", type=int, default=None)
    p_ecmp.add_argument("--inner-vlan", type=int, default=None, help="Inner VLAN for Q-in-Q (outer=--vlan, inner=this)")
    p_ecmp.add_argument("--base-ip", default="10.99.212.10", help="First peer IP")
    p_ecmp.add_argument("--ip-step", default="1", help="IP increment per peer (int or dotted: 1 = 0.0.0.1)")
    p_ecmp.add_argument("--mac", default=None, help="First peer MAC (default 00:10:94:00:00:0a)")
    p_ecmp.add_argument("--mac-step", default="1", help="MAC increment per peer (int or colon-hex)")
    p_ecmp.add_argument("--gateway", default=None, help="DUT gateway IP")
    p_ecmp.add_argument("--prefix", default="200.0.0.0", help="Route prefix to advertise")
    p_ecmp.add_argument("--route-count", type=int, default=100)
    p_ecmp.add_argument("--as", dest="as_num", type=int, default=65200)
    p_ecmp.add_argument("--dut-as", type=int, default=1234567)
    p_ecmp.add_argument("--negotiate-afi", dest="negotiate_afi", default=None,
                        help="Comma-separated AFIs to negotiate: ipv4-unicast,ipv4-flowspec,ipv6-unicast,ipv6-flowspec,ipv4-vpn,ipv6-vpn,all")
    p_ecmp.add_argument("--wait-established", type=int, default=120,
                        help="Seconds to wait for BGP convergence (0=skip, default 120)")
    p_ecmp.add_argument("--gen-dut-config", action="store_true",
                        help="Print DNOS neighbor-group config for DUT (does not apply)")
    p_ecmp.add_argument("--clean-stale", action="store_true", default=True,
                        help="Remove stale EmulatedDevice objects before creating (default True)")

    p_vpls_stream = sub.add_parser("vpls-stream", help="Create MPLS-encapsulated L2 stream for VPLS PW MAC learning/mobility")
    p_vpls_stream.add_argument("--mpls-label", type=int, required=True,
                               help="MPLS ingress label (from 'show evpn vpls-pw' Ingress-label)")
    p_vpls_stream.add_argument("--outer-vlan", type=int, default=None,
                               help="Outer VLAN (DNAAS transport, e.g. 214)")
    p_vpls_stream.add_argument("--inner-vlan", type=int, default=None,
                               help="Inner VLAN (PW peer Q-in-Q inner tag, e.g. 4 or 5)")
    p_vpls_stream.add_argument("--inner-src-mac", default="00:DE:AD:00:01:01",
                               help="Inner Ethernet src MAC (this is the MAC the DUT learns)")
    p_vpls_stream.add_argument("--inner-dst-mac", default="FF:FF:FF:FF:FF:FF",
                               help="Inner Ethernet dst MAC (default broadcast)")
    p_vpls_stream.add_argument("--dst-mac", default=None,
                               help="Outer Ethernet dst MAC (DUT interface MAC)")
    p_vpls_stream.add_argument("--src-mac-outer", default="00:10:94:00:06:06",
                               help="Outer Ethernet src MAC (Spirent port MAC)")
    p_vpls_stream.add_argument("--control-word", default="00000000",
                               help="MPLS Control Word hex (default 00000000)")
    p_vpls_stream.add_argument("--rate-mbps", default="1", help="Rate in Mbps (default 1)")
    p_vpls_stream.add_argument("--frame-size", default="128", help="Frame size (default 128)")
    p_vpls_stream.add_argument("--name", default=None, help="Stream name")

    p_isis = sub.add_parser("isis-peer", help="Configure ISIS on an emulated device for IGP adjacency with DUT")
    p_isis.add_argument("--device-name", required=True, help="Emulated device name")
    p_isis.add_argument("--system-id", default="0000.0000.0003", help="ISIS System ID")
    p_isis.add_argument("--area-id", default="49.0001", help="ISIS Area ID")
    p_isis.add_argument("--level", default="LEVEL2", choices=["LEVEL1", "LEVEL2", "LEVEL1_AND_2"],
                        help="ISIS level (default LEVEL2)")
    p_isis.add_argument("--loopback", default=None, help="Loopback IP to advertise via ISIS (e.g. 3.3.3.3)")
    p_isis.add_argument("--loopback-metric", type=int, default=10, help="ISIS metric for loopback route")
    p_isis.add_argument("--wide-metric", action="store_true", default=True,
                        help="Use wide metrics (default True)")

    p_ldp = sub.add_parser("ldp-peer", help="Configure LDP on an emulated device for label distribution with DUT")
    p_ldp.add_argument("--device-name", required=True, help="Emulated device name")
    p_ldp.add_argument("--router-id", default=None, help="LDP Router ID (default: device IP)")
    p_ldp.add_argument("--transport-address", default=None,
                       help="LDP transport address (default: loopback from isis-peer, or device IP)")
    p_ldp.add_argument("--dut-ip", default=None, help="DUT interface IP for LDP Hello (default: device gateway)")
    p_ldp.add_argument("--hello-interval", type=int, default=5, help="LDP Hello interval (default 5s)")
    p_ldp.add_argument("--keepalive-interval", type=int, default=60, help="LDP Keepalive (default 60s)")
    p_ldp.add_argument("--fec-prefix", default=None,
                       help="FEC prefix to advertise label for (default: loopback from isis-peer)")

    p_proto_start = sub.add_parser("protocol-start", help="Start protocols on devices")
    p_proto_start.add_argument("--device-name", default=None)

    p_proto_stop = sub.add_parser("protocol-stop", help="Stop protocols on devices")
    p_proto_stop.add_argument("--device-name", default=None)

    p_dut_ctx = sub.add_parser("store-dut-context", help="Store DUT discovery context in session")
    p_dut_ctx.add_argument("--device", default=None, help="DUT hostname (e.g. PE-4)")
    p_dut_ctx.add_argument("--vrfs", default=None, help="Comma-separated VRF names")
    p_dut_ctx.add_argument("--bgp-as", default=None, help="DUT BGP AS number")
    p_dut_ctx.add_argument("--bgp-peers", type=int, default=None, help="Number of BGP peers configured")
    p_dut_ctx.add_argument("--flowspec", default=None, help="Pipe-separated FlowSpec summaries")
    p_dut_ctx.add_argument("--ready-subifs", default=None, help="Comma-separated ready sub-interfaces")
    p_dut_ctx.add_argument("--suggested-streams", default=None, help="Pipe-separated auto-suggested streams")
    p_dut_ctx.add_argument("--json-input", default=None, help="Full DUT context as JSON string")
    p_dut_ctx.add_argument("--json-file", default=None, help="Path to JSON file with DUT context")
    p_dut_ctx.add_argument("--merge", action="store_true", help="Merge with existing context instead of replacing")

    p_dnaas_dx = sub.add_parser("dnaas-diagnose",
        help="Walk all DNAAS hops for a VLAN path; flag sticky Local-Loop / admin-disabled / oper-down faults")
    p_dnaas_dx.add_argument("--vlan", required=True, type=int, help="Transport VLAN (e.g. 214)")
    p_dnaas_dx.add_argument("--json-output", action="store_true", help="Emit full report as JSON")

    p_arp_chk = sub.add_parser("arp-check",
        help="Fail-fast gate: report GatewayMacResolveState for EmulatedDevices on a VLAN. "
             "Exits 3 when any device shows RESOLVE_FAILED (broken L2 path to DUT).")
    p_arp_chk.add_argument("--vlan", type=int, default=None, help="Filter by outer VLAN (e.g. 214)")
    p_arp_chk.add_argument("--inner-vlan", type=int, default=None, help="Filter by inner VLAN (Q-in-Q)")
    p_arp_chk.add_argument("--name", type=str, default=None, help="Device name regex")
    p_arp_chk.add_argument("--json-output", action="store_true", help="Emit full report as JSON")

    p_dnaas_fx = sub.add_parser("dnaas-fix",
        help="Apply delete+recreate recovery on DNAAS hops with sticky faults (idempotent)")
    p_dnaas_fx.add_argument("--vlan", required=True, type=int, help="Transport VLAN (e.g. 214)")
    p_dnaas_fx.add_argument("--dry-run", action="store_true", help="commit-check only (no apply); see what would happen")
    p_dnaas_fx.add_argument("--force-all", action="store_true", help="Recover all hops, even those reporting clean")
    p_dnaas_fx.add_argument("--all-subifs", action="store_true",
        help="Recover EVERY subif on a faulted hop (blast radius). "
             "Default is surgical: touch only the faulted subif(s).")

    p_dnaas_st = sub.add_parser("dnaas-stabilize",
        help="Prevent DNAAS AC flaps via interface dampening + carrier-delay + BD LLP tuning "
             "(live-validated syntax). Default --check reads state; --dry-run commit-checks; "
             "--apply commits + clears stuck state.")
    p_dnaas_st.add_argument("--vlan", required=True, type=int, help="Transport VLAN (e.g. 214)")
    p_dnaas_st.add_argument("--check", dest="check", action="store_true", default=True,
                            help="Read-only state check (default)")
    p_dnaas_st.add_argument("--dry-run", action="store_true",
                            help="Build config block, commit-check on each hop, rollback 0")
    p_dnaas_st.add_argument("--apply", action="store_true",
                            help="Commit the config + run operator-mode clears (ac-suppression, "
                                 "ac-history, mac-history). Use after confirming --dry-run.")
    p_dnaas_st.add_argument("--disable-llp", action="store_true",
                            help="[DANGER] Also disable BD local-loop-prevention per-instance. "
                                 "Only for controlled test runs; re-enable after.")
    p_dnaas_st.add_argument("--json-output", action="store_true",
                            help="Emit structured JSON after the table report")

    p_dut_mat = sub.add_parser("dut-match",
        help="Smart DNOS-syntax cross-check: for each Spirent EmulatedDevice, find the matching "
             "DUT sub-interface via vlan-tags/vlan-id/ipv4-address. Fails on any MISS.")
    p_dut_mat.add_argument("--dut", default=None,
                           help="DUT hostname / alias (e.g. PE-1); resolved via SCALER devices.json")
    p_dut_mat.add_argument("--dut-ip", default=None,
                           help="DUT mgmt IP (e.g. 100.64.4.200 for PE-1); used if --dut is not set "
                                "or cannot be resolved to an IP")
    p_dut_mat.add_argument("--user", default="dnroot",
                           help="DUT SSH user (default: dnroot)")
    p_dut_mat.add_argument("--password", default=None,
                           help="DUT SSH password (default: dnroot or $DNOS_DUT_PW)")
    p_dut_mat.add_argument("--vlan", type=int, default=None,
                           help="Filter devices by any VLAN tag (outer or inner)")
    p_dut_mat.add_argument("--name", default=None,
                           help="Filter devices by name regex")
    p_dut_mat.add_argument("--json-output", action="store_true",
                           help="Emit structured JSON report")

    p_fp = sub.add_parser("footprint",
        help="Smart search -- list every SPIRENT:*/TEST:* tagged DUT object via "
             "`show config | flatten | include description`. Instant ownership + state snapshot.")
    p_fp.add_argument("--dut", required=True, help="DUT hostname or mgmt IP (alias accepted)")
    p_fp.add_argument("--user", default="dnroot", help="DUT SSH user (default: dnroot)")
    p_fp.add_argument("--password", default=None,
                     help="DUT SSH password (default: dnroot or $DNOS_DUT_PW)")
    p_fp.add_argument("--owner", choices=["SPIRENT", "TEST", "spirent", "test"],
                     default=None, help="Filter by owner tag")
    p_fp.add_argument("--handle", default=None,
                     help="Substring filter on handle (e.g. 'EVPN_RT2_Peer' or 'mac_mobility')")
    p_fp.add_argument("--with-state", action="store_true", default=True,
                     help="(default) Cross-check BGP peer state + interface admin/oper")
    p_fp.add_argument("--no-state", dest="with_state", action="store_false",
                     help="Skip state cross-check (faster, config-only view)")
    p_fp.add_argument("--json-output", action="store_true", help="Emit as JSON")

    p_mark = sub.add_parser("mark-dnos",
        help="Tag DNOS objects (sub-ifs, BGP neighbors, fabric BDs) with SPIRENT:<session>/<device> descriptions")
    p_mark.add_argument("--dut", default=None, help="DUT hostname or IP (required unless --fabric-vlan)")
    p_mark.add_argument("--user", default="dnroot", help="DUT SSH user (default: dnroot)")
    p_mark.add_argument("--password", default=None,
                        help="DUT SSH password (default: dnroot or $DNOS_DUT_PW)")
    p_mark.add_argument("--fabric-vlan", default=None, type=int,
                        help="Tag all DNAAS fabric hops in _default_dnaas_topology(VLAN) "
                             "with SPIRENT-fabric-v<VLAN> descriptions (uses sisaev/Drive1234!).")
    p_mark.add_argument("--dry-run", action="store_true",
                        help="Show patch plan without committing")
    p_mark.add_argument("--json-output", action="store_true", help="Emit plan as JSON")

    p_flap = sub.add_parser("mac-mob-flap",
        help="Flap a MAC between two existing streams (operator priming helper for MAC mobility / suppression tests)")
    p_flap.add_argument("--stream-a", required=True,
                        help="Name of the first StreamBlock (e.g. AC1_TEST_MAC)")
    p_flap.add_argument("--stream-b", required=True,
                        help="Name of the second StreamBlock (e.g. AC2_TEST_MAC)")
    p_flap.add_argument("--cycles", type=int, default=6,
                        help="Number of A->B flaps (default 6; clear_operations uses 10+)")
    p_flap.add_argument("--interval-sec", type=float, default=0.5,
                        dest="interval_sec",
                        help="Seconds between Active flips (default 0.5)")
    p_flap.add_argument("--start-first", action="store_true", dest="start_first",
                        help="Start port traffic once up-front and only toggle Active "
                             "(faster; default is start/stop around every cycle)")
    p_flap.add_argument("--json-output", action="store_true", dest="json_output",
                        help="Emit a JSON report at the end")

    # F5: daemon subcommand -- manage the long-running spirent_daemon.py
    p_daemon = sub.add_parser("daemon",
        help="Control the long-running spirent_daemon (keeps StcHttp warm across CLI calls)")
    p_daemon.add_argument("action", choices=["start", "stop", "status", "run"],
                          help="start/stop/status/run -- 'run' routes the rest of argv through the daemon")
    p_daemon.add_argument("--no-warm", action="store_true",
                          help="On start: skip the initial heal-on-startup warm-up")
    p_daemon.add_argument("--timeout", type=float, default=300.0,
                          help="Client timeout for 'run' (default 300s)")
    p_daemon.add_argument("run_argv", nargs=argparse.REMAINDER,
                          help="Arguments to forward to spirent_tool.py inside the daemon (for 'run')")

    # ---- Multicast / IGMP / MLD (EVPN IGMP-Proxy, SW-211037) ----
    p_mc_src = sub.add_parser("create-mcast-source",
        help="Create a multicast data SOURCE stream (auto group MAC; (S,G) src + group dst)")
    p_mc_src.add_argument("--group", required=True, help="Multicast group G (dst IP, e.g. 239.1.1.1 or ff38::1)")
    p_mc_src.add_argument("--source", default=None, help="Multicast source S (src IP); alias of --src-ip")
    p_mc_src.add_argument("--src-ip", default=None, help="Source IP S (if --source not given)")
    p_mc_src.add_argument("--family", default="ipv4", choices=["ipv4", "ipv6"], help="ipv4 (IGMP) or ipv6 (MLD)")
    p_mc_src.add_argument("--src-mac", default=None, help="Source MAC")
    p_mc_src.add_argument("--vlan", type=int, default=None, help="Outer VLAN")
    p_mc_src.add_argument("--inner-vlan", type=int, default=None, help="Inner VLAN (auto Q-in-Q if unset)")
    p_mc_src.add_argument("--no-qinq", action="store_true", help="Force single-tagged")
    p_mc_src.add_argument("--rate-mbps", default=None, help="Rate in Mbps (default 1)")
    p_mc_src.add_argument("--rate-pps", default=None, help="Rate in frames/sec (overrides --rate-mbps)")
    p_mc_src.add_argument("--frame-size", default=None, help="Frame size bytes (default 128)")
    p_mc_src.add_argument("--name", default=None, help="Stream name")

    def _add_membership_args(p, *, with_action=False):
        p.add_argument("--group", required=True, help="Multicast group G")
        p.add_argument("--version", default=None, choices=["1", "2", "3"],
                       help="IGMP version (ipv4) / MLD version 1|2 (ipv6); default 2 (ipv4) / 1 (ipv6)")
        p.add_argument("--family", default="ipv4", choices=["ipv4", "ipv6"], help="ipv4 (IGMP) / ipv6 (MLD)")
        p.add_argument("--source", default=None, help="Comma-separated source list S for (S,G) (v3 / MLDv2)")
        p.add_argument("--filter-mode", default=None, choices=["include", "exclude"],
                       help="v3/MLDv2 filter mode (default include if --source else exclude)")
        p.add_argument("--record-type", default=None,
                       help="Override v3 GroupRecord type (mode_is_include|mode_is_exclude|"
                            "change_to_include|change_to_exclude|allow_new_sources|block_old_sources)")
        p.add_argument("--src-ip", default=None, help="Host source IP")
        p.add_argument("--src-mac", default=None, help="Host source MAC")
        p.add_argument("--vlan", type=int, default=None, help="Outer VLAN")
        p.add_argument("--inner-vlan", type=int, default=None, help="Inner VLAN")
        p.add_argument("--no-qinq", action="store_true", help="Force single-tagged")
        p.add_argument("--rate-pps", default=None, help="Frames/sec (default 1)")
        p.add_argument("--frame-size", default=None, help="Frame size bytes (default 64)")
        p.add_argument("--name", default=None, help="Stream name")

    p_mc_rcv = sub.add_parser("create-mcast-receiver",
        help="Create a stateless IGMP/MLD membership report (join): v1/v2/v3, (*,G)/(S,G), include/exclude")
    _add_membership_args(p_mc_rcv)

    p_mc_lv = sub.add_parser("mcast-leave",
        help="Create a stateless IGMP/MLD leave/done (v2 Leave / v3 block / MLD Done)")
    _add_membership_args(p_mc_lv)

    p_mc_q = sub.add_parser("mcast-querier",
        help="Emulate an external mrouter: send an IGMP/MLD General or Group-Specific Query (src != 0)")
    p_mc_q.add_argument("--group", default=None, help="Group for a Group-Specific Query (omit for General Query)")
    p_mc_q.add_argument("--version", default=None, choices=["1", "2", "3"], help="IGMP/MLD query version")
    p_mc_q.add_argument("--family", default="ipv4", choices=["ipv4", "ipv6"], help="ipv4 (IGMP) / ipv6 (MLD)")
    p_mc_q.add_argument("--src-ip", default=None, help="Querier source IP (must be non-zero to mark mrouter)")
    p_mc_q.add_argument("--src-mac", default=None, help="Querier source MAC")
    p_mc_q.add_argument("--vlan", type=int, default=None, help="Outer VLAN")
    p_mc_q.add_argument("--inner-vlan", type=int, default=None, help="Inner VLAN")
    p_mc_q.add_argument("--no-qinq", action="store_true", help="Force single-tagged")
    p_mc_q.add_argument("--rate-pps", default=None, help="Frames/sec (default 1)")
    p_mc_q.add_argument("--frame-size", default=None, help="Frame size bytes (default 64)")
    p_mc_q.add_argument("--name", default=None, help="Stream name")

    p_igmp_host = sub.add_parser("igmp-host",
        help="Configure a STATEFUL IGMP host stack (IgmpHostConfig) on an existing emulated device")
    p_igmp_host.add_argument("--device-name", default=None, help="Existing emulated device to attach the host stack to")
    p_igmp_host.add_argument("--group", required=True, help="Multicast group G (start of pool)")
    p_igmp_host.add_argument("--group-count", type=int, default=1, help="Number of groups in the pool (default 1)")
    p_igmp_host.add_argument("--version", default=None, choices=["1", "2", "3"], help="IGMP version (default 3)")
    p_igmp_host.add_argument("--source", default=None, help="Comma-separated source list for (S,G) (v3)")
    p_igmp_host.add_argument("--filter-mode", default=None, choices=["include", "exclude"],
                             help="v3 filter mode (default include if --source else exclude)")

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        sys.exit(0)

    cmds = {
        "connect": cmd_connect,
        "reserve": cmd_reserve,
        "create-stream": cmd_create_stream,
        "create-modifier-stream": cmd_create_modifier_stream,
        "start": cmd_start,
        "stop": cmd_stop,
        "release": cmd_release,
        "detach": cmd_detach,
        "stats": cmd_stats,
        "cleanup": cmd_cleanup,
        "reconcile": cmd_reconcile,
        "recover": cmd_recover,
        "heal": cmd_heal,
        "list-sessions": cmd_list_sessions,
        "status": cmd_status,
        "capacity": cmd_capacity,
        "create-device": cmd_create_device,
        "bgp-peer": cmd_bgp_peer,
        "bgp-status": cmd_bgp_status,
        "add-afi": cmd_add_afi,
        "list-devices": cmd_list_devices,
        "remove-stream": cmd_remove_stream,
        "set-stream-active": cmd_set_stream_active,
        "remove-device": cmd_remove_device,
        "prune-test-scope": cmd_prune_test_scope,
        "add-routes": cmd_add_routes,
        "evpn-routes": cmd_evpn_routes,
        "withdraw-routes": cmd_withdraw_routes,
        "evpn-rt1": cmd_evpn_rt1,
        "evpn-rt4": cmd_evpn_rt4,
        "ecmp": cmd_ecmp,
        "vpls-stream": cmd_vpls_stream,
        "isis-peer": cmd_isis_peer,
        "ldp-peer": cmd_ldp_peer,
        "protocol-start": cmd_protocol_start,
        "protocol-stop": cmd_protocol_stop,
        "store-dut-context": cmd_store_dut_context,
        "dnaas-diagnose": cmd_dnaas_diagnose,
        "arp-check": cmd_arp_check,
        "dnaas-fix": cmd_dnaas_fix,
        "dnaas-stabilize": cmd_dnaas_stabilize,
        "dut-match": cmd_dut_match,
        "mark-dnos": cmd_mark_dnos,
        "footprint": cmd_footprint,
        "mac-mob-flap": cmd_mac_mob_flap,
        "daemon": cmd_daemon,
        "create-mcast-source": cmd_create_mcast_source,
        "create-mcast-receiver": cmd_create_mcast_receiver,
        "mcast-leave": cmd_mcast_leave,
        "mcast-querier": cmd_mcast_querier,
        "igmp-host": cmd_igmp_host,
    }
    rc = cmds[args.command](args)
    return rc


if __name__ == "__main__":
    sys.exit(main() or 0)
