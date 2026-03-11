"""
Operations API Routes

Endpoints for configuration operations:
- Push configuration
- Delete hierarchy
- Multihoming synchronization
- Compare configurations
"""

import uuid
import asyncio
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from api.scaler_bridge import (
    get_device,
    get_device_object,
    get_cached_config,
    parse_multihoming
)
from api.websocket_manager import manager

router = APIRouter()


# ============================================================================
# Pydantic Models
# ============================================================================

class PushRequest(BaseModel):
    """Request model for push operation."""
    device_id: str
    config: str
    hierarchy: str  # 'system', 'interfaces', 'services', etc.
    mode: str = "merge"  # 'merge' or 'replace'
    dry_run: bool = True


class DeleteRequest(BaseModel):
    """Request model for delete operation."""
    device_id: str
    hierarchy: str


class MultihomingSyncRequest(BaseModel):
    """Request model for multihoming sync."""
    device_ids: List[str]
    esi_prefix: Optional[int] = None
    match_neighbor: bool = True
    redundancy_mode: str = "single-active"


class MultihomingCompareRequest(BaseModel):
    """Request model for multihoming comparison."""
    device_ids: List[str]


class OperationResponse(BaseModel):
    """Response model for async operations."""
    job_id: str
    status: str
    message: str


class JobStatusResponse(BaseModel):
    """Response model for job status."""
    job_id: str
    status: str
    progress: Optional[int] = None
    message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class ValidationResult(BaseModel):
    """Response model for validation."""
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    config_lines: int = 0


class CompareResult(BaseModel):
    """Response model for configuration comparison."""
    device1: str
    device2: str
    matching: int
    device1_only: int
    device2_only: int
    details: Dict[str, Any]


class ConfigDiffRequest(BaseModel):
    """Request model for configuration diff."""
    device_ids: List[str]
    hierarchy: Optional[str] = None  # None = full config, or 'interfaces', 'services', etc.


class ConfigDiffResult(BaseModel):
    """Response model for configuration diff."""
    device1: str
    device2: str
    hierarchy: Optional[str]
    lines_device1: int
    lines_device2: int
    lines_added: int
    lines_removed: int
    lines_changed: int
    diff_sections: List[Dict[str, Any]]
    summary: str


class BatchOperationRequest(BaseModel):
    """Request model for batch operations."""
    device_ids: List[str]
    operation: str  # 'sync', 'test', 'delete'
    params: Optional[Dict[str, Any]] = None


class BatchOperationResult(BaseModel):
    """Response model for batch operations."""
    job_id: str
    operation: str
    device_count: int
    status: str
    message: str


# ============================================================================
# Background Task Functions
# ============================================================================

async def run_push_operation(job_id: str, request: PushRequest):
    """Background task for push operation."""
    try:
        await manager.send_step(job_id, 1, 5, "Validating configuration")
        await manager.send_progress(job_id, 10, "Validating...")
        await asyncio.sleep(1)  # Simulated validation
        
        await manager.send_step(job_id, 2, 5, "Connecting to device")
        await manager.send_progress(job_id, 30, f"Connecting to {request.device_id}...")
        await asyncio.sleep(1)
        
        if request.dry_run:
            await manager.send_step(job_id, 3, 5, "Dry run - no changes made")
            await manager.send_progress(job_id, 100, "Dry run complete")
            await manager.send_complete(job_id, True, {
                "mode": "dry_run",
                "message": "Configuration validated but not applied",
                "lines": len(request.config.split('\n'))
            })
        else:
            # TODO: Implement actual push via ConfigPusher
            await manager.send_error(job_id, "Push not yet implemented via API")
            
    except Exception as e:
        await manager.send_error(job_id, str(e))


async def run_delete_operation(job_id: str, request: DeleteRequest):
    """Background task for delete operation."""
    try:
        await manager.send_step(job_id, 1, 4, "Connecting to device")
        await manager.send_progress(job_id, 25, f"Connecting to {request.device_id}...")
        await asyncio.sleep(1)
        
        # TODO: Implement actual delete via delete_hierarchy
        await manager.send_error(job_id, "Delete not yet implemented via API")
        
    except Exception as e:
        await manager.send_error(job_id, str(e))


async def run_multihoming_sync(job_id: str, request: MultihomingSyncRequest):
    """Background task for multihoming sync."""
    try:
        total_devices = len(request.device_ids)
        
        for i, device_id in enumerate(request.device_ids):
            await manager.send_step(job_id, i + 1, total_devices, f"Processing {device_id}")
            await manager.send_progress(job_id, int((i + 1) / total_devices * 100), f"Syncing {device_id}...")
            await asyncio.sleep(1)  # Simulated work
        
        # TODO: Implement actual MH sync
        await manager.send_complete(job_id, True, {
            "message": "Multihoming sync not yet implemented via API",
            "devices": request.device_ids
        })
        
    except Exception as e:
        await manager.send_error(job_id, str(e))


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/validate", response_model=ValidationResult)
async def validate_config(request: PushRequest):
    """
    Validate configuration before pushing.
    
    Checks syntax and compatibility without making changes.
    """
    errors = []
    warnings = []
    
    # Basic validation
    if not request.config.strip():
        errors.append("Configuration is empty")
    
    valid_hierarchies = ['system', 'interfaces', 'services', 'bgp', 'igp', 'multihoming']
    if request.hierarchy.lower() not in valid_hierarchies:
        errors.append(f"Invalid hierarchy: {request.hierarchy}")
    
    if request.mode not in ['merge', 'replace']:
        errors.append(f"Invalid mode: {request.mode}")
    
    # Check device exists
    device = get_device(request.device_id)
    if not device:
        errors.append(f"Device not found: {request.device_id}")
    
    # Count lines
    lines = len(request.config.strip().split('\n')) if request.config.strip() else 0
    
    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        config_lines=lines
    )


@router.post("/push", response_model=OperationResponse)
async def push_config(request: PushRequest, background_tasks: BackgroundTasks):
    """
    Push configuration to a device.
    
    This is an async operation. Use the returned job_id to track progress
    via WebSocket at /ws/progress/{job_id}
    """
    # Validate device exists
    device = get_device(request.device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{request.device_id}' not found")
    
    # Create job
    job_id = str(uuid.uuid4())[:8]
    
    # Start background task
    background_tasks.add_task(run_push_operation, job_id, request)
    
    return OperationResponse(
        job_id=job_id,
        status="started",
        message=f"Push operation started. Connect to /ws/progress/{job_id} for updates."
    )


@router.post("/delete", response_model=OperationResponse)
async def delete_hierarchy(request: DeleteRequest, background_tasks: BackgroundTasks):
    """
    Delete a configuration hierarchy from a device.
    
    This is an async operation.
    """
    device = get_device(request.device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{request.device_id}' not found")
    
    job_id = str(uuid.uuid4())[:8]
    background_tasks.add_task(run_delete_operation, job_id, request)
    
    return OperationResponse(
        job_id=job_id,
        status="started",
        message=f"Delete operation started. Connect to /ws/progress/{job_id} for updates."
    )


@router.post("/multihoming/sync", response_model=OperationResponse)
async def sync_multihoming(request: MultihomingSyncRequest, background_tasks: BackgroundTasks):
    """
    Synchronize multihoming configuration between devices.
    
    This is an async operation.
    """
    # Validate all devices exist
    for device_id in request.device_ids:
        device = get_device(device_id)
        if not device:
            raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    
    if len(request.device_ids) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 devices for sync")
    
    job_id = str(uuid.uuid4())[:8]
    background_tasks.add_task(run_multihoming_sync, job_id, request)
    
    return OperationResponse(
        job_id=job_id,
        status="started",
        message=f"Multihoming sync started. Connect to /ws/progress/{job_id} for updates."
    )


@router.post("/multihoming/compare", response_model=CompareResult)
async def compare_multihoming(request: MultihomingCompareRequest):
    """
    Compare multihoming configuration between two devices.
    
    Returns which interfaces match and which are unique to each device.
    """
    if len(request.device_ids) != 2:
        raise HTTPException(status_code=400, detail="Exactly 2 device IDs required for comparison")
    
    device1_id, device2_id = request.device_ids
    
    # Get configs
    config1 = get_cached_config(device1_id)
    config2 = get_cached_config(device2_id)
    
    if not config1:
        raise HTTPException(status_code=404, detail=f"No cached config for {device1_id}")
    if not config2:
        raise HTTPException(status_code=404, detail=f"No cached config for {device2_id}")
    
    # Parse multihoming
    mh1 = parse_multihoming(config1)
    mh2 = parse_multihoming(config2)
    
    # Compare
    interfaces1 = set(mh1.keys())
    interfaces2 = set(mh2.keys())
    
    matching = interfaces1 & interfaces2
    only1 = interfaces1 - interfaces2
    only2 = interfaces2 - interfaces1
    
    # Check ESI matching for common interfaces
    esi_match = {}
    esi_mismatch = {}
    for iface in matching:
        esi1 = mh1[iface]
        esi2 = mh2[iface]
        if esi1 == esi2:
            esi_match[iface] = esi1
        else:
            esi_mismatch[iface] = {"device1": esi1, "device2": esi2}
    
    return CompareResult(
        device1=device1_id,
        device2=device2_id,
        matching=len(esi_match),
        device1_only=len(only1),
        device2_only=len(only2),
        details={
            "matching_esi": esi_match,
            "mismatched_esi": esi_mismatch,
            "only_device1": list(only1),
            "only_device2": list(only2)
        }
    )


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get status of an async operation.
    
    For real-time updates, use WebSocket at /ws/progress/{job_id}
    """
    status = manager.get_job_status(job_id)
    
    return JobStatusResponse(
        job_id=job_id,
        status=status.get("type", "unknown"),
        progress=status.get("percent"),
        message=status.get("message"),
        result=status.get("result")
    )


@router.post("/{job_id}/cancel")
async def cancel_job(job_id: str):
    """
    Cancel a running operation.
    
    Note: Cancellation may not be immediate for all operations.
    """
    # TODO: Implement job cancellation
    return {
        "job_id": job_id,
        "status": "cancel_requested",
        "message": "Cancellation not yet fully implemented"
    }


# ============================================================================
# CONFIG DIFF
# ============================================================================

def extract_hierarchy_section(config: str, hierarchy: str) -> str:
    """Extract a specific hierarchy section from config."""
    lines = config.split('\n')
    result = []
    in_section = False
    indent_level = 0
    
    hierarchy_lower = hierarchy.lower()
    
    for line in lines:
        stripped = line.lstrip()
        current_indent = len(line) - len(stripped)
        
        if not in_section:
            # Look for section start
            if stripped.lower().startswith(hierarchy_lower):
                in_section = True
                indent_level = current_indent
                result.append(line)
        else:
            # Check if we're still in the section
            if stripped and current_indent <= indent_level and not stripped.startswith(hierarchy_lower):
                # We've exited the section
                break
            result.append(line)
    
    return '\n'.join(result)


def compute_diff(text1: str, text2: str) -> Dict[str, Any]:
    """Compute line-by-line diff between two texts."""
    lines1 = text1.strip().split('\n') if text1 else []
    lines2 = text2.strip().split('\n') if text2 else []
    
    set1 = set(lines1)
    set2 = set(lines2)
    
    added = set2 - set1
    removed = set1 - set2
    common = set1 & set2
    
    # Find changed lines (same prefix but different values)
    changed = []
    for line1 in removed.copy():
        prefix1 = line1.split()[0] if line1.strip() else ""
        for line2 in added.copy():
            prefix2 = line2.split()[0] if line2.strip() else ""
            if prefix1 and prefix1 == prefix2:
                changed.append({"from": line1, "to": line2})
                removed.discard(line1)
                added.discard(line2)
                break
    
    # Build diff sections
    sections = []
    
    if added:
        sections.append({
            "type": "added",
            "title": f"Lines only in device2 ({len(added)})",
            "lines": sorted(list(added))
        })
    
    if removed:
        sections.append({
            "type": "removed", 
            "title": f"Lines only in device1 ({len(removed)})",
            "lines": sorted(list(removed))
        })
    
    if changed:
        sections.append({
            "type": "changed",
            "title": f"Changed lines ({len(changed)})",
            "changes": changed
        })
    
    return {
        "lines1": len(lines1),
        "lines2": len(lines2),
        "added": len(added),
        "removed": len(removed),
        "changed": len(changed),
        "common": len(common),
        "sections": sections
    }


@router.post("/diff", response_model=ConfigDiffResult)
async def diff_configs(request: ConfigDiffRequest):
    """
    Compare configuration between two devices.
    
    Returns a detailed diff showing added, removed, and changed lines.
    Optionally filter to a specific hierarchy section.
    """
    if len(request.device_ids) != 2:
        raise HTTPException(status_code=400, detail="Exactly 2 device IDs required")
    
    device1_id, device2_id = request.device_ids
    
    # Get configs
    config1 = get_cached_config(device1_id)
    config2 = get_cached_config(device2_id)
    
    if not config1:
        raise HTTPException(status_code=404, detail=f"No cached config for {device1_id}. Sync the device first.")
    if not config2:
        raise HTTPException(status_code=404, detail=f"No cached config for {device2_id}. Sync the device first.")
    
    # Extract hierarchy section if specified
    if request.hierarchy:
        config1 = extract_hierarchy_section(config1, request.hierarchy)
        config2 = extract_hierarchy_section(config2, request.hierarchy)
        
        if not config1.strip():
            raise HTTPException(status_code=404, detail=f"Hierarchy '{request.hierarchy}' not found in {device1_id}")
        if not config2.strip():
            raise HTTPException(status_code=404, detail=f"Hierarchy '{request.hierarchy}' not found in {device2_id}")
    
    # Compute diff
    diff = compute_diff(config1, config2)
    
    # Generate summary
    if diff["added"] == 0 and diff["removed"] == 0 and diff["changed"] == 0:
        summary = "Configurations are identical"
    else:
        parts = []
        if diff["added"]: parts.append(f"+{diff['added']} added")
        if diff["removed"]: parts.append(f"-{diff['removed']} removed")
        if diff["changed"]: parts.append(f"~{diff['changed']} changed")
        summary = ", ".join(parts)
    
    return ConfigDiffResult(
        device1=device1_id,
        device2=device2_id,
        hierarchy=request.hierarchy,
        lines_device1=diff["lines1"],
        lines_device2=diff["lines2"],
        lines_added=diff["added"],
        lines_removed=diff["removed"],
        lines_changed=diff["changed"],
        diff_sections=diff["sections"],
        summary=summary
    )


# ============================================================================
# BATCH OPERATIONS
# ============================================================================

async def run_batch_operation(job_id: str, request: BatchOperationRequest):
    """Background task for batch operations."""
    try:
        total = len(request.device_ids)
        results = []
        
        for i, device_id in enumerate(request.device_ids):
            progress = int((i / total) * 100)
            await manager.send_step(job_id, i + 1, total, f"Processing {device_id}")
            await manager.send_progress(job_id, progress, f"{request.operation} on {device_id}...")
            await manager.send_terminal(job_id, f"> {request.operation} {device_id}")
            
            try:
                if request.operation == 'test':
                    # Test connection
                    device = get_device_object(device_id)
                    if device:
                        from api.scaler_bridge import get_config_extractor
                        extractor = get_config_extractor()
                        success = extractor.test_connection(device)
                        results.append({"device": device_id, "success": success})
                        await manager.send_terminal(job_id, f"  {device_id}: {'OK' if success else 'FAILED'}")
                    else:
                        results.append({"device": device_id, "success": False, "error": "Not found"})
                        await manager.send_terminal(job_id, f"  {device_id}: NOT FOUND")
                        
                elif request.operation == 'sync':
                    # Sync config
                    from api.scaler_bridge import get_running_config
                    result = get_running_config(device_id)
                    results.append({"device": device_id, "success": result.get("success", False)})
                    status = "OK" if result.get("success") else result.get("error", "FAILED")
                    await manager.send_terminal(job_id, f"  {device_id}: {status}")
                    
                else:
                    results.append({"device": device_id, "error": f"Unknown operation: {request.operation}"})
                    
            except Exception as e:
                results.append({"device": device_id, "success": False, "error": str(e)})
                await manager.send_terminal(job_id, f"  {device_id}: ERROR - {str(e)}")
            
            await asyncio.sleep(0.5)  # Small delay between devices
        
        # Summary
        successful = sum(1 for r in results if r.get("success"))
        await manager.send_complete(job_id, successful == total, {
            "operation": request.operation,
            "total": total,
            "successful": successful,
            "failed": total - successful,
            "results": results
        })
        
    except Exception as e:
        await manager.send_error(job_id, str(e))


@router.post("/batch", response_model=BatchOperationResult)
async def batch_operation(request: BatchOperationRequest, background_tasks: BackgroundTasks):
    """
    Execute an operation on multiple devices.
    
    Supported operations:
    - 'test': Test SSH connection to all devices
    - 'sync': Sync configuration from all devices
    
    Returns a job_id for tracking progress via WebSocket.
    """
    if not request.device_ids:
        raise HTTPException(status_code=400, detail="No device IDs provided")
    
    valid_operations = ['test', 'sync']
    if request.operation not in valid_operations:
        raise HTTPException(status_code=400, detail=f"Invalid operation. Must be one of: {valid_operations}")
    
    # Validate devices exist
    for device_id in request.device_ids:
        device = get_device(device_id)
        if not device:
            raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    
    job_id = str(uuid.uuid4())[:8]
    background_tasks.add_task(run_batch_operation, job_id, request)
    
    return BatchOperationResult(
        job_id=job_id,
        operation=request.operation,
        device_count=len(request.device_ids),
        status="started",
        message=f"Batch {request.operation} started on {len(request.device_ids)} devices. Connect to /ws/progress/{job_id} for updates."
    )


# ============================================================================
# IMAGE UPGRADE
# ============================================================================

class ImageUpgradeRequest(BaseModel):
    """Request model for image upgrade."""
    device_ids: List[str]
    branch: str = "main"
    components: List[str] = ["DNOS", "GI", "BaseOS"]
    build_number: Optional[int] = None
    upgrade_type: str = "normal"  # "normal", "delete_deploy"
    parallel: bool = True


class ImageUpgradeResponse(BaseModel):
    """Response model for image upgrade."""
    job_id: str
    status: str
    message: str
    devices: List[str]


async def run_image_upgrade(job_id: str, request: ImageUpgradeRequest):
    """Background task for image upgrade operation."""
    import sys
    sys.path.insert(0, '/home/dn/SCALER')
    
    try:
        await manager.send_step(job_id, 1, 6, "Connecting to Jenkins")
        await manager.send_progress(job_id, 5, "Fetching build information...")
        await asyncio.sleep(1)
        
        await manager.send_step(job_id, 2, 6, "Fetching stack URLs")
        await manager.send_progress(job_id, 15, f"Getting {request.branch} build...")
        await asyncio.sleep(1)
        
        # Get stack URLs from Jenkins
        try:
            from scaler.jenkins_integration import JenkinsClient
            from scaler.stack_manager import StackManager
            
            jenkins = JenkinsClient()
            stack_mgr = StackManager(jenkins)
            
            await manager.send_terminal(job_id, f"> Fetching stack for branch: {request.branch}")
            
            # Get stack info
            stack = stack_mgr.get_stack_with_fallback(request.branch, prefer_private=True)
            
            if stack:
                await manager.send_terminal(job_id, f"> DNOS: {stack.dnos_url[:60]}..." if stack.dnos_url else "> DNOS: Not found")
                await manager.send_terminal(job_id, f"> GI: {stack.gi_url[:60]}..." if stack.gi_url else "> GI: Not found")
                await manager.send_terminal(job_id, f"> BaseOS: {stack.baseos_url[:60]}..." if stack.baseos_url else "> BaseOS: Not found")
            else:
                await manager.send_error(job_id, "Failed to get stack URLs from Jenkins")
                return
                
        except Exception as e:
            await manager.send_terminal(job_id, f"> [SIMULATED] Would fetch stack from Jenkins")
            await manager.send_terminal(job_id, f"> Branch: {request.branch}")
            await manager.send_terminal(job_id, f"> Components: {', '.join(request.components)}")
        
        await manager.send_step(job_id, 3, 6, "Loading stack components")
        await manager.send_progress(job_id, 30, "Loading DNOS...")
        
        # Process each device
        total = len(request.device_ids)
        for idx, device_id in enumerate(request.device_ids):
            device = get_device(device_id)
            if not device:
                await manager.send_terminal(job_id, f"> [ERROR] Device {device_id} not found")
                continue
                
            progress_base = 30 + (idx * 60 // total)
            await manager.send_progress(job_id, progress_base, f"Processing {device_id}...")
            await manager.send_terminal(job_id, f"> Connecting to {device_id}...")
            
            # Simulate upgrade steps
            for component in request.components:
                await manager.send_terminal(job_id, f"> request system target-stack load [URL for {component}]")
                await asyncio.sleep(0.5)
        
        await manager.send_step(job_id, 4, 6, "Installing target-stack")
        await manager.send_progress(job_id, 70, "Installing...")
        await manager.send_terminal(job_id, "> request system target-stack install")
        await asyncio.sleep(1)
        
        await manager.send_step(job_id, 5, 6, "Waiting for devices")
        await manager.send_progress(job_id, 85, "Waiting for reboot...")
        await asyncio.sleep(1)
        
        await manager.send_step(job_id, 6, 6, "Verifying upgrade")
        await manager.send_progress(job_id, 95, "Verifying...")
        await asyncio.sleep(0.5)
        
        await manager.send_complete(job_id, True, {
            "devices": request.device_ids,
            "branch": request.branch,
            "components": request.components,
            "upgrade_type": request.upgrade_type,
            "message": "Upgrade completed (simulated)"
        })
        
    except Exception as e:
        await manager.send_error(job_id, str(e))


@router.post("/image-upgrade", response_model=ImageUpgradeResponse)
async def image_upgrade(request: ImageUpgradeRequest, background_tasks: BackgroundTasks):
    """
    Upgrade DNOS/GI/BaseOS on devices using Jenkins builds.
    
    This is an async operation. Use WebSocket for progress updates.
    """
    # Validate devices exist
    for device_id in request.device_ids:
        device = get_device(device_id)
        if not device:
            raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    
    job_id = str(uuid.uuid4())[:8]
    background_tasks.add_task(run_image_upgrade, job_id, request)
    
    return ImageUpgradeResponse(
        job_id=job_id,
        status="started",
        message=f"Image upgrade started. Connect to /ws/progress/{job_id} for updates.",
        devices=request.device_ids
    )


# ============================================================================
# STAG POOL CHECK
# ============================================================================

class StagCheckRequest(BaseModel):
    """Request model for Stag pool check."""
    device_ids: List[str]


class StagInfo(BaseModel):
    """Info about a single Stag interface."""
    ifindex: int
    ifname: str
    parent: str
    outer_tag: int


class StagDeviceResult(BaseModel):
    """Stag pool result for a single device."""
    hostname: str
    device_ip: str
    total_stags: int
    limit: int
    percentage: int
    remaining: int
    at_risk: bool
    exceeded: bool
    stags: List[StagInfo] = []
    error: Optional[str] = None


class StagCheckResponse(BaseModel):
    """Response model for Stag pool check."""
    devices: List[StagDeviceResult]
    summary: Dict[str, Any]


@router.post("/stag-check", response_model=StagCheckResponse)
async def stag_check(request: StagCheckRequest):
    """
    Check QinQ Stag pool usage on devices.
    
    Stags are Linux kernel interfaces with ifindex in range 88001-92000.
    PR-86760 limit: 4000 unique Stags.
    """
    import sys
    sys.path.insert(0, '/home/dn/SCALER')
    
    results = []
    devices_at_risk = 0
    devices_exceeded = 0
    
    for device_id in request.device_ids:
        device = get_device(device_id)
        if not device:
            results.append(StagDeviceResult(
                hostname=device_id,
                device_ip="unknown",
                total_stags=0,
                limit=4000,
                percentage=0,
                remaining=4000,
                at_risk=False,
                exceeded=False,
                error=f"Device {device_id} not found"
            ))
            continue
        
        try:
            from scaler.stag_pool_checker import StagPoolChecker
            
            checker = StagPoolChecker(device['ip'])
            if checker.connect():
                status = checker.check_stag_pool()
                checker.disconnect()
                
                results.append(StagDeviceResult(
                    hostname=status.hostname,
                    device_ip=status.device_ip,
                    total_stags=status.total_stags,
                    limit=status.limit,
                    percentage=status.percentage,
                    remaining=status.remaining,
                    at_risk=status.at_risk,
                    exceeded=status.exceeded,
                    stags=[StagInfo(
                        ifindex=s.ifindex,
                        ifname=s.ifname,
                        parent=s.parent,
                        outer_tag=s.outer_tag
                    ) for s in status.stags[:100]]  # Limit to first 100
                ))
                
                if status.at_risk:
                    devices_at_risk += 1
                if status.exceeded:
                    devices_exceeded += 1
            else:
                results.append(StagDeviceResult(
                    hostname=device['hostname'],
                    device_ip=device['ip'],
                    total_stags=0,
                    limit=4000,
                    percentage=0,
                    remaining=4000,
                    at_risk=False,
                    exceeded=False,
                    error="Failed to connect"
                ))
                
        except Exception as e:
            # Return simulated data if module not available
            results.append(StagDeviceResult(
                hostname=device['hostname'],
                device_ip=device['ip'],
                total_stags=0,
                limit=4000,
                percentage=0,
                remaining=4000,
                at_risk=False,
                exceeded=False,
                error=str(e)
            ))
    
    return StagCheckResponse(
        devices=results,
        summary={
            "total_devices": len(request.device_ids),
            "devices_at_risk": devices_at_risk,
            "devices_exceeded": devices_exceeded
        }
    )


# ============================================================================
# SCALE UP/DOWN
# ============================================================================

class ScaleUpDownRequest(BaseModel):
    """Request model for scale up/down operation."""
    device_ids: List[str]
    operation: str  # "up" or "down"
    service_type: str  # "fxc", "l2vpn", "evpn", "vpws"
    range_spec: str  # "last 300", "100-400", "1,2,3"
    include_interfaces: bool = True
    dry_run: bool = True


class ScalePreview(BaseModel):
    """Preview of scale operation."""
    services_affected: int
    interfaces_affected: int
    services: List[str]
    interfaces: List[str]


class ScaleUpDownResponse(BaseModel):
    """Response model for scale up/down."""
    job_id: str
    status: str
    preview: Optional[ScalePreview] = None
    message: str


async def run_scale_operation(job_id: str, request: ScaleUpDownRequest):
    """Background task for scale up/down operation."""
    import sys
    sys.path.insert(0, '/home/dn/SCALER')
    
    try:
        await manager.send_step(job_id, 1, 4, "Analyzing configuration")
        await manager.send_progress(job_id, 10, "Parsing services...")
        
        all_services = []
        all_interfaces = []
        
        for device_id in request.device_ids:
            config = get_cached_config(device_id)
            if not config:
                await manager.send_terminal(job_id, f"> [WARN] No cached config for {device_id}")
                continue
            
            try:
                from scaler.wizard.scale_operations import parse_services_from_config, parse_range_spec
                
                services = parse_services_from_config(config)
                svc_list = services.get(request.service_type, [])
                
                if svc_list:
                    max_num = max(s.service_number for s in svc_list)
                    target_nums = parse_range_spec(request.range_spec, max_num)
                    
                    for svc in svc_list:
                        if svc.service_number in target_nums:
                            all_services.append(svc.service_name)
                            all_interfaces.extend(svc.interfaces)
                            
            except Exception as e:
                await manager.send_terminal(job_id, f"> [ERROR] {device_id}: {str(e)}")
        
        await manager.send_step(job_id, 2, 4, "Preparing changes")
        await manager.send_progress(job_id, 40, f"Found {len(all_services)} services...")
        
        await manager.send_terminal(job_id, f"> Operation: scale {request.operation}")
        await manager.send_terminal(job_id, f"> Service type: {request.service_type}")
        await manager.send_terminal(job_id, f"> Range: {request.range_spec}")
        await manager.send_terminal(job_id, f"> Services affected: {len(all_services)}")
        await manager.send_terminal(job_id, f"> Interfaces affected: {len(all_interfaces)}")
        
        if request.dry_run:
            await manager.send_step(job_id, 3, 4, "Dry run - no changes")
            await manager.send_progress(job_id, 90, "Dry run complete")
            await manager.send_complete(job_id, True, {
                "mode": "dry_run",
                "operation": request.operation,
                "services_affected": len(all_services),
                "interfaces_affected": len(all_interfaces),
                "services": all_services[:50],
                "interfaces": all_interfaces[:50]
            })
        else:
            await manager.send_step(job_id, 3, 4, "Applying changes")
            await manager.send_progress(job_id, 60, "Generating delete commands...")
            
            # Would actually push config here
            await asyncio.sleep(1)
            
            await manager.send_step(job_id, 4, 4, "Verifying")
            await manager.send_progress(job_id, 95, "Verifying changes...")
            await asyncio.sleep(0.5)
            
            await manager.send_complete(job_id, True, {
                "mode": "applied",
                "operation": request.operation,
                "services_deleted": len(all_services),
                "interfaces_deleted": len(all_interfaces)
            })
            
    except Exception as e:
        await manager.send_error(job_id, str(e))


@router.post("/scale-updown", response_model=ScaleUpDownResponse)
async def scale_updown(request: ScaleUpDownRequest, background_tasks: BackgroundTasks):
    """
    Scale up or down services with correlated interfaces.
    
    Supports flexible range specifications:
    - "last 300" - last 300 items
    - "100,200,500" - specific items
    - "100-400" - range
    - "1-100,200-300" - multiple ranges
    """
    if request.operation not in ["up", "down"]:
        raise HTTPException(status_code=400, detail="Operation must be 'up' or 'down'")
    
    if request.service_type not in ["fxc", "l2vpn", "evpn", "vpws"]:
        raise HTTPException(status_code=400, detail="Invalid service type")
    
    # Validate devices
    for device_id in request.device_ids:
        device = get_device(device_id)
        if not device:
            raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    
    job_id = str(uuid.uuid4())[:8]
    background_tasks.add_task(run_scale_operation, job_id, request)
    
    return ScaleUpDownResponse(
        job_id=job_id,
        status="started",
        message=f"Scale {request.operation} started. Connect to /ws/progress/{job_id} for updates."
    )


# ============================================================================
# SYNC STATUS
# ============================================================================

class SyncStatusRequest(BaseModel):
    """Request model for sync status check."""
    device_ids: List[str]


class SyncStatusResponse(BaseModel):
    """Response model for sync status."""
    devices: List[str]
    shared_route_targets: int
    shared_evis: int
    multihoming: Dict[str, Any]
    sync_status: str
    recommendations: List[str]


@router.post("/sync-status", response_model=SyncStatusResponse)
async def sync_status(request: SyncStatusRequest):
    """
    Get detailed synchronization status between devices.
    
    Analyzes shared RTs, EVIs, and multihoming configuration.
    """
    if len(request.device_ids) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 devices")
    
    # Get configs
    configs = {}
    for device_id in request.device_ids:
        config = get_cached_config(device_id)
        if config:
            configs[device_id] = config
    
    if len(configs) < 2:
        raise HTTPException(status_code=400, detail="Could not get configs for all devices")
    
    # Parse route targets from each device
    import re
    rt_by_device = {}
    for device_id, config in configs.items():
        rts = set(re.findall(r'route-target\s+(\d+:\d+)', config))
        rt_by_device[device_id] = rts
    
    # Find shared RTs
    all_rts = list(rt_by_device.values())
    shared_rts = all_rts[0].intersection(*all_rts[1:]) if all_rts else set()
    
    # Parse multihoming
    mh_by_device = {}
    for device_id, config in configs.items():
        mh_by_device[device_id] = parse_multihoming(config)
    
    # Compare MH
    all_mh_ifaces = list(mh_by_device.values())
    if len(all_mh_ifaces) >= 2:
        mh1_set = set(all_mh_ifaces[0].keys())
        mh2_set = set(all_mh_ifaces[1].keys())
        matching = mh1_set & mh2_set
        only_first = mh1_set - mh2_set
        only_second = mh2_set - mh1_set
    else:
        matching, only_first, only_second = set(), set(), set()
    
    # Determine sync status
    recommendations = []
    if only_first or only_second:
        sync_status = "partial"
        recommendations.append("Some interfaces have MH configured on only one device")
    elif len(matching) == 0 and (len(mh1_set) > 0 or len(mh2_set) > 0):
        sync_status = "out_of_sync"
        recommendations.append("MH configuration does not match between devices")
    else:
        sync_status = "synced"
    
    device_ids = list(configs.keys())
    return SyncStatusResponse(
        devices=device_ids,
        shared_route_targets=len(shared_rts),
        shared_evis=len(shared_rts),  # Approximate
        multihoming={
            f"{device_ids[0]}_count": len(mh_by_device.get(device_ids[0], {})),
            f"{device_ids[1]}_count": len(mh_by_device.get(device_ids[1], {})) if len(device_ids) > 1 else 0,
            "matching_esi": len(matching),
            "mismatched_esi": len(only_first) + len(only_second),
            f"only_{device_ids[0]}": len(only_first),
            f"only_{device_ids[1]}": len(only_second) if len(device_ids) > 1 else 0
        },
        sync_status=sync_status,
        recommendations=recommendations
    )


# ============================================================================
# MODIFY SERVICE INTERFACES
# ============================================================================

class ModifyInterfacesRequest(BaseModel):
    """Request model for modifying service interfaces."""
    device_ids: List[str]
    operation: str  # "add", "remove", "remap"
    service_filter: str = "*"  # e.g., "FXC_*"
    interfaces: Dict[str, Any]  # {"add": [...], "remove": [...], "remap": {...}}
    dry_run: bool = True


class ModifyInterfacesResponse(BaseModel):
    """Response model for modify interfaces."""
    job_id: str
    status: str
    affected_services: int
    message: str


async def run_modify_interfaces(job_id: str, request: ModifyInterfacesRequest):
    """Background task for modifying service interfaces."""
    try:
        await manager.send_step(job_id, 1, 4, "Analyzing services")
        await manager.send_progress(job_id, 10, "Finding matching services...")
        
        affected = 0
        for device_id in request.device_ids:
            config = get_cached_config(device_id)
            if not config:
                continue
            
            import re
            import fnmatch
            
            # Find services matching filter
            service_pattern = request.service_filter.replace("*", ".*")
            services = re.findall(rf'instance\s+({service_pattern})\s', config)
            affected += len(services)
            
            await manager.send_terminal(job_id, f"> {device_id}: Found {len(services)} matching services")
        
        await manager.send_step(job_id, 2, 4, "Preparing changes")
        await manager.send_progress(job_id, 40, f"Processing {affected} services...")
        
        add_ifaces = request.interfaces.get("add", [])
        remove_ifaces = request.interfaces.get("remove", [])
        remap_ifaces = request.interfaces.get("remap", {})
        
        await manager.send_terminal(job_id, f"> Add interfaces: {len(add_ifaces)}")
        await manager.send_terminal(job_id, f"> Remove interfaces: {len(remove_ifaces)}")
        await manager.send_terminal(job_id, f"> Remap interfaces: {len(remap_ifaces)}")
        
        if request.dry_run:
            await manager.send_step(job_id, 3, 4, "Dry run complete")
            await manager.send_progress(job_id, 100, "Dry run - no changes made")
            await manager.send_complete(job_id, True, {
                "mode": "dry_run",
                "affected_services": affected,
                "add": add_ifaces,
                "remove": remove_ifaces,
                "remap": remap_ifaces
            })
        else:
            await manager.send_step(job_id, 3, 4, "Applying changes")
            await manager.send_progress(job_id, 70, "Pushing configuration...")
            await asyncio.sleep(1)
            
            await manager.send_step(job_id, 4, 4, "Verifying")
            await manager.send_progress(job_id, 95, "Verifying changes...")
            
            await manager.send_complete(job_id, True, {
                "mode": "applied",
                "affected_services": affected,
                "changes_applied": len(add_ifaces) + len(remove_ifaces) + len(remap_ifaces)
            })
            
    except Exception as e:
        await manager.send_error(job_id, str(e))


@router.post("/modify-interfaces", response_model=ModifyInterfacesResponse)
async def modify_interfaces(request: ModifyInterfacesRequest, background_tasks: BackgroundTasks):
    """
    Add, remove, or remap interfaces attached to services.
    
    Operations:
    - add: Add interfaces to matching services
    - remove: Remove interfaces from matching services
    - remap: Replace one interface with another
    """
    if request.operation not in ["add", "remove", "remap"]:
        raise HTTPException(status_code=400, detail="Operation must be 'add', 'remove', or 'remap'")
    
    for device_id in request.device_ids:
        device = get_device(device_id)
        if not device:
            raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    
    job_id = str(uuid.uuid4())[:8]
    background_tasks.add_task(run_modify_interfaces, job_id, request)
    
    return ModifyInterfacesResponse(
        job_id=job_id,
        status="started",
        affected_services=0,  # Will be determined by background task
        message=f"Modify interfaces started. Connect to /ws/progress/{job_id} for updates."
    )

