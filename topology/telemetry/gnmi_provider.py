"""Phase-2 gNMI provider placeholder.

The dispatcher keeps this provider in the chain so device objects can grow a
``gnmiConfig`` later without changing the frontend schema or API routes.
"""
from __future__ import annotations

from typing import List, Optional

from .provider_base import (
    BundleRow,
    CanvasDevice,
    CounterRow,
    DeviceTelemetry,
    InterfaceRow,
    LldpEdge,
    SubInterfaceRow,
    TelemetryProvider,
)


class GnmiTelemetryProvider(TelemetryProvider):
    name = "gnmi"

    def __init__(self, app_user: str = "default"):
        self.app_user = app_user or "default"

    def available(self, device: CanvasDevice) -> bool:
        cfg = (device.raw or {}).get("gnmiConfig") or {}
        if not cfg:
            return False
        try:
            import pygnmi  # noqa: F401
        except Exception:
            return False
        return bool(cfg.get("host"))

    def _not_ready(self):
        raise NotImplementedError("gNMI link telemetry is planned for Phase 2")

    def fetch_device(self, device: CanvasDevice, *, force: bool = False) -> DeviceTelemetry:
        self._not_ready()

    def fetch_interfaces(self, device: CanvasDevice, *, ifname: Optional[str] = None) -> List[InterfaceRow]:
        self._not_ready()

    def fetch_bundles(self, device: CanvasDevice) -> List[BundleRow]:
        self._not_ready()

    def fetch_subinterfaces(self, device: CanvasDevice, *, parent: Optional[str] = None) -> List[SubInterfaceRow]:
        self._not_ready()

    def fetch_lldp(self, device: CanvasDevice) -> List[LldpEdge]:
        self._not_ready()

    def fetch_counters(self, device: CanvasDevice, ifname: str) -> CounterRow:
        self._not_ready()
