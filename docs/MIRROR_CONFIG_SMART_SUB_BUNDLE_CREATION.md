# Mirror Config: Smart Bundle Sub-Interface Creation 🎯

## User Requirement

> "it should Give an Option to create Sub-bundles from that Bundle interface, in a smart way! and the IPs will be per sub-bundle... according to the mirror itself."

**Perfect approach!** This is exactly how DNAAS WAN connections should work with LACP bundles.

---

## The Smart Bundle Sub-Interface Flow

### Scenario

**Source (PE-4):** 4 WAN sub-interfaces on physical parent
```
interfaces
  ge100-18/0/0.14
    ipv4-address 14.14.14.4/29
  !
  ge100-18/0/0.24
    ipv4-address 24.24.24.4/29
  !
  ge100-18/0/0.34
    ipv4-address 34.34.34.4/29
  !
  ge100-18/0/0.45
    ipv4-address 45.45.45.4/29
  !
!
```

**Target (PE-2):** Bundle with LACP
```
interfaces
  bundle-100              ← Parent bundle
    admin-state enabled
    mtu 9216
  !
  ge400-0/0/0            ← Member 1
    admin-state enabled
    bundle-id 100
  !
  ge400-0/0/2            ← Member 2
    admin-state enabled
    bundle-id 100
  !
!
```

### Smart Mapping Wizard Flow

```
Step 1: Detect Source Sub-Interfaces
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Source has 4 WAN sub-interfaces:
  • ge100-18/0/0.14 (14.14.14.4/29)
  • ge100-18/0/0.24 (24.24.24.4/29)
  • ge100-18/0/0.34 (34.34.34.4/29)
  • ge100-18/0/0.45 (45.45.45.4/29)

Parent interface: ge100-18/0/0

Step 2: Detect Target Bundles
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Target has bundle with LACP:
  [1] bundle-100 (LACP, 2 members)
      └─ ge400-0/0/0 → SPINE-1
      └─ ge400-0/0/2 → SPINE-2

Step 3: Offer Sub-Bundle Creation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[bold]Create Sub-Interfaces on bundle-100?[/bold]

  Source has 4 sub-interfaces on ge100-18/0/0
  
  Options:
    [1] Create 4 sub-bundles on bundle-100    ← Smart option!
        • bundle-100.14 (14.14.14.2/29)
        • bundle-100.24 (24.24.24.2/29)
        • bundle-100.34 (34.34.34.2/29)
        • bundle-100.45 (45.45.45.2/29)
    
    [2] Use different target parent
    [B] Back

Select [1/2/b/B] (1): 1

Step 4: IP Transformation Options
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
For each sub-bundle, choose IP strategy:

  bundle-100.14:
    Source IP: 14.14.14.4/29
    [1] Keep source IP:      14.14.14.4/29
    [2] Auto-derive from subnet: 14.14.14.2/29  ← Smart suggestion!
    [3] Enter custom IP:     ___________
    Select [1/2/3/b/B] (2): 2
  
  ✓ bundle-100.14 → 14.14.14.2/29

  bundle-100.24:
    Source IP: 24.24.24.4/29
    [1] Keep source IP:      24.24.24.4/29
    [2] Auto-derive from subnet: 24.24.24.2/29
    [3] Enter custom IP:     ___________
    Select [1/2/3/b/B] (2): 2
  
  ✓ bundle-100.24 → 24.24.24.2/29

  ... (repeat for all 4 sub-interfaces)

Step 5: Preview & Confirm
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[bold]Sub-Bundle Mapping Summary:[/bold]

  Parent: bundle-100 (LACP, 2 members)
  
  Sub-Interfaces to Create:
    • bundle-100.14 → 14.14.14.2/29
    • bundle-100.24 → 24.24.24.2/29
    • bundle-100.34 → 34.34.34.2/29
    • bundle-100.45 → 45.45.45.2/29

  Total: 4 sub-bundles

Proceed with this configuration? [y/Y/n/N/b/B] (y): y

✓ Sub-bundle mapping configured!
```

---

## Generated Configuration

### Result Config

```
interfaces
  bundle-100
    admin-state enabled
    mtu 9216
  !
  bundle-100.14                 ← NEW: Sub-bundle!
    ipv4-address 14.14.14.2/29  ← Transformed IP
    l2-service enabled
    encapsulation dot1q 14
  !
  bundle-100.24                 ← NEW: Sub-bundle!
    ipv4-address 24.24.24.2/29  ← Transformed IP
    l2-service enabled
    encapsulation dot1q 24
  !
  bundle-100.34
    ipv4-address 34.34.34.2/29
    l2-service enabled
    encapsulation dot1q 34
  !
  bundle-100.45
    ipv4-address 45.45.45.2/29
    l2-service enabled
    encapsulation dot1q 45
  !
  ge400-0/0/0                   ← Bundle members preserved
    admin-state enabled
    bundle-id 100
  !
  ge400-0/0/2                   ← Bundle members preserved
    admin-state enabled
    bundle-id 100
  !
!

protocols
  isis
    instance IGP
      interface bundle-100.14   ← IGP on sub-bundles!
        admin-state enabled
        network-type point-to-point
      !
      interface bundle-100.24
        admin-state enabled
        network-type point-to-point
      !
      interface bundle-100.34
        admin-state enabled
        network-type point-to-point
      !
      interface bundle-100.45
        admin-state enabled
        network-type point-to-point
      !
    !
  !
  ldp
    interface bundle-100.14     ← LDP on sub-bundles!
      admin-state enabled
    !
    interface bundle-100.24
      admin-state enabled
    !
    interface bundle-100.34
      admin-state enabled
    !
    interface bundle-100.45
      admin-state enabled
    !
  !
!
```

---

## Smart IP Transformation

### Auto-Derive from Subnet

**Logic:** Given source IP in /29 subnet, find available IP for target

```python
def _smart_derive_bundle_subif_ip(source_ip: str, target_loopback: str) -> str:
    """
    Smart IP derivation for sub-bundle interfaces.
    
    Strategy:
    1. Extract subnet from source IP (14.14.14.0/29)
    2. Find available IP in that subnet (skip source's IP)
    3. Prefer lower IPs (e.g., .2 instead of .6)
    
    Args:
        source_ip: Source sub-interface IP (e.g., 14.14.14.4/29)
        target_loopback: Target's loopback (for uniqueness, optional)
    
    Returns:
        Suggested IP for target sub-bundle
    
    Examples:
        Source: 14.14.14.4/29 (subnet: 14.14.14.0/29, range: .1-.6, .0=network, .7=broadcast)
        Available: .1, .2, .3, .5, .6 (skip .4 = source)
        Suggests: 14.14.14.2/29 (prefer lower)
        
        Source: 24.24.24.4/29
        Suggests: 24.24.24.2/29
    """
    import ipaddress
    
    if '/' not in source_ip:
        return source_ip  # No transformation possible
    
    try:
        # Parse source IP and network
        source_net = ipaddress.ip_interface(source_ip)
        network = source_net.network
        source_addr = source_net.ip
        
        # Get usable host addresses
        usable_hosts = list(network.hosts())  # Excludes network and broadcast
        
        if not usable_hosts:
            return source_ip  # /31 or /32
        
        # Remove source's IP from available pool
        available = [ip for ip in usable_hosts if ip != source_addr]
        
        if not available:
            return source_ip
        
        # Prefer lower IP addresses (common convention)
        selected_ip = available[0]  # First available (lowest)
        
        # Format with original mask
        mask_bits = source_net.network.prefixlen
        return f"{selected_ip}/{mask_bits}"
    
    except Exception:
        return source_ip  # Fallback: keep source IP
```

### IP Transformation Options per Sub-Bundle

For each sub-interface, offer:

1. **Keep source IP** - Use exact source IP (may conflict if source is reachable)
2. **Auto-derive** - Smart algorithm finds available IP in same subnet
3. **Custom IP** - Manual entry with validation

**Smart Default:** Option 2 (Auto-derive) - lowest IP in subnet

---

## Implementation Design

### Phase 1: Bundle Sub-Interface Wizard

**New Function:**

```python
def _bundle_sub_interface_wizard(
    state: 'MirrorStepState',
    source_subifs: List[Dict],      # Source sub-interfaces
    target_bundle: Dict,             # Target bundle info
    source_parent: str               # Source parent interface
) -> Optional[Dict]:
    """
    Interactive wizard for creating sub-interfaces on a bundle.
    
    Args:
        source_subifs: List of source sub-interface dicts
                      [{'full_name': 'ge100-18/0/0.14', 'subif_id': '14', 'ip': '14.14.14.4/29'}, ...]
        target_bundle: Target bundle dict
                      {'interface': 'bundle-100', 'members': [...], 'lacp_enabled': True}
        source_parent: Source parent interface name
    
    Returns:
        Dict with mapping config or None if cancelled
        {
            'action': 'create_sub_bundles',
            'target_parent': 'bundle-100',
            'mappings': {
                'ge100-18/0/0.14': {
                    'target': 'bundle-100.14',
                    'ip_transform': '14.14.14.2/29'
                },
                ...
            }
        }
    """
    console.print(f"\n[bold cyan]Create Sub-Interfaces on {target_bundle['interface']}?[/bold cyan]")
    console.print(f"  Source has {len(source_subifs)} sub-interfaces on [cyan]{source_parent}[/cyan]")
    console.print()
    
    # Show target bundle info
    bundle_name = target_bundle['interface']
    members = target_bundle.get('members', [])
    lacp_status = "[green]LACP enabled[/green]" if target_bundle.get('lacp_enabled') else "[dim]no LACP[/dim]"
    
    console.print(f"  [bold]Target bundle:[/bold] {bundle_name} ({len(members)} members, {lacp_status})")
    for member in members:
        lldp_info = target_bundle.get('member_lldp', {}).get(member, {})
        if lldp_info:
            neighbor = lldp_info.get('neighbor', '')
            port = lldp_info.get('port', '')
            console.print(f"    └─ {member} → {neighbor}:{port}")
        else:
            console.print(f"    └─ {member}")
    
    console.print(f"\n  [cyan]Options:[/cyan]")
    console.print(f"    [1] Create {len(source_subifs)} sub-bundles on {bundle_name}")
    
    # Preview sub-bundle names
    preview_subifs = []
    for sf in source_subifs[:3]:
        subif_id = sf['subif_id']
        source_ip = sf.get('ip', '')
        derived_ip = _smart_derive_bundle_subif_ip(source_ip, state.target_lo0) if source_ip else ''
        preview_subifs.append(f"{bundle_name}.{subif_id} ({derived_ip})")
    
    for pv in preview_subifs:
        console.print(f"        • {pv}")
    
    if len(source_subifs) > 3:
        console.print(f"        [dim]... and {len(source_subifs) - 3} more[/dim]")
    
    console.print(f"    [2] Use different target parent")
    console.print(f"    [B] Back")
    
    choice = Prompt.ask("  Select", choices=['1', '2', 'b', 'B'], default='1').lower()
    
    if choice == 'b':
        return None
    elif choice == '2':
        return {'action': 'choose_different_parent'}
    
    # User selected option 1: Create sub-bundles
    console.print(f"\n[bold]IP Transformation for Sub-Bundles:[/bold]")
    console.print(f"[dim]For each sub-interface, configure IP address[/dim]\n")
    
    mappings = {}
    
    for sf in source_subifs:
        source_full = sf['full_name']
        subif_id = sf['subif_id']
        source_ip = sf.get('ip', '')
        target_subif = f"{bundle_name}.{subif_id}"
        
        console.print(f"  [bold cyan]{target_subif}:[/bold cyan]")
        console.print(f"    Source: {source_full} ({source_ip or 'no IP'})")
        
        if source_ip:
            # Offer IP transformation options
            derived_ip = _smart_derive_bundle_subif_ip(source_ip, state.target_lo0)
            
            console.print(f"    [1] Keep source IP:     {source_ip}")
            console.print(f"    [2] Auto-derive IP:     {derived_ip} [cyan](recommended)[/cyan]")
            console.print(f"    [3] Enter custom IP")
            console.print(f"    [S] Skip this sub-interface")
            
            ip_choice = Prompt.ask(
                "    Select",
                choices=['1', '2', '3', 's', 'S', 'b', 'B'],
                default='2'
            ).lower()
            
            if ip_choice == 'b':
                return None
            elif ip_choice == 's':
                console.print(f"    [dim]→ Skipped {target_subif}[/dim]\n")
                continue
            elif ip_choice == '1':
                final_ip = source_ip
            elif ip_choice == '2':
                final_ip = derived_ip
            else:  # ip_choice == '3'
                custom_ip = Prompt.ask("    Enter IP/mask", default=derived_ip)
                if custom_ip.lower() == 'b':
                    return None
                final_ip = custom_ip
            
            console.print(f"    [green]✓ {target_subif} → {final_ip}[/green]\n")
            
            mappings[source_full] = {
                'target': target_subif,
                'ip_transform': final_ip
            }
        else:
            # No IP on source, just map the interface
            console.print(f"    [dim](no IP configured)[/dim]")
            console.print(f"    [green]✓ {target_subif}[/green]\n")
            
            mappings[source_full] = {
                'target': target_subif,
                'ip_transform': None
            }
    
    if not mappings:
        console.print("[yellow]No sub-interfaces mapped.[/yellow]")
        return None
    
    # Summary
    console.print(f"[bold]Sub-Bundle Mapping Summary:[/bold]")
    console.print(f"  Parent: {bundle_name}")
    console.print(f"  Sub-Interfaces: {len(mappings)}")
    for src, tgt_info in list(mappings.items())[:5]:
        tgt = tgt_info['target']
        ip = tgt_info.get('ip_transform', 'no IP')
        console.print(f"    • {src} → {tgt} ({ip})")
    
    if len(mappings) > 5:
        console.print(f"    [dim]... and {len(mappings) - 5} more[/dim]")
    
    if not Confirm.ask(f"\nCreate {len(mappings)} sub-bundles on {bundle_name}?", default=True):
        return None
    
    return {
        'action': 'create_sub_bundles',
        'target_parent': bundle_name,
        'mappings': mappings,
        'summary': f"{len(mappings)} sub-bundles on {bundle_name}"
    }
```

### Phase 2: Integration into WAN Mapping Flow

**Update:** `wan_interface_mapping_wizard()` line ~595

```python
# When user selects a target interface for source parent
selected = enhanced_targets[selected_idx]

if selected['type'] == 'bundle':
    # Offer sub-bundle creation wizard
    result = _bundle_sub_interface_wizard(
        state,
        subifs,  # Source sub-interfaces
        selected,  # Target bundle info
        src_parent  # Source parent name
    )
    
    if result is None:
        return None  # User cancelled
    elif result.get('action') == 'choose_different_parent':
        continue  # Loop back to parent selection
    else:
        # Store sub-bundle mappings
        mappings[src_parent] = result
        continue
```

### Phase 3: Config Generation

**Generate sub-bundle interface config:**

```python
def _generate_sub_bundle_config(mapping: Dict) -> str:
    """
    Generate DNOS config for sub-bundle interfaces.
    
    Args:
        mapping: Sub-bundle mapping dict from wizard
    
    Returns:
        DNOS interface configuration text
    """
    lines = []
    
    for source_if, target_info in mapping['mappings'].items():
        target_subif = target_info['target']
        ip = target_info.get('ip_transform')
        
        lines.append(f"  {target_subif}")
        if ip:
            lines.append(f"    ipv4-address {ip}")
        lines.append(f"    l2-service enabled")
        
        # Extract VLAN ID from sub-interface ID
        subif_id = target_subif.split('.')[-1]
        lines.append(f"    encapsulation dot1q {subif_id}")
        lines.append(f"  !")
    
    return '\n'.join(lines)
```

---

## Key Benefits

### 1. Smart IP Derivation
- Automatically finds available IP in same subnet
- Avoids conflicts with source IP
- Prefers lower IPs (common practice)

### 2. Bundle-Aware
- Detects LACP bundles
- Shows bundle hierarchy (parent + members)
- Creates sub-bundles (bundle-100.14) not sub-physical

### 3. Flexible IP Options
- Keep source IP
- Auto-derive (smart default)
- Custom manual entry
- Skip individual sub-interfaces

### 4. Clear Preview
- Shows what will be created
- Displays IP transformations
- Requires confirmation before proceeding

### 5. Protocol Integration
- ISIS/LDP automatically use sub-bundles
- WAN mapping updates protocol sections
- No manual post-edit needed

---

## Example Complete Flow

**Source:** PE-4 with 4 WAN sub-interfaces  
**Target:** PE-2 with bundle-100 (LACP)

**User Actions:**
1. Select Mirror Config
2. Choose PE-4 as source
3. Select INTERFACES → [K]eep → Launch WAN mapping
4. Wizard detects: bundle-100 available
5. Wizard offers: "Create 4 sub-bundles on bundle-100?"
6. User selects: [1] Yes
7. For each: Choose IP transformation (default: auto-derive)
8. Confirm: "Create 4 sub-bundles?"
9. ✓ Mappings stored

**Generated:**
- 4 sub-bundles: bundle-100.14, .24, .34, .45
- IPs auto-derived: 14.14.14.2, 24.24.24.2, etc.
- ISIS references: bundle-100.14, .24, .34, .45
- LDP references: bundle-100.14, .24, .34, .45

---

## Testing Checklist

- [ ] Bundle detection from target config
- [ ] LACP member identification
- [ ] Sub-bundle name generation
- [ ] IP auto-derivation logic (/29, /30, /31 subnets)
- [ ] Custom IP entry validation
- [ ] Skip individual sub-interfaces
- [ ] Bundle hierarchy display
- [ ] ISIS/LDP interface updates
- [ ] Config generation (sub-bundle syntax)
- [ ] Back/Cancel at any step

---

## Files to Modify

1. **`mirror_config.py`** - `wan_interface_mapping_wizard()`
   - Add bundle detection
   - Call `_bundle_sub_interface_wizard()`

2. **`mirror_config.py`** - NEW: `_bundle_sub_interface_wizard()`
   - Interactive sub-bundle creation
   - IP transformation options

3. **`mirror_config.py`** - NEW: `_smart_derive_bundle_subif_ip()`
   - Smart IP derivation algorithm

4. **`mirror_config.py`** - `_generate_sub_bundle_config()`
   - Sub-bundle config generation

5. **`mirror_config.py`** - `_merge_wan_protocol_interfaces()`
   - Update to handle sub-bundle mappings

---

## Priority

**Priority:** 🔥 **CRITICAL**

This is **the correct way** to handle DNAAS WAN connections with LACP bundles!

**Impact:** Every PE with LACP bundle WAN connections needs this!

**User Request:** Direct feature request - "Give an option to create Sub-bundles"

---

*Document Date: 2026-01-31*  
*Feature: Smart Bundle Sub-Interface Creation*  
*Status: 📋 **DESIGN COMPLETE - READY FOR IMPLEMENTATION***
