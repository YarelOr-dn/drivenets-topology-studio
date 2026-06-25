"""Pydantic request/response models for the multi-user Topology Creator API.

Validated automatically by FastAPI -- malformed payloads never reach business logic.
Username regex prevents path traversal (../../../etc/passwd).
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Role(str, Enum):
    VIEWER = "viewer"
    ENGINEER = "engineer"
    TEAM_LEADER = "team_leader"
    MANAGER = "manager"
    ADMIN = "admin"


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_.\-]+$")
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    token: str
    username: str
    role: Role
    display_name: str
    is_admin: bool = False
    is_owner: bool = False


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=64, pattern=r"^[a-zA-Z0-9_.\-]+$")
    password: str = Field(..., min_length=2)
    display_name: str = Field(..., min_length=1, max_length=128)
    email: Optional[str] = None
    role: Role = Role.ENGINEER


class SelfRegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=64, pattern=r"^[a-zA-Z0-9_.\-]+$")
    password: str = Field(..., min_length=6)
    display_name: str = Field(..., min_length=1, max_length=128)
    email: Optional[str] = None


class UserInfo(BaseModel):
    username: str
    display_name: str
    role: Role
    email: Optional[str] = None
    created_at: str
    last_login: Optional[str] = None
    topology_count: int = 0
    # Role-tier flags computed by the backend and shipped to the
    # frontend so the user-menu dropdown can show admin-only /
    # owner-only items without duplicating the role-matching logic
    # on both sides of the wire.
    is_admin: bool = False
    is_owner: bool = False


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[Role] = None
    password: Optional[str] = Field(None, min_length=6)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)


# -- Topology Domains --

class TopologyDomainCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: str = ""


class TopologyDomainInfo(BaseModel):
    id: str
    name: str
    description: str
    owner: str
    is_shared: bool = False
    shared_with: List[str] = []
    topology_count: int = 0
    created_at: str
    updated_at: str
    # Built-in (system-provided) domains: 'default' for owners, '__shared_with_me' for everyone.
    # The frontend uses these flags to gate destructive UI (delete/rename/share buttons).
    is_built_in: bool = False
    is_locked: bool = False
    is_shared_with_me_domain: bool = False
    permission: Optional[str] = None
    # For shared-in domains only: the owner-local raw domain id. The
    # composite `<owner>:<original_domain_id>` is the PK of the central
    # shared_domains / domain_shares tables, which the recipient-side
    # remove endpoint needs to evict the share. Exposing the raw id
    # lets the frontend reconstruct that key without re-calling
    # /api/domains/share/incoming (which would double the network cost
    # on every dropdown open).
    original_domain_id: Optional[str] = None


class TopologyDomainUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    description: Optional[str] = None


class ShareDomainRequest(BaseModel):
    target_users: List[str]
    permission: str = Field("read", pattern=r"^(read|write)$")


class UnshareRequest(BaseModel):
    target_user: str


# -- Sharing Observability --

class ShareRecipient(BaseModel):
    username: str
    display_name: Optional[str] = None
    role: Optional[str] = None
    permission: str
    granted_at: str
    granted_by: str


class TopologyMetaLite(BaseModel):
    id: str
    name: str
    domain_id: str
    created_at: str
    updated_at: str
    object_count: int = 0
    device_count: int = 0
    link_count: int = 0


class OutgoingShareInfo(BaseModel):
    domain_id: str
    composite_id: str
    name: str
    description: str = ""
    owner: str
    created_at: str
    updated_at: str
    topology_count: int = 0
    recipient_count: int = 0
    recipients: List[ShareRecipient] = []
    topologies: List[TopologyMetaLite] = []


class IncomingShareInfo(BaseModel):
    domain_id: str
    original_domain_id: str
    name: str
    description: str = ""
    owner: str
    owner_display_name: Optional[str] = None
    owner_role: Optional[str] = None
    permission: str
    granted_at: str
    granted_by: str
    created_at: str
    updated_at: str
    topology_count: int = 0
    topologies: List[TopologyMetaLite] = []


class ShareActivityEntry(BaseModel):
    id: int
    ts: str
    action: str
    domain_id: str
    domain_name: str
    owner: str
    actor: str
    target_user: Optional[str] = None
    permission: Optional[str] = None
    notes: Optional[str] = None


class ShareOverview(BaseModel):
    username: str
    domains_shared_out: int = 0
    topologies_shared_out: int = 0
    files_shared_out: int = 0
    unique_recipients: int = 0
    domains_shared_with_me: int = 0
    files_shared_with_me: int = 0


class ShareTargetUser(BaseModel):
    username: str
    display_name: str
    role: str


# -- Per-file (per-topology) sharing --

class ShareTopologyRequest(BaseModel):
    target_users: List[str]
    permission: str = Field("read", pattern=r"^(read|write)$")


class OutgoingTopologyShareInfo(BaseModel):
    composite_id: str
    owner: str
    domain_id: str
    topology_id: str
    name: str
    created_at: str
    updated_at: str
    object_count: int = 0
    device_count: int = 0
    link_count: int = 0
    recipient_count: int = 0
    recipients: List[ShareRecipient] = []


class IncomingTopologyShareInfo(BaseModel):
    id: str
    composite_id: str
    domain_id: str
    owner: str
    owner_display_name: Optional[str] = None
    owner_role: Optional[str] = None
    source_domain_id: str
    source_domain_name: Optional[str] = None
    source_topology_id: str
    name: str
    created_at: str
    updated_at: str
    object_count: int = 0
    device_count: int = 0
    link_count: int = 0
    permission: str
    granted_at: str
    granted_by: str
    is_shared_with_me: bool = True


# -- Topology Files within a Domain --

class TopologySave(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    data: Dict[str, Any]


class TopologyMeta(BaseModel):
    id: str
    name: str
    domain_id: str
    created_at: str
    updated_at: str
    object_count: int = 0
    device_count: int = 0
    link_count: int = 0
    # Per-file share badges (only populated for rows in the "Shared with me" inbox)
    is_shared_with_me: bool = False
    owner: Optional[str] = None
    owner_display_name: Optional[str] = None
    permission: Optional[str] = None
    source_domain_id: Optional[str] = None
    source_topology_id: Optional[str] = None
    # The `<owner>:<domain_id>:<topology_id>` key used to identify a
    # share when the recipient wants to self-remove it. Only set for
    # inbox rows that come from the central share table.
    composite_id: Optional[str] = None


# -- Admin --

class UserListResponse(BaseModel):
    users: List[UserInfo]
    total: int


class HealthResponse(BaseModel):
    status: str
    multiuser: bool
    users_total: int
    users_online: int
    uptime_seconds: float
