"""Scaler bridge routes: ssh."""
from __future__ import annotations

import json
import logging
import os
import re
import time
from pathlib import Path

from fastapi import APIRouter, Body, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from routes.bridge_helpers import (
    SCALER_ROOT, _connect_virsh_console_sync, _discover_console,
    _discover_ncc_mgmt_ip_sync, _fetch_zohar_db, _get_credentials,
    _get_known_console_servers, _lookup_zohar_pdu, _pdu_power_action,
    _probe_console_server, _resolve_mgmt_ip, _save_discovered_console,
    _ssh_pool,
)
from routes._state import _push_jobs, _push_jobs_lock

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/api/ssh-pool/toggle")
def ssh_pool_toggle(body: dict = None):
    """Toggle SSH connection pool on/off. Body: { enabled: true/false }"""
    body = body or {}
    on = body.get("enabled", False)
    result = _ssh_pool.toggle(on)
    return result


@router.get("/api/ssh-pool/status")
def ssh_pool_status():
    """Return pool state: enabled, count, per-device connection age/state."""
    return _ssh_pool.status()


@router.post("/api/ssh-pool/evict")
def ssh_pool_evict(body: dict = None):
    """Force-close pooled SSH client(s). Body: { ip: str, device_id?: str }

    Pool entries are keyed by management IPv4. The canvas ``ip`` field may be a
    serial or hostname; optional ``device_id`` (usually device label) is passed
    to ``_resolve_mgmt_ip`` together with ``ip`` as ``ssh_host`` so the real
    mgmt IP is evicted. The raw ``ip`` string is also evicted in case it was
    used as a key.
    """
    body = body or {}
    raw = (body.get("ip") or "").strip()
    device_id = (body.get("device_id") or "").strip()
    if not raw:
        raise HTTPException(status_code=400, detail="ip required")

    evicted_keys = []

    def _do_evict(addr: str) -> None:
        addr = (addr or "").strip().split("/")[0]
        if not addr:
            return
        _ssh_pool.evict(addr)
        if addr not in evicted_keys:
            evicted_keys.append(addr)

    _do_evict(raw)

    is_ipv4 = bool(raw and re.match(r"^\d+\.\d+\.\d+\.\d+$", raw))
    if not is_ipv4:
        did = device_id or raw
        ssh_h = raw
        try:
            mgmt_ip, _, _ = _resolve_mgmt_ip(did, ssh_h)
            mgmt_ip = (mgmt_ip or "").strip().split("/")[0]
            if mgmt_ip:
                _do_evict(mgmt_ip)
        except HTTPException:
            pass
        except Exception:
            pass

    primary = evicted_keys[-1] if evicted_keys else raw
    return {"status": "ok", "evicted": primary, "evicted_keys": evicted_keys}


@router.post("/api/ssh/probe")
def probe_connection(body: dict = None):
    """Probe available connection methods for a device.
    Body: { device_id: str, ssh_host?: str }
    Returns: { methods: [{ method: str, host: str, port: int, reachable: bool, latency_ms?: int }],
               recommended: str, device_state: str }
    """
    import socket
    body = body or {}
    device_id = (body.get("device_id") or "").strip()
    ssh_host = (body.get("ssh_host") or "").strip()
    if not device_id:
        raise HTTPException(status_code=400, detail="device_id required")
    try:
        mgmt_ip, scaler_id, _ = _resolve_mgmt_ip(device_id, ssh_host)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
    ip = ssh_host or mgmt_ip
    if not ip:
        raise HTTPException(status_code=400, detail="Could not resolve device IP")
    try:
        from scaler.connection_strategy import DeviceConnector, ConnectionMethod, get_console_config_for_device, _derive_kvm_host
        class _TempDevice:
            pass
        dev = _TempDevice()
        dev.hostname = scaler_id
        dev.ip = ip
        dev.serial_number = None
        dev.username = "dnroot"
        dev.password = "dnroot"
        dev.loopback_ip = None
        try:
            ops_path = Path(SCALER_ROOT) / "db" / "configs" / scaler_id / "operational.json"
            if ops_path.exists():
                ops = json.loads(ops_path.read_text())
                dev.serial_number = ops.get("serial_number") or ops.get("serial")
                dev.loopback_ip = (ops.get("loopback_ip") or "").split("/")[0] or None
        except Exception:
            pass
        console_config = get_console_config_for_device(scaler_id)
        connector = DeviceConnector(dev, console_config)
        targets = connector.get_probe_targets()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Connection strategy: {e}")
    method_map = {
        ConnectionMethod.SSH_SN: "ssh_sn",
        ConnectionMethod.SSH_MGMT: "ssh_mgmt",
        ConnectionMethod.SSH_NCC: "ssh_ncc",
        ConnectionMethod.VIRSH_CONSOLE: "virsh_console",
        ConnectionMethod.CONSOLE: "console",
        ConnectionMethod.SSH_LOOPBACK: "ssh_loopback",
    }
    results = []
    recommended = None
    for method, host, port in targets:
        if not host:
            continue
        t0 = time.perf_counter()
        reachable = False
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        try:
            sock.connect((host, port))
            reachable = True
        except Exception:
            pass
        finally:
            try:
                sock.close()
            except Exception:
                pass
        latency_ms = int((time.perf_counter() - t0) * 1000) if reachable else None
        mname = method_map.get(method, str(method))
        entry = {"method": mname, "host": host, "port": port, "reachable": reachable, "latency_ms": latency_ms}
        if method == ConnectionMethod.VIRSH_CONSOLE:
            try:
                kvm_cfg = connector._get_kvm_host_config() or {}
                entry["kvm_host_name"] = kvm_cfg.get("kvm_host", "")
                entry["kvm_credentials"] = kvm_cfg.get("kvm_host_credentials", {})
                entry["ncc_vms"] = kvm_cfg.get("ncc_vms", [])
                if reachable and kvm_cfg.get("kvm_host_credentials", {}).get("username"):
                    try:
                        import paramiko as _pmk2
                        _kssh = _pmk2.SSHClient()
                        _kssh.set_missing_host_key_policy(_pmk2.AutoAddPolicy())
                        _kc = kvm_cfg["kvm_host_credentials"]
                        _kssh.connect(host, username=_kc["username"],
                                      password=_kc.get("password", ""),
                                      timeout=5, allow_agent=False, look_for_keys=False)
                        _, _out, _ = _kssh.exec_command("sudo virsh list --all 2>/dev/null || virsh list --all 2>/dev/null", timeout=5)
                        _virsh = _out.read().decode("utf-8", errors="replace")
                        _kssh.close()
                        running = [vm for vm in kvm_cfg.get("ncc_vms", [])
                                   if vm in _virsh and "running" in _virsh.split(vm)[1].split("\n")[0].lower()]
                        defined = [vm for vm in kvm_cfg.get("ncc_vms", []) if vm in _virsh]
                        entry["vms_running"] = running
                        entry["vms_defined"] = defined
                        if not running and not defined:
                            entry["reachable"] = True
                            entry["vm_warning"] = "No NCC VMs exist on KVM host -- device needs redeployment"
                        elif not running:
                            entry["vm_warning"] = f"NCC VMs defined but not running: {', '.join(defined)}"
                    except Exception:
                        pass
            except Exception:
                pass
        results.append(entry)
        if reachable and not recommended:
            recommended = mname
    device_state = ""
    cluster_info = None
    ncc_mgmt_ip_out = ""
    ncc_mgmt_verified_at_out = ""
    ops_path = Path(SCALER_ROOT) / "db" / "configs" / scaler_id / "operational.json"
    try:
        if ops_path.exists():
            ops = json.loads(ops_path.read_text())
            device_state = ops.get("device_state", "") or ""
            _nip = (ops.get("ncc_mgmt_ip") or "").strip()
            if _nip:
                ncc_mgmt_ip_out = _nip
                ncc_mgmt_verified_at_out = (ops.get("ncc_mgmt_verified_at") or "").strip()
            needs_ops_write = False
            if recommended:
                ops["last_working_method"] = recommended
                ops["connection_probe_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                needs_ops_write = True
            if ops.get("ncc_type") == "kvm":
                _ipv4_re = re.compile(r"^\d+\.\d+\.\d+\.\d+$")
                best_ssh = None
                for m in results:
                    if not m.get("reachable"):
                        continue
                    if m.get("method") not in ("ssh_mgmt", "ssh_ncc"):
                        continue
                    h = (m.get("host") or "").strip().split("/")[0]
                    if _ipv4_re.match(h):
                        best_ssh = m
                        break
                if best_ssh:
                    new_ip = (best_ssh.get("host") or "").strip().split("/")[0]
                    old_ip = (ops.get("mgmt_ip") or "").strip().split("/")[0]
                    if new_ip and new_ip != old_ip:
                        ops["mgmt_ip"] = new_ip
                        ops["ssh_host"] = new_ip
                        needs_ops_write = True
            if needs_ops_write:
                import tempfile
                tmp_fd, tmp_path = tempfile.mkstemp(dir=str(ops_path.parent), suffix=".tmp")
                try:
                    with os.fdopen(tmp_fd, 'w') as f:
                        json.dump(ops, f, indent=2)
                    os.replace(tmp_path, str(ops_path))
                except Exception:
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass
            if ops.get("ncc_type") == "kvm":
                ncc_vms = ops.get("ncc_vms", [])
                ncc_hosts = ops.get("ncc_hosts", [])
                kvm_host = _derive_kvm_host(ops.get("kvm_host", "") or "")
                console_cfg = ops.get("ncc_console_credentials", {})
                cluster_info = {
                    "is_cluster": True,
                    "ncc_type": "kvm",
                    "kvm_host": kvm_host,
                    "ncc_vms": ncc_vms,
                    "ncc_hosts": ncc_hosts,
                    "active_ncc_vm": ops.get("active_ncc_vm", ""),
                    "ncp_console": None,
                }
                try:
                    from scaler.connection_strategy import get_console_config_for_device as _gcc
                    mappings_path = Path(SCALER_ROOT) / "db" / "configs" / "console_mappings.json"
                    if mappings_path.exists():
                        cdata = json.loads(mappings_path.read_text())
                        d2c = cdata.get("device_to_console", {})
                        for dname, dmapping in d2c.items():
                            if dname.lower() == scaler_id.lower():
                                cluster_info["ncp_console"] = {
                                    "console_server": dmapping.get("console_server"),
                                    "port": dmapping.get("port"),
                                    "source": dmapping.get("source", "cached"),
                                }
                                break
                except Exception:
                    pass
    except Exception:
        pass
    if not cluster_info:
        try:
            cm_path = Path(SCALER_ROOT) / "db" / "console_mappings.json"
            if cm_path.exists():
                cm_data = json.loads(cm_path.read_text())
                ncc_entry = cm_data.get("cluster_ncc_access", {}).get(scaler_id)
                if ncc_entry and ncc_entry.get("ncc_type") == "kvm":
                    _cm_kvm = _derive_kvm_host(ncc_entry.get("kvm_host_ip") or ncc_entry.get("kvm_host") or "")
                    cluster_info = {
                        "is_cluster": True,
                        "ncc_type": "kvm",
                        "kvm_host": _cm_kvm,
                        "ncc_vms": ncc_entry.get("ncc_vms", []),
                        "ncc_hosts": ncc_entry.get("ncc_vms", []),
                        "active_ncc_vm": ncc_entry.get("active_ncc_vm", ""),
                        "ncp_console": None,
                    }
                    d2c = cm_data.get("device_to_console", {})
                    for dname, dmapping in d2c.items():
                        if dname.lower() == scaler_id.lower():
                            cluster_info["ncp_console"] = {
                                "console_server": dmapping.get("console_server"),
                                "port": dmapping.get("port"),
                                "source": dmapping.get("source", "cached"),
                            }
                            break
        except Exception:
            pass
    resp = {
        "methods": results,
        "recommended": recommended or (results[0]["method"] if results else None),
        "device_state": device_state,
    }
    if cluster_info:
        resp["cluster"] = cluster_info
    if ncc_mgmt_ip_out:
        resp["ncc_mgmt_ip"] = ncc_mgmt_ip_out
        resp["ncc_mgmt_verified_at"] = ncc_mgmt_verified_at_out
    return resp


@router.get("/api/ssh/check-port")
def check_ssh_port(host: str = "", port: int = 22):
    """Single TCP connect for quick reachability (e.g. NCC mgmt before iTerm)."""
    import socket as _sock
    host = (host or "").strip()
    if not host:
        raise HTTPException(status_code=400, detail="host required")
    if port < 1 or port > 65535:
        raise HTTPException(status_code=400, detail="invalid port")
    s = _sock.socket(_sock.AF_INET, _sock.SOCK_STREAM)
    s.settimeout(2.0)
    try:
        s.connect((host, port))
        return {"reachable": True, "host": host, "port": port}
    except Exception:
        return {"reachable": False, "host": host, "port": port}
    finally:
        try:
            s.close()
        except Exception:
            pass


@router.post("/api/ssh/discover-ncc-mgmt")
def discover_ncc_mgmt_ip_endpoint(body: dict = None):
    """Background: virsh console to NCC, show interfaces management, verify SSH dnroot; persist if ok."""
    body = body or {}
    device_id = (body.get("device_id") or "").strip()
    kvm_host = (body.get("kvm_host") or "").strip()
    kvm_user = (body.get("kvm_user") or "dn").strip()
    kvm_pass = body.get("kvm_pass") or ""
    ncc_vms = body.get("ncc_vms") or []
    if isinstance(ncc_vms, str):
        ncc_vms = [v.strip() for v in ncc_vms.split(",") if v.strip()]
    active_ncc = (body.get("active_ncc") or "").strip() or None
    if not device_id:
        raise HTTPException(status_code=400, detail="device_id required")
    if not kvm_host:
        raise HTTPException(status_code=400, detail="kvm_host required")
    if not kvm_pass:
        raise HTTPException(status_code=400, detail="kvm_pass required")

    try:
        _, scaler_id, _ = _resolve_mgmt_ip(device_id, "")
    except HTTPException:
        scaler_id = device_id
    except Exception:
        scaler_id = device_id

    result = _discover_ncc_mgmt_ip_sync(kvm_host, kvm_user, kvm_pass, ncc_vms, active_ncc)
    result["device_id"] = device_id
    result["scaler_id"] = scaler_id

    ops_path = Path(SCALER_ROOT) / "db" / "configs" / scaler_id / "operational.json"
    if result.get("ncc_mgmt_ip") and result.get("ssh_auth_ok") and ops_path.exists():
        try:
            ops = json.loads(ops_path.read_text())
            ops["ncc_mgmt_ip"] = result["ncc_mgmt_ip"]
            ops["ncc_mgmt_verified_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            _nip = (result["ncc_mgmt_ip"] or "").strip().split("/")[0]
            if _nip:
                ops["mgmt_ip"] = _nip
                ops["ssh_host"] = _nip
            import tempfile
            tmp_fd, tmp_path = tempfile.mkstemp(dir=str(ops_path.parent), suffix=".tmp")
            try:
                with os.fdopen(tmp_fd, "w") as f:
                    json.dump(ops, f, indent=2)
                os.replace(tmp_path, str(ops_path))
            except Exception:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
        except Exception as e:
            logging.warning(f"[discover_ncc_mgmt] could not save operational.json: {e}")

    return result

@router.post("/api/ssh/discover-console")
def discover_console_path(body: dict = None):
    """Discover console path via Zohar's CSV DB (primary) or Device42 (fallback).
    Auto-saves to console_mappings.json. Returns console_server, port, pdu_entries, source."""
    body = body or {}
    device_id = (body.get("device_id") or "").strip()
    serial_number = (body.get("serial_number") or "").strip()
    ssh_host = (body.get("ssh_host") or "").strip()
    if not device_id and not serial_number:
        raise HTTPException(status_code=400, detail="device_id or serial_number required")
    try:
        result = _discover_console(device_id or "unknown", serial_number, ssh_host)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

    try:
        mappings_path = Path(SCALER_ROOT) / "db" / "console_mappings.json"
        mappings_path.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        if mappings_path.exists():
            data = json.loads(mappings_path.read_text())
        key = device_id or result.get("serial_no", "unknown")
        if "device_to_console" not in data:
            data["device_to_console"] = {}
        entry = {
            "console_server": result.get("console_server"),
            "port": str(result["port"]) if result.get("port") is not None else None,
            "source": result.get("source", "unknown"),
            "discovered_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        if result.get("serial_no"):
            entry["serial_number"] = result["serial_no"]
        if result.get("pdu_entries"):
            entry["pdu_entries"] = result["pdu_entries"]
        data["device_to_console"][key] = entry

        if result.get("serial_no"):
            data.setdefault("serial_to_console", {})[result["serial_no"]] = {
                "console_server": result.get("console_server"),
                "port": str(result["port"]) if result.get("port") is not None else None,
                "hostname": key,
            }
        mappings_path.write_text(json.dumps(data, indent=2))
    except Exception:
        pass
    return result


@router.post("/api/ssh/console-scan")
def console_port_scan(body: dict = None):
    """Scan console server ports to find a device by hostname.
    Tries all known console servers unless a specific one is given.
    Excludes KVM cluster devices (those use virsh console, not serial).
    Body: { device_id, serial_number?, console_server? (optional hint) }
    Returns: { found, console_server, port, scanned, all_results }"""
    body = body or {}
    device_id = (body.get("device_id") or "").strip()
    serial_number = (body.get("serial_number") or "").strip()
    hint = (body.get("console_server") or "").strip().lower()
    if not device_id:
        raise HTTPException(status_code=400, detail="device_id required")

    is_cluster = False
    try:
        ops_path = Path(SCALER_ROOT) / "db" / "configs" / device_id / "operational.json"
        if ops_path.exists():
            ops = json.loads(ops_path.read_text())
            if ops.get("ncc_type") == "kvm":
                is_cluster = True
            if not serial_number:
                serial_number = (ops.get("serial_number") or ops.get("serial") or "").strip()
    except Exception:
        pass
    if is_cluster:
        return {"found": False, "error": "KVM cluster device -- use virsh console instead of serial console",
                "console_server": None, "port": None, "scanned": 0, "all_results": []}

    servers = _get_known_console_servers()
    if hint:
        servers = sorted(servers, key=lambda s: (0 if hint in s["name"] else 1))

    mp = Path(SCALER_ROOT) / "db" / "console_mappings.json"
    known_ports = {}
    if mp.exists():
        try:
            data = json.loads(mp.read_text())
            for sname, sinfo in data.get("console_servers", {}).items():
                known_ports[sname] = [int(p) for p in sinfo.get("ports", {}).keys()]
        except Exception:
            pass

    total_scanned = 0
    all_results = []
    for srv in servers:
        skip = known_ports.get(srv["name"], [])
        results = _probe_console_server(srv, look_for=device_id, skip_ports=skip)
        for r in results:
            r["console_server"] = srv["name"]
            r["console_host"] = srv["host"]
            total_scanned += 1
        all_results.extend(results)
        match = next((r for r in results if r["matched"]), None)
        if match:
            _save_discovered_console(device_id, serial_number, srv["name"],
                                      srv["host"], match["port"])
            return {
                "found": True,
                "console_server": srv["name"],
                "console_host": srv["host"],
                "port": match["port"],
                "scanned": total_scanned,
                "all_results": all_results,
            }

    return {"found": False, "console_server": None, "port": None,
            "scanned": total_scanned, "all_results": all_results}


@router.post("/api/ssh/pdu-power")
def pdu_power_action_endpoint(body: dict = None):
    """Power cycle / power off / power on a device via its PDU.
    Body: { serial_number?, device_id?, action: reboot|off|on|status, pdu_host?, outlet? }
    If pdu_host+outlet not given, looks up from Zohar's PDU mapping by serial."""
    body = body or {}
    action = (body.get("action") or "status").strip().lower()
    if action not in ("reboot", "off", "on", "status"):
        raise HTTPException(status_code=400, detail="action must be reboot, off, on, or status")

    pdu_host = (body.get("pdu_host") or "").strip()
    outlet = body.get("outlet")
    serial = (body.get("serial_number") or "").strip().upper()
    device_id = (body.get("device_id") or "").strip()

    if not pdu_host or outlet is None:
        if not serial and device_id:
            try:
                ops_path = Path(SCALER_ROOT) / "db" / "configs" / device_id / "operational.json"
                if ops_path.exists():
                    ops = json.loads(ops_path.read_text())
                    serial = (ops.get("serial_number") or ops.get("serial") or "").strip().upper()
            except Exception:
                pass
        if serial:
            try:
                _fetch_zohar_db()
            except Exception:
                pass
            entries = _lookup_zohar_pdu(serial)
            if entries:
                pdu_host = entries[0].get("pdu", "")
                outlet = entries[0].get("outlet")
    if not pdu_host or outlet is None:
        raise HTTPException(status_code=404, detail=f"No PDU mapping for serial={serial or 'unknown'}, device={device_id or 'unknown'}")
    try:
        outlet = int(outlet)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail=f"Invalid outlet: {outlet}")

    result = _pdu_power_action(pdu_host, outlet, action)
    if not result["success"]:
        raise HTTPException(status_code=503, detail=result.get("error", "PDU action failed"))
    return result
@router.websocket("/api/terminal/ws")
async def terminal_websocket(
    websocket: WebSocket,
    device_id: str = "",
    ssh_host: str = "",
    method: str = "ssh_mgmt",
    kvm_host: str = "",
    kvm_user: str = "",
    ncc_vms: str = "",
):
    """Interactive terminal via WebSocket. Streams stdin/stdout between browser and device.
    Query params: device_id, ssh_host, method (ssh_mgmt|virsh_console|...)
    For virsh_console: kvm_host, kvm_user, ncc_vms (comma-separated). kvm_pass sent in first message.
    """
    await websocket.accept()
    channel = None
    ssh_client = None
    import asyncio

    try:
        logging.info(f"[terminal_ws] New connection: device={device_id} host={ssh_host} method={method}")
        if method == "virsh_console":
            if not kvm_host or not kvm_user:
                await websocket.send_json({"type": "error", "message": "virsh_console requires kvm_host and kvm_user"})
                return
            ncc_list = [v.strip() for v in ncc_vms.split(",") if v.strip()]
            kvm_pass = None
            active_ncc_hint = None
            first_msg = await websocket.receive_json()
            if first_msg.get("type") == "virsh_auth":
                kvm_pass = first_msg.get("kvm_pass") or first_msg.get("password") or ""
                active_ncc_hint = first_msg.get("active_ncc") or None
            elif first_msg.get("type") == "auth":
                kvm_pass = first_msg.get("password") or ""
            if not kvm_pass:
                await websocket.send_json({"type": "error", "message": "KVM password required"})
                return
            await websocket.send_json({"type": "data", "text": "[INFO] Connecting via KVM virsh console...\r\n"})
            loop = asyncio.get_event_loop()
            ssh_client, channel, virsh_initial = await loop.run_in_executor(
                None,
                lambda: _connect_virsh_console_sync(kvm_host, kvm_user, kvm_pass, ncc_list, active_ncc_hint),
            )
            if virsh_initial:
                await websocket.send_json({"type": "data", "text": virsh_initial.decode("utf-8", errors="replace")})
        else:
            host = ssh_host
            if not host and device_id:
                try:
                    mgmt_ip, _, _ = _resolve_mgmt_ip(device_id, ssh_host)
                    host = mgmt_ip
                except Exception:
                    pass
            if not host:
                await websocket.send_json({"type": "error", "message": "Could not resolve device IP"})
                return
            user, password = _get_credentials()
            try:
                first_msg = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)
                if first_msg.get("type") == "auth":
                    if first_msg.get("user"):
                        user = first_msg["user"]
                    if first_msg.get("password"):
                        password = first_msg["password"]
            except asyncio.TimeoutError:
                logging.warning("[terminal_ws] Auth message timeout -- using default credentials")
            except Exception as auth_err:
                logging.warning(f"[terminal_ws] Auth message error: {auth_err} -- using default credentials")
            import paramiko
            pw = password

            def _ssh_connect_sync(h, u, p):
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(h, username=u, password=p, timeout=15, banner_timeout=15,
                            allow_agent=False, look_for_keys=False)
                chan = ssh.invoke_shell(width=120, height=40)
                chan.settimeout(0)
                return ssh, chan

            await websocket.send_json({"type": "data", "text": f"[INFO] Connecting to {host}...\r\n"})
            loop = asyncio.get_event_loop()
            ssh_client, channel = await loop.run_in_executor(
                None, lambda: _ssh_connect_sync(host, user, pw)
            )

            def _auto_login_if_needed(chan, u, p):
                import time as _t
                buf = b""
                for _ in range(30):
                    _t.sleep(0.2)
                    if chan.recv_ready():
                        buf += chan.recv(4096)
                    text = buf.decode("utf-8", errors="replace")
                    stripped = text.rstrip()
                    last_line = stripped.split("\n")[-1].strip().lower() if stripped else ""
                    if "#" in last_line or ">" in last_line or "dncli" in text.lower():
                        return buf
                    is_login_prompt = last_line.endswith("login:") and "last login" not in last_line
                    if is_login_prompt:
                        chan.send(u.encode() + b"\n")
                        buf = b""
                        for __ in range(20):
                            _t.sleep(0.2)
                            if chan.recv_ready():
                                buf += chan.recv(4096)
                            lo2 = buf.decode("utf-8", errors="replace").lower()
                            ll2 = lo2.rstrip().split("\n")[-1].strip() if lo2.rstrip() else ""
                            if ll2.endswith("password:") or ll2.endswith("password :"):
                                chan.send(p.encode() + b"\n")
                                return buf
                            if "#" in ll2 or ">" in ll2:
                                return buf
                        return buf
                    if last_line.endswith("password:") or last_line.endswith("password :"):
                        chan.send(p.encode() + b"\n")
                        return buf
                return buf

            initial_buf = await loop.run_in_executor(None, lambda: _auto_login_if_needed(channel, user, pw))
            if initial_buf:
                await websocket.send_json({"type": "data", "text": initial_buf.decode("utf-8", errors="replace")})

        logging.info(f"[terminal_ws] Connected: device={device_id} host={ssh_host or host} method={method}")

        async def send_output():
            idle_count = 0
            while True:
                try:
                    if channel.closed or channel.exit_status_ready():
                        try:
                            await websocket.send_json({"type": "closed", "message": "Remote session ended"})
                        except Exception:
                            pass
                        break
                    if channel.recv_ready():
                        data = channel.recv(4096)
                        if data:
                            await websocket.send_text(json.dumps({"type": "data", "text": data.decode("utf-8", errors="replace")}))
                            idle_count = 0
                        else:
                            idle_count += 1
                    else:
                        idle_count += 1
                    await asyncio.sleep(0.03)
                except Exception:
                    break

        recv_task = asyncio.create_task(send_output())

        while True:
            try:
                msg = await websocket.receive_json()
                msg_type = msg.get("type")
                if msg_type == "input" and msg.get("data"):
                    if channel and not channel.closed:
                        channel.send(msg["data"])
                elif msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
                elif msg_type == "resize":
                    cols = msg.get("cols", 120)
                    rows = msg.get("rows", 40)
                    if channel and not channel.closed:
                        try:
                            channel.resize_pty(width=cols, height=rows)
                        except Exception:
                            pass
                elif msg_type == "disconnect":
                    break
            except WebSocketDisconnect:
                break
            except Exception as e:
                if "disconnect" not in str(e).lower():
                    try:
                        await websocket.send_json({"type": "error", "message": str(e)})
                    except Exception:
                        pass
                break

        recv_task.cancel()
        try:
            await recv_task
        except (asyncio.CancelledError, Exception):
            pass

        logging.info(f"[terminal_ws] Disconnected: device={device_id}")
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        if channel:
            try:
                channel.close()
            except Exception:
                pass
        if ssh_client:
            try:
                ssh_client.close()
            except Exception:
                pass
        try:
            await websocket.close()
        except Exception:
            pass

