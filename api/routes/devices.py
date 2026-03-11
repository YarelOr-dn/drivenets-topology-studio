"""
Device Management API Routes

Endpoints for managing network devices:
- List, add, update, delete devices
- Test connections
- Sync configurations
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.scaler_bridge import (
    list_devices,
    get_device,
    get_device_object,
    test_device_connection,
    get_running_config,
    reload_device_manager
)

router = APIRouter()


# ============================================================================
# Pydantic Models
# ============================================================================

class DeviceResponse(BaseModel):
    """Device response model."""
    id: str
    hostname: str
    ip: str
    platform: str
    last_sync: Optional[str] = None
    description: Optional[str] = None
    mgmt_ip: Optional[str] = None  # From SCALER operational.json (current management IP)
    serial_number: Optional[str] = None  # From SCALER operational.json (for SSH via serial)
    connection_method: Optional[str] = None  # How SCALER connected: "SSH→SN", "SSH→MGMT", "Console"
    ssh_host: Optional[str] = None  # The actual SSH host that worked (use this for SSH connections)


class DeviceListResponse(BaseModel):
    """Device list response model."""
    devices: List[DeviceResponse]
    count: int


class DeviceCreateRequest(BaseModel):
    """Request model for creating a device."""
    hostname: str
    ip: str
    username: str
    password: str
    platform: str = "NCP"
    description: Optional[str] = None


class ConnectionTestResponse(BaseModel):
    """Response model for connection test."""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None


class SyncResponse(BaseModel):
    """Response model for config sync."""
    success: bool
    lines: Optional[int] = None
    error: Optional[str] = None


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/", response_model=DeviceListResponse)
async def get_all_devices():
    """
    List all configured devices.
    
    Returns a list of all devices registered in the SCALER database.
    """
    devices = list_devices()
    return DeviceListResponse(
        devices=[DeviceResponse(**d) for d in devices],
        count=len(devices)
    )


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device_by_id(device_id: str):
    """
    Get a single device by ID.
    
    - **device_id**: The unique identifier for the device (e.g., 'pe1')
    """
    device = get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    return DeviceResponse(**device)


@router.post("/", response_model=DeviceResponse)
async def create_device(request: DeviceCreateRequest):
    """
    Add a new device.
    
    Creates a new device in the SCALER database.
    """
    # TODO: Implement device creation via DeviceManager
    # For now, return a placeholder error
    raise HTTPException(
        status_code=501, 
        detail="Device creation via API not yet implemented. Use SCALER CLI."
    )


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(device_id: str, request: DeviceCreateRequest):
    """
    Update an existing device.
    """
    device = get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    
    # TODO: Implement device update via DeviceManager
    raise HTTPException(
        status_code=501,
        detail="Device update via API not yet implemented. Use SCALER CLI."
    )


@router.delete("/{device_id}")
async def delete_device(device_id: str):
    """
    Delete a device.
    """
    device = get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    
    # TODO: Implement device deletion via DeviceManager
    raise HTTPException(
        status_code=501,
        detail="Device deletion via API not yet implemented. Use SCALER CLI."
    )


@router.post("/{device_id}/test", response_model=ConnectionTestResponse)
async def test_connection(device_id: str):
    """
    Test SSH connection to a device.
    
    Attempts to establish an SSH connection and run a simple command.
    """
    result = test_device_connection(device_id)
    return ConnectionTestResponse(**result)


@router.post("/{device_id}/sync", response_model=SyncResponse)
async def sync_device_config(device_id: str):
    """
    Sync (refresh) device configuration.
    
    Extracts the running configuration from the device and caches it.
    """
    result = get_running_config(device_id)
    if result["success"]:
        return SyncResponse(
            success=True,
            lines=result.get("lines", 0)
        )
    else:
        return SyncResponse(
            success=False,
            error=result.get("error", "Unknown error")
        )


@router.post("/reload")
async def reload_devices():
    """
    Reload device manager.
    
    Forces a refresh of the device database from disk.
    """
    reload_device_manager()
    return {"success": True, "message": "Device manager reloaded"}











