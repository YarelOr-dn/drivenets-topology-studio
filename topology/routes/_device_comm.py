"""Unified device communication for scaler bridge routes (DNOSSession + SSH pool).

Wave 5.3 -- *Always-on per-user SSH pool keying.*

Before Wave 5.3 each public helper on :class:`DeviceCommHelper` called
``_ssh_pool.get_client(mgmt_ip, user, password)`` without threading
``app_user`` through. The pool then keyed the connection under
``"default@ip"`` for every logged-in user, so two users could end up
sharing a single pooled SSH client authenticated with whoever
connected first. This is both a correctness bug (later users see
another user's session state) and a security concern (the second user
rides on the first user's RBAC credentials).

After Wave 5.3, every helper:

1. Resolves ``app_user`` from the per-request :class:`ContextVar`
   (``current_app_user.get()``) when the caller does not pass it.
2. Passes ``app_user=app_user`` to both ``_ssh_pool.get_client`` and
   ``_ssh_pool.release`` so the pool key is always
   ``"<app_user>@<mgmt_ip>"``.
3. Calls ``_get_credentials(app_user=...)`` so the resolved app user
   also drives per-user device credential lookups.

Callers that already know the app user (e.g. a background thread that
has entered :func:`routes._state.app_user_context`) can pass
``app_user=...`` explicitly and skip the ContextVar lookup.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from scaler.dnos_session import DNOSSession


def _resolve_app_user(app_user: str = "") -> str:
    """Pick the effective app user: explicit arg > ContextVar > 'default'."""
    if app_user:
        return app_user
    try:
        from routes.bridge_helpers import current_app_user
        ctx_user = current_app_user.get() or ""
    except Exception:
        ctx_user = ""
    return ctx_user or "default"


class DeviceCommHelper:
    """Single entry point for route-level SSH show/config helpers."""

    def run_show(
        self,
        device_id: str,
        command: str,
        *,
        ssh_host: str = "",
        timeout: int = 60,
        app_user: str = "",
    ) -> str:
        """Resolve device, obtain pooled SSH client, run ``DNOSSession.send_command``."""
        from routes.bridge_helpers import (
            _get_credentials,
            _resolve_mgmt_ip,
            _ssh_pool,
        )
        from scaler.dnos_session import DNOSSession

        effective_user = _resolve_app_user(app_user)
        mgmt_ip, _, _ = _resolve_mgmt_ip(device_id, ssh_host)
        user, password = _get_credentials(app_user=effective_user, device_id=device_id)
        pool = _ssh_pool
        client = pool.get_client(mgmt_ip, user, password, app_user=effective_user)
        if not client:
            return "[SSH ERROR] Could not obtain SSH client"
        owns = not pool._user_enabled(effective_user)
        try:
            with DNOSSession(
                mgmt_ip,
                user,
                password,
                client=client,
                owns_client=owns,
            ) as sess:
                return sess.send_command(command, timeout=timeout)
        finally:
            if pool._user_enabled(effective_user):
                pool.release(mgmt_ip, app_user=effective_user)
            elif owns:
                try:
                    client.close()
                except Exception:
                    pass

    def run_show_ip(
        self,
        mgmt_ip: str,
        user: str,
        password: str,
        command: str,
        *,
        timeout: int = 60,
        app_user: str = "",
    ) -> str:
        """Run a show command when management IP and credentials are already known."""
        from routes.bridge_helpers import _ssh_pool
        from scaler.dnos_session import DNOSSession

        effective_user = _resolve_app_user(app_user)
        pool = _ssh_pool
        client = pool.get_client(mgmt_ip, user, password, app_user=effective_user)
        if not client:
            return "[SSH ERROR] Could not obtain SSH client"
        owns = not pool._user_enabled(effective_user)
        try:
            with DNOSSession(
                mgmt_ip,
                user,
                password,
                client=client,
                owns_client=owns,
            ) as sess:
                return sess.send_command(command, timeout=timeout)
        finally:
            if pool._user_enabled(effective_user):
                pool.release(mgmt_ip, app_user=effective_user)
            elif owns:
                try:
                    client.close()
                except Exception:
                    pass

    def run_show_batch(
        self,
        device_id: str,
        commands: list[str],
        *,
        ssh_host: str = "",
        timeout: int = 60,
        app_user: str = "",
    ) -> dict[str, str]:
        """Run multiple show commands on one session; returns ``{cmd: output}``."""
        from routes.bridge_helpers import (
            _get_credentials,
            _resolve_mgmt_ip,
            _ssh_pool,
        )
        from scaler.dnos_session import DNOSSession

        effective_user = _resolve_app_user(app_user)
        mgmt_ip, _, _ = _resolve_mgmt_ip(device_id, ssh_host)
        user, password = _get_credentials(app_user=effective_user, device_id=device_id)
        pool = _ssh_pool
        client = pool.get_client(mgmt_ip, user, password, app_user=effective_user)
        if not client:
            return {c: "[SSH ERROR] Could not obtain SSH client" for c in commands}
        owns = not pool._user_enabled(effective_user)
        out: dict[str, str] = {}
        try:
            with DNOSSession(
                mgmt_ip,
                user,
                password,
                client=client,
                owns_client=owns,
            ) as sess:
                for cmd in commands:
                    out[cmd] = sess.send_command(cmd, timeout=timeout)
        finally:
            if pool._user_enabled(effective_user):
                pool.release(mgmt_ip, app_user=effective_user)
            elif owns:
                try:
                    client.close()
                except Exception:
                    pass
        return out

    def fetch_running_config(
        self,
        device_id: str,
        ssh_host: str = "",
        *,
        mgmt_ip: Optional[str] = None,
        scaler_id: Optional[str] = None,
        app_user: str = "",
    ) -> str:
        """Fetch full running config (delegates to ``InteractiveExtractor``).

        If ``mgmt_ip`` and ``scaler_id`` are already resolved (e.g. from
        ``_resolve_mgmt_ip``), pass them to avoid a second resolve.
        """
        from routes.bridge_helpers import (
            _fetch_config_via_ssh,
            _get_credentials,
            _resolve_mgmt_ip,
        )

        effective_user = _resolve_app_user(app_user)
        if mgmt_ip is None or scaler_id is None:
            mgmt_ip, scaler_id, _ = _resolve_mgmt_ip(device_id, ssh_host)
        user, password = _get_credentials(app_user=effective_user, device_id=device_id)
        return _fetch_config_via_ssh(scaler_id, mgmt_ip, user, password)

    def get_session(
        self,
        device_id: str,
        *,
        ssh_host: str = "",
        app_user: str = "",
    ) -> tuple["DNOSSession", str]:
        """Return ``(DNOSSession, mgmt_ip)`` using a pooled client.

        Caller **must** ``close()`` the session and release the pool::

            sess, ip = comm.get_session(did)
            try:
                ...
            finally:
                sess.close()
                _ssh_pool.release(ip, app_user=<same app_user passed here>)
        """
        from routes.bridge_helpers import (
            _get_credentials,
            _resolve_mgmt_ip,
            _ssh_pool,
        )
        from scaler.dnos_session import DNOSSession

        effective_user = _resolve_app_user(app_user)
        mgmt_ip, _, _ = _resolve_mgmt_ip(device_id, ssh_host)
        user, password = _get_credentials(app_user=effective_user, device_id=device_id)
        pool = _ssh_pool
        client = pool.get_client(mgmt_ip, user, password, app_user=effective_user)
        if not client:
            raise RuntimeError("Could not obtain SSH client")
        owns = not pool._user_enabled(effective_user)
        sess = DNOSSession(
            mgmt_ip,
            user,
            password,
            client=client,
            owns_client=owns,
        )
        return sess, mgmt_ip


def get_device_comm() -> DeviceCommHelper:
    """Singleton-style helper for routes."""
    return DeviceCommHelper()
