# Mirror Config Enhancement: Add [E]dit Option for All Sub-Sections

## Problem

User Issue: "Why can't i Edit This value?"

**Current Behavior:**
```
For each sub-section: [K]eep=Mirror | [T]arget=Keep target's | [S]kip=Keep target's

  Hostname (→ PE-2)  [k/K/t/T/s/S/b/B] (k):
```

**Missing:** `[E]dit` option to **manually enter custom values**!

Currently only offers:
- `[K]eep` - Use source value (PE-4)
- `[T]arget` - Keep target's value (PE-2)
- `[S]kip` - Same as target

**But NO way to enter:**
- Custom hostname (e.g., "PE-2-NEW")
- Custom loopback IP
- Custom NTP servers
- Custom BGP ASN
- etc.

---

## User Request

> "instead of Skip add edit per Value with smart suggestion, in the mirror implementation per each option"

**Requirements:**
1. Add `[E]dit` option for **ALL** sub-sections (not just services)
2. Provide **smart suggestions** based on:
   - Source value
   - Target value
   - Common patterns
   - Detected values
3. Allow **manual entry** with validation

---

## Current Code Issues

### Location: `scaler/wizard/mirror_config.py:8459-8546`

```python
# Line 8459: Only mentions services can be edited
console.print("[dim]For each sub-section: [K]eep=[green]Mirror[/green] | [T]arget=[cyan]Keep target's[/cyan] | [S]kip=[cyan]Keep target's[/cyan][/dim]")
if hierarchy_key == 'network-services':
    console.print("[dim]Service sub-sections also support: [E]dit=[yellow]Edit knobs/interfaces[/yellow][/dim]")

# Line 8537-8540: Only services get [E]dit option
if key in service_keys:  # Only ('fxc', 'vpws', 'vpls', 'vrf')
    action_choices = ['k', 'K', 'e', 'E', 't', 'T', 's', 'S', 'b', 'B']
else:
    action_choices = ['k', 'K', 't', 'T', 's', 'S', 'b', 'B']  # ❌ NO EDIT!
```

---

## Enhancement Design

### 1. Add [E]dit Option to ALL Sub-Sections

```python
# ALWAYS include [E]dit option
action_choices = ['k', 'K', 'e', 'E', 't', 'T', 's', 'S', 'b', 'B']

# Update prompt hint
console.print("[dim]For each sub-section:[/dim]")
console.print("[dim]  [K]eep=[green]Mirror from source[/green] | [E]dit=[yellow]Enter custom value[/yellow][/dim]")
console.print("[dim]  [T]arget=[cyan]Keep target's[/cyan] | [S]kip=[cyan]Keep target's[/cyan][/dim]")
```

### 2. Implement Smart Suggestions Per Sub-Section Type

#### A. Hostname
```python
if key == 'hostname' and action == 'e':
    source_hostname_val = extract_hostname_from_config(mirror.source_config)
    target_hostname_val = extract_hostname_from_config(mirror.target_config)
    
    console.print("\n[bold]Enter Custom Hostname[/bold]")
    console.print(f"  Source: [dim]{source_hostname_val}[/dim]")
    console.print(f"  Target: [dim]{target_hostname_val}[/dim]")
    console.print(f"  [cyan]Suggestions:[/cyan]")
    console.print(f"    • {target_hostname_val} (keep target's)")
    console.print(f"    • {target_hostname_val}-NEW")
    console.print(f"    • {target_hostname_val}-MIRROR")
    
    custom_hostname = Prompt.ask(
        "  Enter hostname [B]ack",
        default=target_hostname_val
    )
    
    if custom_hostname.lower() == 'b':
        continue
    
    selections[key] = {'action': 'custom', 'value': custom_hostname}
```

#### B. Loopback (lo0)
```python
if key == 'lo0' and action == 'e':
    source_lo0 = get_lo0_ip_from_config(mirror.source_config)
    target_lo0 = get_lo0_ip_from_config(mirror.target_config)
    
    console.print("\n[bold]Enter Custom Loopback IP[/bold]")
    console.print(f"  Source lo0: [dim]{source_lo0 or 'N/A'}[/dim]")
    console.print(f"  Target lo0: [dim]{target_lo0 or 'N/A'}[/dim]")
    console.print(f"  [cyan]Suggestions:[/cyan]")
    
    # Smart suggestions based on patterns
    suggestions = []
    if source_lo0:
        suggestions.append(source_lo0)
    if target_lo0:
        suggestions.append(target_lo0)
    
    # Extract base IP and suggest next
    if source_lo0 and '.' in source_lo0:
        base = source_lo0.split('.')[0:3]
        last = int(source_lo0.split('.')[3].split('/')[0])
        suggestions.append(f"{'.'.join(base)}.{last+1}/32")
    
    for i, sug in enumerate(suggestions, 1):
        console.print(f"    [{i}] {sug}")
    
    custom_lo0 = Prompt.ask(
        "  Enter loopback IP/mask [B]ack",
        default=target_lo0 or source_lo0 or "1.1.1.1/32"
    )
    
    if custom_lo0.lower() == 'b':
        continue
    
    # Validate IP format
    if not re.match(r'^\d+\.\d+\.\d+\.\d+(/\d+)?$', custom_lo0):
        console.print("[red]Invalid IP format. Using target's value.[/red]")
        selections[key] = 'keep_target'
    else:
        selections[key] = {'action': 'custom', 'value': custom_lo0}
```

#### C. NTP Servers
```python
if key == 'ntp' and action == 'e':
    source_ntp = extract_ntp_servers_from_config(mirror.source_config)
    target_ntp = extract_ntp_servers_from_config(mirror.target_config)
    
    console.print("\n[bold]Configure NTP Servers[/bold]")
    console.print(f"  Source: [dim]{', '.join(source_ntp) if source_ntp else 'N/A'}[/dim]")
    console.print(f"  Target: [dim]{', '.join(target_ntp) if target_ntp else 'N/A'}[/dim]")
    console.print(f"\n  [cyan]Options:[/cyan]")
    console.print(f"    [1] Use source NTP servers: {source_ntp}")
    console.print(f"    [2] Use target NTP servers: {target_ntp}")
    console.print(f"    [3] Enter custom NTP servers")
    
    choice = Prompt.ask("  Select", choices=['1', '2', '3', 'b', 'B'], default='2')
    
    if choice == 'b':
        continue
    elif choice == '1':
        selections[key] = {'action': 'mirror'}
    elif choice == '2':
        selections[key] = {'action': 'keep_target'}
    else:
        ntp_list = Prompt.ask("  Enter NTP servers (comma-separated)")
        selections[key] = {'action': 'custom', 'value': ntp_list.split(',')}
```

#### D. BGP ASN (in protocols → bgp)
```python
if key == 'bgp' and action == 'e':
    source_asn = extract_bgp_asn_from_config(mirror.source_config)
    target_asn = extract_bgp_asn_from_config(mirror.target_config)
    
    console.print("\n[bold]Edit BGP Configuration[/bold]")
    console.print(f"\n  [yellow]BGP ASN:[/yellow]")
    console.print(f"    Source ASN: [dim]{source_asn or 'N/A'}[/dim]")
    console.print(f"    Target ASN: [dim]{target_asn or 'N/A'}[/dim]")
    
    asn_choice = Prompt.ask(
        "  Use [S]ource, [T]arget, or enter [C]ustom ASN",
        choices=['s', 'S', 't', 'T', 'c', 'C', 'b', 'B'],
        default='t'
    ).lower()
    
    if asn_choice == 'b':
        continue
    elif asn_choice == 's':
        custom_asn = source_asn
    elif asn_choice == 't':
        custom_asn = target_asn
    else:
        custom_asn = Prompt.ask("  Enter BGP ASN", default=str(target_asn or source_asn))
    
    # Validate ASN
    try:
        asn_int = int(custom_asn)
        if 1 <= asn_int <= 4294967295:
            selections[key] = {'action': 'custom', 'bgp_asn': asn_int}
        else:
            console.print("[red]Invalid ASN range. Using target's.[/red]")
            selections[key] = 'keep_target'
    except:
        console.print("[red]Invalid ASN. Using target's.[/red]")
        selections[key] = 'keep_target'
```

### 3. Summary of Editable Sub-Sections

| Hierarchy | Sub-Section | Smart Suggestions | Validation |
|-----------|-------------|-------------------|------------|
| **system** | hostname | Target+suffixes (-NEW, -MIRROR) | Alphanumeric+dash |
| | ntp | Source/target/custom list | IP format |
| | logging | Source/target/custom | IP format |
| | aaa | Source/target/edit users | Username format |
| **interfaces** | lo0 | Source/target/next IP | IP/mask format |
| | wan | Interactive mapping wizard | Already implemented |
| **protocols** | bgp | Edit ASN, router-id | ASN: 1-4294967295 |
| | isis | Edit NET address | ISO format |
| | ldp | Edit router-id | IP format |
| **network-services** | fxc/vpws/vpls/vrf | Edit knobs/ranges | Already implemented |

---

## Implementation Plan

### Phase 1: Core Edit Infrastructure ✅

1. **Add [E]dit to all action_choices** (line 8540)
   ```python
   action_choices = ['k', 'K', 'e', 'E', 't', 'T', 's', 'S', 'b', 'B']
   ```

2. **Update prompt hints** (line 8459)
   ```python
   console.print("[dim]For each sub-section:[/dim]")
   console.print("[dim]  [K]eep=[green]Use source[/green] | [E]dit=[yellow]Custom value[/yellow] | [T]arget=[cyan]Keep target's[/cyan] | [S]kip=[cyan]Same as target[/cyan][/dim]")
   ```

3. **Add edit handler dispatch**
   ```python
   elif action == 'e':
       result = _edit_subsection_value(key, name, mirror, source_hostname, target_hostname, analysis)
       if result:
           selections[key] = result
       else:
           # User cancelled, keep target
           selections[key] = 'keep_target'
   ```

### Phase 2: Per-SubSection Edit Handlers ✅

Create `_edit_subsection_value()` function:

```python
def _edit_subsection_value(
    key: str,
    name: str,
    mirror: 'ConfigMirror',
    source_hostname: str,
    target_hostname: str,
    analysis: dict
) -> Optional[Dict]:
    """
    Edit wizard for individual sub-section values.
    
    Provides smart suggestions based on source/target values.
    
    Args:
        key: Sub-section key (e.g., 'hostname', 'lo0', 'ntp')
        name: Display name
        mirror: ConfigMirror object
        source_hostname: Source device hostname
        target_hostname: Target device hostname
        analysis: Config analysis dict
    
    Returns:
        Dict with {'action': 'custom', 'value': ...} or None if cancelled
    """
    if key == 'hostname':
        return _edit_hostname_value(mirror, source_hostname, target_hostname)
    elif key == 'lo0':
        return _edit_loopback_value(mirror, source_hostname, target_hostname)
    elif key == 'ntp':
        return _edit_ntp_value(mirror)
    elif key == 'logging':
        return _edit_logging_value(mirror)
    elif key == 'aaa':
        return _edit_aaa_value(mirror)
    elif key == 'bgp':
        return _edit_bgp_value(mirror, analysis)
    elif key == 'isis':
        return _edit_isis_value(mirror)
    elif key == 'ldp':
        return _edit_ldp_value(mirror)
    else:
        console.print(f"[yellow]Edit not yet implemented for {name}[/yellow]")
        Prompt.ask("[dim]Press Enter[/dim]", default="")
        return None
```

### Phase 3: Helper Functions ✅

```python
def extract_hostname_from_config(config: str) -> Optional[str]:
    """Extract hostname from config."""
    match = re.search(r'^\s*system\s*\n(?:.*\n)*?\s*name\s+(.+?)$', config, re.MULTILINE)
    return match.group(1).strip() if match else None

def extract_ntp_servers_from_config(config: str) -> List[str]:
    """Extract NTP server IPs from config."""
    servers = []
    in_ntp = False
    for line in config.split('\n'):
        if re.match(r'^\s*ntp\s*$', line):
            in_ntp = True
        elif in_ntp and re.match(r'^\s*server\s+(\d+\.\d+\.\d+\.\d+)', line):
            servers.append(re.match(r'^\s*server\s+(\d+\.\d+\.\d+\.\d+)', line).group(1))
        elif in_ntp and re.match(r'^\s*!\s*$', line):
            break
    return servers

def extract_bgp_asn_from_config(config: str) -> Optional[int]:
    """Extract BGP AS number from config."""
    match = re.search(r'^\s*bgp\s*\n\s*as-number\s+(\d+)', config, re.MULTILINE)
    return int(match.group(1)) if match else None
```

---

## Benefits

1. **Full Control**: User can customize ANY value during mirror
2. **Smart Suggestions**: Context-aware defaults reduce typing
3. **Validation**: Prevent invalid values (IPs, ASNs, hostnames)
4. **Consistency**: Same [E]dit pattern across all sub-sections
5. **Backward Compatible**: Default behavior unchanged (K/T/S still work)

---

## Example User Flow

### Before Enhancement ❌
```
  Hostname (→ PE-2)  [k/K/t/T/s/S/b/B] (k): k
```
**Result:** Must use target hostname "PE-2" or source "PE-4", no custom option!

### After Enhancement ✅
```
  Hostname (→ PE-2)  [k/K/e/E/t/T/s/S/b/B] (k): e

Enter Custom Hostname
  Source: PE-4
  Target: PE-2
  Suggestions:
    • PE-2 (keep target's)
    • PE-2-NEW
    • PE-2-MIRROR
  
  Enter hostname [B]ack (PE-2): PE-2-BACKUP
  
✓ Custom hostname: PE-2-BACKUP
```

---

## Files to Modify

1. **`scaler/wizard/mirror_config.py`**
   - Line 8459: Update prompt hint text
   - Line 8537-8540: Add 'e'/'E' to all action_choices
   - Line 8546+: Add `elif action == 'e':` handler
   - New functions:
     - `_edit_subsection_value()`
     - `_edit_hostname_value()`
     - `_edit_loopback_value()`
     - `_edit_ntp_value()`
     - `_edit_bgp_value()`
     - etc.

2. **`scaler/wizard/mirror_config.py` (helpers section)**
   - Add extraction helper functions:
     - `extract_hostname_from_config()`
     - `extract_ntp_servers_from_config()`
     - `extract_bgp_asn_from_config()`
     - etc.

---

## Testing Checklist

- [ ] Edit hostname → Custom value used
- [ ] Edit loopback → IP validation works
- [ ] Edit NTP → Multi-server entry works
- [ ] Edit BGP ASN → Range validation (1-4294967295)
- [ ] [B]ack works in all edit sub-wizards
- [ ] Invalid input shows error + keeps target value
- [ ] Default (K/T/S) still work as before
- [ ] Final config shows custom values correctly

---

**Status:** 📋 **DESIGN COMPLETE - Ready for Implementation**  
**Priority:** 🔥 **HIGH** (User explicitly requested)  
**Effort:** ~2-3 hours (implement edit handlers + helpers)

*Document Date: 2026-01-31*  
*Feature Request: Add [E]dit option with smart suggestions to Mirror Config*
