# BGP Labeled-Unicast (BGP-LU) Implementation in SCALER

## Overview

SCALER now supports **smart BGP Labeled-Unicast (BGP-LU)** configuration with proper handling of BOTH configuration hierarchies as defined in DNOS 26.x:

1. **Global AFI Level** - Protocol-wide defaults
2. **Neighbor Level** - Per-peer configuration (REQUIRED for peering)

---

## Architecture

### Two Configuration Hierarchies

```
┌─────────────────────────────────────────┐
│  GLOBAL AFI LEVEL (Optional)            │
│  protocols bgp <ASN>                    │
│    address-family ipv4-unicast          │
│      labeled-unicast                    │  ← Sub-command (global config)
│        prefix-sid enabled               │
│        entropy-label ...                │
│        explicit-null enabled            │
│      !                                   │
│      label-allocation per-prefix        │
│    !                                     │
└─────────────────────────────────────────┘
           │
           │ Sets defaults for all peers
           ▼
┌─────────────────────────────────────────┐
│  NEIGHBOR LEVEL (REQUIRED)              │
│  protocols bgp <ASN>                    │
│    neighbor 10.0.0.1                    │
│      address-family ipv4-labeled-unicast│  ← Direct AFI (neighbor config)
│        sr-labeled-unicast               │
│          allow-external-sid send-recv   │
│        !                                 │
│        explicit-null disabled           │  ← Override global
│        nexthop self                     │
│        maximum-prefix limit 50000       │
│      !                                   │
│    !                                     │
└─────────────────────────────────────────┘
```

---

## Implementation Details

### When User Selects BGP-LU AFI

When `ipv4-labeled-unicast` or `ipv6-labeled-unicast` is selected in the wizard:

1. **Global AFI Configuration Prompt** appears:
   ```
   ═══ BGP Labeled-Unicast (BGP-LU) Configuration ═══
   
   1. Global AFI Configuration (protocol-wide defaults)
      Configure router-wide labeled-unicast behavior
   ```

2. **Options Presented:**
   - **Prefix-SID (RFC 8669)** - Allocate labels from SRGB
   - **Entropy Label (RFC 6790)** - Request ELC from peers
     - elc-interop (ELCv2)
     - no-nexthop-validation
   - **Explicit-null** - Send explicit-null (label 0) vs implicit-null
   - **Label Allocation Mode** - per-prefix or per-nexthop

3. **Neighbor-Level Configuration:**
   - **SR Labeled-Unicast** - For eBGP Prefix-SID exchange
     - allow-external-sid (send-only, receive-only, send-receive, disabled)
   - **Explicit-null Override** - Override global default per-neighbor
   - **Nexthop Self** - Set next-hop to self (common for iBGP RR)
   - **Maximum-prefix** - Limit routes from BGP-LU peers

---

## Generated Configuration Example

### Scenario: eBGP BGP-LU Peer with SR Prefix-SID

**User Selections:**
- AFI: Labeled Unicast (BGP-LU)
- Global: prefix-sid enabled, explicit-null enabled, per-prefix allocation
- Neighbor: eBGP with SR allow-external-sid send-receive, nexthop self, max-prefix 50000

**Generated Config:**

```
protocols
  bgp 65000
    router-id 10.0.0.1
    
    # GLOBAL AFI CONFIGURATION
    address-family ipv4-unicast
      label-allocation per-prefix
      labeled-unicast
        prefix-sid enabled
        explicit-null enabled
      !
    !
    
    address-family ipv6-unicast
      label-allocation per-prefix
      labeled-unicast
        prefix-sid enabled
        explicit-null enabled
      !
    !
    
    # NEIGHBOR CONFIGURATION
    neighbor 10.1.1.1
      remote-as 65001
      description "PEER-1"
      address-family ipv4-labeled-unicast
        sr-labeled-unicast
          allow-external-sid send-receive
        !
        send-community community-type both
        soft-reconfiguration inbound
        nexthop self
        maximum-prefix
          limit 50000
          threshold 80
          exceed-action warning-only
        !
      !
      address-family ipv6-labeled-unicast
        sr-labeled-unicast
          allow-external-sid send-receive
        !
        send-community community-type both
        soft-reconfiguration inbound
        nexthop self
        maximum-prefix
          limit 50000
          threshold 80
          exceed-action warning-only
        !
      !
    !
  !
!
```

---

## Key Features

### 1. Smart Detection
- Automatically detects when labeled-unicast AFI is selected
- Prompts for both global and neighbor-level configuration

### 2. eBGP vs iBGP Awareness
- **eBGP peers**: Offers SR labeled-unicast options for Prefix-SID exchange
- **iBGP peers**: Skips SR options (not needed for iBGP)

### 3. Global Defaults with Neighbor Overrides
- Global settings apply to ALL neighbors by default
- Neighbor-level settings override global defaults
- Example: Global explicit-null enabled, but neighbor can disable it

### 4. Comprehensive Options

| Category | Options | Applies To |
|----------|---------|------------|
| **Global AFI** | prefix-sid, entropy-label, explicit-null, label-allocation | All peers |
| **Neighbor SR** | allow-external-sid (send-only/receive-only/send-receive) | Per-peer |
| **Neighbor Opts** | nexthop self, maximum-prefix, explicit-null override | Per-peer |

### 5. Proper DNOS Syntax
- **Global**: Uses `address-family ipv4-unicast labeled-unicast` (sub-command)
- **Neighbor**: Uses `address-family ipv4-labeled-unicast` (direct AFI)
- This is the correct DNOS 26.x syntax pattern

---

## Configuration Variables

### Global AFI Config (`bgp_lu_global_config`)

```python
{
    'prefix_sid': True,              # Enable Prefix-SID (RFC 8669)
    'entropy_label': True,           # Enable Entropy Label (RFC 6790)
    'elc_interop': True,            # ELCv2 interop mode
    'no_nexthop_validation': True,  # Allow NH mismatch in ELC
    'explicit_null': True,          # Send explicit-null (label 0)
    'label_allocation': 'per-prefix'  # or 'per-nexthop'
}
```

### Neighbor Config (`bgp_lu_neighbor_config`)

```python
{
    'explicit_null_override': 'disabled',  # Override global default
    'nexthop_self': True,                  # Set next-hop to self
    'maximum_prefix': {
        'limit': 50000,
        'threshold': 80,
        'exceed_action': 'warning-only'  # or 'restart' or 'excess-discard'
    }
}
```

### SR Options (`sr_labeled_unicast_options`)

```python
{
    'ipv4-labeled-unicast': {
        'allow_external_sid': 'send-receive'  # or 'send-only' or 'receive-only'
    },
    'ipv6-labeled-unicast': {
        'allow_external_sid': 'send-receive'
    }
}
```

---

## Workflow in SCALER

### Step-by-Step User Flow

1. **Select AFI/SAFI**: Choose option `[A] Labeled Unicast (BGP-LU)`
   - Result: `ipv4-labeled-unicast` and `ipv6-labeled-unicast` selected

2. **BGP-LU Configuration Section** appears:
   ```
   ═══ BGP Labeled-Unicast (BGP-LU) Configuration ═══
   ```

3. **Global AFI Prompt**:
   - "Configure global BGP-LU settings?" [Y/n]
   - If YES: Configure prefix-sid, entropy-label, explicit-null, label-allocation

4. **Neighbor-Level Prompt**:
   - For eBGP: "Enable allow-external-sid for eBGP peers?" [y/N]
   - "Enable nexthop self for BGP-LU?" [y/N]
   - "Configure maximum-prefix limit?" [y/N]

5. **Summary** displayed showing all configured options

6. **Continue** to rest of BGP configuration (send-community, soft-reconfig, etc.)

7. **Configuration Generated** with both global AFI and neighbor-level config

---

## Validation Rules

### DNOS Syntax Validation

The implementation ensures:

1. ✅ **Global AFI syntax**: `address-family ipv4-unicast labeled-unicast` (sub-command)
2. ✅ **Neighbor AFI syntax**: `address-family ipv4-labeled-unicast` (direct AFI)
3. ✅ **Proper hierarchy**: Global config appears before neighbor config
4. ✅ **Valid options**: All options validated against DNOS CLI rules

### Consistency Checks

- If global explicit-null is enabled, wizard offers per-neighbor override
- If iBGP (local_as == peer_as), SR options are skipped
- Maximum-prefix only applies to labeled-unicast AFIs

---

## Testing Recommendations

### Test Scenarios

1. **Basic BGP-LU with Global Defaults**
   - Select BGP-LU AFI
   - Configure global prefix-sid, entropy-label
   - Verify both hierarchies in generated config

2. **eBGP with SR Prefix-SID**
   - Select BGP-LU with eBGP peer
   - Enable allow-external-sid send-receive
   - Verify sr-labeled-unicast block in neighbor config

3. **iBGP Route Reflector**
   - Select BGP-LU with iBGP peer (same AS)
   - Verify SR options are NOT offered
   - Enable nexthop self and route-reflector-client

4. **Per-Neighbor Override**
   - Enable global explicit-null
   - Configure neighbor to disable explicit-null
   - Verify override appears in neighbor config

5. **Maximum-prefix with Exceed Actions**
   - Configure maximum-prefix limit 50000
   - Test all three exceed-action options (warning-only, restart, excess-discard)
   - Verify proper DNOS syntax in generated config

---

## References

### DNOS Documentation

- **Global AFI**: `/home/dn/cheetah_26_1/.../afi_ipv4-unicast/labeled-unicast/`
- **Neighbor AFI**: `/home/dn/cheetah_26_1/.../neighbor/address-family/address-family.rst`
- **SR Options**: `.../neighbor/address-family/sr-labeled-unicast/`

### Key RST Files

- `labeled-unicast.rst` - Global AFI labeled-unicast sub-command (Release 18.1)
- `address-family.rst` - Neighbor AFI with `ipv4/6-labeled-unicast` direct AFI (Release TBD)
- `prefix-sid.rst` - BGP Prefix-SID (RFC 8669)
- `entropy-label.rst` - Entropy Label (RFC 6790)
- `explicit-null.rst` - Explicit-null configuration (Release 25.3)
- `allow-external-sid.rst` - eBGP Prefix-SID exchange (Release 18.1)

---

## Future Enhancements

### Potential Additions

1. **Prefix-SID Mapping**
   - `prefix-sid-map` for inbound labeled-unicast routes
   - Map received routes to Prefix-SID with global-block-origination

2. **Per-AFI Options**
   - Support different settings for IPv4 vs IPv6 labeled-unicast
   - Currently applies same settings to both

3. **Add-Path Support**
   - `add-path send/receive` for BGP-LU AFI
   - Multiple path advertisement

4. **AIGP Support**
   - Accumulated IGP metric for BGP-LU routes
   - Already documented in DNOS

5. **Policy Support**
   - Import/export policies specific to labeled-unicast
   - Currently inherits from generic BGP policy prompts

---

## Summary

The SCALER BGP-LU implementation provides a **smart, hierarchical configuration system** that:

✅ Understands the dual nature of BGP-LU configuration (global + neighbor)  
✅ Presents options contextually based on peer type (eBGP vs iBGP)  
✅ Generates correct DNOS 26.x syntax for both hierarchies  
✅ Supports all major BGP-LU features (Prefix-SID, Entropy Label, SR, etc.)  
✅ Allows global defaults with per-neighbor overrides  
✅ Validates configuration against DNOS CLI rules  

This implementation follows **DNOS best practices** and aligns with the latest DNOS 26.x documentation.
