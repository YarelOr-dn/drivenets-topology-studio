"""
Stag Pool Checker - Query actual interface index usage from DNOS devices.

This module provides functionality to check the actual ifindex pool usage
directly from the Linux kernel in the inband-engine container.

Interface Index Pools (from interface_manager_consts.py):
- PH Pool (58882-62881): 4,000 slots - shared by phX and phX.Y (no outer-tag)
- Stag Pool (88001-92000): 4,000 slots - for PWHE phX.Ys (Q-in-Q with outer-tag)
- IRB Pool (41985-46080): 4,096 slots - for IRB interfaces

IMPORTANT: Stag pool is used by ALL Q-in-Q interfaces!
- ANY interface with vlan-tags outer-tag (including ge-*, lag*, ph*) uses Stag pool
- A Stag = unique (parent_interface, outer_vlan_id) combination
- Multiple sub-interfaces with same parent+outer-tag share one Stag slot
- Verified from DNOS source: rorm_interfaces.rs, stag.rs

Soft Limits (from consts.py):
- MAX_IRB_AND_PHXY_INTERFACES: 4,000 - Combined limit for IRB + phX.Y
- MAX_QINQ_INTERFACES: 4,000 - PWHE Stag limit (unique parent+outer_tag combinations)

Author: SCALER Wizard
Date: 2026-01-01
"""

import paramiko
import time
import re
import json
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


@dataclass
class IfindexPoolStats:
    """Statistics for an interface index pool."""
    name: str
    range_min: int
    range_max: int
    used: int
    breakdown: Dict[str, int]  # interface type -> count
    samples: List[str]
    
    @property
    def max_capacity(self) -> int:
        return self.range_max - self.range_min + 1
    
    @property
    def remaining(self) -> int:
        return self.max_capacity - self.used
    
    @property
    def usage_percent(self) -> float:
        return (self.used / self.max_capacity) * 100 if self.max_capacity > 0 else 0


@dataclass
class DevicePoolStatus:
    """Complete pool status for a device."""
    hostname: str
    ph_pool: IfindexPoolStats
    stag_pool: IfindexPoolStats
    irb_pool: IfindexPoolStats
    total_interfaces: int
    phx_count: int
    phxy_count: int
    phxys_count: int  # Stags from PWHE
    irb_count: int
    bundle_count: int = 0       # bundle-X parents
    bundlexy_count: int = 0     # bundle-X.Y sub-interfaces (can have stags!)
    ge_subif_count: int = 0     # ge/xe/et sub-interfaces
    vlan_pool: Optional[IfindexPoolStats] = None  # VLAN pool for physical sub-ifs
    error: Optional[str] = None


# Pool definitions from interface_manager_consts.py
POOL_DEFINITIONS = {
    "PH": {"min": 58882, "max": 62881, "description": "phX parents + phX.Y (no outer-tag)"},  # 4000 max
    "STAG": {"min": 88001, "max": 92000, "description": "Q-in-Q sub-interfaces (phX.Ys, bundle.Y with outer-tag)"},
    "IRB": {"min": 41985, "max": 46080, "description": "IRB interfaces"},
    "VLAN": {"min": 13313, "max": 33792, "description": "Physical sub-interfaces (ge-X.Y, bundle-X.Y)"},
}

# Soft limits from consts.py
SOFT_LIMITS = {
    "MAX_IRB_AND_PHXY_INTERFACES": 4000,
    "MAX_QINQ_INTERFACES": 4000,
}


def check_pool_status(hostname: str, username: str, password: str, 
                      shell_password: str = "dnroot") -> DevicePoolStatus:
    """
    Query the actual interface index pool usage from a DNOS device.
    
    Args:
        hostname: Device hostname or IP
        username: SSH username
        password: SSH password
        shell_password: Password for 'run start shell' command
        
    Returns:
        DevicePoolStatus with all pool statistics
    """
    try:
        # Connect to device
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, username=username, password=password, 
                      timeout=30, look_for_keys=False, allow_agent=False)
        
        shell = client.invoke_shell(width=200, height=50)
        time.sleep(2)
        
        # Clear initial output
        while shell.recv_ready():
            shell.recv(4096)
        
        # Enter inband-engine container
        shell.send("run start shell ncc 0 container inband-engine\n")
        time.sleep(2)
        
        output = ""
        while shell.recv_ready():
            output += shell.recv(4096).decode('utf-8', errors='ignore')
        
        # Send shell password if needed
        if "Password" in output or "password" in output:
            shell.send(f"{shell_password}\n")
            time.sleep(2)
            while shell.recv_ready():
                shell.recv(4096)
        
        # Enter inband_ns
        shell.send("ip netns exec inband_ns bash\n")
        time.sleep(1)
        while shell.recv_ready():
            shell.recv(4096)
        
        # Run the analysis script - counts ALL interface types that use pools
        # Improved regex to match actual kernel interface names
        analysis_script = '''ip -j link show 2>/dev/null | python3 -c '
import sys, json, re

data = json.load(sys.stdin)

# Count by pool and type
pools = {
    "PH": {"min": 58882, "max": 62881, "count": 0, "types": {}, "samples": []},  # 4000 max
    "STAG": {"min": 88001, "max": 92000, "count": 0, "types": {}, "samples": []},
    "IRB": {"min": 41985, "max": 46080, "count": 0, "types": {}, "samples": []},
    "VLAN": {"min": 13313, "max": 33792, "count": 0, "types": {}, "samples": []},
}

phx_count = 0
phxy_count = 0
phxys_count = 0
irb_count = 0
bundle_count = 0
bundlexy_count = 0  # bundle-X.Y sub-interfaces
ge_subif_count = 0  # ge100-X/Y/Z.N sub-interfaces
l2ac_count = 0      # L2-AC sub-interfaces (ge/xe with outer-tag in stag pool)

for d in data:
    name = d["ifname"]
    idx = d.get("ifindex", 0)
    
    # Categorize - improved regex patterns for actual kernel names
    # PWHE interfaces
    if re.match(r"^ph\d+$", name):
        itype = "phX"
        phx_count += 1
    elif re.match(r"^ph\d+\.\d+$", name):
        itype = "phX.Y"
        phxy_count += 1
    elif re.match(r"^ph\d+\.\d+s$", name):
        itype = "phX.Ys (stag)"
        phxys_count += 1
    # Bundle interfaces
    elif re.match(r"^bundle-?(ether)?\d+$", name):
        itype = "bundle"
        bundle_count += 1
    elif re.match(r"^bundle-?(ether)?\d+\.\d+", name):
        itype = "bundle.Y"
        bundlexy_count += 1
    # Physical sub-interfaces - multiple kernel naming formats
    # Format 1: ge400-0/0/4.1 (CLI style in kernel)
    # Format 2: ge400-0_0_4.1 (underscores)
    # Format 3: ge_400_0_0_4_1 (all underscores)
    # Format 4: vlan1234 (vlan interface)
    # Format 5: stag_ge400... (stag prefix)
    elif re.match(r"^(ge|xe|et|te)\d+[-_][\d/_]+\.\d+", name):
        itype = "L2-AC (ge/xe.Y)"
        ge_subif_count += 1
        l2ac_count += 1
    elif re.match(r"^(ge|xe|et|te)_?\d+", name) and "." in name:
        itype = "L2-AC (ge/xe.Y)"
        ge_subif_count += 1
        l2ac_count += 1
    elif re.match(r"^stag_", name):
        # Stag-prefixed interface (explicit stag)
        itype = "stag interface"
        l2ac_count += 1
    elif re.match(r"^vlan\d+", name):
        itype = "vlan interface"
        l2ac_count += 1
    elif name.startswith("irb"):
        itype = "irb"
        irb_count += 1
    elif re.match(r"^lag\d+", name):
        itype = "lag"
        bundle_count += 1
    else:
        itype = "other"
    
    # Add to pools based on ifindex range
    for pname, pinfo in pools.items():
        if pinfo["min"] <= idx <= pinfo["max"]:
            pinfo["count"] += 1
            pinfo["types"][itype] = pinfo["types"].get(itype, 0) + 1
            # Collect samples for debugging (first 5 of each type)
            if len(pinfo["samples"]) < 10:
                pinfo["samples"].append(f"{name}({idx})")

result = {
    "total": len(data),
    "phx_count": phx_count,
    "phxy_count": phxy_count,
    "phxys_count": phxys_count,
    "irb_count": irb_count,
    "bundle_count": bundle_count,
    "bundlexy_count": bundlexy_count,
    "ge_subif_count": ge_subif_count,
    "l2ac_count": l2ac_count,
    "pools": pools,
}
print("POOL_RESULT:" + json.dumps(result))
'
'''
        shell.send(analysis_script + "\n")
        time.sleep(10)
        
        output = ""
        while shell.recv_ready():
            output += shell.recv(4096).decode('utf-8', errors='ignore')
        
        client.close()
        
        # Parse the result
        match = re.search(r'POOL_RESULT:(\{.*\})', output)
        if not match:
            return DevicePoolStatus(
                hostname=hostname,
                ph_pool=IfindexPoolStats("PH", 58882, 62881, 0, {}, []),  # 4000 max
                stag_pool=IfindexPoolStats("STAG", 88001, 92000, 0, {}, []),
                irb_pool=IfindexPoolStats("IRB", 41985, 46080, 0, {}, []),
                total_interfaces=0,
                phx_count=0, phxy_count=0, phxys_count=0, irb_count=0,
                error="Failed to parse pool data from device"
            )
        
        result = json.loads(match.group(1))
        pools = result["pools"]
        
        return DevicePoolStatus(
            hostname=hostname,
            ph_pool=IfindexPoolStats(
                "PH Pool (phX + phX.Y)",
                58882, 62881,  # 4000 slots max
                pools["PH"]["count"],
                pools["PH"]["types"],
                pools["PH"].get("samples", [])
            ),
            stag_pool=IfindexPoolStats(
                "Stag Pool (Q-in-Q)",
                88001, 92000,
                pools["STAG"]["count"],
                pools["STAG"]["types"],
                pools["STAG"].get("samples", [])
            ),
            irb_pool=IfindexPoolStats(
                "IRB Pool",
                41985, 46080,
                pools["IRB"]["count"],
                pools["IRB"]["types"],
                pools["IRB"].get("samples", [])
            ),
            vlan_pool=IfindexPoolStats(
                "VLAN Pool (physical sub-ifs)",
                13313, 33792,
                pools.get("VLAN", {}).get("count", 0),
                pools.get("VLAN", {}).get("types", {}),
                pools.get("VLAN", {}).get("samples", [])
            ) if "VLAN" in pools else None,
            total_interfaces=result["total"],
            phx_count=result["phx_count"],
            phxy_count=result["phxy_count"],
            phxys_count=result["phxys_count"],
            irb_count=result["irb_count"],
            bundle_count=result.get("bundle_count", 0),
            bundlexy_count=result.get("bundlexy_count", 0),
            ge_subif_count=result.get("ge_subif_count", 0),
        )
        
    except Exception as e:
        return DevicePoolStatus(
            hostname=hostname,
            ph_pool=IfindexPoolStats("PH", 58882, 62881, 0, {}, []),  # 4000 max
            stag_pool=IfindexPoolStats("STAG", 88001, 92000, 0, {}, []),
            irb_pool=IfindexPoolStats("IRB", 41985, 46080, 0, {}, []),
            total_interfaces=0,
            phx_count=0, phxy_count=0, phxys_count=0, irb_count=0,
            error=str(e)
        )


def calculate_max_services(status: DevicePoolStatus) -> Tuple[int, str]:
    """
    Calculate the maximum number of additional PWHE+FXC services that can be added.
    
    For FXC with outer-tag (Q-in-Q) - each service uses:
    - 2 PH pool slots (1 phX parent + 1 phX.Y sub-interface)
    - 1 Stag pool slot (the sub-interface with outer-tag also registers in Stag)
    
    Returns:
        Tuple of (max_services, limiting_factor)
    """
    ph_remaining = status.ph_pool.remaining
    stag_remaining = status.stag_pool.remaining
    
    # FXC with outer-tag: each service uses 2 PH slots + 1 Stag slot
    # - phX parent: 1 PH slot
    # - phX.Y sub-interface: 1 PH slot + 1 Stag slot
    max_by_ph = ph_remaining // 2  # Each service uses 2 PH slots
    max_by_stag = stag_remaining   # Each service uses 1 Stag slot
    
    # The bottleneck for Q-in-Q services
    max_qinq_services = min(max_by_ph, max_by_stag)
    
    # Determine limiting factor
    if max_by_ph <= max_by_stag:
        return max_qinq_services, f"PH Pool ({ph_remaining} remaining, need 2/service = {max_by_ph} max)"
    else:
        return max_qinq_services, f"Stag Pool ({stag_remaining} remaining)"


def display_pool_status(status: DevicePoolStatus):
    """Display pool status in a rich table."""
    if status.error:
        console.print(f"[red]Error querying {status.hostname}: {status.error}[/red]")
        return
    
    # Create main table
    table = Table(title=f"🔍 Interface Pool Status: {status.hostname}", 
                  show_header=True, header_style="bold cyan")
    table.add_column("Pool", style="bold")
    table.add_column("Used", justify="right")
    table.add_column("Max", justify="right")
    table.add_column("Remaining", justify="right")
    table.add_column("Usage", justify="right")
    table.add_column("Status")
    
    # Add rows for each pool
    for pool in [status.ph_pool, status.stag_pool, status.irb_pool]:
        pct = pool.usage_percent
        if pct >= 90:
            status_icon = "🔴 CRITICAL"
            style = "red"
        elif pct >= 75:
            status_icon = "🟡 WARNING"
            style = "yellow"
        else:
            status_icon = "🟢 OK"
            style = "green"
        
        table.add_row(
            pool.name,
            f"{pool.used:,}",
            f"{pool.max_capacity:,}",
            f"{pool.remaining:,}",
            f"{pct:.1f}%",
            status_icon,
            style=style
        )
    
    console.print(table)
    
    # Interface breakdown - show ALL interface types
    console.print(f"\n📊 [bold]Interface Breakdown:[/bold]")
    console.print(f"   [cyan]PWHE Interfaces:[/cyan]")
    console.print(f"     phX parents:     {status.phx_count:,}")
    console.print(f"     phX.Y (no stag): {status.phxy_count:,}")
    console.print(f"     phX.Ys (stag):   {status.phxys_count:,}")
    console.print(f"   [cyan]Bundle/LAG Interfaces:[/cyan]")
    console.print(f"     bundle parents:  {status.bundle_count:,}")
    console.print(f"     bundle.Y subs:   {status.bundlexy_count:,}")
    console.print(f"   [cyan]L2-AC Sub-interfaces (ge/xe/et.Y with outer-tag):[/cyan]")
    console.print(f"     ge/xe/et.Y:      {status.ge_subif_count:,}")
    console.print(f"   [cyan]Other:[/cyan]")
    console.print(f"     IRB:             {status.irb_count:,}")
    console.print(f"   [bold]Total:            {status.total_interfaces:,}[/bold]")
    
    # Show what types are in each pool if there are items
    if status.stag_pool.used > 0 and status.ge_subif_count == 0 and status.phxys_count == 0:
        # Stag pool has items but our categorization missed them - show breakdown
        console.print(f"\n   [yellow]Note: {status.stag_pool.used:,} interfaces in Stag pool may be L2-AC with outer-tag[/yellow]")
    
    # Show Stag pool breakdown (what's actually consuming stags)
    stag_types = status.stag_pool.breakdown if status.stag_pool.breakdown else {}
    if stag_types:
        console.print(f"\n📋 [bold]Stag Pool Breakdown (what's using Q-in-Q slots):[/bold]")
        for itype, count in sorted(stag_types.items(), key=lambda x: -x[1]):
            # Color-code by interface type
            if "L2-AC" in itype or "ge" in itype or "xe" in itype:
                console.print(f"     [cyan]{itype}[/cyan]: {count:,}")
            elif "phX.Ys" in itype or "stag" in itype.lower():
                console.print(f"     [yellow]{itype}[/yellow]: {count:,}")
            elif itype == "other":
                console.print(f"     [dim]{itype}[/dim]: {count:,}")
            else:
                console.print(f"     {itype}: {count:,}")
        
        # Show sample interface names if available
        if status.stag_pool.samples:
            console.print(f"\n   [dim]Sample interfaces in Stag pool:[/dim]")
            for sample in status.stag_pool.samples[:5]:
                console.print(f"     [dim]• {sample}[/dim]")
    
    # Soft limits check - include bundle sub-interfaces in stag count
    total_stags_used = status.stag_pool.used  # Use actual pool count
    irb_phxy_total = status.irb_count + status.phxy_count
    console.print(f"\n📋 [bold]Soft Limits:[/bold]")
    console.print(f"   IRB + phX.Y: {irb_phxy_total:,} / {SOFT_LIMITS['MAX_IRB_AND_PHXY_INTERFACES']:,}")
    console.print(f"   Stags (Q-in-Q): {total_stags_used:,} / {SOFT_LIMITS['MAX_QINQ_INTERFACES']:,}")
    
    # Max services calculation (PWHE-based only)
    max_services, limiting_factor = calculate_max_services(status)
    console.print(f"\n🚀 [bold]Maximum Additional PWHE+FXC Services (Q-in-Q):[/bold]")
    console.print(f"   [green]{max_services:,}[/green] services")
    console.print(f"   [dim](Each service = 2 PH slots [parent+sub] + 1 Stag slot)[/dim]")
    console.print(f"   [dim]PH calc: {status.ph_pool.remaining} ÷ 2 = {status.ph_pool.remaining // 2} max[/dim]")
    console.print(f"   [dim]Stag calc: {status.stag_pool.remaining} ÷ 1 = {status.stag_pool.remaining} max[/dim]")
    console.print(f"   Limited by: {limiting_factor}")


def run_stag_pool_check(devices: List[dict], shell_password: str = "dnroot"):
    """
    Run Stag pool check on multiple devices with PARALLEL SSH queries.
    
    Args:
        devices: List of device dicts with hostname, ip, username, password
        shell_password: Password for shell access
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from rich.live import Live
    from rich.columns import Columns
    from rich.spinner import Spinner
    
    console.print(Panel.fit(
        "[bold cyan]🔍 Stag Pool Checker[/bold cyan]\n"
        "Querying actual interface index usage from device kernel\n"
        f"[dim]Checking {len(devices)} device(s) in parallel...[/dim]",
        border_style="cyan"
    ))
    
    all_status = []
    device_status = {d['hostname']: "⏳ Querying..." for d in devices}
    
    def query_device(device):
        """Query a single device - runs in thread."""
        hostname = device['hostname']
        try:
            status = check_pool_status(
                hostname=device.get('ip', device.get('hostname')),
                username=device.get('username', 'dnroot'),
                password=device.get('password', 'dnroot'),
                shell_password=shell_password
            )
            status.hostname = hostname
            return status
        except Exception as e:
            return DevicePoolStatus(
                hostname=hostname,
                ph_pool=IfindexPoolStats("PH", 58882, 62881, 0, {}, []),  # 4000 max
                stag_pool=IfindexPoolStats("STAG", 88001, 92000, 0, {}, []),
                irb_pool=IfindexPoolStats("IRB", 41985, 46080, 0, {}, []),
                total_interfaces=0,
                phx_count=0, phxy_count=0, phxys_count=0, irb_count=0,
                error=str(e)
            )
    
    # Run queries in parallel
    if len(devices) > 1:
        console.print(f"[cyan]Querying {len(devices)} devices in parallel...[/cyan]")
        with ThreadPoolExecutor(max_workers=min(len(devices), 5)) as executor:
            futures = {executor.submit(query_device, d): d['hostname'] for d in devices}
            
            for future in as_completed(futures):
                hostname = futures[future]
                try:
                    status = future.result()
                    all_status.append(status)
                    if status.error:
                        console.print(f"  [red]✗ {hostname}: {status.error}[/red]")
                    else:
                        console.print(f"  [green]✓ {hostname}: Done[/green]")
                except Exception as e:
                    console.print(f"  [red]✗ {hostname}: {e}[/red]")
    else:
        # Single device - just query it
        for device in devices:
            console.print(f"\n[cyan]Querying {device['hostname']}...[/cyan]")
            status = query_device(device)
            all_status.append(status)
    
    # Sort by hostname for consistent display
    all_status.sort(key=lambda s: s.hostname)
    
    # Display results
    console.print(f"\n{'═' * 60}")
    for status in all_status:
        display_pool_status(status)
    
    # Summary if multiple devices
    if len(all_status) > 1:
        console.print(Panel.fit(
            "[bold]📊 Multi-Device Summary[/bold]",
            border_style="cyan"
        ))
        
        summary_table = Table(show_header=True, header_style="bold")
        summary_table.add_column("Device")
        summary_table.add_column("PH Used", justify="right")
        summary_table.add_column("Stag Used", justify="right")
        summary_table.add_column("Bundle.Y", justify="right")
        summary_table.add_column("Max Add", justify="right")
        summary_table.add_column("Bottleneck")
        
        for status in all_status:
            if status.error:
                summary_table.add_row(status.hostname, "ERROR", "-", "-", "-", status.error[:30])
            else:
                max_add, bottleneck = calculate_max_services(status)
                summary_table.add_row(
                    status.hostname,
                    f"{status.ph_pool.used:,}/{status.ph_pool.max_capacity:,}",
                    f"{status.stag_pool.used:,}/{status.stag_pool.max_capacity:,}",
                    f"{status.bundlexy_count:,}",
                    f"{max_add:,}",
                    bottleneck.split('(')[0].strip()
                )
        
        console.print(summary_table)
    
    return all_status


if __name__ == "__main__":
    # Test with a single device
    import sys
    if len(sys.argv) > 1:
        hostname = sys.argv[1]
        status = check_pool_status(hostname, "dnroot", "dnroot")
        display_pool_status(status)
    else:
        print("Usage: python stag_pool_checker.py <hostname>")
