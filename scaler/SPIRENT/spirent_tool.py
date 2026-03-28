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
    python3 spirent_tool.py start [--stream-name NAME]
    python3 spirent_tool.py stop [--stream-name NAME]
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
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

CONFIG_PATH = os.path.expanduser("~/.spirent_config.json")
SESSION_DIR = os.path.expanduser("~/SCALER/SPIRENT/sessions")
STATS_DIR = os.path.expanduser("~/SCALER/SPIRENT/stats")

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

try:
    from stcrestclient import stchttp
except ImportError:
    print("ERROR: stcrestclient not installed. Run: pip3 install stcrestclient")
    sys.exit(1)


def load_config():
    if not os.path.exists(CONFIG_PATH):
        print(f"ERROR: Config file not found: {CONFIG_PATH}")
        print("Run /SPIRENT setup to create it.")
        sys.exit(1)
    with open(CONFIG_PATH) as f:
        return json.load(f)


def save_session(session_data):
    os.makedirs(SESSION_DIR, exist_ok=True)
    session_id = session_data.get("session_name", "default")
    path = os.path.join(SESSION_DIR, f"{session_id}.json")
    with open(path, "w") as f:
        json.dump(session_data, f, indent=2)
    return path


def load_session(session_name=None):
    """Load session file. Uses FIXED_SESSION_NAME when session_name is None. No fallback."""
    name = session_name or FIXED_SESSION_NAME
    path = os.path.join(SESSION_DIR, f"{name}.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def _stc_http(config):
    """Create a StcHttp instance with timeout. Single place to enforce timeout policy."""
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
    """Force-kill a zombie session that exists in REST list but can't be joined."""
    import urllib.request
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
        except Exception:
            pass


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
    return True, None


def _require_ready(config):
    """Combined validation: load session, verify port, validate server, connect, check handles.
    Returns (stc, sess) or sys.exit on failure. Single REST connection for the entire check."""
    sess = load_session()
    if not sess or not sess.get("port_reserved"):
        print("ERROR: Port not reserved. Run 'connect' then 'reserve' first.")
        sys.exit(1)
    ok, err = _validate_session(config, sess)
    if not ok:
        print(f"ERROR: {err}")
        sys.exit(1)
    stc, _ = get_stc(config)
    ok, err = _validate_handles(stc, sess)
    if not ok:
        print(f"[WARN] Stale handles detected: {err}")
        print("[INFO] Run 'connect --force-new' then 'reserve' to get fresh handles.")
        sys.exit(1)
    return stc, sess


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


def get_stc(config, session_name=None, force_new=False):
    """Connect to the Lab Server: join existing session first, create only if none exists.

    Resilient connection with:
    - Connection cache: reuse StcHttp across calls within same process
    - Health probe before any STC API call (catches dead stcweb instantly)
    - HTTP timeout on all connections (prevents infinite hangs)
    - Fallback session names when primary is a zombie
    - Handle validation (detects stale port/project handles from BLL restart)
    - Hard cap at MAX_TOTAL_SESSION_ATTEMPTS total attempts per invocation
    """
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
    if not force_new:
        for name in names_to_try:
            sess = load_session(name)
            if sess and sess.get("active") and sess.get("session_id_on_server"):
                sid = sess["session_id_on_server"]
                if sid not in server_sessions:
                    sess["active"] = False
                    sess["_stale_reason"] = "server session gone (health probe)"
                    save_session(sess)
                    continue
                try:
                    stc = _stc_http(config)
                    stc.join_session(sid)
                    sess["last_joined"] = datetime.utcnow().isoformat()
                    sess["join_count"] = sess.get("join_count", 0) + 1
                    return _cache_and_return(stc, sess)
                except Exception as e:
                    print(f"[WARN] Join failed for {name}: {e}")

    # Phase 2: Create path -- try primary, then fallback names on zombie
    for name in names_to_try:
        session_id = f"{name} - {user}"
        _inc_and_check()
        stc = _stc_http(config)

        for create_attempt in range(MAX_SESSION_RETRIES):
            try:
                stc.new_session(user_name=user, session_name=name, kill_existing=force_new or create_attempt > 0)
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
    """Connect to Lab Server, join or create persistent session (dn_spirent_main)."""
    config = load_config()

    _clean_stale_local_sessions(config)

    stc, sess = get_stc(config, force_new=getattr(args, "force_new", False))

    if sess.get("project_handle"):
        project = sess["project_handle"]
        print(f"Reusing existing project: {project}")
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

    sess["port_handle"] = port
    sess["port_reserved"] = True
    save_session(sess)

    print(f"Port reserved: {port_loc}")
    print(f"Port handle: {port}")


def cmd_create_stream(args):
    """Create a VLAN-tagged traffic stream on the reserved port."""
    config = load_config()
    stc, sess = _require_ready(config)

    stream_name = args.name or f"stream_{len(sess.get('streams', []))}"
    frame_size = int(args.frame_size) if args.frame_size else 128
    rate_mbps = float(args.rate_mbps) if args.rate_mbps else 100.0

    load_unit = "MEGABITS_PER_SECOND"
    if args.rate_pps:
        load_unit = "FRAMES_PER_SECOND"
        rate_mbps = float(args.rate_pps)

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
        src_ip = args.src_ip or "10.0.0.1"
        dst_ip = args.dst_ip or "10.0.0.2"
        ip_args = {"sourceAddr": src_ip, "destAddr": dst_ip}
        existing_ip = stc.get(sb, "children-ipv4:IPv4")
        if args.protocol == "ipv6":
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
    sess.setdefault("streams", []).append(stream_info)
    save_session(sess)

    print(f"Stream created: {stream_name}")
    print(json.dumps(stream_info, indent=2))


def cmd_start(args):
    """Start traffic generation."""
    config = load_config()
    stc, sess = _require_ready(config)

    gen_handle = stc.get(sess["port_handle"], "children-Generator")
    if not gen_handle:
        print("ERROR: No generator found on port. Create a stream first.")
        sys.exit(1)

    ana_handle = stc.get(sess["port_handle"], "children-Analyzer")
    if ana_handle:
        stc.perform("AnalyzerStart", AnalyzerList=ana_handle)

    stc.perform("GeneratorStart", GeneratorList=gen_handle)

    sess["traffic_running"] = True
    sess["traffic_started"] = datetime.utcnow().isoformat()
    save_session(sess)

    print(f"Traffic STARTED at {sess['traffic_started']}")
    print(f"Active streams: {len(sess.get('streams', []))}")


def cmd_stop(args):
    """Stop traffic generation."""
    config = load_config()
    stc, sess = _require_ready(config)

    gen_handle = stc.get(sess["port_handle"], "children-Generator")
    if gen_handle:
        stc.perform("GeneratorStop", GeneratorList=gen_handle)

    sess["traffic_running"] = False
    sess["traffic_stopped"] = datetime.utcnow().isoformat()
    save_session(sess)

    print(f"Traffic STOPPED at {sess['traffic_stopped']}")


def _collect_per_stream_stats(stc, sess, project_handle, per_stream):
    """Collect per-stream TX/RX stats using TxStreamBlockResults and RxStreamBlockResults."""
    streams_out = []
    stream_list = sess.get("streams", [])
    if not per_stream or not stream_list:
        return streams_out

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
        return streams_out

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
    streams_data = _collect_per_stream_stats(stc, sess, project_handle, per_stream)
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
    """Create EmulatedDevice(s) with EthIIIf + Ipv4If stack (optional VlanIf).

    Supports STC Device Block multiplier: --device-count N creates N logical devices
    with auto-stepping IP (--ip-step) and MAC (--mac-step). Single REST object,
    ~15 API calls regardless of N.
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

    dev_count = getattr(args, "device_count", 1) or 1
    ip_step_raw = getattr(args, "ip_step", None)
    mac_step_raw = getattr(args, "mac_step", None)
    device_name = args.name or f"BGP_Peer_{len(sess.get('devices', []))}"
    prefix_len = int(args.prefix_len) if args.prefix_len else 24
    router_id = args.router_id or args.ip
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

    ipv4_attrs = {
        "Address": args.ip,
        "Gateway": args.gateway,
        "PrefixLength": str(prefix_len),
    }
    if dev_count > 1:
        ipv4_attrs["AddrStep"] = ip_step
        ipv4_attrs["GatewayStep"] = "0.0.0.0"
    ipv4 = stc.create("Ipv4If", under=device, **ipv4_attrs)

    stc.config(device, **{"TopLevelIf-targets": [ipv4]})
    stc.config(device, **{"PrimaryIf-targets": [ipv4]})

    if outer_vlan is not None and inner_vlan_id is not None:
        inner_vlan_if = stc.create("VlanIf", under=device, VlanId=str(inner_vlan_id))
        outer_vlan_if = stc.create("VlanIf", under=device, VlanId=str(outer_vlan))
        stc.config(ipv4, **{"StackedOnEndpoint-targets": [inner_vlan_if]})
        stc.config(inner_vlan_if, **{"StackedOnEndpoint-targets": [outer_vlan_if]})
        stc.config(outer_vlan_if, **{"StackedOnEndpoint-targets": [eth]})
    elif outer_vlan is not None:
        vlan_if = stc.create("VlanIf", under=device, VlanId=str(outer_vlan))
        stc.config(ipv4, **{"StackedOnEndpoint-targets": [vlan_if]})
        stc.config(vlan_if, **{"StackedOnEndpoint-targets": [eth]})
    else:
        stc.config(ipv4, **{"StackedOnEndpoint-targets": [eth]})

    existing_devices = [d["handle"] for d in sess.get("devices", []) if d.get("handle")]
    all_devices = existing_devices + [device]
    stc.config(port, **{"AffiliationPort-sources": all_devices})

    stc.apply()

    dev_info = {
        "name": device_name,
        "handle": device,
        "ip": args.ip,
        "gateway": args.gateway,
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
    else:
        print(f"Device created: {device_name} ({args.ip})")
    print(json.dumps(dev_info, indent=2))


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

    devices = sess.get("devices", [])
    dev_match = next((d for d in devices if d["name"] == args.device_name), None)
    if not dev_match:
        print(f"ERROR: Device '{args.device_name}' not found. Run 'list-devices' to see available devices.")
        sys.exit(1)

    if not dev_match.get("bgp_handle"):
        _preflight_capacity_warn(config, sess, new_peer=True)

    device_handle = dev_match["handle"]
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

    print("Starting ARP/ND and device protocols...")
    stc.perform("ArpNdStartCommand", HandleList=port)
    time.sleep(2)
    stc.perform("DeviceStartCommand", DeviceList=device_handle)
    stc.apply()

    print("Waiting for BGP session (ESTABLISHED)...")
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

    for _ in range(30):
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

    print("WARNING: BGP session not ESTABLISHED within 30s. Check DUT config and connectivity.")


def cmd_add_afi(args):
    """Add AFI/SAFI route config objects to an existing BGP peer (triggers capability renegotiation)."""
    config = load_config()
    stc, sess = _require_ready(config)

    devices = sess.get("devices", [])
    dev_match = next((d for d in devices if d["name"] == args.device_name), None)
    if not dev_match:
        print(f"ERROR: Device '{args.device_name}' not found.")
        sys.exit(1)
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
    """Show BGP session state and route counts for emulated devices."""
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

    out = []
    for dev in devices:
        bgp_handle = dev.get("bgp_handle")
        if not bgp_handle:
            out.append({"device": dev["name"], "bgp": "not configured"})
            continue

        try:
            results_handle = stc.get(bgp_handle, "children-BgpRouterResults")
            if results_handle:
                rh = results_handle.split()[0]
                results = stc.get(rh)
                out.append({
                    "device": dev["name"],
                    "state": results.get("SessionState", "N/A"),
                    "routes_advertised": results.get("RoutesAdvertised", "0"),
                    "routes_received": results.get("RoutesReceived", "0"),
                    "updates_sent": results.get("UpdatesSent", "0"),
                    "updates_received": results.get("UpdatesReceived", "0"),
                })
            else:
                out.append({"device": dev["name"], "state": "no results"})
        except Exception as e:
            out.append({"device": dev["name"], "error": str(e)})

    if args.json_output:
        print(json.dumps(out, indent=2))
    else:
        print("=== BGP Session Status ===")
        for r in out:
            print(f"\n  {r['device']}:")
            for k, v in r.items():
                if k != "device":
                    print(f"    {k}: {v}")


# ────────────────────────────────────────────
# Phase 2: Route Scale Advertising
# ────────────────────────────────────────────

def cmd_add_routes(args):
    """Add route blocks to a BGP router (IPv4, IPv6, VPNv4, VPNv6)."""
    config = load_config()
    stc, sess = _require_ready(config)

    devices = sess.get("devices", [])
    dev_match = next((d for d in devices if d["name"] == args.device_name), None)
    if not dev_match:
        print(f"ERROR: Device '{args.device_name}' not found.")
        sys.exit(1)

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


def _wait_bgp_convergence(stc, device_handle, count, timeout_sec, port):
    """Poll BGP session states until all are ESTABLISHED or timeout.
    Returns (established_count, total_count).
    Retries ARP every 15 seconds if sessions are stuck.
    """
    import time as _time
    start = _time.time()
    poll_interval = 5
    arp_retry_interval = 15
    last_arp = start
    best_established = 0

    while (_time.time() - start) < timeout_sec:
        try:
            bgp_children = stc.get(device_handle, "children-BgpRouterConfig")
            if not bgp_children:
                _time.sleep(poll_interval)
                continue
            bgp_handle = bgp_children.split()[0]
            results = stc.get(bgp_handle)
            block_state = results.get("BlockState", "")
            established = 0
            total = count

            if block_state == "ALL_ESTABLISHED" or block_state == "ESTABLISHED":
                established = count
            elif "BlockState" in results:
                state_str = results.get("BlockState", "")
                if "MIXED" in state_str or "SOME" in state_str:
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

            best_established = max(best_established, established)
            elapsed = int(_time.time() - start)
            print(f"  [{elapsed}s] BGP: {established}/{total} established", flush=True)

            if established >= total:
                print(f"  [OK] All {total} BGP sessions ESTABLISHED in {elapsed}s")
                return established, total

            now = _time.time()
            if (now - last_arp) >= arp_retry_interval and established < total:
                print(f"  [ARP] Retrying ARP/ND resolution...", flush=True)
                try:
                    stc.perform("ArpNdStartCommand", HandleList=port)
                except Exception:
                    pass
                last_arp = now

        except Exception as e:
            print(f"  [WARN] Poll error: {e}")

        _time.sleep(poll_interval)

    elapsed = int(_time.time() - start)
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
        bgp_children = stc.get(bgp, "children")
        if bgp_children:
            for child_handle in bgp_children.split():
                if "modifier" in child_handle.lower():
                    try:
                        stc.config(child_handle, StepValue="0")
                    except Exception:
                        try:
                            stc.config(child_handle, StepValue="0.0.0.0")
                        except Exception:
                            pass
            print(f"  [OK] All BGP modifier steps set to 0 (constant AS/DUT across {count} devices)")

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
    """List all emulated devices in the session."""
    sess = load_session()
    if not sess:
        print("ERROR: No active session.")
        sys.exit(1)

    devices = sess.get("devices", [])
    if not devices:
        print("No emulated devices in session.")
        return

    print("=== Emulated Devices ===")
    for d in devices:
        bgp = "BGP configured" if d.get("bgp_handle") else "no BGP"
        print(f"  {d['name']}: {d['ip']} (gw: {d['gateway']}) vlan={d.get('vlan', 'none')} [{bgp}]")


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
        all_devices = [d["handle"] for d in devices if d["name"] != args.name]
        stc.config(port, **{"AffiliationPort-sources": all_devices})
        stc.delete(dev_handle)
        stc.apply()
    except Exception as e:
        print(f"ERROR: Could not remove device from STC: {e}")
        sys.exit(1)

    sess["devices"] = [d for d in devices if d["name"] != args.name]
    save_session(sess)
    print(f"Device removed: {args.name}")


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
            except Exception:
                pass
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
                gen_handle = stc.get(sess["port_handle"], "children-Generator")
                if gen_handle:
                    stc.perform("GeneratorStop", GeneratorList=gen_handle)
        except Exception as e:
            print(f"Warning stopping traffic: {e}")

        try:
            if sess.get("port_reserved") and sess.get("port_handle"):
                stc.perform("DetachPorts", portList=sess["port_handle"])
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
    for attempt in range(3):
        time.sleep(2)
        ok, result = _health_probe(config)
        if ok:
            print(f"[OK] Lab Server recovered. {len(result)} sessions.")
            for sf in Path(SESSION_DIR).glob("*.json"):
                try:
                    with open(sf) as f:
                        sd = json.load(f)
                    if sd.get("active"):
                        sd["active"] = False
                        sd["_stale_reason"] = f"post-recovery invalidation ({level})"
                        with open(sf, "w") as f:
                            json.dump(sd, f, indent=2)
                except Exception:
                    pass
            print("[INFO] All local sessions marked inactive. Run 'connect' to create fresh session.")
            return
        print(f"  Health check attempt {attempt+1}/3 failed: {result}")

    print("[ERROR] Lab Server did not recover after restart.")
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
                "rate": f"{st['rate']} {st['rate_unit']}",
                "frame_size": st.get("frame_size"),
                "protocol": st.get("protocol", "L2"),
                "dst_ip": st.get("dst_ip"),
                "src_ip": st.get("src_ip"),
            }
            output["streams"].append(s_info)

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


def main():
    parser = argparse.ArgumentParser(description="Spirent TestCenter CLI tool")
    sub = parser.add_subparsers(dest="command")

    p_conn = sub.add_parser("connect", help="Connect to Lab Server, join or create persistent session")
    p_conn.add_argument("--force-new", action="store_true", help="Kill existing session and create fresh")

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
    p_stream.add_argument("--protocol", default="ipv4", choices=["ipv4", "ipv6", "l2"])

    p_start = sub.add_parser("start", help="Start traffic generation")
    p_start.add_argument("--stream-name", default=None)

    p_stop = sub.add_parser("stop", help="Stop traffic generation")
    p_stop.add_argument("--stream-name", default=None)

    p_stats = sub.add_parser("stats", help="Get traffic statistics")
    p_stats.add_argument("--json", dest="json_output", action="store_true")
    p_stats.add_argument("--no-per-stream", dest="per_stream", action="store_false", default=True,
                         help="Skip per-stream stats (faster, port-level only)")

    p_clean = sub.add_parser("cleanup", help="Release port and end session (use --confirm after user approval)")
    p_clean.add_argument("--session-name", default=None, help="'--all' to clean all dn_spirent sessions")
    p_clean.add_argument("--confirm", action="store_true", help="User confirmed; proceed with cleanup")

    p_reconcile = sub.add_parser("reconcile", help="Compare local vs server sessions, mark stale, optionally kill orphans")
    p_reconcile.add_argument("--kill-orphans", action="store_true", help="Kill orphan server sessions not in local files")

    p_recover = sub.add_parser("recover", help="Diagnose and recover crashed Lab Server (SSH restart stcweb/engine/container)")
    p_recover.add_argument("--level", default="stcweb", choices=["stcweb", "engine", "full"],
                           help="Recovery level: stcweb (light), engine (medium), full (docker restart)")

    p_list = sub.add_parser("list-sessions", help="List Lab Server sessions")

    p_status = sub.add_parser("status", help="Show current status (fast from session file, --live for STC query)")
    p_status.add_argument("--live", action="store_true", help="Query live STC API for BGP state and traffic stats")
    p_status.add_argument("--json", dest="json_output", action="store_true", help="Output as JSON")

    p_capacity = sub.add_parser("capacity", help="Show capacity usage: bandwidth, streams, BGP peers, routes, FlowSpec TCAM")
    p_capacity.add_argument("--live", action="store_true", help="Query STC API for route counts")
    p_capacity.add_argument("--json", dest="json_output", action="store_true", help="Output as JSON")

    p_create_dev = sub.add_parser("create-device", help="Create emulated device(s) with IP stack (supports multiplier)")
    p_create_dev.add_argument("--ip", required=True, help="Device IP address (base IP if --device-count > 1)")
    p_create_dev.add_argument("--gateway", required=True, help="Gateway (DUT) IP address")
    p_create_dev.add_argument("--prefix-len", default="24", help="Prefix length (default 24)")
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
                            help="Comma-separated AFIs to negotiate: ipv4-unicast,ipv4-flowspec,ipv6-unicast,ipv6-flowspec,ipv4-vpn,ipv6-vpn,all")

    p_bgp_status = sub.add_parser("bgp-status", help="Show BGP session state")
    p_bgp_status.add_argument("--device-name", default=None, help="Filter by device")
    p_bgp_status.add_argument("--json", dest="json_output", action="store_true")

    p_add_afi = sub.add_parser("add-afi", help="Add AFI capabilities to existing BGP peer (renegotiates session)")
    p_add_afi.add_argument("--device-name", required=True, help="Emulated device name")
    p_add_afi.add_argument("--afis", required=True,
                           help="Comma-separated: ipv4-unicast,ipv4-flowspec,ipv6-unicast,ipv6-flowspec,ipv4-vpn,ipv6-vpn,all")

    p_list_dev = sub.add_parser("list-devices", help="List emulated devices")

    p_remove_stream = sub.add_parser("remove-stream", help="Remove a stream from the session")
    p_remove_stream.add_argument("--name", required=True, help="Stream name to remove")

    p_remove_device = sub.add_parser("remove-device", help="Remove device from session (stops BGP first)")
    p_remove_device.add_argument("--name", required=True, help="Device name to remove")

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

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    cmds = {
        "connect": cmd_connect,
        "reserve": cmd_reserve,
        "create-stream": cmd_create_stream,
        "start": cmd_start,
        "stop": cmd_stop,
        "stats": cmd_stats,
        "cleanup": cmd_cleanup,
        "reconcile": cmd_reconcile,
        "recover": cmd_recover,
        "list-sessions": cmd_list_sessions,
        "status": cmd_status,
        "capacity": cmd_capacity,
        "create-device": cmd_create_device,
        "bgp-peer": cmd_bgp_peer,
        "bgp-status": cmd_bgp_status,
        "add-afi": cmd_add_afi,
        "list-devices": cmd_list_devices,
        "remove-stream": cmd_remove_stream,
        "remove-device": cmd_remove_device,
        "add-routes": cmd_add_routes,
        "ecmp": cmd_ecmp,
        "protocol-start": cmd_protocol_start,
        "protocol-stop": cmd_protocol_stop,
        "store-dut-context": cmd_store_dut_context,
    }
    cmds[args.command](args)


if __name__ == "__main__":
    main()
