"""
Atomic, per-file-locked writer for ``operational.json``.

Why this exists
---------------
Multiple producers write ``operational.json`` for the same device:

* ``_persist_live_status_to_ops`` (after every live SSH status probe)
* ``_ensure_operational_json`` (on first-touch device bootstrap)
* ``_console_fallback.capture_from_ops`` (copies KVM/NCC fallback into
  a per-user devices.json backup)
* ``image_upgrade_execute`` handlers (mark ``upgrade_in_progress``)
* ``request system delete`` handlers (mark ``_delete_pending``)
* ``_persist_ghost_event``, ``snapshot_active_ncc_for_upgrade``,
  ``clear_active_ncc_upgrade_snapshot``, and the
  ``build_device_context`` self-heal block in ``bridge_helpers``.

Before this helper existed, two concurrent writers could interleave
and produce a truncated / invalid-JSON file, which then cascaded into
the UI (stack dialog empty, upgrade wizard showing ``-`` for versions,
DeviceMonitor flipping modes to ``unknown``).

Contract
--------
``update_ops(path, mutator)`` takes the path to an ``operational.json``
and a callable that MUTATES a dict in place. The helper:

1. Acquires a per-path ``threading.Lock`` (intra-process serialization).
2. Acquires a ``fcntl.flock`` on the target file (cross-process
   serialization between uvicorn workers + scaler monitor.py +
   scaler_bridge subprocesses).
3. Reads the current JSON (or starts from an empty dict when the file
   is missing/corrupted; corrupt content is preserved as
   ``operational.json.corrupt-<ts>`` for forensics).
4. Calls the mutator with that dict.
5. Writes the result to a sibling ``.tmp`` file and ``os.replace``s it
   on top of the target -- atomic from the reader's POV.

Readers of ``operational.json`` remain lock-free: ``os.replace`` is
atomic at the VFS layer, so a concurrent read always sees either the
old complete file or the new complete file, never a partial write.

When you add another writer, PLEASE route it through this helper so
the file-level lock is honored. Writing via raw ``path.write_text``
will re-introduce the partial-write race.
"""
from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Callable, Dict, Optional, Tuple

try:
    import fcntl  # POSIX-only; cross-process advisory locking
    _HAVE_FCNTL = True
except ImportError:  # pragma: no cover - Windows path
    fcntl = None  # type: ignore
    _HAVE_FCNTL = False


_log = logging.getLogger(__name__)

_locks: Dict[str, threading.Lock] = {}
_locks_guard = threading.Lock()
_FLOCK_WAIT_SECONDS = 5.0

# Canonical set of accepted device_state values. Any value outside this
# set written via ``update_ops`` is logged + dropped (we prefer to keep
# the prior value than commit garbage). Callers can extend this list
# at runtime via ``register_device_state(name)``; we only do that for
# backwards-compat with one-off scaler statuses.
_VALID_DEVICE_STATES = {
    "GI", "DNOS", "RECOVERY", "BASEOS_SHELL", "ONIE",
    "UPGRADING", "DEPLOYING",
    # Empty string allowed: means "not classified yet". Some legacy
    # writers explicitly clear the field; do not reject those.
    "",
}

# Observability counters -- exposed via ``snapshot()`` so the resilience
# tests + `/api/devicemode/monitor` endpoint can see how often invariants
# fire. Cheap to keep; never block the write path.
_invariant_hits: Dict[str, int] = {
    "cidr_stripped": 0,
    "kvm_host_ip_blocked": 0,
    "invalid_state_dropped": 0,
    "no_shrink_reverted": 0,
    "schema_repaired": 0,
    "writes_total": 0,
    "writes_aborted": 0,
}
_invariant_lock = threading.Lock()


def _bump(counter: str) -> None:
    with _invariant_lock:
        _invariant_hits[counter] = _invariant_hits.get(counter, 0) + 1


def snapshot() -> Dict[str, int]:
    """Return a copy of invariant counters for observability."""
    with _invariant_lock:
        return dict(_invariant_hits)


def register_device_state(name: str) -> None:
    """Allow callers to whitelist an extra ``device_state`` value at runtime.

    Used sparingly -- for example, scaler may emit transitional states we
    haven't seen before; rather than reject the write outright, we log
    once and add it to the whitelist.
    """
    if not name:
        return
    _VALID_DEVICE_STATES.add(name.upper())


def _lock_for(path: Path) -> threading.Lock:
    key = str(path.resolve() if path.exists() else path)
    with _locks_guard:
        lock = _locks.get(key)
        if lock is None:
            lock = threading.Lock()
            _locks[key] = lock
        return lock


def _quarantine_corrupt(path: Path, raw_text: str) -> None:
    """Save a copy of unparseable ``operational.json`` for forensics.

    The runtime continues with an empty dict so the UI doesn't break;
    the snapshot lets us figure out *why* the file was corrupt later.
    Cap the number of snapshots at 10 per device by trimming the
    oldest -- without this, a flapping device could fill the disk.
    """
    if not raw_text:
        return
    try:
        ts = time.strftime("%Y%m%d-%H%M%S")
        snap = path.with_suffix(path.suffix + f".corrupt-{ts}")
        snap.write_text(raw_text)
        # Trim oldest beyond 10
        siblings = sorted(
            path.parent.glob(path.name + ".corrupt-*"),
            key=lambda p: p.stat().st_mtime,
        )
        for stale in siblings[:-10]:
            try:
                stale.unlink()
            except Exception:
                pass
        _log.warning("[ops_writer] quarantined corrupt %s -> %s", path, snap)
    except Exception:
        # Quarantining is best-effort. Never raise from here.
        pass


def read_ops(path: Path) -> Dict:
    """Read ``operational.json``; return ``{}`` on missing, salvage the
    valid prefix on corrupt input.

    Bug history:
    * (2026-04-26) When the file existed but was corrupted (a partial
      write from a non-atomic legacy site, or a disk-full truncation),
      the previous version silently returned ``{}``. Every subsequent
      ``update_ops`` round would then *overwrite* the corrupt bytes
      with the new partial state -- effectively losing the device's
      history (mgmt_ip, system_type, deploy params, ...).
    * (2026-04-27) Returning ``{}`` after quarantine still lost data
      when scaler's legacy raw ``json.dump`` got interrupted: e.g.
      YOR_PE-1's file had two concatenated objects (``Extra data:
      line 48 column 2``); the *first* object was a complete, valid
      18-key snapshot. Pure-``json.loads`` rejected the whole file,
      we returned ``{}``, and ``_persist_live_status_to_ops`` wrote
      back a 5-key file that lost ``_identity``, ``stack_components``,
      ``mgmt_ip``, etc.

    Current behaviour: always quarantine the raw bytes for forensic
    inspection, but try ``json.JSONDecoder().raw_decode()`` to salvage
    the longest valid JSON prefix before falling back to ``{}``. This
    is exactly what the corruption pattern produces (truncated tail
    or duplicate-object suffix), so the fast path recovers ~all of
    the device's metadata even when scaler races us.
    """
    try:
        if not path.exists():
            return {}
    except Exception:
        return {}
    try:
        raw = path.read_text()
    except Exception:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        _quarantine_corrupt(path, raw)

    # Salvage path: pull the longest valid JSON object prefix.
    try:
        obj, _end = json.JSONDecoder().raw_decode(raw)
        if isinstance(obj, dict):
            _log.warning(
                "[ops_writer] salvaged %d-key prefix from corrupt %s",
                len(obj), path,
            )
            return obj
    except Exception:
        pass
    return {}


def _flock_locked(fileobj):
    """Best-effort cross-process advisory lock with timeout.

    ``fcntl.flock(LOCK_EX)`` is blocking; if a peer crashed mid-update
    we don't want to wedge the API. Try-lock with backoff and fall
    back to thread-only locking after the timeout so the write still
    proceeds (correctness is degraded but liveness preserved).
    """
    if not _HAVE_FCNTL:
        return True
    deadline = time.monotonic() + _FLOCK_WAIT_SECONDS
    while True:
        try:
            fcntl.flock(fileobj, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except BlockingIOError:
            if time.monotonic() >= deadline:
                _log.warning("[ops_writer] flock contended >%.1fs on %s; "
                             "proceeding with thread-lock only",
                             _FLOCK_WAIT_SECONDS, getattr(fileobj, "name", "?"))
                return False
            time.sleep(0.05)


def _apply_invariants(before: Dict, after: Dict, path: Path) -> Dict:
    """Validate + repair ``after`` in place to enforce the schema contract.

    Invariants enforced (cheap; all O(few keys)):

    * ``mgmt_ip`` / ``ssh_host`` / ``ncc_mgmt_ip`` / ``kvm_host_ip``: strip
      CIDR suffix (``/20`` etc) so dialers don't accidentally pass a
      network spec to ``socket.gethostbyname``. Real bug: PE-1 had
      ``100.64.4.200/20`` and connect_for_upgrade timed out because
      ``socket.create_connection`` got that as a host string.
    * ``mgmt_ip`` must not equal ``kvm_host_ip``. We've seen scaler write
      the hypervisor IP into ``mgmt_ip`` after a messy refresh, which
      then routed user SSH at the KVM (not the NCC). Block here in
      addition to ``_safe_set_mgmt_ip``.
    * ``device_state`` must be one of ``_VALID_DEVICE_STATES``. Unknown
      values are dropped (the prior value, if any, stays). We've never
      seen a real bad state, but the guard means a future scaler bug
      can't poison the canvas.
    * **No-shrink guard**: if the previous file had a key that the new
      version is silently dropping (and the previous value was
      non-empty), we restore the old value. This is the single biggest
      protection against scaler's legacy non-atomic writers: they read
      a partial JSON object, write back a 5-key file, and would otherwise
      lose ``stack_components``, ``_identity``, etc. With this guard,
      the salvage path in ``read_ops`` plus this restoration means the
      file never silently shrinks.

      Exception: keys explicitly listed in ``after.get("_drop_keys", [])``
      are honored as deletions. (We pop ``_drop_keys`` after applying.)
    """
    if not isinstance(after, dict):
        return after

    # 1. CIDR strip on IP-shaped fields. Don't be clever -- only touch
    #    the canonical IP keys; avoid touching prefix lists, neighbor
    #    tables, etc.
    for key in ("mgmt_ip", "ssh_host", "ncc_mgmt_ip", "kvm_host_ip"):
        v = after.get(key)
        if isinstance(v, str) and "/" in v:
            cleaned = v.split("/", 1)[0].strip()
            if cleaned and cleaned != v:
                after[key] = cleaned
                _bump("cidr_stripped")
                _log.info("[ops_writer] %s: stripped CIDR on %s (%r -> %r)",
                          path.parent.name, key, v, cleaned)

    # 2. mgmt_ip == kvm_host_ip is always wrong for cluster devices.
    #    Revert to the previous value if we have one; otherwise blank it.
    kvm_ip = (after.get("kvm_host_ip") or "").strip()
    mgmt_ip = (after.get("mgmt_ip") or "").strip()
    if kvm_ip and mgmt_ip and kvm_ip == mgmt_ip:
        prev = (before.get("mgmt_ip") or "").strip()
        if prev and prev != kvm_ip:
            after["mgmt_ip"] = prev
        else:
            after["mgmt_ip"] = ""
        _bump("kvm_host_ip_blocked")
        _log.warning("[ops_writer] %s: mgmt_ip==kvm_host_ip blocked, "
                     "reverted to %r", path.parent.name, after["mgmt_ip"])

    # 3. device_state whitelist.
    state = after.get("device_state")
    if isinstance(state, str):
        norm = state.strip().upper()
        if norm and norm not in _VALID_DEVICE_STATES:
            prev = before.get("device_state", "")
            after["device_state"] = prev
            _bump("invalid_state_dropped")
            _log.warning("[ops_writer] %s: rejected device_state=%r "
                         "(reverted to %r)", path.parent.name, state, prev)
        elif norm != state:
            after["device_state"] = norm

    # 4. No-shrink guard.
    drop_keys = set(after.pop("_drop_keys", []) or [])
    for key, prev_val in (before or {}).items():
        if key in after:
            continue
        if key in drop_keys:
            continue
        # Don't restore null / empty string / empty container -- they
        # carry no information and the writer probably meant to clear.
        if prev_val in (None, "", [], {}):
            continue
        # Don't restore internal markers that callers explicitly clear.
        if key.startswith("__"):
            continue
        after[key] = prev_val
        _bump("no_shrink_reverted")
    return after


def update_ops(
    path: Path,
    mutator: Callable[[Dict], Optional[bool]],
    *,
    create_if_missing: bool = False,
    skip_invariants: bool = False,
) -> Tuple[bool, Optional[Dict]]:
    """Load, mutate, atomically persist.

    Returns ``(ok, final_data)``. ``ok=False`` means the write was
    suppressed (e.g. mutator returned ``False`` to abort, or the file
    does not exist and ``create_if_missing`` is False).

    The mutator may:
    * Mutate the passed dict in place (return value ignored).
    * Return ``False`` explicitly to skip the write.
    """
    path = Path(path)
    if not path.exists() and not create_if_missing:
        return False, None

    lock = _lock_for(path)
    with lock:
        # Cross-process file lock. We open (or create) the file once
        # here in r+/w mode so we can flock the actual inode -- not a
        # sibling lockfile -- and so the read+mutate+write sequence is
        # serialized against other processes too.
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            # Open for read+write, creating if needed. Don't truncate;
            # we want to read existing JSON then rewrite via a temp
            # file + os.replace.
            lock_fd = os.open(str(path), os.O_RDWR | os.O_CREAT, 0o644)
        except Exception:
            return False, None
        lock_fobj = os.fdopen(lock_fd, "r+")
        try:
            _flock_locked(lock_fobj)
            data = read_ops(path)
            # Snapshot the pre-mutation state so the invariant pass can
            # do shrink detection. dict.copy() is shallow which is fine
            # for our schema (no nested mutations crossover).
            before = dict(data)
            try:
                result = mutator(data)
            except Exception:
                _bump("writes_aborted")
                return False, None
            if result is False:
                return False, data
            if not skip_invariants:
                try:
                    data = _apply_invariants(before, data, path)
                except Exception:
                    # Invariants must never break the write path; log and
                    # continue with the unmodified mutator output.
                    _log.exception("[ops_writer] invariant pass failed for %s", path)
            try:
                fd, tmp_path = tempfile.mkstemp(
                    dir=str(path.parent), suffix=".tmp", prefix=path.name + ".",
                )
                try:
                    with os.fdopen(fd, "w") as fh:
                        json.dump(data, fh, indent=2)
                        fh.flush()
                        try:
                            os.fsync(fh.fileno())
                        except Exception:
                            pass
                    os.replace(tmp_path, str(path))
                    _bump("writes_total")
                except Exception:
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass
                    _bump("writes_aborted")
                    return False, data
            except Exception:
                _bump("writes_aborted")
                return False, data
            return True, data
        finally:
            try:
                if _HAVE_FCNTL:
                    fcntl.flock(lock_fobj, fcntl.LOCK_UN)
            except Exception:
                pass
            try:
                lock_fobj.close()
            except Exception:
                pass


def self_heal_sweep(configs_root: Path) -> Dict[str, int]:
    """Walk every ``operational.json`` under ``configs_root``, salvage corrupt
    files, and apply invariants in place. Returns a stats dict.

    Cheap; designed to be called on startup and piggy-backed onto the
    existing 5-minute global poller. The actual heal work happens via
    a no-op ``update_ops`` call (read_ops salvages on the way in,
    invariants run on the way out, atomic replace lands on disk).

    A file that ``read_ops`` could not even partially parse is left in
    place after quarantine; the resolver will repopulate it on the next
    live probe via ``_persist_live_status_to_ops``.
    """
    stats = {
        "scanned": 0, "healed": 0, "quarantined": 0,
        "skipped_empty": 0, "errors": 0,
    }
    if not configs_root.exists():
        return stats
    for dev_dir in configs_root.iterdir():
        if not dev_dir.is_dir():
            continue
        ops_path = dev_dir / "operational.json"
        if not ops_path.exists():
            continue
        stats["scanned"] += 1
        # Detect corruption by attempting a strict parse first.
        try:
            raw = ops_path.read_text()
            try:
                json.loads(raw)
                # File is valid JSON; still pass it through update_ops
                # with a no-op mutator so the invariant pass tightens
                # any subtle violations (CIDR, kvm_host_ip mismatch).
                ok, after = update_ops(ops_path, lambda d: None)
                if ok and after != json.loads(raw):
                    stats["healed"] += 1
                continue
            except json.JSONDecodeError:
                pass
            # Salvage path: read_ops + atomic rewrite. The mere act of
            # update_ops with a no-op mutator produces a valid file
            # because read_ops returns the salvaged dict.
            ok, after = update_ops(ops_path, lambda d: None, create_if_missing=True)
            if ok:
                if after:
                    stats["healed"] += 1
                else:
                    stats["skipped_empty"] += 1
                stats["quarantined"] += 1
            else:
                stats["errors"] += 1
        except Exception:
            stats["errors"] += 1
    if stats["scanned"]:
        _log.info("[ops_writer] self_heal_sweep: %s", stats)
    return stats


__all__ = [
    "read_ops", "update_ops",
    "snapshot", "register_device_state",
    "self_heal_sweep",
]
