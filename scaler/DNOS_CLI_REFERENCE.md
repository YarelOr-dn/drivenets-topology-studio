# DNOS CLI Configuration Reference

## ⚠️ IMPORTANT: Always Consult the Official DNOS CLI Documentation

When implementing any new configuration commands or modifying existing ones in the SCALER application, **ALWAYS** refer to the official DNOS CLI documentation:

### Primary Reference:
- **PDF**: `/home/dn/SCALER/docs/DNOS_CLI.pdf`
- **RST Docs**: `/home/dn/SCALER/dnos_cheetah_docs/`

### Why This Matters:
1. DNOS CLI syntax can be complex and version-specific
2. Incorrect syntax causes commit failures on real devices
3. The documentation contains exact parameter formats, ranges, and validation rules

---

## Network Services Configuration Syntax Reference

### VRF / L3VPN Configuration

**IMPORTANT**: VRF configuration is **NOT fully implemented** in the Scaler wizard. The current implementation uses the FXC code path which generates incorrect VRF syntax.

#### Correct VRF Instance Syntax:
```
configure
network-services
  vrf
    instance <vrf-name>
      interface <interface-name>
      protocols
        bgp <as-number>
          router-id <router-id>
          route-distinguisher <rd-value>
          address-family ipv4-unicast
            import-vpn route-target <rt-value>
            export-vpn route-target <rt-value>
            redistribute connected
          !
        !
      !
    !
  !
!
```

#### Example - Complete L3VPN VRF:
```
network-services
  vrf
    instance customer_vrf_1
      interface ge100-1/1/1.10
      interface bundle-1.100
      protocols
        bgp 65000
          route-distinguisher 10.0.0.1:100
          address-family ipv4-unicast
            import-vpn route-target 65000:100
            export-vpn route-target 65000:100
            redistribute connected
          !
        !
      !
    !
  !
!
```

### FXC (EVPN-VPWS-FXC) Configuration

**Status**: ✅ Fully implemented

#### Correct FXC Syntax:
```
network-services
  evpn-vpws-fxc
    instance <name>
      admin-state enabled
      evpn-vpws-fxc-protocols
        evpn
          route-distinguisher <rd>
          route-target export <rt>
          route-target import <rt>
        !
      !
      transport-protocol
        mpls
          control-word enabled
          fat-label enabled
        !
      !
      interface <pwhe-interface>
        service-point-id <spid>
      !
    !
  !
!
```

### EVPN Configuration

**Status**: ⚠️ Partially implemented

### Multihoming Configuration

**Status**: ✅ Fully implemented

#### Correct Multihoming Syntax:
```
network-services
  multihoming
    redundancy-mode single-active
    startup-delay <seconds>
    designated-forwarder
      algorithm highest-preference
    !
    interface <interface>
      esi arbitrary value <esi-value>
      redundancy-mode single-active
      designated-forwarder
        algorithm highest-preference value <preference>
      !
    !
  !
!
```

---

## Hierarchy Delete Commands

### Full Hierarchy Deletion (from configure mode):
| Hierarchy | Command |
|-----------|---------|
| System | `no system` |
| Interfaces | `no interfaces` |
| Network Services | `no network-services` |
| BGP | `no protocols bgp` |
| ISIS | `no protocols isis` |
| OSPF | `no protocols ospf` |
| Multihoming | `no network-services multihoming` |

### Sub-Hierarchy Deletion:
| Item | Command |
|------|---------|
| FXC Instance | `no network-services evpn-vpws-fxc instance <name>` |
| VRF Instance | `no network-services vrf instance <name>` |
| BGP Neighbor | `protocols bgp` → `no neighbor <ip>` |
| Interface | `no interfaces <name>` |

---

## Documentation Locations

### RST Documentation Structure:
```
/home/dn/SCALER/dnos_cheetah_docs/
├── Network-services/
│   ├── vrf/                    # L3VPN/VRF configuration
│   ├── evpn-vpws-fxc/          # FXC services
│   ├── evpn/                   # EVPN services
│   ├── multihoming/            # ESI/multihoming
│   └── ...
├── Protocols/
│   ├── bgp/                    # BGP configuration
│   ├── isis/                   # ISIS configuration
│   └── ...
├── Interfaces/                 # Interface configuration
├── System/                     # System configuration
└── ...
```

---

## Implementation Status Summary

| Feature | Status | Notes |
|---------|--------|-------|
| FXC Configuration | ✅ Full | Wizard generates correct syntax |
| EVPN Configuration | ⚠️ Partial | Basic support only |
| VPWS Configuration | ⚠️ Partial | Basic support only |
| **VRF / L3VPN** | ✅ **Full** | Dedicated wizard with all options |
| Multihoming | ✅ Full | ESI, DF, redundancy modes |
| BGP | ✅ Full | Neighbors, address families |
| IGP (ISIS/OSPF) | ✅ Full | SR-MPLS support |
| Interfaces | ✅ Full | PWHE, physical, bundles |

---

## Adding New Configuration Features

When adding new configuration features to SCALER:

1. **FIRST**: Look up the exact syntax in `/home/dn/SCALER/dnos_cheetah_docs/`
2. **SECOND**: Verify against `/home/dn/SCALER/docs/DNOS_CLI.pdf`
3. **THIRD**: Test on a real device or simulator with `commit check`
4. **FOURTH**: Document the syntax in this file

### Example: Looking up VRF configuration
```bash
# Find all VRF-related documentation
ls -la /home/dn/SCALER/dnos_cheetah_docs/Network-services/vrf/

# Read specific command syntax
cat /home/dn/SCALER/dnos_cheetah_docs/Network-services/vrf/instance/instance.rst
cat /home/dn/SCALER/dnos_cheetah_docs/Network-services/vrf/instance/protocols/bgp/bgp.rst
```

---

*Last updated: December 2025*

