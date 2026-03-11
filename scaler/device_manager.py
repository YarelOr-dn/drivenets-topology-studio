"""Device management for SCALER - handles device CRUD and settings."""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

from .models import Device, Platform


class DeviceManager:
    """Manages DNOS devices and settings."""
    
    def __init__(self, db_path: str = None):
        """Initialize device manager.
        
        Args:
            db_path: Path to devices.json file. Defaults to db/devices.json
        """
        if db_path:
            self.db_path = Path(db_path)
        else:
            # Default to db/devices.json relative to SCALER root
            self.db_path = Path(__file__).parent.parent / "db" / "devices.json"
        
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """Ensure the database file exists with proper structure."""
        if not self.db_path.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._save_db({"devices": [], "settings": self._default_settings()})
    
    def _default_settings(self) -> Dict[str, Any]:
        """Return default settings."""
        return {
            "sync_interval_minutes": 60,
            "auto_sync_enabled": False,
            "default_platform": "NCP"
        }
    
    def _load_db(self) -> Dict[str, Any]:
        """Load database from JSON file."""
        try:
            with open(self.db_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"devices": [], "settings": self._default_settings()}
    
    def _save_db(self, data: Dict[str, Any]):
        """Save database to JSON file."""
        with open(self.db_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def list_devices(self) -> List[Device]:
        """List all configured devices.
        
        Returns:
            List of Device objects
        """
        db = self._load_db()
        devices = []
        for d in db.get("devices", []):
            try:
                devices.append(Device(**d))
            except Exception:
                # Skip invalid entries
                pass
        return devices
    
    def get_device(self, device_id: str) -> Optional[Device]:
        """Get a device by ID.
        
        Args:
            device_id: Device ID to look up
        
        Returns:
            Device object or None if not found
        """
        db = self._load_db()
        for d in db.get("devices", []):
            if d.get("id") == device_id:
                try:
                    return Device(**d)
                except Exception:
                    return None
        return None
    
    def device_exists(self, device_id: str) -> bool:
        """Check if a device exists.
        
        Args:
            device_id: Device ID to check
        
        Returns:
            True if device exists
        """
        return self.get_device(device_id) is not None
    
    def add_device(
        self,
        device_id: str,
        hostname: str,
        ip: str,
        username: str = "dnroot",
        password: str = None,
        platform: Platform = Platform.NCP,
        description: str = None
    ) -> Device:
        """Add a new device.
        
        Args:
            device_id: Unique device ID
            hostname: Device hostname
            ip: IP address or DNS name
            username: SSH username
            password: SSH password (plain text, will be encoded)
            platform: Hardware platform
            description: Device description
        
        Returns:
            Created Device object
        """
        if self.device_exists(device_id):
            raise ValueError(f"Device {device_id} already exists")
        
        # Encode password
        encoded_password = Device.encode_password(password) if password else ""
        
        device = Device(
            id=device_id,
            hostname=hostname,
            ip=ip,
            username=username,
            password=encoded_password,
            platform=platform,
            description=description
        )
        
        db = self._load_db()
        db["devices"].append(device.model_dump())
        self._save_db(db)
        
        return device
    
    def remove_device(self, device_id: str) -> bool:
        """Remove a device.
        
        Args:
            device_id: Device ID to remove
        
        Returns:
            True if device was removed, False if not found
        """
        db = self._load_db()
        original_count = len(db["devices"])
        db["devices"] = [d for d in db["devices"] if d.get("id") != device_id]
        
        if len(db["devices"]) < original_count:
            self._save_db(db)
            return True
        return False
    
    def update_device(
        self,
        device_id: str,
        hostname: str = None,
        ip: str = None,
        username: str = None,
        password: str = None,
        platform: Platform = None,
        description: str = None,
        last_sync: datetime = None,
        management_ip: str = None
    ) -> Optional[Device]:
        """Update a device.
        
        Args:
            device_id: Device ID to update
            **kwargs: Fields to update
        
        Returns:
            Updated Device object or None if not found
        """
        db = self._load_db()
        
        for i, d in enumerate(db["devices"]):
            if d.get("id") == device_id:
                if hostname is not None:
                    d["hostname"] = hostname
                if ip is not None:
                    d["ip"] = ip
                if username is not None:
                    d["username"] = username
                if password is not None:
                    d["password"] = Device.encode_password(password)
                if platform is not None:
                    d["platform"] = platform.value if isinstance(platform, Platform) else platform
                if description is not None:
                    d["description"] = description
                if last_sync is not None:
                    d["last_sync"] = last_sync.isoformat() if isinstance(last_sync, datetime) else last_sync
                if management_ip is not None:
                    d["management_ip"] = management_ip
                
                db["devices"][i] = d
                self._save_db(db)
                
                try:
                    return Device(**d)
                except Exception:
                    return None
        
        return None
    
    def get_settings(self) -> Dict[str, Any]:
        """Get current settings.
        
        Returns:
            Settings dictionary
        """
        db = self._load_db()
        return db.get("settings", self._default_settings())
    
    def update_settings(
        self,
        sync_interval_minutes: int = None,
        auto_sync_enabled: bool = None,
        default_platform: str = None
    ) -> Dict[str, Any]:
        """Update settings.
        
        Args:
            **kwargs: Settings to update
        
        Returns:
            Updated settings dictionary
        """
        db = self._load_db()
        settings = db.get("settings", self._default_settings())
        
        if sync_interval_minutes is not None:
            settings["sync_interval_minutes"] = sync_interval_minutes
        if auto_sync_enabled is not None:
            settings["auto_sync_enabled"] = auto_sync_enabled
        if default_platform is not None:
            settings["default_platform"] = default_platform
        
        db["settings"] = settings
        self._save_db(db)
        
        return settings














