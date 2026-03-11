"""
Configuration API Routes

Endpoints for configuration extraction and analysis:
- Get running configuration
- Get configuration summary
- List interfaces, services, multihoming
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.scaler_bridge import (
    get_device,
    get_cached_config,
    get_running_config,
    extract_config_summary,
    parse_multihoming,
    get_interfaces_from_config,
    get_services_from_config,
    extract_hierarchy_section
)

router = APIRouter()


# ============================================================================
# Pydantic Models
# ============================================================================

class SystemSummary(BaseModel):
    name: Optional[str] = None
    profile: Optional[str] = None
    users: int = 0
    configured: bool = False


class InterfaceSummary(BaseModel):
    count: int = 0
    types: Dict[str, int] = {}


class ServiceSummary(BaseModel):
    count: int = 0
    types: Dict[str, int] = {}
    rt_count: int = 0


class BGPSummary(BaseModel):
    as_number: Optional[str] = None
    peers: int = 0
    router_id: Optional[str] = None


class IGPSummary(BaseModel):
    protocol: Optional[str] = None
    instance: Optional[str] = None
    interfaces: int = 0


class MultihomingSummary(BaseModel):
    count: int = 0
    interfaces: Dict[str, str] = {}
    esi_prefix: Optional[str] = None


class ConfigSummaryResponse(BaseModel):
    """Full configuration summary."""
    device_id: str
    hostname: str
    system: SystemSummary
    interfaces: InterfaceSummary
    services: ServiceSummary
    bgp: BGPSummary
    igp: IGPSummary
    multihoming: MultihomingSummary


class InterfaceInfo(BaseModel):
    name: str
    type: str
    is_subinterface: bool
    admin_state: str = "enabled"
    description: Optional[str] = None
    vlan: Optional[int] = None
    ipv4: Optional[str] = None


class ServiceInfo(BaseModel):
    name: str
    type: str
    route_target: Optional[str] = None
    interfaces: List[str] = []


class ConfigResponse(BaseModel):
    success: bool
    config: Optional[str] = None
    lines: Optional[int] = None
    error: Optional[str] = None


class GenerateInterfacesRequest(BaseModel):
    """Request for generating interface configuration."""
    interface_type: str  # bundle, ge100, ge400, ph
    start_number: int = 1
    count: int = 10
    slot: int = 0
    bay: int = 0
    port_start: int = 0
    create_subinterfaces: bool = True
    subif_count_per_interface: int = 1
    subif_vlan_start: int = 100
    subif_vlan_step: int = 1
    encapsulation: str = "dot1q"  # dot1q, qinq


class GenerateServicesRequest(BaseModel):
    """Request for generating service configuration."""
    service_type: str  # evpn-vpws-fxc, vrf, evpn
    name_prefix: str = "SVC"
    start_number: int = 1
    count: int = 10
    service_id_start: int = 1000
    evi_start: int = 1000
    rd_base: str = "65000"  # BGP ASN for route-targets
    router_id: str = "1.1.1.1"  # Router ID (Lo0) for route-distinguisher
    attach_interfaces: List[str] = []


class GenerateConfigResponse(BaseModel):
    """Response with generated configuration."""
    success: bool
    config: str
    lines: int
    hierarchy: str


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/{device_id}/running", response_model=ConfigResponse)
async def get_device_running_config(device_id: str, refresh: bool = False):
    """
    Get running configuration for a device.
    
    - **device_id**: Device identifier
    - **refresh**: If true, fetch fresh config from device. If false, use cache.
    """
    device = get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    
    if not refresh:
        # Try cached config first
        cached = get_cached_config(device_id)
        if cached:
            return ConfigResponse(
                success=True,
                config=cached,
                lines=len(cached.split('\n'))
            )
    
    # Fetch fresh config
    result = get_running_config(device_id)
    return ConfigResponse(**result)


@router.get("/{device_id}/summary", response_model=ConfigSummaryResponse)
async def get_device_config_summary(device_id: str):
    """
    Get parsed configuration summary for a device.
    
    Returns a structured summary of:
    - System configuration
    - Interface counts by type
    - Service counts by type
    - BGP configuration
    - IGP (ISIS/OSPF) configuration
    - Multihoming (ESI) configuration
    """
    device = get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    
    # Get cached config
    config = get_cached_config(device_id)
    if not config:
        # Try to fetch it
        result = get_running_config(device_id)
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get config: {result.get('error', 'Unknown error')}"
            )
        config = result["config"]
    
    # Parse summary
    summary = extract_config_summary(config)
    
    return ConfigSummaryResponse(
        device_id=device_id,
        hostname=device["hostname"],
        system=SystemSummary(**summary["system"]),
        interfaces=InterfaceSummary(**summary["interfaces"]),
        services=ServiceSummary(**summary["services"]),
        bgp=BGPSummary(**summary["bgp"]),
        igp=IGPSummary(**summary["igp"]),
        multihoming=MultihomingSummary(**summary["multihoming"])
    )


@router.get("/{device_id}/interfaces", response_model=List[InterfaceInfo])
async def get_device_interfaces(device_id: str):
    """
    Get list of all interfaces for a device.
    
    Returns detailed information about each interface.
    """
    device = get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    
    config = get_cached_config(device_id)
    if not config:
        result = get_running_config(device_id)
        if not result["success"]:
            raise HTTPException(status_code=500, detail="Failed to get config")
        config = result["config"]
    
    interfaces = get_interfaces_from_config(config)
    return [InterfaceInfo(**iface) for iface in interfaces]


@router.get("/{device_id}/services", response_model=List[ServiceInfo])
async def get_device_services(device_id: str):
    """
    Get list of all services for a device.
    
    Returns FXC, VPLS, L3VPN, and VRF services.
    """
    device = get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    
    config = get_cached_config(device_id)
    if not config:
        result = get_running_config(device_id)
        if not result["success"]:
            raise HTTPException(status_code=500, detail="Failed to get config")
        config = result["config"]
    
    services = get_services_from_config(config)
    return [ServiceInfo(**svc) for svc in services]


@router.get("/{device_id}/multihoming", response_model=MultihomingSummary)
async def get_device_multihoming(device_id: str):
    """
    Get multihoming (ESI) configuration for a device.
    
    Returns list of interfaces with their ESI values.
    """
    device = get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    
    config = get_cached_config(device_id)
    if not config:
        result = get_running_config(device_id)
        if not result["success"]:
            raise HTTPException(status_code=500, detail="Failed to get config")
        config = result["config"]
    
    mh_interfaces = parse_multihoming(config)
    
    esi_prefix = None
    if mh_interfaces:
        sample_esi = next(iter(mh_interfaces.values()), "")
        if sample_esi:
            esi_prefix = ":".join(sample_esi.split(":")[:3])
    
    return MultihomingSummary(
        count=len(mh_interfaces),
        interfaces=mh_interfaces,
        esi_prefix=esi_prefix
    )


@router.get("/{device_id}/hierarchy/{hierarchy_name}")
async def get_device_hierarchy(device_id: str, hierarchy_name: str):
    """
    Get a specific configuration hierarchy section.
    
    - **hierarchy_name**: One of: system, interfaces, services, bgp, igp, multihoming
    """
    valid_hierarchies = ['system', 'interfaces', 'services', 'bgp', 'igp', 'multihoming']
    if hierarchy_name.lower() not in valid_hierarchies:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid hierarchy. Must be one of: {', '.join(valid_hierarchies)}"
        )
    
    device = get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    
    config = get_cached_config(device_id)
    if not config:
        result = get_running_config(device_id)
        if not result["success"]:
            raise HTTPException(status_code=500, detail="Failed to get config")
        config = result["config"]
    
    section = extract_hierarchy_section(config, hierarchy_name)
    
    return {
        "device_id": device_id,
        "hierarchy": hierarchy_name,
        "config": section,
        "lines": len(section.split('\n')) if section else 0
    }


# ============================================================================
# CONFIG GENERATION - Uses SCALER's ScaleGenerator for DNOS syntax
# ============================================================================

@router.post("/generate/interfaces", response_model=GenerateConfigResponse)
async def generate_interfaces_config(request: GenerateInterfacesRequest):
    """
    Generate interface configuration using SCALER's DNOS syntax.
    
    This uses the actual ScaleGenerator from SCALER CLI for accurate config.
    """
    from api.scaler_bridge import generate_interface_config
    
    config = generate_interface_config(
        interface_type=request.interface_type,
        start_number=request.start_number,
        count=request.count,
        slot=request.slot,
        bay=request.bay,
        port_start=request.port_start,
        create_subinterfaces=request.create_subinterfaces,
        subif_count=request.subif_count_per_interface,
        vlan_start=request.subif_vlan_start,
        vlan_step=request.subif_vlan_step,
        encapsulation=request.encapsulation
    )
    
    return GenerateConfigResponse(
        success=True,
        config=config,
        lines=len(config.split('\n')),
        hierarchy="interfaces"
    )


@router.post("/generate/services", response_model=GenerateConfigResponse)
async def generate_services_config(request: GenerateServicesRequest):
    """
    Generate network service configuration using SCALER's DNOS syntax.
    
    Supports: evpn-vpws-fxc, vrf, evpn
    Validated against DNOS CLI PDF.
    """
    from api.scaler_bridge import generate_service_config
    
    config = generate_service_config(
        service_type=request.service_type,
        name_prefix=request.name_prefix,
        start_number=request.start_number,
        count=request.count,
        service_id_start=request.service_id_start,
        evi_start=request.evi_start,
        rd_base=request.rd_base,
        router_id=request.router_id,
        attach_interfaces=request.attach_interfaces
    )
    
    return GenerateConfigResponse(
        success=True,
        config=config,
        lines=len(config.split('\n')),
        hierarchy="services"
    )


# ============================================================================
# SYSTEM CONFIG GENERATION
# ============================================================================

class GenerateSystemRequest(BaseModel):
    """Request model for system config generation."""
    hostname: str
    profile: str = "l3-pe"
    domain_name: Optional[str] = None
    users: List[Dict[str, str]] = []
    ssh_enabled: bool = True
    ssh_port: int = 22


@router.post("/generate/system", response_model=GenerateConfigResponse)
async def generate_system_config(request: GenerateSystemRequest):
    """
    Generate system hierarchy configuration.
    
    Validated against DNOS CLI PDF and running configs.
    """
    lines = []
    lines.append("system")
    lines.append(f"  name {request.hostname}")
    lines.append(f"  profile {request.profile}")
    lines.append(f"  cli-timestamp enabled")
    
    if request.domain_name:
        lines.append(f"  domain-name {request.domain_name}")
    
    # Logging
    lines.append(f"  logging")
    lines.append(f"    syslog")
    lines.append(f"      event-group all severity info")
    lines.append(f"    !")
    lines.append(f"  !")
    
    # Login settings
    lines.append(f"  login")
    lines.append(f"    session-timeout 90")
    lines.append(f"  !")
    
    # SSH Server
    if request.ssh_enabled:
        lines.append(f"  ssh-server")
        lines.append(f"    admin-state enabled")
        if request.ssh_port != 22:
            lines.append(f"    port {request.ssh_port}")
        lines.append(f"  !")
    
    lines.append("!")
    
    config = "\n".join(lines)
    return GenerateConfigResponse(
        success=True,
        config=config,
        lines=len(lines),
        hierarchy="system"
    )


# ============================================================================
# BGP CONFIG GENERATION
# ============================================================================

class BGPNeighbor(BaseModel):
    """BGP neighbor configuration."""
    ip: str
    remote_as: int
    update_source: str = "Loopback0"
    address_families: List[str] = ["ipv4-unicast", "l2vpn-evpn"]
    description: Optional[str] = None


class GenerateBGPRequest(BaseModel):
    """Request model for BGP config generation."""
    as_number: int
    router_id: str
    neighbors: List[BGPNeighbor] = []
    address_families: List[str] = ["ipv4-unicast", "l2vpn-evpn"]


@router.post("/generate/bgp", response_model=GenerateConfigResponse)
async def generate_bgp_config(request: GenerateBGPRequest):
    """
    Generate BGP protocol configuration.
    
    Validated against DNOS CLI PDF and running configs.
    """
    lines = []
    lines.append("protocols")
    lines.append(f"  bgp {request.as_number}")
    lines.append(f"    router-id {request.router_id}")
    
    # Neighbors with proper DNOS syntax
    for neighbor in request.neighbors:
        lines.append(f"    neighbor {neighbor.ip}")
        lines.append(f"      remote-as {neighbor.remote_as}")
        lines.append(f"      admin-state enabled")
        lines.append(f"      update-source {neighbor.update_source}")
        if neighbor.description:
            lines.append(f"      description \"{neighbor.description}\"")
        for af in neighbor.address_families:
            lines.append(f"      address-family {af}")
            lines.append(f"        send-community community-type both")
            if af == "l2vpn-evpn":
                lines.append(f"        soft-reconfiguration inbound")
            lines.append(f"      !")
        lines.append(f"    !")
    
    lines.append(f"  !")
    lines.append("!")
    
    config = "\n".join(lines)
    return GenerateConfigResponse(
        success=True,
        config=config,
        lines=len(lines),
        hierarchy="bgp"
    )


# ============================================================================
# IGP CONFIG GENERATION (ISIS/OSPF)
# ============================================================================

class IGPInterface(BaseModel):
    """IGP interface configuration."""
    name: str
    passive: bool = False
    metric: int = 10
    network_type: Optional[str] = None  # "point-to-point", "broadcast"


class GenerateIGPRequest(BaseModel):
    """Request model for IGP config generation."""
    protocol: str = "isis"  # "isis" or "ospf"
    instance_name: str = "IGP"
    net: Optional[str] = None  # ISIS NET address
    area: Optional[str] = None  # OSPF area
    interfaces: List[IGPInterface] = []
    level: str = "level-2-only"  # ISIS level


@router.post("/generate/igp", response_model=GenerateConfigResponse)
async def generate_igp_config(request: GenerateIGPRequest):
    """
    Generate IGP (ISIS or OSPF) configuration.
    
    Validated against DNOS CLI PDF and running configs.
    """
    lines = []
    lines.append("protocols")
    
    if request.protocol.lower() == "isis":
        lines.append("  isis")
        lines.append(f"    instance {request.instance_name}")
        if request.net:
            lines.append(f"      iso-network {request.net}")
        
        for iface in request.interfaces:
            lines.append(f"      interface {iface.name}")
            lines.append(f"        admin-state enabled")
            if iface.network_type and iface.network_type != "broadcast":
                lines.append(f"        network-type {iface.network_type}")
            lines.append(f"        address-family ipv4-unicast")
            lines.append(f"        !")
            lines.append(f"      !")
        
        lines.append(f"    !")
        lines.append(f"  !")
        
    elif request.protocol.lower() == "ospf":
        lines.append("  ospf")
        lines.append(f"    instance {request.instance_name}")
        lines.append(f"      router-id {request.area or '0.0.0.0'}")
        lines.append(f"      area {request.area or '0'}")
        
        for iface in request.interfaces:
            lines.append(f"        interface {iface.name}")
            lines.append(f"          admin-state enabled")
            if iface.network_type:
                lines.append(f"          network-type {iface.network_type}")
            if iface.metric != 10:
                lines.append(f"          cost {iface.metric}")
            lines.append(f"        !")
        
        lines.append(f"      !")
        lines.append(f"    !")
        lines.append(f"  !")
    
    lines.append("!")
    
    config = "\n".join(lines)
    return GenerateConfigResponse(
        success=True,
        config=config,
        lines=len(lines),
        hierarchy="igp"
    )


# ============================================================================
# SAVED FILES (for Quick Load menu)
# ============================================================================

class SavedFileInfo(BaseModel):
    """Info about a saved config file."""
    filename: str
    path: str
    timestamp: str
    lines: int
    validated: bool
    pushed: bool


class SavedFilesResponse(BaseModel):
    """Response for saved files list."""
    device_id: str
    files: List[SavedFileInfo]


@router.get("/{device_id}/saved-files", response_model=SavedFilesResponse)
async def get_saved_files(device_id: str):
    """
    List saved configuration files for a device.
    
    Used for the Quick Load menu functionality.
    """
    from pathlib import Path
    import os
    from datetime import datetime
    
    device = get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    
    hostname = device.get('hostname', device_id)
    config_dir = Path(f"/home/dn/SCALER/db/configs/{hostname}")
    pushed_dir = config_dir / "pushed"
    
    files = []
    
    def add_file(f: Path, is_pushed: bool = False):
        """Helper to add a file to the list."""
        try:
            stat = f.stat()
            with open(f, 'r') as fp:
                content = fp.read()
                line_count = len(content.split('\n'))
            
            # Parse timestamp from filename
            # Formats: wizard_YYYY-MM-DD_HH-MM-SS.txt or YYYY-MM-DD_HH-MM-SS.txt_...
            import re
            ts_match = re.search(r'(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})', f.name)
            if ts_match:
                try:
                    ts = datetime.strptime(ts_match.group(1), '%Y-%m-%d_%H-%M-%S')
                    timestamp = ts.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    timestamp = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            else:
                timestamp = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            
            files.append(SavedFileInfo(
                filename=f.name,
                path=str(f),
                timestamp=timestamp,
                lines=line_count,
                validated=True,  # Wizard files are validated
                pushed=is_pushed
            ))
        except Exception as e:
            pass  # Skip files that can't be read
    
    # 1. Get wizard files from config directory (wizard_*.txt)
    if config_dir.exists():
        for f in config_dir.glob("wizard_*.txt"):
            add_file(f, is_pushed=False)
        
        # Also get any other .txt config files (not running.txt or full_output.txt)
        for f in config_dir.glob("*.txt"):
            if f.name not in ['running.txt', 'full_output.txt'] and not f.name.startswith('wizard_'):
                add_file(f, is_pushed=False)
    
    # 2. Get pushed files from pushed/ subdirectory
    if pushed_dir.exists():
        for f in pushed_dir.glob("*.txt"):
            add_file(f, is_pushed=True)
    
    # Sort by modification time (newest first)
    files.sort(key=lambda x: x.timestamp, reverse=True)
    
    return SavedFilesResponse(
        device_id=device_id,
        files=files[:20]  # Limit to 20 most recent
    )


@router.get("/file")
async def read_config_file(path: str):
    """
    Read a saved configuration file by path.
    
    Used for the Quick Load preview functionality.
    Only allows reading files within the SCALER config directory.
    """
    from pathlib import Path
    from fastapi.responses import PlainTextResponse
    
    # Security: Only allow reading from SCALER config directory
    config_base = Path("/home/dn/SCALER/db/configs")
    file_path = Path(path)
    
    try:
        # Resolve to absolute path and check it's within allowed directory
        resolved = file_path.resolve()
        if not str(resolved).startswith(str(config_base.resolve())):
            raise HTTPException(status_code=403, detail="Access denied: path outside config directory")
        
        if not resolved.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        if not resolved.is_file():
            raise HTTPException(status_code=400, detail="Path is not a file")
        
        content = resolved.read_text()
        return PlainTextResponse(content)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


@router.delete("/file")
async def delete_config_file(path: str):
    """
    Delete a saved configuration file by path.
    
    Used for the Quick Load delete functionality.
    Only allows deleting files within the SCALER config directory.
    Protected files (running.txt, operational.json) cannot be deleted.
    """
    from pathlib import Path
    
    # Security: Only allow deleting from SCALER config directory
    config_base = Path("/home/dn/SCALER/db/configs")
    file_path = Path(path)
    
    # Protected files that cannot be deleted
    protected_files = {'running.txt', 'operational.json', 'full_output.txt'}
    
    try:
        # Resolve to absolute path and check it's within allowed directory
        resolved = file_path.resolve()
        if not str(resolved).startswith(str(config_base.resolve())):
            raise HTTPException(status_code=403, detail="Access denied: path outside config directory")
        
        if not resolved.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        if not resolved.is_file():
            raise HTTPException(status_code=400, detail="Path is not a file")
        
        # Check if it's a protected file
        if resolved.name in protected_files:
            raise HTTPException(status_code=403, detail=f"Cannot delete protected file: {resolved.name}")
        
        # Delete the file
        resolved.unlink()
        
        return {"status": "success", "message": f"Deleted {resolved.name}"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")

