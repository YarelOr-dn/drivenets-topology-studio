"""
DNAAS Discovery API Routes (Proxy)

Proxies requests to the discovery_api.py server running on port 8765.
This provides a unified API endpoint for the frontend while reusing
the existing DNAAS discovery implementation.
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import httpx
import paramiko
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor

# SSH credentials (same as dnaas_path_discovery.py)
DEFAULT_SSH_USER = "dnroot"
DEFAULT_SSH_PASS = "dnroot"
SSH_TIMEOUT = 30

# Thread pool for blocking SSH operations
ssh_executor = ThreadPoolExecutor(max_workers=4)

router = APIRouter()

# Discovery API server configuration
DISCOVERY_API_HOST = "localhost"
DISCOVERY_API_PORT = 8765
DISCOVERY_API_BASE = f"http://{DISCOVERY_API_HOST}:{DISCOVERY_API_PORT}"

# Timeout for proxy requests (discovery can take a while)
PROXY_TIMEOUT = 300.0  # 5 minutes


# ============================================================================
# Pydantic Models
# ============================================================================

class DiscoveryStartRequest(BaseModel):
    """Request model for starting a discovery job."""
    serial1: str
    serial2: Optional[str] = None
    bd_aware: Optional[bool] = False


class DiscoveryStartResponse(BaseModel):
    """Response model for discovery job start."""
    job_id: str
    message: str


class DiscoveryStatusResponse(BaseModel):
    """Response model for discovery job status."""
    job_id: str
    status: str
    progress: int
    output_lines: list[str]
    result_file: Optional[str] = None
    error: Optional[str] = None


class DiscoveryFileInfo(BaseModel):
    """Info about a discovery result file."""
    name: str
    path: str
    size: int
    modified: float


class DiscoveryListResponse(BaseModel):
    """Response model for listing discovery files."""
    files: list[DiscoveryFileInfo]


# ============================================================================
# Helper Functions
# ============================================================================

async def proxy_request(
    method: str,
    path: str,
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Proxy a request to the discovery API server.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        path: API path (e.g., /api/discovery/start)
        params: Query parameters
        json_data: JSON body for POST requests
        
    Returns:
        JSON response from the discovery API
        
    Raises:
        HTTPException: If the discovery API is unavailable or returns an error
    """
    url = f"{DISCOVERY_API_BASE}{path}"
    
    try:
        async with httpx.AsyncClient(timeout=PROXY_TIMEOUT) as client:
            if method.upper() == "GET":
                response = await client.get(url, params=params)
            elif method.upper() == "POST":
                response = await client.post(url, params=params, json=json_data)
            else:
                raise HTTPException(status_code=405, detail=f"Method {method} not supported")
            
            # Check for HTTP errors
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=error_data.get("error", "Discovery API error")
                    )
                except Exception:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Discovery API returned status {response.status_code}"
                    )
            
            return response.json()
            
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail=f"Discovery API server not available at {DISCOVERY_API_BASE}. "
                   f"Please run: python3 /home/dn/CURSOR/discovery_api.py"
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Discovery API request timed out"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Proxy error: {str(e)}"
        )


async def proxy_file_request(path: str) -> bytes:
    """
    Proxy a file download request to the discovery API server.
    
    Args:
        path: API path for the file
        
    Returns:
        File content as bytes
    """
    url = f"{DISCOVERY_API_BASE}{path}"
    
    try:
        async with httpx.AsyncClient(timeout=PROXY_TIMEOUT) as client:
            response = await client.get(url)
            
            if response.status_code >= 400:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="File not found or error retrieving file"
                )
            
            return response.content
            
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Discovery API server not available"
        )


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/discovery/start", response_model=DiscoveryStartResponse)
async def start_discovery(request: DiscoveryStartRequest):
    """
    Start a DNAAS path discovery job.
    
    This will trace the path through the DNAAS fabric for the specified
    device serial number(s).
    
    - **serial1**: First device serial number or hostname (required)
    - **serial2**: Second device serial number or hostname (optional)
    - **bd_aware**: Enable bridge domain discovery (optional)
    
    Returns a job_id that can be used to poll for status.
    """
    result = await proxy_request(
        "POST",
        "/api/discovery/start",
        json_data={
            "serial1": request.serial1,
            "serial2": request.serial2,
            "bd_aware": request.bd_aware
        }
    )
    
    return DiscoveryStartResponse(
        job_id=result.get("job_id", ""),
        message=result.get("message", "Discovery started")
    )


@router.get("/discovery/status")
async def get_discovery_status(job_id: str = Query(..., description="Job ID to check")):
    """
    Get the status of a running discovery job.
    
    - **job_id**: The job ID returned from /discovery/start
    
    Returns current progress, output lines, and result file when complete.
    """
    result = await proxy_request(
        "GET",
        "/api/discovery/status",
        params={"job_id": job_id}
    )
    
    return result


@router.get("/discovery/list", response_model=DiscoveryListResponse)
async def list_discovery_files():
    """
    List available discovery result files.
    
    Returns the most recent discovery result files (JSON format).
    """
    result = await proxy_request("GET", "/api/discovery/list")
    
    return DiscoveryListResponse(
        files=[DiscoveryFileInfo(**f) for f in result.get("files", [])]
    )


@router.get("/discovery/file/{filename}")
async def get_discovery_file(filename: str):
    """
    Get a specific discovery result file.
    
    - **filename**: Name of the file (e.g., dnaas_path_20251230_123456.json)
    
    Returns the JSON content of the discovery result.
    """
    # Security: only allow expected file patterns (dnaas_path_* or multi_bd_*)
    valid_prefix = filename.startswith("dnaas_path_") or filename.startswith("multi_bd_") or filename.startswith("dnaas_")
    if not valid_prefix or not filename.endswith(".json"):
        raise HTTPException(
            status_code=400,
            detail="Invalid filename. Only dnaas_path_*.json or multi_bd_*.json files are allowed."
        )
    
    content = await proxy_file_request(f"/api/discovery/file/{filename}")
    
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )


@router.get("/discovery/health")
async def discovery_health_check():
    """
    Check if the discovery API server is available.
    
    Returns status of the discovery_api.py server.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{DISCOVERY_API_BASE}/api/discovery/list")
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "discovery_api": DISCOVERY_API_BASE,
                    "message": "Discovery API server is running"
                }
            else:
                return {
                    "status": "unhealthy",
                    "discovery_api": DISCOVERY_API_BASE,
                    "message": f"Discovery API returned status {response.status_code}"
                }
    except httpx.ConnectError:
        return {
            "status": "unavailable",
            "discovery_api": DISCOVERY_API_BASE,
            "message": "Discovery API server is not running. Start with: python3 discovery_api.py"
        }
    except Exception as e:
        return {
            "status": "error",
            "discovery_api": DISCOVERY_API_BASE,
            "message": str(e)
        }


class DiscoveryCancelRequest(BaseModel):
    """Request model for cancelling a discovery job."""
    job_id: str


@router.post("/discovery/cancel")
async def cancel_discovery(request: DiscoveryCancelRequest):
    """
    Cancel a running DNAAS path discovery job.
    
    - **job_id**: The job ID to cancel
    
    Returns cancellation status.
    """
    result = await proxy_request(
        "POST",
        "/api/discovery/cancel",
        json_data={"job_id": request.job_id}
    )
    
    return result


# ============================================================================
# Interface Details Endpoint (On-Demand Link Table Auto-Fill)
# ============================================================================

class InterfaceDetailsRequest(BaseModel):
    """Request model for fetching interface details."""
    device_a: str  # Device hostname or IP for side A
    device_b: Optional[str] = None  # Device hostname or IP for side B
    interface_a: str  # Interface name on side A
    interface_b: Optional[str] = None  # Interface name on side B
    username: Optional[str] = None
    password: Optional[str] = None


class VlanConfig(BaseModel):
    """VLAN manipulation configuration."""
    encapsulation: Optional[str] = None  # e.g., "dot1q 210"
    rewrite_ingress: Optional[str] = None  # e.g., "push dot1q 210"
    rewrite_egress: Optional[str] = None
    outer_vlan: Optional[int] = None
    inner_vlan: Optional[int] = None


class InterfaceDetailsResponse(BaseModel):
    """Response model for interface details."""
    device: str
    interface: str
    transceiver_type: Optional[str] = None
    vlan_config: Optional[VlanConfig] = None
    raw_config: Optional[str] = None
    error: Optional[str] = None


def _ssh_get_interface_details(
    host: str,
    interface: str,
    username: str,
    password: str
) -> Dict[str, Any]:
    """
    SSH to DNAAS device and get interface details (blocking).
    Uses DNOS CLI syntax.
    
    Returns dict with transceiver_type, vlan_config, interface_state, raw_config.
    """
    result = {
        "device": host,
        "interface": interface,
        "transceiver_type": None,
        "vlan_config": None,
        "interface_state": None,
        "raw_config": None,
        "error": None
    }
    
    try:
        # Connect via SSH
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            host,
            username=username,
            password=password,
            timeout=SSH_TIMEOUT,
            look_for_keys=False,
            allow_agent=False
        )
        
        # DNOS: Get interface configuration using 'show configure interface <interface>'
        config_cmd = f"show configure interface {interface}"
        stdin, stdout, stderr = client.exec_command(config_cmd, timeout=30)
        config_output = stdout.read().decode('utf-8', errors='ignore')
        result["raw_config"] = config_output
        
        # Parse VLAN config from DNOS output
        vlan_cfg = {}
        
        # DNOS encapsulation patterns:
        # - encapsulation dot1q <outer-vlan>
        # - encapsulation dot1q <outer> second-dot1q <inner>
        # - vlan-id <vlan>
        encap_match = re.search(r'encapsulation\s+dot1q\s+(\d+)(?:\s+second-dot1q\s+(\d+))?', config_output)
        if encap_match:
            vlan_cfg["outer_vlan"] = int(encap_match.group(1))
            if encap_match.group(2):
                vlan_cfg["inner_vlan"] = int(encap_match.group(2))
            vlan_cfg["encapsulation"] = encap_match.group(0)
        
        # DNOS vlan-id pattern (for sub-interfaces)
        vlan_id_match = re.search(r'vlan-id\s+(\d+)', config_output)
        if vlan_id_match and "outer_vlan" not in vlan_cfg:
            vlan_cfg["outer_vlan"] = int(vlan_id_match.group(1))
        
        # DNOS rewrite ingress/egress patterns
        rewrite_match = re.search(r'rewrite\s+ingress\s+tag\s+(push|pop|translate)\s+(.+)', config_output)
        if rewrite_match:
            vlan_cfg["rewrite_ingress"] = rewrite_match.group(0)
            vlan_in_rewrite = re.search(r'dot1q\s+(\d+)', rewrite_match.group(2))
            if vlan_in_rewrite and "outer_vlan" not in vlan_cfg:
                vlan_cfg["outer_vlan"] = int(vlan_in_rewrite.group(1))
        
        rewrite_egress_match = re.search(r'rewrite\s+egress\s+tag\s+(push|pop|translate)\s+(.+)', config_output)
        if rewrite_egress_match:
            vlan_cfg["rewrite_egress"] = rewrite_egress_match.group(0)
        
        # L2 service type
        if 'l2-service' in config_output.lower():
            vlan_cfg["l2_service"] = True
        if 'l3vpn' in config_output.lower():
            vlan_cfg["l3_service"] = True
        
        if vlan_cfg:
            result["vlan_config"] = vlan_cfg
        
        # DNOS: Get interface state using 'show interface <interface>'
        state_cmd = f"show interface {interface}"
        stdin, stdout, stderr = client.exec_command(state_cmd, timeout=30)
        state_output = stdout.read().decode('utf-8', errors='ignore')
        
        interface_state = {}
        # Parse admin-state and oper-state
        admin_match = re.search(r'admin[- ]?state[:\s]+(\w+)', state_output, re.IGNORECASE)
        if admin_match:
            interface_state["admin_state"] = admin_match.group(1).lower()
        
        oper_match = re.search(r'oper[- ]?(?:state|status)[:\s]+(\w+)', state_output, re.IGNORECASE)
        if oper_match:
            interface_state["oper_state"] = oper_match.group(1).lower()
        
        # Line protocol state
        line_match = re.search(r'line protocol is (\w+)', state_output, re.IGNORECASE)
        if line_match:
            interface_state["line_protocol"] = line_match.group(1).lower()
        
        if interface_state:
            result["interface_state"] = interface_state
        
        # Get transceiver info (base interface only, no sub-interface suffix)
        # Skip transceiver extraction for bundle interfaces (they don't have physical transceivers)
        base_interface = interface.split('.')[0]
        is_bundle = base_interface.lower().startswith('bundle') or 'lag' in base_interface.lower()
        
        if not is_bundle:
            xcvr_cmd = f"show interface transceiver {base_interface}"
            stdin, stdout, stderr = client.exec_command(xcvr_cmd, timeout=30)
            xcvr_output = stdout.read().decode('utf-8', errors='ignore')
            
            # Parse transceiver type from output
            # Common patterns: "Transceiver type: QSFP28", "Type: SFP+", "Module type: QSFP-DD"
            xcvr_patterns = [
                r'(?:Transceiver|Module)\s+type[:\s]+([A-Z0-9\-+]+)',
                r'Type[:\s]+([A-Z0-9\-+]+)',
                r'Form\s+Factor[:\s]+([A-Z0-9\-+]+)',
                r'(SFP\+?|SFP28|QSFP\+?|QSFP28|QSFP-DD|OSFP|CFP[24]?)'
            ]
            
            for pattern in xcvr_patterns:
                match = re.search(pattern, xcvr_output, re.IGNORECASE)
                if match:
                    xcvr_type = match.group(1).upper()
                    # Normalize common types
                    if xcvr_type == "SFP":
                        xcvr_type = "SFP"
                    elif "SFP28" in xcvr_type:
                        xcvr_type = "SFP28"
                    elif "SFP+" in xcvr_type or xcvr_type == "SFP+":
                        xcvr_type = "SFP+"
                    elif "QSFP-DD" in xcvr_type:
                        xcvr_type = "QSFP-DD"
                    elif "QSFP28" in xcvr_type:
                        xcvr_type = "QSFP28"
                    elif "QSFP+" in xcvr_type or xcvr_type == "QSFP+":
                        xcvr_type = "QSFP+"
                    elif "OSFP" in xcvr_type:
                        xcvr_type = "OSFP"
                    result["transceiver_type"] = xcvr_type
                    break
        else:
            # Bundle interfaces have no transceiver - mark as N/A
            result["transceiver_type"] = "Bundle (N/A)"
        
        client.close()
        
    except paramiko.AuthenticationException:
        result["error"] = f"SSH authentication failed for {host}"
    except paramiko.SSHException as e:
        result["error"] = f"SSH error for {host}: {str(e)}"
    except Exception as e:
        result["error"] = f"Error connecting to {host}: {str(e)}"
    
    return result


# ============================================================================
# Multi-BD Discovery Endpoints
# ============================================================================

class MultiBDDiscoveryRequest(BaseModel):
    """Request model for starting a multi-BD discovery job."""
    serial: str  # Device serial or hostname
    username: Optional[str] = None
    password: Optional[str] = None


class MultiBDDiscoveryResponse(BaseModel):
    """Response model for multi-BD discovery."""
    job_id: str
    message: str


@router.post("/multi-bd/start", response_model=MultiBDDiscoveryResponse)
async def start_multi_bd_discovery(request: MultiBDDiscoveryRequest):
    """
    Start a Multi-BD path discovery job.
    
    This discovers ALL Bridge Domains from a device and traces their paths
    through the DNAAS fabric, generating a color-coded topology.
    
    - **serial**: Device serial number or hostname (required)
    
    Returns a job_id that can be used to poll for status.
    """
    result = await proxy_request(
        "POST",
        "/api/multi-bd/start",
        json_data={
            "serial": request.serial,
            "username": request.username,
            "password": request.password
        }
    )
    
    return MultiBDDiscoveryResponse(
        job_id=result.get("job_id", ""),
        message=result.get("message", "Multi-BD discovery started")
    )


@router.get("/multi-bd/status")
async def get_multi_bd_status(job_id: str = Query(..., description="Job ID to check")):
    """
    Get the status of a running Multi-BD discovery job.
    
    - **job_id**: The job ID returned from /multi-bd/start
    
    Returns current progress, BD count, and result file when complete.
    """
    result = await proxy_request(
        "GET",
        "/api/multi-bd/status",
        params={"job_id": job_id}
    )
    
    return result


@router.get("/multi-bd/file/{filename}")
async def get_multi_bd_file(filename: str):
    """
    Get a specific multi-BD discovery result file.
    
    - **filename**: Name of the file (e.g., multi_bd_20260104_123456.json)
    
    Returns the JSON content with BD metadata and topology.
    """
    # Security: only allow expected file patterns
    if not (filename.startswith("multi_bd_") or filename.startswith("dnaas_")) or not filename.endswith(".json"):
        raise HTTPException(
            status_code=400,
            detail="Invalid filename. Only multi_bd_*.json or dnaas_*.json files are allowed."
        )
    
    content = await proxy_file_request(f"/api/multi-bd/file/{filename}")
    
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )


class MultiBDCancelRequest(BaseModel):
    """Request model for cancelling a multi-BD discovery job."""
    job_id: str


@router.post("/multi-bd/cancel")
async def cancel_multi_bd_discovery(request: MultiBDCancelRequest):
    """
    Cancel a running Multi-BD discovery job.
    
    - **job_id**: The job ID to cancel
    
    Returns cancellation status.
    """
    result = await proxy_request(
        "POST",
        "/api/multi-bd/cancel",
        json_data={"job_id": request.job_id}
    )
    
    return result


@router.post("/interface-details")
async def get_interface_details(request: InterfaceDetailsRequest):
    """
    Fetch interface details from devices via SSH (on-demand).
    
    Retrieves:
    - Transceiver type from `show interface transceiver <interface>`
    - VLAN manipulation config from `show running-config interface <interface>`
    
    Used by Link Table "Fetch Details" button.
    """
    username = request.username or DEFAULT_SSH_USER
    password = request.password or DEFAULT_SSH_PASS
    
    results = []
    loop = asyncio.get_event_loop()
    
    # Fetch details for side A
    result_a = await loop.run_in_executor(
        ssh_executor,
        _ssh_get_interface_details,
        request.device_a,
        request.interface_a,
        username,
        password
    )
    results.append(result_a)
    
    # Fetch details for side B if provided
    if request.device_b and request.interface_b:
        result_b = await loop.run_in_executor(
            ssh_executor,
            _ssh_get_interface_details,
            request.device_b,
            request.interface_b,
            username,
            password
        )
        results.append(result_b)
    
    return {"interfaces": results}


class EnableLldpRequest(BaseModel):
    """Request to enable LLDP on a device."""
    serial: str


@router.post("/enable-lldp")
async def enable_lldp_on_device(request: EnableLldpRequest):
    """
    Enable LLDP and admin-state on all interfaces of a device.
    
    - **serial**: Device serial number, hostname, or IP address
    
    This helps discover DNAAS neighbors when interfaces are admin-down or LLDP is disabled.
    """
    result = await proxy_request(
        "POST",
        "/api/enable-lldp",
        json_data={"serial": request.serial}
    )
    
    return result


@router.get("/enable-lldp/status")
async def enable_lldp_status(job_id: str = Query(..., description="LLDP enable job ID")):
    """Get status of an LLDP enable job (for real-time feedback)."""
    return await proxy_request("GET", "/api/enable-lldp/status", params={"job_id": job_id})
@router.post("/enable-lldp/cancel")
async def enable_lldp_cancel(job_id: str = Query(..., description="LLDP enable job ID")):
    """Cancel an LLDP enable job and close SSH session."""
    return await proxy_request("POST", "/api/enable-lldp/cancel", params={"job_id": job_id})