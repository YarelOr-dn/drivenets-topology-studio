"""Unified device communication for scaler bridge routes (DNOSSession + SSH pool)."""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from scaler.dnos_session import DNOSSession


class DeviceCommHelper:
    """Single entry point for route-level SSH show/config helpers."""

    def run_show(
        self,
        device_id: str,
        command: str,
        *,
        ssh_host: str = "",
        timeout: int = 60,
    ) -> str:
        """Resolve device, obtain pooled SSH client, run ``DNOSSession.send_command``."""
        from routes.bridge_helpers import (
            _get_credentials,
            _resolve_mgmt_ip,
            _ssh_pool,
        )
        from scaler.dnos_session import DNOSSession

        mgmt_ip, _, _ = _resolve_mgmt_ip(device_id, ssh_host)
        user, password = _get_credentials()
        pool = _ssh_pool
        client = pool.get_client(mgmt_ip, user, password)
        if not client:
            return "[SSH ERROR] Could not obtain SSH client"
        owns = not pool.enabled
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
            if pool.enabled:
                pool.release(mgmt_ip)
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
    ) -> str:
        """Run a show command when management IP and credentials are already known."""
        from routes.bridge_helpers import _ssh_pool
        from scaler.dnos_session import DNOSSession

        pool = _ssh_pool
        client = pool.get_client(mgmt_ip, user, password)
        if not client:
            return "[SSH ERROR] Could not obtain SSH client"
        owns = not pool.enabled
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
            if pool.enabled:
                pool.release(mgmt_ip)
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
    ) -> dict[str, str]:
        """Run multiple show commands on one session; returns ``{cmd: output}``."""
        from routes.bridge_helpers import (
            _get_credentials,
            _resolve_mgmt_ip,
            _ssh_pool,
        )
        from scaler.dnos_session import DNOSSession

        mgmt_ip, _, _ = _resolve_mgmt_ip(device_id, ssh_host)
        user, password = _get_credentials()
        pool = _ssh_pool
        client = pool.get_client(mgmt_ip, user, password)
        if not client:
            return {c: "[SSH ERROR] Could not obtain SSH client" for c in commands}
        owns = not pool.enabled
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
            if pool.enabled:
                pool.release(mgmt_ip)
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

        if mgmt_ip is None or scaler_id is None:
            mgmt_ip, scaler_id, _ = _resolve_mgmt_ip(device_id, ssh_host)
        user, password = _get_credentials()
        return _fetch_config_via_ssh(scaler_id, mgmt_ip, user, password)

    def get_session(
        self,
        device_id: str,
        *,
        ssh_host: str = "",
    ) -> tuple["DNOSSession", str]:
        """Return ``(DNOSSession, mgmt_ip)`` using a pooled client.

        Caller **must** ``close()`` the session and release the pool::

            sess, ip = comm.get_session(did)
            try:
                ...
            finally:
                sess.close()
                _ssh_pool.release(ip)
        """
        from routes.bridge_helpers import (
            _get_credentials,
            _resolve_mgmt_ip,
            _ssh_pool,
        )
        from scaler.dnos_session import DNOSSession

        mgmt_ip, _, _ = _resolve_mgmt_ip(device_id, ssh_host)
        user, password = _get_credentials()
        pool = _ssh_pool
        client = pool.get_client(mgmt_ip, user, password)
        if not client:
            raise RuntimeError("Could not obtain SSH client")
        owns = not pool.enabled
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
