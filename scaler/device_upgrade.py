"""
Device Upgrade Module for DNOS Stack Management

Handles SSH-based upgrade operations on DNOS devices:
- Loading stack components to target-stack
- Installing target-stack
- Monitoring installation progress
- Deploying from GI mode
"""

import re
import time
import json
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple, Callable, Any
from enum import Enum
from datetime import datetime
from pathlib import Path

from .stack_manager import StackInfo, StackComponent


# =============================================================================
# Upgrade Timing Tracking
# =============================================================================

UPGRADE_TIMING_DB_PATH = Path(__file__).parent.parent / "db" / "upgrade_timing_history.json"


def _load_upgrade_timing_db() -> Dict[str, Any]:
    """Load upgrade timing history database."""
    if UPGRADE_TIMING_DB_PATH.exists():
        try:
            with open(UPGRADE_TIMING_DB_PATH, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"entries": [], "averages": {}}
    return {"entries": [], "averages": {}}


def _save_upgrade_timing_db(db: Dict[str, Any]):
    """Save upgrade timing history database."""
    UPGRADE_TIMING_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(UPGRADE_TIMING_DB_PATH, 'w') as f:
        json.dump(db, f, indent=2, default=str)


def save_upgrade_timing(
    device_hostname: str,
    platform: str,
    from_version: str,
    to_version: str,
    components_loaded: List[str],
    load_times: Dict[str, float],
    install_time: float,
    total_time: float,
    upgrade_type: str = "normal",  # "normal", "delete_deploy", "gi_deploy"
    success: bool = True
) -> Dict:
    """
    Save an upgrade timing record after completion.
    
    Args:
        device_hostname: Device name
        platform: Device platform (SA-36CD-S, NCP, etc.)
        from_version: Source DNOS version
        to_version: Target DNOS version
        components_loaded: List of components loaded (DNOS, GI, BaseOS)
        load_times: Dict of component -> load time in seconds
        install_time: Time for install phase in seconds
        total_time: Total upgrade time in seconds
        upgrade_type: Type of upgrade (normal, delete_deploy, gi_deploy)
        success: Whether upgrade completed successfully
    """
    db = _load_upgrade_timing_db()
    
    # Determine upgrade category
    upgrade_category = _categorize_upgrade(from_version, to_version, components_loaded)
    
    record = {
        "timestamp": datetime.now().isoformat(),
        "device": device_hostname,
        "platform": platform,
        "from_version": from_version,
        "to_version": to_version,
        "components": components_loaded,
        "load_times": load_times,
        "install_time": install_time,
        "total_time": total_time,
        "upgrade_type": upgrade_type,
        "upgrade_category": upgrade_category,
        "success": success,
        # Derived metrics
        "total_load_time": sum(load_times.values()),
        "component_count": len(components_loaded),
    }
    
    db["entries"].append(record)
    
    # Keep last 50 entries
    if len(db["entries"]) > 50:
        db["entries"] = db["entries"][-50:]
    
    # Recalculate averages
    db["averages"] = _calculate_upgrade_averages(db["entries"])
    
    _save_upgrade_timing_db(db)
    
    return record


def _categorize_upgrade(from_version: str, to_version: str, components: List[str]) -> str:
    """Categorize the type of upgrade for timing predictions."""
    # Extract major.minor versions
    from_match = re.search(r'(\d+)\.(\d+)', from_version or "0.0")
    to_match = re.search(r'(\d+)\.(\d+)', to_version or "0.0")
    
    if not from_match or not to_match:
        return "unknown"
    
    from_major, from_minor = int(from_match.group(1)), int(from_match.group(2))
    to_major, to_minor = int(to_match.group(1)), int(to_match.group(2))
    
    # Categorize by component count and version change
    if "BaseOS" in components:
        base_category = "with_baseos"
    else:
        base_category = "dnos_gi_only"
    
    if to_major > from_major:
        version_change = "major_upgrade"
    elif to_minor > from_minor:
        version_change = "minor_upgrade"
    elif to_version != from_version:
        version_change = "patch_upgrade"
    else:
        version_change = "reinstall"
    
    return f"{base_category}_{version_change}"


def _calculate_upgrade_averages(entries: List[Dict]) -> Dict[str, Dict]:
    """Calculate average timing metrics from historical data."""
    averages = {}
    
    # Group by upgrade category
    category_data = {}
    for entry in entries:
        if not entry.get("success", False):
            continue  # Only use successful upgrades for estimates
        
        category = entry.get("upgrade_category", "unknown")
        if category not in category_data:
            category_data[category] = {
                "total_times": [],
                "load_times": [],
                "install_times": [],
            }
        
        cd = category_data[category]
        cd["total_times"].append(entry.get("total_time", 0))
        cd["load_times"].append(entry.get("total_load_time", 0))
        cd["install_times"].append(entry.get("install_time", 0))
    
    # Calculate averages
    for category, data in category_data.items():
        if data["total_times"]:
            averages[category] = {
                "avg_total_time": sum(data["total_times"]) / len(data["total_times"]),
                "avg_load_time": sum(data["load_times"]) / len(data["load_times"]),
                "avg_install_time": sum(data["install_times"]) / len(data["install_times"]),
                "sample_count": len(data["total_times"]),
                "min_time": min(data["total_times"]),
                "max_time": max(data["total_times"]),
                "last_updated": datetime.now().isoformat(),
            }
    
    # Also calculate overall averages
    all_totals = [e.get("total_time", 0) for e in entries if e.get("success")]
    all_loads = [e.get("total_load_time", 0) for e in entries if e.get("success")]
    all_installs = [e.get("install_time", 0) for e in entries if e.get("success")]
    
    if all_totals:
        averages["_overall"] = {
            "avg_total_time": sum(all_totals) / len(all_totals),
            "avg_load_time": sum(all_loads) / len(all_loads),
            "avg_install_time": sum(all_installs) / len(all_installs),
            "sample_count": len(all_totals),
            "last_updated": datetime.now().isoformat(),
        }
    
    return averages


def get_upgrade_time_estimate(
    from_version: str = None,
    to_version: str = None,
    components: List[str] = None,
    platform: str = None
) -> Dict[str, Any]:
    """
    Get estimated upgrade time based on historical data.
    
    Returns:
        Dict with estimated times and confidence info
    """
    db = _load_upgrade_timing_db()
    averages = db.get("averages", {})
    
    if not averages:
        # No historical data - return default estimates
        return {
            "estimated_total": 1800,  # 30 min default
            "estimated_load": 600,    # 10 min default
            "estimated_install": 1200,  # 20 min default
            "confidence": "low",
            "sample_count": 0,
            "source": "default"
        }
    
    # Try to find matching category
    components = components or ["DNOS", "GI"]
    category = _categorize_upgrade(from_version or "", to_version or "", components)
    
    if category in averages:
        cat_avg = averages[category]
        return {
            "estimated_total": cat_avg["avg_total_time"],
            "estimated_load": cat_avg["avg_load_time"],
            "estimated_install": cat_avg["avg_install_time"],
            "confidence": "high" if cat_avg["sample_count"] >= 3 else "medium",
            "sample_count": cat_avg["sample_count"],
            "source": f"category:{category}",
            "range": (cat_avg.get("min_time", 0), cat_avg.get("max_time", 0))
        }
    
    # Fall back to overall average
    if "_overall" in averages:
        overall = averages["_overall"]
        return {
            "estimated_total": overall["avg_total_time"],
            "estimated_load": overall["avg_load_time"],
            "estimated_install": overall["avg_install_time"],
            "confidence": "medium",
            "sample_count": overall["sample_count"],
            "source": "overall"
        }
    
    # No data
    return {
        "estimated_total": 1800,
        "estimated_load": 600,
        "estimated_install": 1200,
        "confidence": "low",
        "sample_count": 0,
        "source": "default"
    }


def format_time_estimate(seconds: float) -> str:
    """Format seconds as human readable time."""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        mins = int(seconds / 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s" if secs > 0 else f"{mins}m"
    else:
        hours = int(seconds / 3600)
        mins = int((seconds % 3600) / 60)
        return f"{hours}h {mins}m"


class DeviceMode(Enum):
    """Device operating mode."""
    DNOS = "dnos"      # Full DNOS running
    GI = "gi"          # Golden Image mode (gicli)
    UNKNOWN = "unknown"


class LoadStatus(Enum):
    """Status of a target-stack load operation."""
    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class InstallStatus(Enum):
    """Status of installation."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class LoadTask:
    """Represents a target-stack load task."""
    component: str
    url: str
    task_id: Optional[str] = None
    status: LoadStatus = LoadStatus.PENDING
    start_time: Optional[datetime] = None
    finish_time: Optional[datetime] = None
    error_message: str = ""


@dataclass
class InstallTask:
    """Represents an installation task."""
    task_id: Optional[str] = None
    status: InstallStatus = InstallStatus.NOT_STARTED
    install_type: str = ""  # "upgrade", "deploy"
    start_time: Optional[datetime] = None
    elapsed_time: str = ""
    packages: List[Dict] = field(default_factory=list)
    running_tasks: List[Dict] = field(default_factory=list)
    finished_tasks: List[Dict] = field(default_factory=list)
    error_message: str = ""


@dataclass
class DeviceStackState:
    """Current stack state on a device."""
    current: Dict[str, str] = field(default_factory=dict)
    target: Dict[str, str] = field(default_factory=dict)
    revert: Dict[str, str] = field(default_factory=dict)


class DeviceUpgrader:
    """Handles upgrade operations on a single device."""
    
    def __init__(self, hostname: str, ssh_executor: Callable[[str], Tuple[str, int]] = None):
        """
        Args:
            hostname: Device hostname or IP
            ssh_executor: Function that executes SSH commands and returns (output, exit_code)
        """
        self.hostname = hostname
        self._ssh_executor = ssh_executor
        self._mode: DeviceMode = DeviceMode.UNKNOWN
    
    def set_ssh_executor(self, executor: Callable[[str], Tuple[str, int]]):
        """Set the SSH command executor."""
        self._ssh_executor = executor
    
    def _exec(self, command: str) -> Tuple[str, int]:
        """Execute a command via SSH."""
        if not self._ssh_executor:
            raise RuntimeError("SSH executor not configured")
        return self._ssh_executor(command)
    
    def _exec_cli(self, cli_command: str) -> str:
        """Execute a DNOS/GI CLI command."""
        # Wrap command appropriately based on mode
        output, _ = self._exec(cli_command)
        return output
    
    # =========================================================================
    # Mode Detection
    # =========================================================================
    
    def detect_mode(self) -> DeviceMode:
        """Detect if device is in DNOS or GI mode."""
        output, exit_code = self._exec("show version 2>/dev/null || echo GICLI")
        
        if "GICLI" in output or "gicli" in output.lower():
            self._mode = DeviceMode.GI
        elif "DNOS" in output or "DriveNets" in output:
            self._mode = DeviceMode.DNOS
        else:
            # Try another method
            output2, _ = self._exec("show system stack | no-more")
            if "DNOS" in output2:
                self._mode = DeviceMode.DNOS
            else:
                self._mode = DeviceMode.GI
        
        return self._mode
    
    # =========================================================================
    # Stack Information
    # =========================================================================
    
    def get_current_stack(self) -> DeviceStackState:
        """Get current stack state from device."""
        output = self._exec_cli("show system stack | no-more")
        return self._parse_stack_output(output)
    
    def _parse_stack_output(self, output: str) -> DeviceStackState:
        """Parse 'show system stack' output."""
        state = DeviceStackState()
        
        # Parse table format:
        # | Component | HW Model | HW Revision | Revert | Current | Target |
        lines = output.split('\n')
        
        for line in lines:
            if '|' not in line:
                continue
            
            parts = [p.strip() for p in line.split('|')]
            if len(parts) < 7:
                continue
            
            component = parts[1].upper()
            if component in ['COMPONENT', '']:
                continue
            
            revert = parts[4] if len(parts) > 4 else ''
            current = parts[5] if len(parts) > 5 else ''
            target = parts[6] if len(parts) > 6 else ''
            
            if revert:
                state.revert[component] = revert
            if current:
                state.current[component] = current
            if target:
                state.target[component] = target
        
        return state
    
    # =========================================================================
    # Loading Components
    # =========================================================================
    
    def load_component(self, url: str, component_name: str = "") -> LoadTask:
        """Load a component into the target stack.
        
        Args:
            url: Minio URL of the component
            component_name: Human-readable name (e.g., 'DNOS', 'GI', 'BaseOS')
            
        Returns:
            LoadTask with status
        """
        task = LoadTask(
            component=component_name or self._detect_component_from_url(url),
            url=url,
            start_time=datetime.now()
        )
        
        # Execute load command - the ssh_exec handles the "Yes/No" prompt interactively
        # Command: request system target-stack load <URL>
        command = f"request system target-stack load {url}"
        output = self._exec_cli(command)
        
        # Parse task ID from output
        # Example: "started target-stack load NCC 0, task ID = 1720672287369"
        match = re.search(r'task ID\s*=\s*(\d+)', output, re.IGNORECASE)
        if match:
            task.task_id = match.group(1)
            task.status = LoadStatus.IN_PROGRESS
        elif 'error' in output.lower() or 'failed' in output.lower():
            task.status = LoadStatus.FAILED
            task.error_message = output
        elif 'started' in output.lower():
            task.status = LoadStatus.IN_PROGRESS
        else:
            # Assume started if no error
            task.status = LoadStatus.IN_PROGRESS
        
        return task
    
    def _detect_component_from_url(self, url: str) -> str:
        """Detect component type from URL."""
        url_lower = url.lower()
        if 'dnos' in url_lower:
            return 'DNOS'
        elif '_gi_' in url_lower:
            return 'GI'
        elif 'baseos' in url_lower:
            return 'BaseOS'
        elif 'firmware' in url_lower:
            return 'Firmware'
        elif 'onie' in url_lower:
            return 'ONIE'
        return 'Unknown'
    
    def check_load_status(self, task_id: str = None) -> Tuple[LoadStatus, str]:
        """Check status of load operation.
        
        Returns:
            Tuple of (LoadStatus, raw_output) for display
        Uses 'show system target-stack load' to check load progress.
        """
        output = self._exec_cli("show system target-stack load | no-more")
        
        # Parse status from output
        output_lower = output.lower()
        
        # Check for completion indicators
        if 'completed' in output_lower or 'success' in output_lower:
            return LoadStatus.COMPLETED, output
        
        # "There are no download tasks in progress" means load is DONE (or was never started)
        # This is the key indicator that loading has finished
        if 'no download tasks' in output_lower or 'no tasks' in output_lower:
            return LoadStatus.COMPLETED, output
        
        # Check for failure indicators
        if 'failed' in output_lower or 'error' in output_lower:
            return LoadStatus.FAILED, output
        
        # Check for in-progress indicators (must come AFTER "no download tasks" check)
        if 'downloading' in output_lower or 'loading' in output_lower:
            return LoadStatus.IN_PROGRESS, output
        
        # Look for percentage progress (e.g., "50%")
        if re.search(r'\d+\s*%', output):
            return LoadStatus.IN_PROGRESS, output
        
        # Parse Task status field if present
        match = re.search(r'Task status:\s*(\S+)', output, re.IGNORECASE)
        if match:
            status_str = match.group(1).lower()
            if 'complete' in status_str:
                return LoadStatus.COMPLETED, output
            elif 'progress' in status_str:
                return LoadStatus.IN_PROGRESS, output
            elif 'fail' in status_str:
                return LoadStatus.FAILED, output
        
        # If task_id specified and appears in output, still in progress
        if task_id and task_id in output:
            return LoadStatus.IN_PROGRESS, output
        
        # Default: If no clear status and no tasks shown, assume completed
        return LoadStatus.COMPLETED, output
    
    def wait_for_load(self, task: LoadTask, timeout: int = 300, 
                      poll_interval: int = 15,
                      progress_callback: Callable[[str], None] = None,
                      output_callback: Callable[[str], None] = None) -> LoadTask:
        """Wait for a load task to complete.
        
        Args:
            task: LoadTask to monitor
            timeout: Maximum wait time in seconds (default 5 min)
            poll_interval: Time between status checks (default 15s for load operations)
            progress_callback: Optional callback for progress updates
            output_callback: Optional callback for raw output display
            
        Returns:
            Updated LoadTask
        """
        start_time = time.time()
        
        # Initial delay to let the load operation start
        time.sleep(3)
        
        while time.time() - start_time < timeout:
            status, output = self.check_load_status(task.task_id)
            task.status = status
            
            # Send raw output for display
            if output_callback and output:
                output_callback(output)
            
            if progress_callback:
                elapsed = int(time.time() - start_time)
                progress_callback(f"Loading {task.component}: {status.value} ({elapsed}s)")
            
            if status == LoadStatus.COMPLETED:
                task.finish_time = datetime.now()
                return task
            
            if status == LoadStatus.FAILED:
                task.finish_time = datetime.now()
                # Extract error message from output
                task.error_message = output[:200] if output else "Unknown error"
                return task
            
            time.sleep(poll_interval)
        
        task.status = LoadStatus.TIMEOUT
        task.error_message = f"Timeout after {timeout}s"
        return task
    
    def load_stack(self, stack: StackInfo, 
                   progress_callback: Callable[[str, int], None] = None) -> List[LoadTask]:
        """Load all components of a stack.
        
        Loads in order: BaseOS -> GI -> DNOS (recommended order)
        
        Args:
            stack: StackInfo with component URLs
            progress_callback: Optional callback(message, percent)
            
        Returns:
            List of LoadTask results
        """
        tasks = []
        components = []
        
        # Build component list in recommended order
        if stack.baseos and stack.baseos.is_valid:
            components.append(('BaseOS', stack.baseos.url))
        if stack.gi and stack.gi.is_valid:
            components.append(('GI', stack.gi.url))
        if stack.dnos and stack.dnos.is_valid:
            components.append(('DNOS', stack.dnos.url))
        
        total = len(components)
        
        for i, (name, url) in enumerate(components):
            if progress_callback:
                progress_callback(f"Loading {name}...", int((i / total) * 100))
            
            # Start load
            task = self.load_component(url, name)
            
            # Wait for completion
            task = self.wait_for_load(
                task, 
                timeout=600,  # 10 min per component
                progress_callback=lambda msg: progress_callback(msg, int(((i + 0.5) / total) * 100)) if progress_callback else None
            )
            
            tasks.append(task)
            
            # Check for failure
            if task.status == LoadStatus.FAILED:
                if progress_callback:
                    progress_callback(f"Failed to load {name}: {task.error_message}", 100)
                break
        
        if progress_callback:
            progress_callback("Stack loading complete", 100)
        
        return tasks
    
    # =========================================================================
    # Installation
    # =========================================================================
    
    def start_install(self) -> InstallTask:
        """Start target-stack installation (upgrade from DNOS mode)."""
        task = InstallTask(start_time=datetime.now())
        
        # The command prompts: "Do you want to continue? (yes/no)?"
        # ssh_exec handles the Yes/No prompts interactively
        output = self._exec_cli("request system target-stack install")
        
        # Parse response - check for SUCCESS first (task ID means it started)
        match = re.search(r'task ID\s*[=:]\s*(\d+)', output, re.IGNORECASE)
        if match:
            task.task_id = match.group(1)
            task.status = InstallStatus.IN_PROGRESS
            task.install_type = "upgrade"
        elif 'started target stack' in output.lower() or 'started target-stack' in output.lower():
            # Install started even if we didn't get task ID
            task.status = InstallStatus.IN_PROGRESS
            task.install_type = "upgrade"
        elif 'error' in output.lower() and 'task id' not in output.lower():
            # Only fail if there's an error AND no task ID (meaning real failure)
            task.status = InstallStatus.FAILED
            task.error_message = output
        else:
            # Default to in-progress if no clear failure
            task.status = InstallStatus.IN_PROGRESS
            task.install_type = "upgrade"
        
        return task
    
    def start_deploy(self, system_type: str, name: str, ncc_id: int = 0) -> InstallTask:
        """Start deployment (from GI mode).
        
        Args:
            system_type: System type (e.g., 'SA-40C', 'SA-36CD-S', 'CL-16')
            name: System name
            ncc_id: NCC ID (usually 0)
            
        Returns:
            InstallTask
        """
        task = InstallTask(start_time=datetime.now())
        
        # GI deploy command - ssh_exec handles Yes/No prompts interactively
        command = f"request system deploy system-type {system_type} name {name} ncc-id {ncc_id}"
        output = self._exec_cli(command)
        
        if 'error' in output.lower() or 'failed' in output.lower():
            task.status = InstallStatus.FAILED
            task.error_message = output
        else:
            task.status = InstallStatus.IN_PROGRESS
            task.install_type = "deploy"
        
        return task
    
    def check_install_status(self) -> InstallTask:
        """Check installation progress."""
        output = self._exec_cli("show system install | no-more")
        return self._parse_install_output(output)
    
    def _parse_install_output(self, output: str) -> InstallTask:
        """Parse 'show system install' output with full node details."""
        task = InstallTask()
        
        # Parse key fields
        # Task ID: 1719993530376
        match = re.search(r'Task ID:\s*(\S+)', output)
        if match:
            task.task_id = match.group(1)
        
        # Installation type: upgrade
        match = re.search(r'Installation type:\s*(\S+)', output)
        if match:
            task.install_type = match.group(1)
        
        # Task status: IN-PROGRESS / COMPLETED
        match = re.search(r'Task status:\s*(\S+)', output)
        if match:
            status_str = match.group(1).upper()
            if 'COMPLETE' in status_str:
                task.status = InstallStatus.COMPLETED
            elif 'PROGRESS' in status_str:
                task.status = InstallStatus.IN_PROGRESS
            elif 'FAIL' in status_str:
                task.status = InstallStatus.FAILED
        
        # Task elapsed time: 0:05:09
        match = re.search(r'Task elapsed time:\s*(\S+)', output)
        if match:
            task.elapsed_time = match.group(1)
        
        # Parse running tasks table
        # | Node Type | Node ID | Serial Number | Package Type | Start time | ...
        running_section = False
        finished_section = False
        
        for line in output.split('\n'):
            if 'Running tasks:' in line:
                running_section = True
                finished_section = False
                continue
            elif 'Finished tasks:' in line:
                running_section = False
                finished_section = True
                continue
            
            if '|' in line and ('NCC' in line or 'NCP' in line or 'NCF' in line):
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 5:
                    node_info = {
                        'node_type': parts[1] if len(parts) > 1 else '',
                        'node_id': parts[2] if len(parts) > 2 else '',
                        'serial': parts[3] if len(parts) > 3 else '',
                        'package': parts[4] if len(parts) > 4 else '',
                    }
                    
                    if running_section:
                        task.running_tasks.append(node_info)
                    elif finished_section:
                        # Also capture status for finished
                        if len(parts) > 5:
                            node_info['status'] = parts[5]
                        task.finished_tasks.append(node_info)
        
        # Parse installed packages
        # | Type | Version | Name | HW Model | HW Revision |
        packages_section = False
        for line in output.split('\n'):
            if 'Installed Packages:' in line:
                packages_section = True
                continue
            if packages_section and '|' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 4 and parts[1] not in ['Type', '']:
                    task.packages.append({
                        'type': parts[1],
                        'version': parts[2] if len(parts) > 2 else '',
                        'name': parts[3] if len(parts) > 3 else ''
                    })
            if packages_section and 'Running tasks:' in line:
                packages_section = False
        
        return task
    
    def wait_for_install(self, timeout: int = 3600, poll_interval: int = 30,
                          progress_callback: Callable[[str, int], None] = None,
                          live_output_callback: Callable[[str], None] = None) -> InstallTask:
        """Wait for installation to complete with SSH reconnection handling.
        
        Args:
            timeout: Maximum wait time in seconds
            poll_interval: Time between status checks
            progress_callback: Optional callback(message, percent)
            live_output_callback: Optional callback for raw show system install output
            
        Returns:
            Final InstallTask status
        """
        start_time = time.time()
        last_task = InstallTask()
        consecutive_failures = 0
        max_consecutive_failures = 10  # After 10 failures, give up
        
        while time.time() - start_time < timeout:
            try:
                # Get full output for live display
                output = self._exec_cli("show system install | no-more")
                
                if live_output_callback:
                    live_output_callback(output)
                
                task = self._parse_install_output(output)
                last_task = task
                consecutive_failures = 0  # Reset on success
                
                if progress_callback:
                    elapsed = int(time.time() - start_time)
                    # Build status message with node info
                    status_parts = [f"Install {task.status.value}"]
                    if task.elapsed_time:
                        status_parts.append(task.elapsed_time)
                    if task.running_tasks:
                        running = len(task.running_tasks)
                        status_parts.append(f"{running} node(s) in progress")
                    if task.finished_tasks:
                        finished = len(task.finished_tasks)
                        status_parts.append(f"{finished} completed")
                    
                    progress_callback(
                        " | ".join(status_parts), 
                        min(95, int((elapsed / timeout) * 100))
                    )
                
                if task.status == InstallStatus.COMPLETED:
                    return task
                
                if task.status == InstallStatus.FAILED:
                    return task
                
            except Exception as e:
                consecutive_failures += 1
                
                if progress_callback:
                    elapsed = int(time.time() - start_time)
                    if consecutive_failures < 3:
                        progress_callback(f"Connection lost, reconnecting... ({elapsed}s)", 50)
                    else:
                        progress_callback(f"Device rebooting... retry {consecutive_failures}/{max_consecutive_failures}", 50)
                
                if consecutive_failures >= max_consecutive_failures:
                    # Too many failures, but let's do one final check after a longer wait
                    time.sleep(60)
                    try:
                        task = self.check_install_status()
                        if task.status == InstallStatus.COMPLETED:
                            return task
                    except:
                        pass
                    
                    last_task.status = InstallStatus.FAILED
                    last_task.error_message = f"Lost connection to device after {consecutive_failures} retries"
                    return last_task
            
            time.sleep(poll_interval)
        
        last_task.status = InstallStatus.TIMEOUT
        last_task.error_message = f"Timeout after {timeout}s"
        return last_task
    
    def get_current_version(self) -> Optional[str]:
        """Get current DNOS version from device."""
        try:
            output = self._exec_cli("show system stack | no-more")
            # Parse DNOS version from stack output
            for line in output.split('\n'):
                if 'DNOS' in line and '|' in line:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 6:
                        return parts[5]  # Current column
        except:
            pass
        return None
    
    def requires_delete_deploy(self, target_version: str) -> bool:
        """Check if upgrade to target requires delete + deploy."""
        from .stack_manager import StackManager
        
        current = self.get_current_version()
        if not current:
            return False  # Can't determine
        
        return StackManager.requires_delete_deploy(current, target_version)
    
    def delete_dnos(self, progress_callback: Callable[[str], None] = None) -> bool:
        """Delete DNOS to enter GI mode (for major version upgrades).
        
        Returns:
            True if delete initiated successfully
        """
        if progress_callback:
            progress_callback("Initiating DNOS delete (entering GI mode)...")
        
        # request system delete - ssh_exec handles Yes/No prompts
        output = self._exec_cli("request system delete")
        
        if 'error' in output.lower():
            return False
        
        # Wait for device to enter GI mode
        if progress_callback:
            progress_callback("Waiting for device to enter GI mode...")
        
        return True
    
    def deploy_from_gi(self, system_type: str, name: str, ncc_id: int = 0,
                       progress_callback: Callable[[str], None] = None) -> InstallTask:
        """Deploy DNOS from GI mode.
        
        Args:
            system_type: System type (SA-40C, SA-36CD-S, CL-16, etc.)
            name: System name
            ncc_id: NCC ID
            progress_callback: Progress callback
            
        Returns:
            InstallTask
        """
        if progress_callback:
            progress_callback(f"Deploying: system-type={system_type} name={name}")
        
        return self.start_deploy(system_type, name, ncc_id)
    
    # =========================================================================
    # High-Level Operations
    # =========================================================================
    
    def upgrade_stack(self, stack: StackInfo,
                      progress_callback: Callable[[str, int], None] = None) -> Tuple[bool, str]:
        """Perform full stack upgrade.
        
        1. Load all components to target-stack
        2. Start installation
        3. Wait for completion
        
        Args:
            stack: StackInfo with component URLs
            progress_callback: Optional callback(message, percent)
            
        Returns:
            Tuple of (success, message)
        """
        # Load components
        if progress_callback:
            progress_callback("Loading stack components...", 10)
        
        load_tasks = self.load_stack(
            stack, 
            lambda msg, pct: progress_callback(msg, int(10 + pct * 0.3)) if progress_callback else None
        )
        
        # Check load results
        failed_loads = [t for t in load_tasks if t.status != LoadStatus.COMPLETED]
        if failed_loads:
            return False, f"Failed to load: {', '.join(t.component for t in failed_loads)}"
        
        # Start install
        if progress_callback:
            progress_callback("Starting installation...", 40)
        
        install = self.start_install()
        if install.status == InstallStatus.FAILED:
            return False, f"Install failed to start: {install.error_message}"
        
        # Wait for install
        if progress_callback:
            progress_callback("Installing...", 50)
        
        final = self.wait_for_install(
            timeout=3600,
            progress_callback=lambda msg, pct: progress_callback(msg, int(50 + pct * 0.5)) if progress_callback else None
        )
        
        if final.status == InstallStatus.COMPLETED:
            return True, "Upgrade completed successfully"
        else:
            return False, f"Install {final.status.value}: {final.error_message}"


# =============================================================================
# Multi-Device Upgrade Coordinator
# =============================================================================

@dataclass
class DeviceUpgradeStatus:
    """Status of upgrade for a single device."""
    hostname: str
    stage: str = "pending"
    progress: int = 0
    message: str = ""
    success: Optional[bool] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class MultiDeviceUpgrader:
    """Coordinates upgrades across multiple devices."""
    
    def __init__(self):
        self.devices: Dict[str, DeviceUpgrader] = {}
        self.status: Dict[str, DeviceUpgradeStatus] = {}
    
    def add_device(self, hostname: str, ssh_executor: Callable[[str], Tuple[str, int]]):
        """Add a device to upgrade."""
        upgrader = DeviceUpgrader(hostname, ssh_executor)
        self.devices[hostname] = upgrader
        self.status[hostname] = DeviceUpgradeStatus(hostname=hostname)
    
    def upgrade_all(self, stack: StackInfo, 
                    parallel: bool = False,
                    progress_callback: Callable[[Dict[str, DeviceUpgradeStatus]], None] = None) -> Dict[str, bool]:
        """Upgrade all devices.
        
        Args:
            stack: Stack to deploy
            parallel: Whether to upgrade in parallel
            progress_callback: Callback with status dict
            
        Returns:
            Dict of hostname -> success
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        results = {}
        
        def upgrade_device(hostname: str) -> Tuple[str, bool, str]:
            upgrader = self.devices[hostname]
            status = self.status[hostname]
            status.start_time = datetime.now()
            status.stage = "upgrading"
            
            def update_progress(msg: str, pct: int):
                status.message = msg
                status.progress = pct
                if progress_callback:
                    progress_callback(self.status.copy())
            
            success, message = upgrader.upgrade_stack(stack, update_progress)
            
            status.end_time = datetime.now()
            status.success = success
            status.stage = "completed" if success else "failed"
            status.message = message
            
            if progress_callback:
                progress_callback(self.status.copy())
            
            return hostname, success, message
        
        if parallel:
            with ThreadPoolExecutor(max_workers=len(self.devices)) as executor:
                futures = {
                    executor.submit(upgrade_device, h): h 
                    for h in self.devices
                }
                
                for future in as_completed(futures):
                    hostname, success, message = future.result()
                    results[hostname] = success
        else:
            for hostname in self.devices:
                hostname, success, message = upgrade_device(hostname)
                results[hostname] = success
        
        return results


# =============================================================================
# Convenience Functions  
# =============================================================================

def get_device_stack_state(hostname: str, ssh_executor: Callable) -> Dict:
    """Get current stack state from a device."""
    upgrader = DeviceUpgrader(hostname, ssh_executor)
    state = upgrader.get_current_stack()
    return {
        'current': state.current,
        'target': state.target,
        'revert': state.revert
    }


def load_component_to_device(hostname: str, url: str, ssh_executor: Callable) -> Dict:
    """Load a single component to a device."""
    upgrader = DeviceUpgrader(hostname, ssh_executor)
    task = upgrader.load_component(url)
    return {
        'component': task.component,
        'status': task.status.value,
        'task_id': task.task_id,
        'error': task.error_message
    }

