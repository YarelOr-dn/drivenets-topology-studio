"""Canonical live link telemetry schemas and provider contract.

The browser consumes these shapes regardless of whether the data came from
DNOS SSH/CLI today or gNMI in a later phase.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CanvasDevice(BaseModel):
    device_id: str = ""
    label: str = ""
    ssh_host: str = ""
    raw: Dict[str, Any] = Field(default_factory=dict)


class AttachmentInfo(BaseModel):
    kind: str = "none"
    service_name: str = ""
    vrf: str = ""
    rd: str = ""
    rt: str = ""
    evi: str = ""
    bridge_domain: str = ""


class ProtocolNeighbor(BaseModel):
    protocol: str = ""
    peer: str = ""
    state: str = ""
    afi: str = ""
    local_as: str = ""
    remote_as: str = ""


class ProtocolInfo(BaseModel):
    bgp_neighbors: List[ProtocolNeighbor] = Field(default_factory=list)
    isis: str = ""
    ldp: str = ""
    ospf: str = ""


class InterfaceRow(BaseModel):
    name: str
    kind: str = "physical"
    admin_state: str = ""
    oper_state: str = ""
    description: str = ""
    speed: str = ""
    duplex: str = ""
    mtu: str = ""
    fec: str = ""
    transceiver: str = ""
    errors: str = ""
    lldp_neighbor: str = ""
    lldp_neighbor_interface: str = ""
    attachment: AttachmentInfo = Field(default_factory=AttachmentInfo)
    protocols: ProtocolInfo = Field(default_factory=ProtocolInfo)
    raw: Dict[str, Any] = Field(default_factory=dict)


class BundleMemberRow(BaseModel):
    interface: str
    role: str = ""
    port_state: str = ""
    protocol_state: str = ""
    flags: str = ""


class BundleRow(BaseModel):
    name: str
    mode: str = ""
    lacp_mode: str = ""
    lacp_period: str = ""
    lacp_system_id: str = ""
    force_up: str = ""
    min_links: str = ""
    admin_state: str = ""
    oper_state: str = ""
    speed_sum: str = ""
    mtu: str = ""
    members: List[BundleMemberRow] = Field(default_factory=list)
    members_config: List[BundleMemberRow] = Field(default_factory=list)
    attachment: AttachmentInfo = Field(default_factory=AttachmentInfo)
    protocols: ProtocolInfo = Field(default_factory=ProtocolInfo)
    raw: Dict[str, Any] = Field(default_factory=dict)


class SubInterfaceRow(BaseModel):
    name: str
    parent: str = ""
    outer_vlan: str = ""
    inner_vlan: str = ""
    tpid: str = ""
    vlan_manipulation_egress: str = ""
    ip: str = ""
    mtu: str = ""
    admin_state: str = ""
    oper_state: str = ""
    bridge_domain: str = ""
    description: str = ""
    attachment: AttachmentInfo = Field(default_factory=AttachmentInfo)
    protocols: ProtocolInfo = Field(default_factory=ProtocolInfo)
    raw: Dict[str, Any] = Field(default_factory=dict)


class LldpEdge(BaseModel):
    device: str = ""
    local_interface: str
    peer_hostname: str = ""
    peer_interface: str = ""
    peer_chassis_id: str = ""
    evidence: str = ""
    confidence: str = "verified"


class CounterRow(BaseModel):
    interface: str
    rx_packets: str = ""
    tx_packets: str = ""
    rx_errors: str = ""
    tx_errors: str = ""
    raw: Dict[str, Any] = Field(default_factory=dict)


class DeviceTelemetry(BaseModel):
    physical: List[InterfaceRow] = Field(default_factory=list)
    bundles: List[BundleRow] = Field(default_factory=list)
    subifs: List[SubInterfaceRow] = Field(default_factory=list)
    lldp: List[LldpEdge] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    provider: str = ""
    cached: bool = False


class LinkTelemetryPayload(BaseModel):
    link_id: str
    side_a: DeviceTelemetry = Field(default_factory=DeviceTelemetry)
    side_b: DeviceTelemetry = Field(default_factory=DeviceTelemetry)
    lldp: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class TelemetryProvider(ABC):
    name = "base"

    @abstractmethod
    def available(self, device: CanvasDevice) -> bool:
        """Return whether this provider can serve telemetry for ``device``."""

    @abstractmethod
    def fetch_device(self, device: CanvasDevice, *, force: bool = False) -> DeviceTelemetry:
        """Fetch all link-table telemetry for a single canvas device."""

    @abstractmethod
    def fetch_interfaces(self, device: CanvasDevice, *, ifname: Optional[str] = None) -> List[InterfaceRow]:
        """Fetch physical interfaces for ``device``."""

    @abstractmethod
    def fetch_bundles(self, device: CanvasDevice) -> List[BundleRow]:
        """Fetch bundle interfaces and LACP member state for ``device``."""

    @abstractmethod
    def fetch_subinterfaces(self, device: CanvasDevice, *, parent: Optional[str] = None) -> List[SubInterfaceRow]:
        """Fetch sub-interfaces for ``device``."""

    @abstractmethod
    def fetch_lldp(self, device: CanvasDevice) -> List[LldpEdge]:
        """Fetch LLDP edges for ``device``."""

    @abstractmethod
    def fetch_counters(self, device: CanvasDevice, ifname: str) -> CounterRow:
        """Fetch counters for one interface."""
