# Mirror Config: Bundle Detection for WAN Mapping Enhancement

## Problem Statement

**User Issue:**  
> "BUT the device 2 interface for some example have lacp interface as the DNAAS connection, since the physical interfaces are part of a bundle and that bundle is configured under lacp, and is up via show lacp interfaces, so i want the wizard to detect this to suggest the bundle as a WAN..."

**Current Behavior:** ❌
- Wizard shows physical interfaces (ge400-0/0/0, ge400-0/0/2) as WAN targets
- These are LACP bundle members, not actual WAN interfaces!
- User must manually understand bundle hierarchy

**Required Behavior:** ✅
- Detect that physical interfaces are bundle members (`bundle-id` configured)
- Show **parent bundle** (bundle-100) as WAN mapping target
- Indicate bundle members with LLDP neighbors
- Verify bundle operational status via `show lacp interfaces`

---

## Example Scenario

### PE-2 Config (Target)

```
interfaces
  bundle-100                    ← Actual WAN interface with IP
    admin-state enabled
    ipv4-address 14.14.14.2/29
    mtu 9216
  !
  ge400-0/0/0                   ← Bundle member (physical)
    admin-state enabled
    bundle-id 100               ← Part of bundle-100
    speed 100
  !
  ge400-0/0/2                   ← Bundle member (physical)
    admin-state enabled
    bundle-id 100               ← Part of bundle-100
    speed 100
  !
!

protocols
  lacp
    interface ge400-0/0/0       ← LACP on physical members
      admin-state enabled
    !
    interface ge400-0/0/2       ← LACP on physical members
      admin-state enabled
    !
  !
  isis
    instance IGP
      interface bundle-100      ← IGP runs on bundle, not physical!
        admin-state enabled
      !
    !
  !
!
```

### Current Wizard Display ❌

```
Target Available Interfaces (with LLDP neighbors):
  [1] ge400-0/0/0 → SPINE-1 (Ethernet1/1)
  [2] ge400-0/0/2 → SPINE-2 (Ethernet1/2)

Select target parent interface: _
```

**Problem:** User sees physical interfaces, doesn't know they're bundle members!

### Desired Wizard Display ✅

```
Target Available Interfaces:

  Bundles (LACP):
  [1] bundle-100 (2 members, admin-state: enabled)
      └─ ge400-0/0/0 → SPINE-1 (Ethernet1/1) [LACP: enabled]
      └─ ge400-0/0/2 → SPINE-2 (Ethernet1/2) [LACP: enabled]

  Physical (non-bundled):
  [2] ge400-0/0/4 → SPINE-3 (Ethernet1/3)

Select target parent interface: _
```

**Benefits:**
- Clear hierarchy (bundle vs physical)
- User knows bundle-100 is the WAN interface
- Shows LACP status
- Indicates physical member connectivity

---

## Detection Logic

### Step 1: Identify Bundle Members

**Parse interface config for `bundle-id`:**

```python
def _detect_bundle_members(config: str) -> Dict[str, List[str]]:
    """
    Detect physical interfaces that are bundle members.
    
    Returns:
        Dict of {bundle_name: [member_interfaces]}
        Example: {'bundle-100': ['ge400-0/0/0', 'ge400-0/0/2']}
    """
    bundles = {}
    current_iface = None
    current_bundle_id = None
    
    for line in config.split('\n'):
        # Detect interface start
        if re.match(r'^  (ge|xe|et|hu|ce)[0-9]+', line):
            # Save previous interface's bundle membership
            if current_iface and current_bundle_id:
                bundle_name = f'bundle-{current_bundle_id}'
                if bundle_name not in bundles:
                    bundles[bundle_name] = []
                bundles[bundle_name].append(current_iface)
            
            # Start new interface
            current_iface = line.strip()
            current_bundle_id = None
        
        # Detect bundle-id
        elif 'bundle-id' in line:
            match = re.search(r'bundle-id\s+(\d+)', line)
            if match:
                current_bundle_id = match.group(1)
    
    # Save last interface
    if current_iface and current_bundle_id:
        bundle_name = f'bundle-{current_bundle_id}'
        if bundle_name not in bundles:
            bundles[bundle_name] = []
        bundles[bundle_name].append(current_iface)
    
    return bundles
```

### Step 2: Detect Bundle Interfaces

**Find bundle interfaces in config:**

```python
def _detect_bundles(config: str) -> Dict[str, Dict]:
    """
    Detect bundle interfaces and their properties.
    
    Returns:
        Dict of {bundle_name: {ip, admin_state, mtu, ...}}
        Example: {'bundle-100': {'ip': '14.14.14.2/29', 'admin_state': 'enabled'}}
    """
    bundles = {}
    current_bundle = None
    current_config = {}
    
    for line in config.split('\n'):
        # Detect bundle interface
        if re.match(r'^  (bundle(?:-ether)?-?\d+)$', line.strip()):
            # Save previous bundle
            if current_bundle:
                bundles[current_bundle] = current_config
            
            # Start new bundle
            current_bundle = line.strip()
            current_config = {}
        
        # Parse bundle attributes
        elif current_bundle and re.match(r'^\s{4}', line):
            if 'admin-state' in line:
                current_config['admin_state'] = 'enabled' if 'enabled' in line else 'disabled'
            elif 'ipv4-address' in line:
                match = re.search(r'ipv4-address\s+(\S+)', line)
                if match:
                    current_config['ip'] = match.group(1)
            elif 'mtu' in line:
                match = re.search(r'mtu\s+(\d+)', line)
                if match:
                    current_config['mtu'] = match.group(1)
    
    # Save last bundle
    if current_bundle:
        bundles[current_bundle] = current_config
    
    return bundles
```

### Step 3: Verify LACP Status

**Check LACP protocol section:**

```python
def _detect_lacp_interfaces(config: str) -> Set[str]:
    """
    Detect interfaces with LACP configured.
    
    Returns:
        Set of interface names with LACP enabled
    """
    lacp_ifaces = set()
    in_lacp = False
    
    for line in config.split('\n'):
        if re.match(r'^\s*lacp\s*$', line):
            in_lacp = True
        elif in_lacp and re.match(r'^\s*!\s*$', line) and len(line.strip()) == 1:
            in_lacp = False
        elif in_lacp and 'interface' in line:
            match = re.search(r'interface\s+(\S+)', line)
            if match:
                lacp_ifaces.add(match.group(1))
    
    return lacp_ifaces
```

### Step 4: Combine Bundle Info with LLDP

**Enhanced interface detection:**

```python
def _get_enhanced_target_interfaces(
    target_config: str,
    target_lldp: List[Dict]
) -> List[Dict]:
    """
    Get target interfaces with bundle awareness.
    
    Returns:
        List of interface entries with structure:
        [
            {
                'type': 'bundle',
                'interface': 'bundle-100',
                'ip': '14.14.14.2/29',
                'members': ['ge400-0/0/0', 'ge400-0/0/2'],
                'member_lldp': {
                    'ge400-0/0/0': {'neighbor': 'SPINE-1', 'port': 'Ethernet1/1'},
                    'ge400-0/0/2': {'neighbor': 'SPINE-2', 'port': 'Ethernet1/2'}
                },
                'lacp_enabled': True
            },
            {
                'type': 'physical',
                'interface': 'ge400-0/0/4',
                'lldp_neighbor': 'SPINE-3',
                'lldp_port': 'Ethernet1/3'
            }
        ]
    """
    result = []
    
    # Detect bundles and their members
    bundle_members = _detect_bundle_members(target_config)
    bundles = _detect_bundles(target_config)
    lacp_ifaces = _detect_lacp_interfaces(target_config)
    
    # Build LLDP lookup
    lldp_lookup = {}
    for n in target_lldp:
        iface = n.get('local_interface', '')
        if iface:
            lldp_lookup[iface] = {
                'neighbor': n.get('neighbor_device', ''),
                'port': n.get('neighbor_port', '')
            }
    
    # Add bundles first
    for bundle_name, members in bundle_members.items():
        if bundle_name in bundles:
            bundle_info = bundles[bundle_name]
            
            # Collect LLDP info for members
            member_lldp = {}
            for member in members:
                if member in lldp_lookup:
                    member_lldp[member] = lldp_lookup[member]
            
            # Check if LACP is enabled on members
            lacp_enabled = any(m in lacp_ifaces for m in members)
            
            result.append({
                'type': 'bundle',
                'interface': bundle_name,
                'ip': bundle_info.get('ip'),
                'admin_state': bundle_info.get('admin_state'),
                'members': members,
                'member_lldp': member_lldp,
                'lacp_enabled': lacp_enabled
            })
    
    # Add non-bundled physical interfaces with LLDP
    bundled_ifaces = set()
    for members in bundle_members.values():
        bundled_ifaces.update(members)
    
    for iface, lldp_info in lldp_lookup.items():
        if iface not in bundled_ifaces and '.' not in iface:
            result.append({
                'type': 'physical',
                'interface': iface,
                'lldp_neighbor': lldp_info['neighbor'],
                'lldp_port': lldp_info['port']
            })
    
    return result
```

---

## Enhanced UI Display

### Display Function

```python
def _display_target_interfaces(interfaces: List[Dict]):
    """Display target interfaces with bundle hierarchy."""
    
    # Separate bundles and physical
    bundles = [i for i in interfaces if i['type'] == 'bundle']
    physical = [i for i in interfaces if i['type'] == 'physical']
    
    idx = 1
    choices = []
    
    if bundles:
        console.print("\n[bold cyan]  Bundles (LACP):[/bold cyan]")
        for bundle in bundles:
            bundle_name = bundle['interface']
            ip_info = f" ({bundle['ip']})" if bundle.get('ip') else ""
            member_count = len(bundle.get('members', []))
            lacp_status = "[green]LACP enabled[/green]" if bundle.get('lacp_enabled') else "[dim]no LACP[/dim]"
            
            console.print(f"  [{idx}] [bold]{bundle_name}[/bold]{ip_info} ({member_count} members, {lacp_status})")
            
            # Show members with LLDP
            for member in bundle.get('members', []):
                lldp_info = bundle.get('member_lldp', {}).get(member, {})
                if lldp_info:
                    neighbor = lldp_info.get('neighbor', 'unknown')
                    port = lldp_info.get('port', '')
                    port_info = f":{port}" if port else ""
                    console.print(f"      └─ {member} → {neighbor}{port_info}")
                else:
                    console.print(f"      └─ {member} (no LLDP neighbor)")
            
            choices.append(str(idx))
            idx += 1
    
    if physical:
        console.print("\n[bold cyan]  Physical (non-bundled):[/bold cyan]")
        for phys in physical:
            iface = phys['interface']
            neighbor = phys.get('lldp_neighbor', '')
            port = phys.get('lldp_port', '')
            neighbor_info = f" → {neighbor}" if neighbor else ""
            if port:
                neighbor_info += f":{port}"
            
            console.print(f"  [{idx}] {iface}{neighbor_info}")
            choices.append(str(idx))
            idx += 1
    
    return choices
```

---

## Integration Points

### 1. Update `wan_interface_mapping_wizard()`

**Line ~550-560 in mirror_config.py:**

```python
# OLD: Only physical interfaces from LLDP
available_targets = []
for n in target_lldp:
    iface = n.get('local_interface')
    if iface and '.' not in iface:
        available_targets.append({'interface': iface, ...})

# NEW: Bundle-aware detection
enhanced_targets = _get_enhanced_target_interfaces(
    state.target_config,
    target_lldp
)

# Display with bundle hierarchy
if not enhanced_targets:
    console.print("[yellow]No interfaces available...[/yellow]")
    return None

choices = _display_target_interfaces(enhanced_targets)
```

### 2. Update Mapping Result

When user selects a bundle, store bundle name (not physical):

```python
selected = enhanced_targets[selected_idx]

if selected['type'] == 'bundle':
    target_parent = selected['interface']  # 'bundle-100'
    console.print(f"  [green]✓ Selected bundle: {target_parent}[/green]")
    console.print(f"    Members: {', '.join(selected['members'])}")
else:
    target_parent = selected['interface']  # 'ge400-0/0/4'
```

### 3. Handle Bundle Sub-Interfaces

If source has sub-interfaces and target is a bundle:

```python
if selected['type'] == 'bundle':
    console.print(f"\n  [bold]Creating sub-interfaces on bundle {target_parent}:[/bold]")
    for src_subif in source_subifs:
        target_subif = f"{target_parent}.{src_subif['subif_id']}"
        console.print(f"    {src_subif['full_name']} → {target_subif}")
```

---

## Testing Scenarios

### Test Case 1: Bundle with 2 Members

**Setup:**
- PE-2 has bundle-100 with ge400-0/0/0 + ge400-0/0/2
- Both members have LLDP neighbors
- LACP configured

**Expected:**
```
Target Available Interfaces:
  Bundles (LACP):
  [1] bundle-100 (14.14.14.2/29) (2 members, LACP enabled)
      └─ ge400-0/0/0 → SPINE-1:Ethernet1/1
      └─ ge400-0/0/2 → SPINE-2:Ethernet1/2
```

### Test Case 2: Mixed Bundle + Physical

**Setup:**
- bundle-100 (members: ge400-0/0/0, 0/0/2)
- ge400-0/0/4 (physical, not bundled)

**Expected:**
```
Bundles (LACP):
  [1] bundle-100 (2 members)
      └─ ge400-0/0/0 → SPINE-1
      └─ ge400-0/0/2 → SPINE-2

Physical (non-bundled):
  [2] ge400-0/0/4 → SPINE-3
```

### Test Case 3: Bundle Without LACP

**Setup:**
- bundle-100 exists but no LACP protocol configured

**Expected:**
```
Bundles (LACP):
  [1] bundle-100 (2 members, no LACP)
      └─ ge400-0/0/0
      └─ ge400-0/0/2
```

---

## Benefits

1. **Correct WAN Identification** - Shows bundles as WAN targets, not physical members
2. **Clear Hierarchy** - User sees bundle → members relationship
3. **LLDP Visibility** - Shows which physical ports connect where
4. **LACP Status** - Indicates if LACP is configured
5. **Prevents Errors** - User won't accidentally map to bundle members

---

## Implementation Priority

**Priority:** 🔥 **HIGH**

**Impact:**
- Most DNAAS connections use LACP bundles
- Current wizard is misleading (shows wrong interfaces)
- Users may create invalid configs

**Dependencies:**
- Requires LLDP data refresh (from earlier PE-2 SSH fix)
- Bundle detection functions (some already exist in codebase)

**Files to Modify:**
1. `mirror_config.py` - `wan_interface_mapping_wizard()` (~line 419)
2. `mirror_config.py` - Add bundle detection functions
3. `mirror_config.py` - Update display logic

---

## Summary

**Current:** Shows physical interfaces (ge400-0/0/0) even when they're bundle members ❌

**Required:** Detect bundles, show bundle-100 as WAN target with member details ✅

**User Need:** "detect this to suggest the bundle as a WAN"

**Solution:** 
1. Parse `bundle-id` from interface config
2. Group members by bundle
3. Show bundles first, then non-bundled physical interfaces
4. Display member LLDP neighbors under bundle

---

*Document Date: 2026-01-31*  
*Feature: Bundle Detection for WAN Mapping*  
*Status: 📋 **DESIGN COMPLETE - NEEDS IMPLEMENTATION***
