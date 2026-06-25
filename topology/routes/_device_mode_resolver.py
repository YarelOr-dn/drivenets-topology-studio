"""Unified device-mode resolver.

Single source of truth for "what mode is this device in right now?"
used by recovery, the upgrade auto-detect, the GUI status endpoint, the
orphan post-deploy scanner, and the in-flight poller.

Probe pipeline (per call)
-------------------------

1. **Cache hit** within ``max_age_s`` returns immediately. Callers
   wanting ground truth pass ``force=True`` (recovery, orphan scanner)
   or a small ``max_age_s`` like 3 s (GUI wizard polling).

2. **TCP probe** on port 22 (~1.5 s timeout) tells us if the SSH
   attempt has any chance of succeeding. The TCP result NEVER short-
   circuits the mode probe -- TCP-up does not imply DNOS, RECOVERY also
   listens on 22, and our caller asked for the *mode*. TCP only sets the
   per-step SSH timeout: 4 s when TCP is up (fast path), 10 s otherwise
   (give a flapping link a chance).

3. **Fast SSH classifier** opens paramiko with the tight timeout, sends
   one ``\\r\\n``, reads ≤ 1.5 s of output, and feeds it to
   ``scaler.connection_strategy.detect_device_mode`` -- the canonical
   prompt classifier already used by every other DNOS/GI/RECOVERY
   detection in the codebase. This typically returns in 2-4 s for a
   healthy device. If it returns a definitive mode + a trustworthy
   ``dnos_ver`` (when applicable), we're done.

4. **Full classifier fallback** via
   ``scaler.interactive_scale._check_single_device_status`` runs ONLY
   when the fast probe returned ``""`` / ``?``. That's the slow path
   (10-30 s) but it's the same code the wizard uses today, so we don't
   regress accuracy for ambiguous prompts.

5. **Single-flight + TTL cache** via the existing ``_live_coalescer``
   so 10 callers in the same second share one SSH session.

6. **Write-through** to ``operational.json`` via
   ``_persist_live_status_to_ops`` on every fresh probe -- GUI badge,
   monitor, stack-dialog all see the new value immediately.

7. **Event publish** of ``device_mode_changed`` to per-device watchers
   on transitions, so logged-in tabs update sub-second.

Consistency policy: **live wins**. SSH classification overwrites the
cache regardless of prior value. The one carve-out is a phantom-DNOS
guard: if mode==DNOS but no trustworthy ``dnos_ver`` (``-`` / ``?`` /
empty), we treat the result as ``?`` so we never write garbage from a
prompt-classifier false positive.

In-flight poller
----------------

A daemon thread (``start_inflight_poller``) ticks every
``INFLIGHT_POLL_INTERVAL_S`` (default 45 s) and refreshes any device
with ``upgrade_in_progress`` / ``_delete_pending`` / ``deploy_initiated``
/ ``install_status`` in flight. Steady-state devices are NOT polled
here -- that stays the 5-min monitor's job.
"""
from __future__ import annotations

import json
import logging
import os
import re
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from routes._live_coalescer import LiveCoalescer
from routes._ops_writer import read_ops as _read_ops_safe
from routes._ops_writer import update_ops as _update_ops_safe

logger = logging.getLogger(__name__)


_TCP_PROBE_TIMEOUT_S = float(os.environ.get("TP_DEVICE_MODE_TCP_TIMEOUT_S", "1.5"))
_FAST_SSH_TIMEOUT_S = float(os.environ.get("TP_DEVICE_MODE_FAST_SSH_TIMEOUT_S", "4.0"))
_SLOW_SSH_TIMEOUT_S = float(os.environ.get("TP_DEVICE_MODE_SLOW_SSH_TIMEOUT_S", "10.0"))
_PROMPT_READ_S = float(os.environ.get("TP_DEVICE_MODE_PROMPT_READ_S", "1.5"))
_DEFAULT_MAX_AGE_S = float(os.environ.get("TP_DEVICE_MODE_MAX_AGE_S", "30"))
INFLIGHT_POLL_INTERVAL_S = float(os.environ.get("TP_DEVICE_MODE_INFLIGHT_POLL_S", "45"))
_INFLIGHT_SCAN_BACKOFF_S = float(os.environ.get("TP_DEVICE_MODE_INFLIGHT_BACKOFF_S", "10"))
_PARALLEL_MAX_WORKERS = int(os.environ.get("TP_DEVICE_MODE_PARALLEL_WORKERS", "8"))

# Layered monitoring (Wave: continuous reliability):
#   * IN-FLIGHT poller -- 45 s, only devices currently upgrading/deleting/
#     deploying. Tightest because the GUI wizard polls these.
#   * WATCHER poller -- 15 s, devices with at least one active WebSocket
#     watcher (a user has the device's status panel / wizard open).
#     Covers idle-but-being-looked-at devices without the cost of
#     probing every device every cycle.
#   * GLOBAL poller -- 300 s (5 min), every device with an
#     operational.json. Safety net for lab-side changes (someone
#     reboots into RECOVERY, DHCP reassigns IP) when nobody is
#     watching. Skips ``_stale``-flagged records (the ghost-IP
#     reaper already disowned those) and skips devices already
#     covered by the tighter pollers in this iteration.
WATCHER_POLL_INTERVAL_S = float(os.environ.get("TP_DEVICE_MODE_WATCHER_POLL_S", "15"))
GLOBAL_POLL_INTERVAL_S = float(os.environ.get("TP_DEVICE_MODE_GLOBAL_POLL_S", "300"))
_GLOBAL_POLL_BATCH_SIZE = int(os.environ.get("TP_DEVICE_MODE_GLOBAL_POLL_BATCH", "8"))

_RESOLVER_CACHE = LiveCoalescer(
    ttl_seconds=_DEFAULT_MAX_AGE_S,
    max_wait_seconds=60.0,
    max_entries=512,
)

# Drift counters: every time the live probe disagrees with the cached
# mode in operational.json, we tick this. Exposed via ``snapshot()``
# so ops can grep "[devmode] DRIFT" or curl the health endpoint.
_DRIFT_LOCK = threading.Lock()
_DRIFT_STATS: Dict[str, Any] = {
    "total": 0,
    "last_at": 0.0,
    "last_device": "",
    "last_before": "",
    "last_after": "",
}

_STRIP_MARKUP = re.compile(r"\[/?[^\]]+\]")
_VALID_MODES = ("GI", "DNOS", "RECOVERY", "BASEOS_SHELL", "ONIE")
_TRUSTWORTHY_VER_RE = re.compile(r"^\d+\.\d+\.\d+\.\d+")
_DNOS_VER_RE = re.compile(r"DNOS\s+version\s*[:\s]\s*(\d+\.\d+\.\d+\.\d+)", re.IGNORECASE)
# Capture the hostname token from a DNOS / GI prompt:
#   ``hostname#``                       -> DNOS exec
#   ``hostname(config)#``               -> DNOS config
#   ``[fgi(hostname)]``                 -> fGI cluster
#   ``dn@hostname:~$`` / ``root@hostname:~$`` -> GI shell
_PROMPT_HOSTNAME_RES = (
    re.compile(r"\b([A-Za-z][A-Za-z0-9._\-]{1,63})\s*\(.*?\)\s*#"),
    re.compile(r"\b([A-Za-z][A-Za-z0-9._\-]{1,63})\s*#"),
    re.compile(r"\[f?gi\(([A-Za-z0-9._\-]{1,63})\)"),
    re.compile(r"(?:dn|root)@([A-Za-z0-9._\-]{1,63}):"),
)


def _now() -> float:
    return time.time()


def _is_trustworthy_dnos_ver(ver: str) -> bool:
    if not ver:
        return False
    s = str(ver).strip()
    if s in ("-", "?", ""):
        return False
    return bool(_TRUSTWORTHY_VER_RE.match(s))


def _strip_cidr(host: str) -> str:
    """Operational.json stores ``mgmt_ip`` with a CIDR suffix
    (e.g. ``100.64.4.200/20``). Paramiko + raw sockets need just the
    address, so peel the suffix before passing it down. Also tolerate
    incidental whitespace.
    """
    if not host:
        return ""
    s = str(host).strip()
    if "/" in s:
        s = s.split("/", 1)[0].strip()
    return s


# ----------------------------------------------------------- cluster awareness
#
# Cluster (KVM/NCC) devices have *two* possible SSH targets behind a single
# logical ``mgmt_ip``: ``ncc0`` and ``ncc1``. Only one is the *active* CLI at
# any given moment; the other typically sits in BaseOS shell (or has no useful
# CLI at all in GI mode). The fast-path SSH classifier in this resolver was
# device-agnostic before this helper landed: it would happily SSH to whichever
# NCC answered port 22 first and classify whatever prompt came back -- which
# meant we frequently committed BASEOS_SHELL to ``operational.json`` for a
# perfectly healthy DNOS cluster, just because the standby NCC's baseos
# answered the connection a few ms before the active NCC did.
#
# The cure is a cheap pre-probe that asks the KVM hypervisor (one paramiko
# session, ~1-2 s, no per-NCC SSH attempts) which VM currently owns the VIP.
# We trust the existing helper ``_probe_active_ncc_via_kvm`` in
# ``routes.bridge_helpers`` -- it walks ``virsh list / domifaddr / arp`` in
# that order and is the canonical answer used by the upgrade-wizard, the
# console fallback, and the discovery API.
#
# What we do with the answer:
#   1. If the probe tells us a different active NCC than ``ops.active_ncc_vm``,
#      we atomically rewrite the file (via ``update_ops`` so scaler's racing
#      raw ``json.dump`` cannot lose other keys) with
#      ``active_ncc_source=kvm_virsh_probe`` -- the highest-trust source.
#   2. We return the resolved (mgmt_ip, ssh_host_hint) so the rest of the
#      resolver pipeline aims at the right NCC. For most clusters
#      ``ncc_mgmt_ip`` is the active VIP regardless of which physical NCC
#      currently owns it, so the SSH target IP is unchanged -- but we DO
#      need the per-NCC hostname to expose it on the GUI badge.
#
# This function NEVER raises and is bounded to ~3 s wall time (tcp connect +
# a couple of small ``virsh`` commands). On any failure we return ``None``
# and the caller falls through to the legacy single-target flow, so a
# transient KVM outage cannot hold up monitoring.
def _cluster_preprobe(scaler_hostname: str, op_data: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """Re-validate the active NCC for a cluster device before SSH classify.

    Returns ``None`` for non-cluster devices, for clusters with no
    ``kvm_host`` configured, and for any error path. Returns a small
    dict ``{vm, source, mgmt_ip}`` on success.
    """
    if not isinstance(op_data, dict):
        return None
    is_cluster = bool(op_data.get("is_cluster"))
    ncc_type = (op_data.get("ncc_type") or "").lower()
    if not (is_cluster or ncc_type == "kvm"):
        return None
    ncc_vms = op_data.get("ncc_vms") or []
    if not isinstance(ncc_vms, list) or len(ncc_vms) < 1:
        return None
    kvm_host = (
        op_data.get("kvm_host_ip")
        or op_data.get("kvm_host")
        or ""
    )
    if not kvm_host:
        return None
    creds = op_data.get("kvm_host_credentials") or {}
    kvm_user = (creds.get("username") or "dn").strip() or "dn"
    kvm_pass = (creds.get("password") or "drive1234!")
    ncc_mgmt_ip = _strip_cidr(op_data.get("ncc_mgmt_ip") or op_data.get("mgmt_ip") or "")
    try:
        from routes.bridge_helpers import _probe_active_ncc_via_kvm
    except Exception as exc:
        logger.debug("[devmode] cluster preprobe import failed: %s", exc)
        return None
    try:
        probe = _probe_active_ncc_via_kvm(
            kvm_host=kvm_host,
            kvm_user=kvm_user,
            kvm_pass=kvm_pass,
            ncc_vms=ncc_vms,
            ncc_mgmt_ip=ncc_mgmt_ip,
            timeout_s=3.0,
        ) or {}
    except Exception as exc:
        logger.debug("[devmode] cluster preprobe SSH to %s failed: %s",
                     kvm_host, exc)
        return None
    active_vm = (probe.get("active_ncc_host") or "").strip()
    src = (probe.get("source") or "").strip()
    # Only trust authoritative sources: explicit VIP / MAC matches, and the
    # "exactly one running VM" case. The "first_running" fallback is a
    # last-resort guess and we'd rather leave the file alone than commit it
    # as if it were a real probe.
    trusted = src in ("kvm_domifaddr_match", "kvm_arp_mac_match", "kvm_only_running")
    if not active_vm or active_vm not in ncc_vms or not trusted:
        # GI-mode fallback: the cheap KVM probe is inconclusive whenever
        # neither NCC owns the VIP yet (DHCP / pre-deploy / clean install).
        # In that state the only authoritative answer is the virsh-console
        # probe, which opens a console to each NCC and only accepts the one
        # that returns a CLI prompt. Slow (~10-20 s) but accurate. We run it
        # at most once per cluster per resolver call -- piggybacked on the
        # poller's existing ~5 min cadence so the cost is negligible.
        try:
            from routes.bridge_helpers import _fetch_ops_via_virsh_fallback
            from routes.upgrade import _get_credentials as _gc
            _user, _pw = _gc()
            virsh_result = _fetch_ops_via_virsh_fallback(
                scaler_hostname, _user or "dnroot", _pw or "dnroot",
            )
        except Exception as exc:
            logger.debug(
                "[devmode] cluster preprobe console fallback failed: %s", exc,
            )
            return None
        # _fetch_ops_via_virsh_fallback persists the active_ncc_vm itself
        # via update_ops with source=kvm_virsh_probe (see bridge_helpers.py
        # ~line 1893), so we just need to re-read the file to surface the
        # post-probe value back to the caller.
        if not isinstance(virsh_result, dict) or not virsh_result.get("stack"):
            return None
        try:
            sc_root = os.environ.get("SCALER_ROOT", "/home/dn/SCALER")
            op_path = (
                Path(sc_root) / "db" / "configs" / scaler_hostname
                / "operational.json"
            )
            fresh = _read_ops_safe(op_path)
            active_vm = (fresh.get("active_ncc_vm") or "").strip()
            src = (fresh.get("active_ncc_source") or "").strip()
        except Exception:
            return None
        if not active_vm or active_vm not in ncc_vms:
            return None
        return {"vm": active_vm, "source": src or "kvm_virsh_probe",
                "mgmt_ip": ncc_mgmt_ip}
    stored_vm = (op_data.get("active_ncc_vm") or "").strip()
    stored_src = (op_data.get("active_ncc_source") or "").strip()
    if active_vm != stored_vm or stored_src != "kvm_virsh_probe":
        sc_root = os.environ.get("SCALER_ROOT", "/home/dn/SCALER")
        op_path = (
            Path(sc_root) / "db" / "configs" / scaler_hostname / "operational.json"
        )

        def _mut(d, _vm=active_vm, _src="kvm_virsh_probe"):
            d["active_ncc_vm"] = _vm
            d["active_ncc_source"] = _src

        try:
            _update_ops_safe(op_path, _mut, create_if_missing=False)
            logger.info(
                "[devmode] cluster preprobe: %s active_ncc_vm %r->%r "
                "(via kvm %s, source=%s)",
                scaler_hostname, stored_vm or "(none)", active_vm,
                kvm_host, src,
            )
        except Exception as exc:
            logger.debug(
                "[devmode] cluster preprobe persist failed for %s: %s",
                scaler_hostname, exc,
            )
    return {
        "vm": active_vm,
        "source": src,
        "mgmt_ip": ncc_mgmt_ip,
    }


def _tcp_reachable(host: str, port: int = 22, timeout: float = _TCP_PROBE_TIMEOUT_S) -> bool:
    host = _strip_cidr(host)
    if not host:
        return False
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, socket.timeout, Exception):
        return False


def _strip_markup_dict(raw: Any) -> Dict[str, str]:
    if not isinstance(raw, dict):
        return {}
    return {
        k: _STRIP_MARKUP.sub("", str(v)).strip()
        for k, v in raw.items()
    }


def _extract_prompt_hostname(buf: str) -> str:
    """Pull the device's self-reported hostname out of an SSH prompt grab."""
    if not buf:
        return ""
    tail = buf[-2000:]
    for rx in _PROMPT_HOSTNAME_RES:
        m = rx.search(tail)
        if m:
            return m.group(1).strip()
    return ""


def _hostname_matches(expected: str, actual: str) -> bool:
    """Loose hostname match: case-insensitive, ignore ``YOR_CL_`` / cluster
    prefixes that scaler synthesizes, and treat partial substring matches
    (e.g. ``PE-1`` inside ``YOR_PE-1``) as the same device.
    """
    if not expected or not actual:
        return False
    a = expected.strip().upper()
    b = actual.strip().upper()
    if a == b:
        return True
    for prefix in ("YOR_CL_", "YOR_", "CL_"):
        if a.startswith(prefix):
            a = a[len(prefix):]
        if b.startswith(prefix):
            b = b[len(prefix):]
    if a == b:
        return True
    if a in b or b in a:
        return True
    return False


def _normalize_status(status: Dict[str, str]) -> Dict[str, str]:
    """Canonicalize an incoming status dict.

    Live wins: whatever ``detect_device_mode`` (or the slow scaler
    classifier) returned is the truth. The downstream
    ``_persist_live_status_to_ops`` has its own narrowly-scoped phantom-
    DNOS guard that fires only when prior cached state is GI/BASEOS_SHELL/
    DEPLOYING and no trustworthy version is present -- that's the right
    place to refuse a write, not the resolver. We only normalize the
    mode string here so callers always see uppercase canonical values.
    """
    out = dict(status or {})
    mode = (out.get("mode") or "").strip().upper()
    if mode in _VALID_MODES:
        out["mode"] = mode
    elif mode:
        out["mode"] = "?"
    return out


# --------------------------------------------------------------- SSH probes

def _fast_ssh_classify(host: str, user: str, password: str,
                       connect_timeout: float,
                       expected_hostname: str = "") -> Dict[str, str]:
    """Tight-timeout paramiko classifier: prompt grab + detect_device_mode.

    Returns a dict with at least ``mode``. ``dnos_ver`` is best-effort
    (may stay ``-`` if the prompt didn't include a version banner). On
    any error we return ``{}`` so the caller falls back to the full
    classifier.

    When ``expected_hostname`` is provided, the prompt's self-reported
    hostname is checked against it. On mismatch we return
    ``{"_ghost_ip": "1", "actual_hostname": <seen>}`` -- this signals
    the caller to invoke scaler's ``connect_for_upgrade`` slow path,
    which performs a proper ghost-IP reap via
    ``_mark_device_ip_stale`` and forces re-discovery of the new IP.
    """
    host = _strip_cidr(host)
    if not host or not user:
        return {}
    try:
        import paramiko
    except Exception:
        return {}

    ssh = None
    chan = None
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(
                host,
                username=user,
                password=password,
                timeout=connect_timeout,
                banner_timeout=connect_timeout,
                auth_timeout=connect_timeout,
                allow_agent=False,
                look_for_keys=False,
            )
        except Exception as exc:
            logger.debug("[devmode] fast paramiko connect %s failed: %s", host, exc)
            return {}

        chan = ssh.invoke_shell()
        chan.settimeout(_PROMPT_READ_S)
        try:
            chan.send("\r\n")
        except Exception:
            return {}

        deadline = _now() + _PROMPT_READ_S
        buf = ""
        while _now() < deadline:
            if not chan.recv_ready():
                time.sleep(0.05)
                continue
            try:
                chunk = chan.recv(8192).decode(errors="ignore")
            except Exception:
                break
            if not chunk:
                break
            buf += chunk
            if any(tok in buf for tok in ("#", "$", ">", "login:", "password:")):
                if len(buf) > 64:
                    break

        actual_host = _extract_prompt_hostname(buf)
        if expected_hostname and actual_host and not _hostname_matches(
                expected_hostname, actual_host):
            logger.warning(
                "[devmode] ghost-IP detected for %s @ %s -- prompt reports "
                "hostname %r; falling through to slow path for reap+rediscover",
                expected_hostname, host, actual_host,
            )
            return {
                "_ghost_ip": "1",
                "actual_hostname": actual_host,
            }

        try:
            from scaler.connection_strategy import detect_device_mode
            mode = detect_device_mode(buf) or ""
        except Exception:
            mode = ""

        dnos_ver = "-"
        m = _DNOS_VER_RE.search(buf)
        if m:
            dnos_ver = m.group(1)

        if not mode:
            return {}

        return {
            "mode": mode,
            "dnos_ver": dnos_ver,
            "gi_ver": "-",
            "baseos_ver": "-",
            "install_status": "",
            "_fast": "1",
            "actual_hostname": actual_host,
        }
    finally:
        for closer in (chan, ssh):
            try:
                if closer is not None:
                    closer.close()
            except Exception:
                pass


def _full_ssh_classify(scaler_hostname: str, scaler_root: str) -> Dict[str, str]:
    """Slow but authoritative classifier from scaler.interactive_scale.

    Used as a fallback when the fast probe returns ``?``.
    """
    cwd = os.getcwd()
    try:
        try:
            os.chdir(scaler_root)
        except Exception:
            pass
        from scaler.interactive_scale import _check_single_device_status

        class _Dev:
            hostname = scaler_hostname

        raw = _check_single_device_status(_Dev())
        return _strip_markup_dict(raw)
    finally:
        try:
            os.chdir(cwd)
        except Exception:
            pass


# --------------------------------------------------------------- ops + events

def _read_op_data(scaler_hostname: str, scaler_root: str) -> Dict[str, Any]:
    if not scaler_hostname:
        return {}
    op_path = Path(scaler_root) / "db" / "configs" / scaler_hostname / "operational.json"
    if not op_path.exists():
        return {}
    try:
        return _read_ops_safe(op_path)
    except Exception:
        return {}


def _publish_mode_change(device_id: str, before_mode: str, after_mode: str,
                         status: Dict[str, str]) -> None:
    if before_mode == after_mode:
        return
    try:
        from api.event_bus import event_bus
        event_bus.publish_to_device_watchers_sync(
            device_id=device_id,
            event_type="device_mode_changed",
            payload={
                "before": before_mode or "?",
                "after": after_mode or "?",
                "dnos_ver": status.get("dnos_ver") or "",
                "gi_ver": status.get("gi_ver") or "",
                "baseos_ver": status.get("baseos_ver") or "",
                "install_status": status.get("install_status") or "",
                "source": "device_mode_resolver",
            },
        )
    except Exception:
        pass


def _resolver_key(device_id: str, scaler_hostname: str) -> str:
    return f"devmode:{scaler_hostname or device_id}"


# --------------------------------------------------------------- public API


def get_device_mode(
    device_id: str,
    scaler_hostname: Optional[str] = None,
    *,
    max_age_s: Optional[float] = None,
    force: bool = False,
    fast_only: bool = False,
    scaler_root: Optional[str] = None,
    persist: bool = True,
    publish: bool = True,
    mgmt_ip: Optional[str] = None,
) -> Dict[str, Any]:
    """Resolve the current device mode -- fast and live-verified.

    Args:
      device_id: caller's device id.
      scaler_hostname: canonical hostname (config dir name).
      max_age_s: cache TTL for cached hits. Default 30 s.
      force: skip cache, always re-probe.
      fast_only: stop after the fast SSH classifier; never invoke the
        slow scaler classifier. The orphan scanner uses this to avoid
        burning 30 s per skipped device.
      scaler_root: SCALER root for the slow fallback classifier.
      persist: write the result back into ``operational.json``.
      publish: publish a ``device_mode_changed`` event on transitions.
      mgmt_ip: override mgmt_ip resolution (e.g. when the caller already
        resolved it). Otherwise we read it from operational.json.

    Returns dict::

        {mode, dnos_ver, gi_ver, baseos_ver, install_status,
         source, age_s, reachable, scaler_hostname, mgmt_ip,
         tcp_up, fast_path}
    """
    scaler_hostname = scaler_hostname or device_id
    if max_age_s is None:
        max_age_s = _DEFAULT_MAX_AGE_S
    sc_root = scaler_root or os.environ.get("SCALER_ROOT", "/home/dn/SCALER")

    if force:
        _RESOLVER_CACHE.invalidate(_resolver_key(device_id, scaler_hostname))

    op_before = _read_op_data(scaler_hostname, sc_root)
    before_mode = (op_before.get("device_state") or "").upper()

    # mgmt_ip resolution chain (always live-aware, not just cache):
    #   1. caller override (kept verbatim, only CIDR-stripped)
    #   2. routes.bridge_helpers._resolve_mgmt_ip -- the canonical
    #      resolver that walks scaler ops index -> discovery API ->
    #      device_inventory -> stale-IP last-resort. Honors
    #      ``_safe_set_mgmt_ip`` guards and the ghost-IP reaper. 120s
    #      internal cache so this call is cheap; explicit invalidation
    #      hooks below force a re-walk after deletes/upgrades.
    #   3. operational.json fallback (legacy path)
    mgmt_ip_resolved_via = "caller_override"
    if not mgmt_ip:
        try:
            from routes.bridge_helpers import _resolve_mgmt_ip
            ssh_hint = op_before.get("ssh_host") or op_before.get("mgmt_ip") or ""
            resolved_ip, _scaler_id, resolved_via = _resolve_mgmt_ip(
                device_id, ssh_hint,
            )
            if resolved_ip:
                mgmt_ip = resolved_ip
                mgmt_ip_resolved_via = resolved_via or "_resolve_mgmt_ip"
        except Exception as exc:
            logger.debug(
                "[devmode] _resolve_mgmt_ip failed for %s (%s); "
                "falling back to operational.json",
                device_id, exc,
            )
            mgmt_ip = op_before.get("mgmt_ip") or op_before.get("ssh_host") or ""
            mgmt_ip_resolved_via = "ops_json_fallback"
    mgmt_ip = _strip_cidr(mgmt_ip)

    started = _now()

    def _do_probe() -> Dict[str, Any]:
        tcp_up = _tcp_reachable(mgmt_ip) if mgmt_ip else False
        ssh_timeout = _FAST_SSH_TIMEOUT_S if tcp_up else _SLOW_SSH_TIMEOUT_S

        try:
            from routes.upgrade import _get_credentials
            user, password = _get_credentials()
        except Exception:
            user, password = "", ""

        # Cluster pre-probe (NCC active-VM re-validation). Cheap (one
        # paramiko session to the KVM host, ~1-2 s); only runs for
        # ``is_cluster``/``ncc_type=kvm`` devices. If the active NCC has
        # changed since the on-disk snapshot (cluster failover, manual
        # role swap, scaler-side raw write that lost the field), this
        # rewrites ``active_ncc_vm`` + ``active_ncc_source=kvm_virsh_probe``
        # atomically via ``update_ops`` BEFORE the fast SSH classifier
        # runs. Without this, the classifier could SSH to the standby NCC
        # in baseos and incorrectly flag the device as BASEOS_SHELL.
        #
        # We don't gate the rest of the probe on the result -- a KVM host
        # outage must NOT make us stop monitoring the cluster. The
        # function returns None on any error and we fall straight through.
        try:
            _cluster_preprobe(scaler_hostname, op_before)
        except Exception as exc:
            logger.debug(
                "[devmode] cluster preprobe wrapper crashed for %s: %s",
                scaler_hostname, exc,
            )

        # Fast path: paramiko + prompt classifier.
        # ``scaler_hostname`` is the canonical device id (e.g. ``YOR_PE-1``);
        # we pass it as ``expected_hostname`` so the fast probe can detect
        # ghost-IP landings (prompt's hostname != expected -> fall through
        # to the slow path which reaps + re-discovers via scaler).
        fast_result: Dict[str, str] = {}
        if mgmt_ip and user:
            fast_result = _fast_ssh_classify(
                mgmt_ip, user, password,
                connect_timeout=ssh_timeout,
                expected_hostname=scaler_hostname,
            ) or {}

        if fast_result.get("_ghost_ip") == "1":
            # Ghost-IP detected. Mark the IP stale through the canonical
            # reaper so every subsequent _resolve_mgmt_ip() call ignores
            # it, then fall through to the slow path which will perform
            # ``connect_for_upgrade`` -- the only code that knows how to
            # rediscover the device's new address.
            try:
                from routes.bridge_helpers import _mark_device_ip_stale
                _mark_device_ip_stale(
                    scaler_hostname,
                    stale_ip=mgmt_ip,
                    reason="ghost_ip_fast_probe",
                    actual_hostname=fast_result.get("actual_hostname", ""),
                    acting_user="device_mode_resolver",
                    broadcast=True,
                )
            except Exception as exc:
                logger.debug(
                    "[devmode] _mark_device_ip_stale(%s) failed: %s",
                    scaler_hostname, exc,
                )
            # Drop our own resolver cache + the bridge_helpers resolve
            # cache for this device so the next call re-walks the
            # discovery chain with the new IP.
            try:
                _RESOLVER_CACHE.invalidate(
                    _resolver_key(device_id, scaler_hostname),
                )
            except Exception:
                pass
            try:
                from routes.bridge_helpers import _invalidate_scaler_ops_cache
                _invalidate_scaler_ops_cache()
            except Exception:
                pass
            # NOTE: do not return -- fall through so the slow
            # _full_ssh_classify path runs ``_check_single_device_status``
            # which calls ``connect_for_upgrade`` and gives us the live
            # mode at the rediscovered address in the same probe cycle.

        elif fast_result.get("mode"):
            normalized = _normalize_status(fast_result)
            if normalized.get("mode") in _VALID_MODES:
                normalized.setdefault("_tcp_up", "1" if tcp_up else "0")
                return normalized

        if fast_only:
            return {
                "mode": fast_result.get("mode") or "?",
                "dnos_ver": fast_result.get("dnos_ver") or "-",
                "gi_ver": "-",
                "baseos_ver": "-",
                "install_status": "",
                "_tcp_up": "1" if tcp_up else "0",
                "_fast_only": "1",
            }

        # Slow fallback: full scaler classifier (handles console/virsh,
        # disambiguates RECOVERY shells, fills in versions).
        try:
            full = _full_ssh_classify(scaler_hostname, sc_root)
        except Exception as exc:
            logger.debug("[devmode] slow classify %s failed: %s", scaler_hostname, exc)
            full = {}
        if not full:
            return {"mode": "?", "_tcp_up": "1" if tcp_up else "0"}
        return _normalize_status(full)

    try:
        value, origin = _RESOLVER_CACHE.get(
            _resolver_key(device_id, scaler_hostname),
            _do_probe,
            ttl_seconds=max_age_s,
        )
    except Exception as exc:
        logger.warning("[devmode] resolver fetch failed for %s: %s", scaler_hostname, exc)
        return {
            "mode": "?",
            "dnos_ver": op_before.get("dnos_version") or "-",
            "gi_ver": op_before.get("gi_version") or "-",
            "baseos_ver": op_before.get("baseos_version") or "-",
            "install_status": op_before.get("install_status") or "",
            "source": "ssh_error",
            "age_s": _now() - started,
            "reachable": False,
            "scaler_hostname": scaler_hostname,
            "mgmt_ip": mgmt_ip,
            "tcp_up": False,
            "fast_path": False,
        }

    elapsed = _now() - started
    after_mode = (value.get("mode") or "?").upper()
    fast_path = bool(value.get("_fast"))
    tcp_up = value.get("_tcp_up") == "1"

    # Merge cached versions when the live probe didn't return one. The
    # fast path only grabs versions opportunistically (DNOS often does
    # not print the version in the prompt banner), so we top up from
    # operational.json so the GUI still shows accurate info. This does
    # NOT influence mode -- only the displayed version strings.
    def _pick(key_live: str, key_cached: str, default: str = "-") -> str:
        live = (value.get(key_live) or "").strip()
        if live and live not in ("-", "?", ""):
            return live
        cached = (op_before.get(key_cached) or "").strip()
        return cached or default

    dnos_ver = _pick("dnos_ver", "dnos_version")
    gi_ver = _pick("gi_ver", "gi_version")
    baseos_ver = _pick("baseos_ver", "baseos_version")

    # Silent-drift detection: the cached mode in operational.json
    # disagrees with the live probe. Auto-correct by writing through
    # and publish a ``device_mode_changed`` event so every watcher
    # sees it within the next WebSocket flush. The counter is exposed
    # via ``snapshot()`` for ops visibility.
    if origin == "fresh" and before_mode and after_mode in _VALID_MODES \
            and before_mode != after_mode:
        with _DRIFT_LOCK:
            _DRIFT_STATS["total"] += 1
            _DRIFT_STATS["last_at"] = _now()
            _DRIFT_STATS["last_device"] = scaler_hostname
            _DRIFT_STATS["last_before"] = before_mode
            _DRIFT_STATS["last_after"] = after_mode
        logger.info(
            "[devmode] DRIFT corrected for %s: ops=%s -> live=%s "
            "(probe took %.2fs, mgmt_ip=%s via %s)",
            scaler_hostname, before_mode, after_mode, elapsed,
            mgmt_ip, mgmt_ip_resolved_via,
        )

    if persist and origin == "fresh" and after_mode in _VALID_MODES:
        try:
            from routes.upgrade import _persist_live_status_to_ops
            _persist_live_status_to_ops(device_id, scaler_hostname, value)
        except Exception as exc:
            logger.debug("[devmode] persist failed for %s: %s", scaler_hostname, exc)

    if publish and origin == "fresh":
        _publish_mode_change(device_id, before_mode, after_mode, value)

    return {
        "mode": after_mode,
        "dnos_ver": dnos_ver,
        "gi_ver": gi_ver,
        "baseos_ver": baseos_ver,
        "install_status": value.get("install_status") or "",
        "source": origin,
        "age_s": elapsed,
        "reachable": after_mode in _VALID_MODES,
        "scaler_hostname": scaler_hostname,
        "mgmt_ip": mgmt_ip,
        "tcp_up": tcp_up,
        "fast_path": fast_path,
    }


def get_device_modes_parallel(
    devices: Iterable[Tuple[str, Optional[str]]],
    *,
    max_age_s: Optional[float] = None,
    force: bool = False,
    fast_only: bool = False,
    persist: bool = True,
    publish: bool = True,
    max_workers: int = _PARALLEL_MAX_WORKERS,
) -> Dict[str, Dict[str, Any]]:
    """Fan out ``get_device_mode`` over many devices in parallel.

    ``devices`` is an iterable of ``(device_id, scaler_hostname)``;
    ``scaler_hostname`` may be ``None`` to fall back to ``device_id``.
    """
    pairs: List[Tuple[str, str]] = [
        (d, h or d) for d, h in devices if d
    ]
    if not pairs:
        return {}
    workers = max(1, min(max_workers, len(pairs)))
    out: Dict[str, Dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(
                get_device_mode, did, host,
                max_age_s=max_age_s, force=force,
                fast_only=fast_only, persist=persist, publish=publish,
            ): did
            for did, host in pairs
        }
        for fut in as_completed(futures):
            did = futures[fut]
            try:
                out[did] = fut.result()
            except Exception as exc:
                out[did] = {
                    "mode": "?", "source": "exception",
                    "reachable": False, "scaler_hostname": did,
                    "error": str(exc),
                }
    return out


def invalidate(device_id: str, scaler_hostname: Optional[str] = None) -> None:
    _RESOLVER_CACHE.invalidate(_resolver_key(device_id, scaler_hostname or device_id))


def invalidate_by_mgmt_ip(stale_ip: str) -> int:
    """Flush every cached entry that *might* be tied to ``stale_ip``.

    Cache keys don't include mgmt_ip (it's stored in the value), and
    ``LiveCoalescer.snapshot()`` is metadata-only -- it doesn't expose
    the values. Since the resolver TTL is short (30 s default) and the
    expected entry count is tiny (one per active device), the cheapest
    correct behavior is to flush the whole resolver cache. Subsequent
    probes will re-walk discovery, which is exactly what the caller
    wants after a ghost-IP reap.
    """
    if not stale_ip:
        return 0
    try:
        dropped = _RESOLVER_CACHE.invalidate_matching(lambda _k: True)
    except Exception:
        return 0
    if dropped:
        logger.info(
            "[devmode] invalidate_by_mgmt_ip(%s): flushed %d entries",
            _strip_cidr(stale_ip), dropped,
        )
    return dropped


def snapshot() -> Dict[str, Any]:
    snap = _RESOLVER_CACHE.snapshot()
    with _DRIFT_LOCK:
        snap["drift"] = dict(_DRIFT_STATS)
    snap["pollers"] = {
        "inflight_running": bool(
            _INFLIGHT_THREAD is not None and _INFLIGHT_THREAD.is_alive()
        ),
        "inflight_interval_s": INFLIGHT_POLL_INTERVAL_S,
        "watcher_running": bool(
            _WATCHER_THREAD is not None and _WATCHER_THREAD.is_alive()
        ),
        "watcher_interval_s": WATCHER_POLL_INTERVAL_S,
        "global_running": bool(
            _GLOBAL_THREAD is not None and _GLOBAL_THREAD.is_alive()
        ),
        "global_interval_s": GLOBAL_POLL_INTERVAL_S,
    }
    return snap


# --------------------------------------------------------------- in-flight poll

_INFLIGHT_THREAD_LOCK = threading.Lock()
_INFLIGHT_THREAD: Optional[threading.Thread] = None
_INFLIGHT_STOP = threading.Event()


def _list_inflight_devices(scaler_root: str) -> Iterable[Tuple[str, Dict[str, Any]]]:
    configs_root = Path(scaler_root) / "db" / "configs"
    if not configs_root.exists():
        return
    for device_dir in configs_root.iterdir():
        if not device_dir.is_dir():
            continue
        op_path = device_dir / "operational.json"
        if not op_path.exists():
            continue
        try:
            data = _read_ops_safe(op_path)
        except Exception:
            continue
        if (
            data.get("upgrade_in_progress")
            or data.get("_delete_pending")
            or data.get("deploy_initiated")
            or data.get("install_status") in ("IN_PROGRESS", "DEPLOYING")
        ):
            yield device_dir.name, data


def _inflight_poll_loop() -> None:
    sc_root = os.environ.get("SCALER_ROOT", "/home/dn/SCALER")
    logger.info("[devmode] in-flight poller started (interval=%ss)", INFLIGHT_POLL_INTERVAL_S)
    while not _INFLIGHT_STOP.is_set():
        try:
            targets = list(_list_inflight_devices(sc_root))
            if targets:
                modes = get_device_modes_parallel(
                    [(name, name) for name, _data in targets],
                    max_age_s=0, force=False,
                )
                logger.debug(
                    "[devmode] in-flight poll refreshed %d device(s): %s",
                    len(modes),
                    {k: v.get("mode") for k, v in modes.items()},
                )
        except Exception as exc:
            logger.warning("[devmode] in-flight poll iteration crashed: %s", exc)
            _INFLIGHT_STOP.wait(_INFLIGHT_SCAN_BACKOFF_S)
            continue
        _INFLIGHT_STOP.wait(INFLIGHT_POLL_INTERVAL_S)


def start_inflight_poller() -> None:
    global _INFLIGHT_THREAD
    with _INFLIGHT_THREAD_LOCK:
        if _INFLIGHT_THREAD is not None and _INFLIGHT_THREAD.is_alive():
            return
        _INFLIGHT_STOP.clear()
        _INFLIGHT_THREAD = threading.Thread(
            target=_inflight_poll_loop,
            name="devmode-inflight-poller",
            daemon=True,
        )
        _INFLIGHT_THREAD.start()


def stop_inflight_poller(timeout: float = 5.0) -> None:
    global _INFLIGHT_THREAD
    with _INFLIGHT_THREAD_LOCK:
        if _INFLIGHT_THREAD is None:
            return
        _INFLIGHT_STOP.set()
        _INFLIGHT_THREAD.join(timeout=timeout)
        _INFLIGHT_THREAD = None


# --------------------------------------------------------------- watcher poll

_WATCHER_THREAD_LOCK = threading.Lock()
_WATCHER_THREAD: Optional[threading.Thread] = None
_WATCHER_STOP = threading.Event()


def _list_watched_devices() -> List[str]:
    """Return distinct device_ids that have at least one active watcher
    across ALL users. Falls back to an empty list if the device-state
    DB is unavailable (e.g. import-time errors).
    """
    try:
        from api.device_state import device_state
        return device_state.list_active_watched_devices() or []
    except Exception as exc:
        logger.debug("[devmode] watcher list query failed: %s", exc)
        return []


def _watcher_poll_loop() -> None:
    logger.info(
        "[devmode] watcher poller started (interval=%ss)",
        WATCHER_POLL_INTERVAL_S,
    )
    while not _WATCHER_STOP.is_set():
        try:
            devices = _list_watched_devices()
            if devices:
                modes = get_device_modes_parallel(
                    [(d, d) for d in devices],
                    max_age_s=WATCHER_POLL_INTERVAL_S - 1,
                    force=False,
                )
                logger.debug(
                    "[devmode] watcher poll refreshed %d device(s): %s",
                    len(modes),
                    {k: v.get("mode") for k, v in modes.items()},
                )
        except Exception as exc:
            logger.warning("[devmode] watcher poll iteration crashed: %s", exc)
            _WATCHER_STOP.wait(_INFLIGHT_SCAN_BACKOFF_S)
            continue
        _WATCHER_STOP.wait(WATCHER_POLL_INTERVAL_S)


def start_watcher_poller() -> None:
    global _WATCHER_THREAD
    with _WATCHER_THREAD_LOCK:
        if _WATCHER_THREAD is not None and _WATCHER_THREAD.is_alive():
            return
        _WATCHER_STOP.clear()
        _WATCHER_THREAD = threading.Thread(
            target=_watcher_poll_loop,
            name="devmode-watcher-poller",
            daemon=True,
        )
        _WATCHER_THREAD.start()


def stop_watcher_poller(timeout: float = 5.0) -> None:
    global _WATCHER_THREAD
    with _WATCHER_THREAD_LOCK:
        if _WATCHER_THREAD is None:
            return
        _WATCHER_STOP.set()
        _WATCHER_THREAD.join(timeout=timeout)
        _WATCHER_THREAD = None


# --------------------------------------------------------------- global poll

_GLOBAL_THREAD_LOCK = threading.Lock()
_GLOBAL_THREAD: Optional[threading.Thread] = None
_GLOBAL_STOP = threading.Event()


def _list_all_known_devices(scaler_root: str) -> List[Tuple[str, Dict[str, Any]]]:
    """Return every device with an ``operational.json`` on disk, EXCLUDING
    records that the ghost-IP reaper has already disowned (``_stale``).
    Stale records have no usable mgmt_ip and would burn the slow path
    on every cycle.
    """
    configs_root = Path(scaler_root) / "db" / "configs"
    if not configs_root.exists():
        return []
    out: List[Tuple[str, Dict[str, Any]]] = []
    for device_dir in configs_root.iterdir():
        if not device_dir.is_dir():
            continue
        op_path = device_dir / "operational.json"
        if not op_path.exists():
            continue
        try:
            data = _read_ops_safe(op_path)
        except Exception:
            continue
        if data.get("_stale") is True:
            continue
        out.append((device_dir.name, data))
    return out


def _global_poll_loop() -> None:
    """Walk every known device every GLOBAL_POLL_INTERVAL_S.

    Skips devices that the in-flight or watcher pollers will hit this
    cycle (they're already on a tighter cadence). Probes the rest in
    batches of ``_GLOBAL_POLL_BATCH_SIZE`` to avoid spawning N threads
    at once on a 100-device lab.

    This is the safety net for "someone in the lab rebooted PE-1 into
    RECOVERY at 3 AM" -- without it, no probe runs until a user opens
    the wizard tomorrow morning.
    """
    sc_root = os.environ.get("SCALER_ROOT", "/home/dn/SCALER")
    logger.info(
        "[devmode] global poller started (interval=%ss, batch=%d)",
        GLOBAL_POLL_INTERVAL_S, _GLOBAL_POLL_BATCH_SIZE,
    )
    # Stagger first iteration so we don't dogpile on startup with the
    # in-flight + watcher pollers.
    _GLOBAL_STOP.wait(min(30.0, GLOBAL_POLL_INTERVAL_S / 2.0))
    # Counter that lets us run the on-disk self-heal sweep on every Nth
    # global iteration. The sweep is cheap (file-IO only, no SSH) but
    # we don't need to do it every 5 min -- once an hour is plenty.
    _heal_iter = 0
    while not _GLOBAL_STOP.is_set():
        try:
            # Self-heal sweep: salvage corrupt files, apply invariants
            # in place. Piggy-backed onto the global poller because it
            # already iterates every device once per cycle.
            try:
                from routes._ops_writer import self_heal_sweep
                configs_root = Path(sc_root) / "db" / "configs"
                stats = self_heal_sweep(configs_root)
                if stats.get("healed") or stats.get("quarantined"):
                    logger.warning(
                        "[devmode] self_heal_sweep: %s", stats,
                    )
                _heal_iter += 1
            except Exception as _heal_exc:
                logger.warning("[devmode] self_heal_sweep failed: %s", _heal_exc)

            all_devices = _list_all_known_devices(sc_root)
            inflight_names = {
                name for name, _ in _list_inflight_devices(sc_root)
            }
            watched_names = set(_list_watched_devices())
            already_covered = inflight_names | watched_names
            targets = [
                (name, data) for name, data in all_devices
                if name not in already_covered
            ]
            if targets:
                t0 = _now()
                refreshed = 0
                for i in range(0, len(targets), _GLOBAL_POLL_BATCH_SIZE):
                    if _GLOBAL_STOP.is_set():
                        break
                    batch = targets[i:i + _GLOBAL_POLL_BATCH_SIZE]
                    try:
                        modes = get_device_modes_parallel(
                            [(name, name) for name, _ in batch],
                            max_age_s=GLOBAL_POLL_INTERVAL_S - 5,
                            force=False,
                        )
                        refreshed += len(modes)
                    except Exception as exc:
                        logger.debug(
                            "[devmode] global poll batch failed: %s", exc,
                        )
                logger.info(
                    "[devmode] global poll refreshed %d/%d device(s) "
                    "in %.1fs (skipped %d covered by tighter pollers)",
                    refreshed, len(targets), _now() - t0,
                    len(already_covered),
                )
        except Exception as exc:
            logger.warning("[devmode] global poll iteration crashed: %s", exc)
            _GLOBAL_STOP.wait(_INFLIGHT_SCAN_BACKOFF_S)
            continue
        _GLOBAL_STOP.wait(GLOBAL_POLL_INTERVAL_S)


def start_global_poller() -> None:
    global _GLOBAL_THREAD
    with _GLOBAL_THREAD_LOCK:
        if _GLOBAL_THREAD is not None and _GLOBAL_THREAD.is_alive():
            return
        _GLOBAL_STOP.clear()
        _GLOBAL_THREAD = threading.Thread(
            target=_global_poll_loop,
            name="devmode-global-poller",
            daemon=True,
        )
        _GLOBAL_THREAD.start()


def stop_global_poller(timeout: float = 5.0) -> None:
    global _GLOBAL_THREAD
    with _GLOBAL_THREAD_LOCK:
        if _GLOBAL_THREAD is None:
            return
        _GLOBAL_STOP.set()
        _GLOBAL_THREAD.join(timeout=timeout)
        _GLOBAL_THREAD = None


def start_all_pollers() -> None:
    """Convenience entry point for ``scaler_bridge`` startup hooks.

    Runs a synchronous self-heal sweep first so any operational.json
    that crashed mid-write before this server boot is salvaged before
    we read from it. Then kicks off the three layered pollers.
    """
    try:
        from routes._ops_writer import self_heal_sweep
        sc_root = os.environ.get("SCALER_ROOT", "/home/dn/SCALER")
        configs_root = Path(sc_root) / "db" / "configs"
        stats = self_heal_sweep(configs_root)
        if stats.get("scanned"):
            logger.info("[devmode] startup self_heal_sweep: %s", stats)
    except Exception as exc:
        logger.warning("[devmode] startup self_heal_sweep failed: %s", exc)
    start_inflight_poller()
    start_watcher_poller()
    start_global_poller()


def stop_all_pollers(timeout: float = 5.0) -> None:
    stop_inflight_poller(timeout=timeout)
    stop_watcher_poller(timeout=timeout)
    stop_global_poller(timeout=timeout)


__all__ = [
    "get_device_mode",
    "get_device_modes_parallel",
    "invalidate",
    "invalidate_by_mgmt_ip",
    "snapshot",
    "start_inflight_poller",
    "stop_inflight_poller",
    "start_watcher_poller",
    "stop_watcher_poller",
    "start_global_poller",
    "stop_global_poller",
    "start_all_pollers",
    "stop_all_pollers",
    "INFLIGHT_POLL_INTERVAL_S",
    "WATCHER_POLL_INTERVAL_S",
    "GLOBAL_POLL_INTERVAL_S",
]
