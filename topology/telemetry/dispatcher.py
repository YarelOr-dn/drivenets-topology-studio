"""Telemetry provider dispatcher."""
from __future__ import annotations

from .gnmi_provider import GnmiTelemetryProvider
from .provider_base import CanvasDevice, TelemetryProvider
from .ssh_provider import SshTelemetryProvider


def provider_for(device: CanvasDevice, *, app_user: str = "default") -> TelemetryProvider:
    gnmi = GnmiTelemetryProvider(app_user=app_user)
    if gnmi.available(device):
        return gnmi
    return SshTelemetryProvider(app_user=app_user)
