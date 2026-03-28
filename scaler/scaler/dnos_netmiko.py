#!/usr/bin/env python3
"""
Optional Netmiko backend for simple one-off commands on DNOS-like shells.

Uses ``device_type='generic'`` with a ``#`` prompt terminator. Prefer
:class:`scaler.dnos_session.DNOSSession` for interactive sessions, auto
``| no-more``, HA recovery, and pool integration.
"""

from __future__ import annotations

from typing import Any, Optional


def create_dnos_netmiko_session(
    ip: str,
    username: str,
    password: str,
    *,
    conn_timeout: int = 15,
) -> Any:
    """Return a connected Netmiko ``ConnectHandler`` for quick commands.

    Requires ``netmiko`` to be installed::

        pip install netmiko
    """
    try:
        from netmiko import ConnectHandler
    except ImportError as exc:
        raise ImportError(
            "dnos_netmiko requires netmiko: pip install netmiko"
        ) from exc

    conn = ConnectHandler(
        device_type="generic",
        host=ip,
        username=username,
        password=password,
        conn_timeout=conn_timeout,
    )
    conn.find_prompt()
    conn.set_base_prompt(pri_prompt_terminator="#", alt_prompt_terminator=">")
    return conn


def send_show_via_netmiko(
    ip: str,
    username: str,
    password: str,
    command: str,
    *,
    conn_timeout: int = 15,
    read_timeout: int = 120,
) -> str:
    """Run one show-style command and return output (best-effort)."""
    conn = create_dnos_netmiko_session(ip, username, password, conn_timeout=conn_timeout)
    try:
        if "| no-more" not in command:
            command = f"{command} | no-more"
        return conn.send_command(command, read_timeout=read_timeout)
    finally:
        try:
            conn.disconnect()
        except Exception:
            pass
