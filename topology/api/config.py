"""Centralized typed configuration for Topology Creator multi-user system.

All env vars prefixed with TOPOLOGY_ (e.g. TOPOLOGY_JWT_SECRET).
Validated at import time -- bad values crash before serving requests.
"""

from __future__ import annotations

import secrets
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings


def _load_or_create_jwt_secret() -> str:
    """Persist the JWT secret so tokens survive server restarts."""
    secret_file = Path.home() / ".topology_users" / ".jwt_secret"
    secret_file.parent.mkdir(parents=True, exist_ok=True)
    if secret_file.exists():
        stored = secret_file.read_text().strip()
        if len(stored) >= 32:
            return stored
    new_secret = secrets.token_hex(32)
    secret_file.write_text(new_secret)
    secret_file.chmod(0o600)
    return new_secret


class Settings(BaseSettings):
    multiuser_enabled: bool = True
    jwt_secret: str = _load_or_create_jwt_secret()
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours

    users_base_dir: str = str(Path.home() / ".topology_users")
    shared_topologies_dir: str = str(Path.home() / ".topology_shared")

    default_admin_username: str = "admin"
    default_admin_password: str = "drivenets"

    allowed_roles: List[str] = [
        "viewer",
        "engineer",
        "team_leader",
        "manager",
        "admin",
    ]

    # Role hierarchy (higher index = more privilege)
    # viewer < engineer < team_leader < manager < admin
    role_hierarchy: List[str] = [
        "viewer",
        "engineer",
        "team_leader",
        "manager",
        "admin",
    ]

    allow_self_registration: bool = True
    max_topologies_per_user: int = 50
    max_shared_domains: int = 20

    discovery_api_url: str = "http://127.0.0.1:8765"
    scaler_bridge_url: str = "http://127.0.0.1:8766"

    inventory_path: str = "/home/dn/CURSOR/device_inventory.json"
    inventory_local_filename: str = "device_inventory.json"

    xray_global_config_path: str = str(Path.home() / ".xray_config.json")
    xray_global_captures_dir: str = str(Path.home() / ".xray_captures")
    xray_per_user_config_filename: str = "xray.json"
    xray_per_user_captures_dirname: str = "captures"
    xray_per_user_devices_filename: str = "devices.json"
    xray_per_user_client_filename: str = "client.json"

    model_config = {"env_prefix": "TOPOLOGY_"}


settings = Settings()
