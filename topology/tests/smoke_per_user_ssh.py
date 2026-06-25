#!/usr/bin/env python3
"""End-to-end smoke test for the SSH method/credential fixes.

Checks:
  1. `/api/auth/me/device-credentials` round-trip (PUT -> GET -> list -> DELETE).
  2. `devices.json` is written 0600 under `~/.topology_users/<user>/`.
  3. The bridge's `_get_credentials` helper picks up the new value.
  4. Per-user isolation: user A's saved creds are NOT visible to user B.
  5. Auth: unauthenticated requests are rejected.

Runs against the live proxy on :8080 (browser perspective) so we exercise
the exact path the SSH dialog uses.
"""
from __future__ import annotations

import json
import os
import stat
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = os.environ.get("TOPOLOGY_BASE", "http://localhost:8080")
USERS_BASE = Path(os.environ.get("TOPOLOGY_USERS_BASE", str(Path.home() / ".topology_users")))

PASS_CHECKS = []
FAIL_CHECKS = []


def check(label: str, ok: bool, detail: str = "") -> None:
    mark = "[OK]" if ok else "[FAIL]"
    (PASS_CHECKS if ok else FAIL_CHECKS).append(label)
    suffix = f" -- {detail}" if detail else ""
    print(f"{mark} {label}{suffix}")


def api(method: str, path: str, token: str | None = None, body: dict | None = None,
        accept_404: bool = False) -> tuple[int, dict]:
    req = urllib.request.Request(BASE + path, method=method)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    if body is not None:
        req.add_header("Content-Type", "application/json")
        data = json.dumps(body).encode("utf-8")
    else:
        data = None
    try:
        with urllib.request.urlopen(req, data=data, timeout=15) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        if accept_404 and e.code == 404:
            return 404, {}
        payload = {}
        try:
            payload = json.loads(e.read() or b"{}")
        except Exception:
            pass
        return e.code, payload


def login(username: str, password: str) -> str:
    status, body = api("POST", "/api/auth/login", body={"username": username, "password": password})
    if status != 200:
        raise RuntimeError(f"login failed for {username}: status={status} body={body}")
    return body["token"]


def main() -> int:
    user_a = os.environ.get("SMOKE_USER_A", "admin")
    pass_a = os.environ.get("SMOKE_PASS_A", "drivenets")
    user_b = os.environ.get("SMOKE_USER_B", "alice")
    pass_b = os.environ.get("SMOKE_PASS_B", "drivenets")
    device_id = f"SMOKE-SSH-{int(time.time())}"
    target_user = "smoke_dnroot"
    target_pass = "smoke_Pa55!"

    # 1. unauth access denied
    status, _ = api("GET", "/api/auth/me/device-credentials")
    check("unauthenticated GET returns 401", status == 401, f"status={status}")

    token_a = login(user_a, pass_a)
    token_b = login(user_b, pass_b)
    check(f"login both users ({user_a}, {user_b})", True)

    # 2. PUT for user A
    status, body = api(
        "PUT",
        f"/api/auth/me/device-credentials/{device_id}",
        token=token_a,
        body={"user": target_user, "password": target_pass},
    )
    check("user A PUT credential", status == 200 and body.get("device_id") == device_id, f"status={status}")
    check("response redacts password", body.get("has_password") is True and "password" not in body,
          f"body keys={list(body.keys())}")

    # 3. GET for user A
    status, body = api("GET", f"/api/auth/me/device-credentials/{device_id}", token=token_a)
    check("user A GET credential", status == 200 and body.get("user") == target_user, f"status={status}")

    # 4. List for user A
    status, listing = api("GET", "/api/auth/me/device-credentials", token=token_a)
    found_ids = [c.get("device_id") for c in listing] if isinstance(listing, list) else []
    check("user A list contains new entry", status == 200 and device_id in found_ids,
          f"status={status} found={found_ids[:5]}")

    # 5. File on disk: correct location, correct mode
    devices_file = USERS_BASE / user_a / "devices.json"
    check(f"devices.json created at {devices_file}", devices_file.exists())
    if devices_file.exists():
        mode = stat.S_IMODE(devices_file.stat().st_mode)
        check("devices.json mode is 0600", mode == 0o600, f"actual={oct(mode)}")
        with open(devices_file) as f:
            on_disk = json.load(f)
        entry = on_disk.get(device_id) or {}
        check("on-disk password matches", entry.get("password") == target_pass,
              f"entry={ {k: ('***' if k=='password' else v) for k, v in entry.items()} }")

    # 6. Per-user isolation: user B can't see user A's entry
    status, listing_b = api("GET", "/api/auth/me/device-credentials", token=token_b)
    found_b = [c.get("device_id") for c in listing_b] if isinstance(listing_b, list) else []
    check("user B cannot see user A's entry", status == 200 and device_id not in found_b,
          f"found_b={found_b[:5]}")
    status_b, _ = api("GET", f"/api/auth/me/device-credentials/{device_id}",
                       token=token_b, accept_404=True)
    check("user B GET user A's device_id returns 404", status_b == 404, f"status_b={status_b}")

    # 7. Backend _get_credentials picks it up
    try:
        sys.path.insert(0, "/home/dn/drivenets-topology-studio/topology")
        from routes.bridge_helpers import _get_credentials  # noqa: E402
        u, p = _get_credentials(app_user=user_a, device_id=device_id, hostname=device_id)
        check("bridge _get_credentials returns saved user", u == target_user, f"u={u}")
        check("bridge _get_credentials returns saved password", p == target_pass,
              f"p={'***' if p == target_pass else p}")
    except Exception as e:
        check("bridge _get_credentials importable", False, str(e))

    # 8. DELETE
    status, _ = api("DELETE", f"/api/auth/me/device-credentials/{device_id}", token=token_a)
    check("user A DELETE credential", status == 200, f"status={status}")
    status_after, _ = api("GET", f"/api/auth/me/device-credentials/{device_id}",
                           token=token_a, accept_404=True)
    check("GET after DELETE returns 404", status_after == 404, f"status_after={status_after}")

    print()
    print(f"Results: PASS={len(PASS_CHECKS)}  FAIL={len(FAIL_CHECKS)}")
    if FAIL_CHECKS:
        for f in FAIL_CHECKS:
            print(f"  - {f}")
        return 1
    print("All good.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
