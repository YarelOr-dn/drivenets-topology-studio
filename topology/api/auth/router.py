"""Auth API endpoints: login, register, user management.

All routes require JWT except /login, /register, and /health.
Admin routes (user management) require 'admin' role.
Login/register have per-IP rate limiting (5 attempts/minute).

Per-user device credentials (`/me/device-credentials`) are stored in
``~/.topology_users/<username>/devices.json`` so the bridge's
``_get_credentials`` picks them up on subsequent SSH operations. Storing
them server-side (instead of just the topology JSON) is what makes the
"save my DUT password" UX actually persist across sessions and devices.
"""

from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from ..schemas import (
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    Role,
    SelfRegisterRequest,
    UserInfo,
    UserListResponse,
    UserUpdate,
)
from ..config import settings
from .service import create_access_token, get_current_user, is_owner_user, require_role
from .user_store import user_store

router = APIRouter()

_rate_limit_lock = threading.Lock()
_rate_limit_store: Dict[str, List[float]] = {}
_RATE_LIMIT_MAX = 5
_RATE_LIMIT_WINDOW = 60


def _check_rate_limit(client_ip: str):
    """Enforce max 5 login/register attempts per minute per IP."""
    now = time.time()
    with _rate_limit_lock:
        attempts = _rate_limit_store.get(client_ip, [])
        attempts = [t for t in attempts if now - t < _RATE_LIMIT_WINDOW]
        if len(attempts) >= _RATE_LIMIT_MAX:
            raise HTTPException(
                status_code=429,
                detail=f"Too many attempts. Try again in {int(_RATE_LIMIT_WINDOW - (now - attempts[0]))} seconds.",
            )
        attempts.append(now)
        _rate_limit_store[client_ip] = attempts


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, request: Request):
    _check_rate_limit(request.client.host if request.client else "unknown")
    user = user_store.authenticate(req.username, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    token = create_access_token(user["username"], user["role"])
    is_owner = is_owner_user(user["username"], user.get("display_name", ""))
    return LoginResponse(
        token=token,
        username=user["username"],
        role=Role(user["role"]),
        display_name=user["display_name"],
        is_admin=user["role"] == "admin" or is_owner,
        is_owner=is_owner,
    )


@router.get("/me", response_model=UserInfo)
async def get_me(user=Depends(get_current_user)):
    full = user_store.get_user(user["username"])
    if not full:
        raise HTTPException(status_code=404, detail="User not found")
    is_owner = is_owner_user(full["username"], full.get("display_name", ""))
    return UserInfo(
        username=full["username"],
        display_name=full["display_name"],
        role=Role(full["role"]),
        email=full.get("email"),
        created_at=full["created_at"],
        last_login=full.get("last_login"),
        topology_count=user_store.get_topology_count(full["username"]),
        is_admin=full["role"] == "admin" or is_owner,
        is_owner=is_owner,
    )


@router.post("/register", response_model=LoginResponse)
async def self_register(req: SelfRegisterRequest, request: Request):
    """Public self-registration (when enabled). New users get 'engineer' role."""
    _check_rate_limit(request.client.host if request.client else "unknown")
    if not getattr(settings, "allow_self_registration", True):
        raise HTTPException(status_code=403, detail="Self-registration is disabled")
    existing = user_store.get_user(req.username)
    if existing:
        raise HTTPException(status_code=409, detail=f"User '{req.username}' already exists")
    user = user_store.create_user(
        username=req.username,
        password=req.password,
        display_name=req.display_name,
        email=req.email or "",
        role="engineer",
    )
    token = create_access_token(user["username"], user["role"])
    return LoginResponse(
        token=token,
        username=user["username"],
        role=Role(user["role"]),
        display_name=user["display_name"],
    )


@router.post("/me/change-password")
async def change_password(req: ChangePasswordRequest, user=Depends(get_current_user)):
    ok = user_store.change_password(user["username"], req.current_password, req.new_password)
    if not ok:
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Profile preferences (cloud avatar customisation, theme, accessories)
# ---------------------------------------------------------------------------
# Stored as a single ``profile_prefs.json`` under the user's workspace so
# future per-user visuals (locale, pronouns, sound effects) can slot into
# the same file without new endpoints. The ``avatar`` sub-object is the
# only one consumed today; unknown keys are preserved untouched on save
# so an old client can't wipe a newer field a user set from another tab.

# Catalogue tables the frontend imports so the Customize-Cloud dialog
# renders the exact same label / emoji / palette names the server knows
# about. Keeping both sides in lockstep avoids silent drift when a
# redeploy adds a new face but forgets to bump the UI.
AVATAR_PALETTE_NAMES: List[str] = [
    "sky", "rose", "mint", "butter", "lavender", "peach",
    "blossom", "aqua", "periwinkle", "sage", "honey", "petal",
    "mist", "cloud",
]

# Accessory slot: 0=none, then a small curated set of cute overlays.
# Kept small on purpose -- too many options overwhelms; too few feels
# like the "customize" menu is a joke.
AVATAR_ACCESSORY_IDS: List[int] = list(range(0, 10))

# Face index range. 14 built-in faces matches the CLOUD_FACES table in
# topology-share.js. If that table grows, bump this ceiling too.
AVATAR_FACE_MAX: int = 13


def _load_profile_prefs(username: str) -> Dict[str, Any]:
    """Read ``profile_prefs.json`` for ``username``, returning an empty
    dict if the file is missing or malformed.

    The file is optional -- most users never open the customise dialog,
    so a missing file is the common case and is NOT an error.
    """
    p = user_store.user_profile_prefs_path(username)
    try:
        if not p.exists():
            return {}
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {}
        return data
    except (OSError, json.JSONDecodeError):
        return {}


def _save_profile_prefs(username: str, data: Dict[str, Any]) -> None:
    """Write ``profile_prefs.json`` atomically (temp + rename).

    Permissions are relaxed for this file (0644) because it contains no
    secrets -- just cosmetic overrides -- but we still go through the
    rename dance to avoid a half-written file on crash.
    """
    p = user_store.user_profile_prefs_path(username)
    tmp = p.with_suffix(p.suffix + ".tmp")
    try:
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)
        os.replace(tmp, p)
    finally:
        try:
            tmp.unlink()
        except OSError:
            pass


def _sanitise_avatar_patch(raw: Any) -> Dict[str, Any]:
    """Coerce an ``avatar`` patch to the known keys / types.

    Silently drops anything unexpected so a malicious client can't
    inject arbitrary keys into the stored blob. Each field is also
    bounds-checked against the catalogue so the frontend can't set
    face=9999 and break the renderer.
    """
    out: Dict[str, Any] = {}
    if not isinstance(raw, dict):
        return out
    palette = raw.get("palette")
    if isinstance(palette, str) and palette in AVATAR_PALETTE_NAMES:
        out["palette"] = palette
    face = raw.get("face")
    if isinstance(face, int) and 0 <= face <= AVATAR_FACE_MAX:
        out["face"] = face
    accessory = raw.get("accessory")
    if isinstance(accessory, int) and accessory in AVATAR_ACCESSORY_IDS:
        out["accessory"] = accessory
    return out


class ProfilePatch(BaseModel):
    """Partial update for a user's profile preferences.

    All fields are optional -- the endpoint merges the patch on top of
    whatever is stored already, so a client that only knows about the
    ``avatar`` bucket can PATCH just that and not disturb anything else.
    """

    avatar: Optional[Dict[str, Any]] = None


@router.get("/me/profile")
async def get_my_profile(user=Depends(get_current_user)):
    """Return the caller's profile prefs + the catalogue the UI needs
    to render the customise dialog.

    Served to every authenticated user regardless of role -- cosmetic
    customisation is intentionally universal so engineers, viewers, and
    the owner all see the same friendly UX.
    """
    prefs = _load_profile_prefs(user["username"])
    return {
        "username": user["username"],
        "avatar": prefs.get("avatar") or {},
        "catalogue": {
            "palettes": AVATAR_PALETTE_NAMES,
            "faces": list(range(AVATAR_FACE_MAX + 1)),
            "accessories": AVATAR_ACCESSORY_IDS,
        },
    }


@router.patch("/me/profile")
async def patch_my_profile(patch: ProfilePatch, user=Depends(get_current_user)):
    """Merge the patch into the stored prefs and persist.

    Returns the updated blob so the client can trust its local state
    without a follow-up GET.
    """
    stored = _load_profile_prefs(user["username"])
    if patch.avatar is not None:
        cleaned = _sanitise_avatar_patch(patch.avatar)
        current = stored.get("avatar") or {}
        if not isinstance(current, dict):
            current = {}
        current.update(cleaned)
        stored["avatar"] = current
    _save_profile_prefs(user["username"], stored)
    return {
        "username": user["username"],
        "avatar": stored.get("avatar") or {},
    }


@router.post("/me/profile/reset")
async def reset_my_profile(user=Depends(get_current_user)):
    """Clear the stored avatar override so the deterministic hash
    (palette/face derived from username) takes over again.

    Handy "reset to default" button -- keeps the UX forgiving so a user
    can experiment without fear of being stuck with an ugly combo.
    """
    stored = _load_profile_prefs(user["username"])
    if "avatar" in stored:
        stored.pop("avatar", None)
    _save_profile_prefs(user["username"], stored)
    return {"username": user["username"], "avatar": {}}


# -- Admin: User Management --

@router.get("/users", response_model=UserListResponse)
async def list_users(admin=Depends(require_role("manager"))):
    users = user_store.list_users()
    items = []
    for u in users:
        items.append(UserInfo(
            username=u["username"],
            display_name=u["display_name"],
            role=Role(u["role"]),
            email=u.get("email"),
            created_at=u["created_at"],
            last_login=u.get("last_login"),
            topology_count=user_store.get_topology_count(u["username"]),
        ))
    return UserListResponse(users=items, total=len(items))


@router.post("/users", response_model=UserInfo, status_code=201)
async def register_user(req: RegisterRequest, admin=Depends(require_role("admin"))):
    existing = user_store.get_user(req.username)
    if existing:
        raise HTTPException(status_code=409, detail=f"User '{req.username}' already exists")
    user = user_store.create_user(
        username=req.username,
        password=req.password,
        display_name=req.display_name,
        email=req.email or "",
        role=req.role.value,
    )
    return UserInfo(
        username=user["username"],
        display_name=user["display_name"],
        role=Role(user["role"]),
        email=user.get("email"),
        created_at=user["created_at"],
        last_login=user.get("last_login"),
        topology_count=0,
    )


@router.put("/users/{username}", response_model=UserInfo)
async def update_user(username: str, req: UserUpdate, admin=Depends(require_role("admin"))):
    existing = user_store.get_user(username)
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    updates = req.model_dump(exclude_none=True)
    if "role" in updates:
        updates["role"] = updates["role"].value
    updated = user_store.update_user(username, updates)
    return UserInfo(
        username=updated["username"],
        display_name=updated["display_name"],
        role=Role(updated["role"]),
        email=updated.get("email"),
        created_at=updated["created_at"],
        last_login=updated.get("last_login"),
        topology_count=user_store.get_topology_count(updated["username"]),
    )


@router.delete("/users/{username}")
async def deactivate_user(username: str, admin=Depends(require_role("admin"))):
    if username == admin["username"]:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    user_store.delete_user(username)
    return {"status": "deactivated", "username": username}


# -- Per-user device credentials (persisted to ~/.topology_users/<user>/devices.json) --
#
# This mirrors the shape that ``routes.bridge_helpers._get_credentials``
# already reads. Every write is atomic (rename-in-place) and the file is
# 0600-chmodded so a multi-tenant server never leaks one user's creds to
# another. The wildcard key ``_default`` lets a power user save a single
# credential that applies to every device that doesn't have its own entry.

class DeviceCredentialIn(BaseModel):
    user: str = Field(..., min_length=1, max_length=128)
    password: str = Field(..., min_length=1, max_length=256)


class DeviceCredentialOut(BaseModel):
    device_id: str
    user: str
    has_password: bool
    updated_at: Optional[str] = None


_DEVICE_CRED_FILE = "devices.json"
_cred_lock = threading.Lock()


def _user_dir(username: str) -> Path:
    base = Path(os.environ.get("TOPOLOGY_USERS_BASE", str(Path.home() / ".topology_users")))
    return base / username


def _read_device_creds(username: str) -> Dict[str, Any]:
    path = _user_dir(username) / _DEVICE_CRED_FILE
    if not path.exists():
        return {}
    try:
        with open(path) as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_device_creds(username: str, data: Dict[str, Any]) -> None:
    udir = _user_dir(username)
    udir.mkdir(parents=True, exist_ok=True)
    path = udir / _DEVICE_CRED_FILE
    tmp = path.with_suffix(".tmp")
    payload = json.dumps(data, indent=2, sort_keys=True)
    with _cred_lock:
        tmp.write_text(payload)
        try:
            os.chmod(tmp, 0o600)
        except Exception:
            pass
        os.replace(tmp, path)
        try:
            os.chmod(path, 0o600)
        except Exception:
            pass


def _entry_to_out(device_id: str, entry: Dict[str, Any]) -> DeviceCredentialOut:
    user = entry.get("user") or entry.get("device_user") or ""
    password = entry.get("password") or entry.get("device_password") or ""
    return DeviceCredentialOut(
        device_id=device_id,
        user=user,
        has_password=bool(password),
        updated_at=entry.get("updated_at"),
    )


@router.get("/me/device-credentials", response_model=List[DeviceCredentialOut])
async def list_device_credentials(user=Depends(get_current_user)):
    """Return every per-user device credential (without the password)."""
    data = _read_device_creds(user["username"])
    out: List[DeviceCredentialOut] = []
    for device_id, entry in data.items():
        if isinstance(entry, dict):
            out.append(_entry_to_out(device_id, entry))
    out.sort(key=lambda c: c.device_id)
    return out


@router.get("/me/device-credentials/{device_id}", response_model=DeviceCredentialOut)
async def get_device_credential(device_id: str, user=Depends(get_current_user)):
    data = _read_device_creds(user["username"])
    entry = data.get(device_id)
    if not isinstance(entry, dict):
        raise HTTPException(status_code=404, detail=f"No credential stored for '{device_id}'")
    return _entry_to_out(device_id, entry)


@router.put("/me/device-credentials/{device_id}", response_model=DeviceCredentialOut)
async def put_device_credential(
    device_id: str,
    req: DeviceCredentialIn,
    user=Depends(get_current_user),
):
    device_id = device_id.strip()
    if not device_id:
        raise HTTPException(status_code=400, detail="device_id is required")
    data = _read_device_creds(user["username"])
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    data[device_id] = {
        "user": req.user,
        "password": req.password,
        "updated_at": now,
    }
    _write_device_creds(user["username"], data)
    return _entry_to_out(device_id, data[device_id])


@router.delete("/me/device-credentials/{device_id}")
async def delete_device_credential(device_id: str, user=Depends(get_current_user)):
    data = _read_device_creds(user["username"])
    if device_id in data:
        data.pop(device_id, None)
        _write_device_creds(user["username"], data)
    return {"status": "deleted", "device_id": device_id}


# -- Per-user console / KVM fallback ----------------------------------------
#
# Alongside the SSH user/password block above, we also persist a durable
# "how to reach this device when SSH is down" config per (user, device).
# The backing store is the same ``~/.topology_users/<u>/devices.json``
# file (under ``<device_id>["console_fallback"]``), so a single 0600
# file holds every credential the bridge needs for a device.
#
# The heavy lifting (read priority chain, capture-from-ops,
# capture-from-probe, sanitize, delete) lives in
# ``routes._console_fallback``. This router is just a thin JWT-gated
# shim. See ``topology/DEVELOPMENT_GUIDELINES.md`` section "Console
# Fallback Store (2026-04-23)" for the full design.

class ConsoleFallbackIn(BaseModel):
    kvm_host_ip: Optional[str] = ""
    kvm_host_name: Optional[str] = ""
    kvm_user: Optional[str] = ""
    kvm_pass: Optional[str] = ""
    ncc_vms: Optional[List[str]] = None
    active_ncc_vm_hint: Optional[str] = ""
    ncc_console_user: Optional[str] = ""
    ncc_console_pass: Optional[str] = ""
    ncc_mgmt_ip: Optional[str] = ""
    console_server_host: Optional[str] = ""
    console_server_port: Optional[int] = None
    console_server_user: Optional[str] = ""
    console_server_pass: Optional[str] = ""
    serial_hostname: Optional[str] = ""
    dncli_user: Optional[str] = ""
    dncli_pass: Optional[str] = ""
    ncc_type: Optional[str] = None
    notes: Optional[str] = ""


def _lazy_fallback_module():
    """Lazy-import the fallback module so ``api.auth`` doesn't pull in
    ``routes.bridge_helpers`` during app bootstrap."""
    from routes import _console_fallback as cf
    return cf


@router.get("/me/device-credentials/{device_id}/console-fallback")
async def get_console_fallback(device_id: str, user=Depends(get_current_user)):
    """Return the resolved fallback config for ``device_id`` (redacted).

    Resolution order: per-user devices.json -> global SCALER devices.json
    -> operational.json. Passwords are always redacted (``"***"``) so this
    endpoint is safe to return over the public API.
    """
    cf = _lazy_fallback_module()
    fb = cf.read_fallback(user["username"], device_id)
    payload = cf.sanitize(fb)
    payload["availability"] = cf.describe_availability(fb)
    payload["best_method"] = fb.best_method()
    payload["is_empty"] = fb.is_empty()
    return payload


@router.put("/me/device-credentials/{device_id}/console-fallback")
async def put_console_fallback(
    device_id: str,
    req: ConsoleFallbackIn,
    user=Depends(get_current_user),
):
    """Manually set/update a fallback record. Merges with any existing
    record so users can update one field at a time without wiping others.
    """
    device_id = (device_id or "").strip()
    if not device_id:
        raise HTTPException(status_code=400, detail="device_id is required")
    cf = _lazy_fallback_module()
    incoming = cf.ConsoleFallback(
        device_id=device_id,
        kvm_host_ip=(req.kvm_host_ip or "").strip().split("/")[0],
        kvm_host_name=(req.kvm_host_name or "").strip(),
        kvm_user=(req.kvm_user or "").strip(),
        kvm_pass=req.kvm_pass or "",
        ncc_vms=[v.strip() for v in (req.ncc_vms or []) if v and v.strip()],
        active_ncc_vm_hint=(req.active_ncc_vm_hint or "").strip(),
        ncc_console_user=(req.ncc_console_user or "").strip(),
        ncc_console_pass=req.ncc_console_pass or "",
        ncc_mgmt_ip=(req.ncc_mgmt_ip or "").strip().split("/")[0],
        console_server_host=(req.console_server_host or "").strip(),
        console_server_port=req.console_server_port,
        console_server_user=(req.console_server_user or "").strip(),
        console_server_pass=req.console_server_pass or "",
        serial_hostname=(req.serial_hostname or "").strip(),
        dncli_user=(req.dncli_user or "").strip(),
        dncli_pass=req.dncli_pass or "",
        ncc_type=(req.ncc_type or None),
        notes=(req.notes or "manual_api_write").strip() or "manual_api_write",
    )
    saved = cf.write_fallback(
        user["username"], device_id, incoming, merge_with_existing=True,
    )
    payload = cf.sanitize(saved)
    payload["availability"] = cf.describe_availability(saved)
    payload["best_method"] = saved.best_method()
    return payload


@router.delete("/me/device-credentials/{device_id}/console-fallback")
async def delete_console_fallback(
    device_id: str,
    user=Depends(get_current_user),
):
    """Remove the per-user fallback block. Leaves the SSH-credentials
    entry for this device intact. Does NOT touch operational.json, so
    the auto-capture will re-seed it on the next successful probe.
    """
    cf = _lazy_fallback_module()
    removed = cf.delete_fallback(user["username"], device_id)
    return {"status": "deleted" if removed else "absent", "device_id": device_id}


@router.post("/me/device-credentials/{device_id}/console-fallback/capture")
async def capture_console_fallback(
    device_id: str,
    user=Depends(get_current_user),
):
    """Trigger an on-demand capture from ``operational.json`` into the
    user's fallback store.

    Normally this fires automatically after a successful SSH probe or
    ``connect_for_upgrade`` call, but exposing an explicit button is
    useful after a lab admin has manually populated operational.json
    and the user wants to mirror it into their own workspace.
    """
    cf = _lazy_fallback_module()
    saved = cf.capture_from_ops(user["username"], device_id, reason="manual_capture")
    payload = cf.sanitize(saved)
    payload["availability"] = cf.describe_availability(saved)
    payload["best_method"] = saved.best_method()
    payload["is_empty"] = saved.is_empty()
    return payload
