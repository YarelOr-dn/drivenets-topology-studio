# DNOS Delete Syntax Reference

## Key Rule: DNOS Interfaces are FLAT, Not Hierarchical

In DNOS, interfaces (including sub-interfaces) are **siblings** under the `interfaces` block, NOT nested.

**CRITICAL**: Interface names appear at **2-space indent** with **NO `interface` keyword**:

```
interfaces
  ge400-0/0/4          <- Parent (2-space indent, just the name)
    admin-state enabled
    ...
  !
  ge400-0/0/4.1        <- Sub-interface (sibling, NOT child!)
    admin-state enabled
    l2-service enabled
    vlan-tags outer-tag 1 inner-tag 1
  !
  ge400-0/0/4.2        <- Another sub-interface
    admin-state enabled
    ...
  !
!
```

**NOT** this (wrong format):
```
interfaces
  interface ge400-0/0/4    <- WRONG: "interface" keyword not used!
```

## Correct Delete Syntax

### Single Interface/Sub-interface

```
no interfaces <interface-name>
```

Examples:
```
no interfaces ge400-0/0/4.1      # Delete sub-interface
no interfaces ge400-0/0/4        # Delete parent (only if no sub-ifs)
no interfaces pwhe-1.500         # Delete PWHE sub-interface
```

### Multiple Interfaces (Batch)

Each delete is a separate command:
```
no interfaces ge400-0/0/4.1
no interfaces ge400-0/0/4.2
no interfaces ge400-0/0/4.3
```

## Common Mistakes (NEVER DO)

### ❌ WRONG: Using "interface" keyword
```
no interfaces interface ge400-0/0/4.1   # ERROR: Unknown word 'interface'
```

### ❌ WRONG: Nested deletion syntax
```
interfaces interface ge400-0/0/4
  no interfaces ge400-0/0/4.1            # ERROR: Wrong hierarchy
!
```

### ❌ WRONG: Hierarchical structure assumption
```
interfaces ge400-0/0/4
  no ge400-0/0/4.1                        # ERROR: Sub-ifs are siblings
!
```

## Network Services Delete Syntax

### EVPN-VPWS (Direct P2P Services)

Delete all EVPN-VPWS:
```
no network-services evpn-vpws
```

**Note**: Interface attachments inside `evpn-vpws > instance > interface <name>` are 
automatically deleted when the service is deleted. They are NOT defined under the 
`interfaces` hierarchy.

### EVPN-VPWS-FXC (Flexible Cross-Connect)

Delete all FXC:
```
no network-services evpn-vpws-fxc
```

Delete specific xconnect group:
```
network-services evpn-vpws-fxc
  no xconnect group XC-GROUP-NAME
!
```

**Note**: PWHE sub-interfaces used with FXC ARE typically defined under `interfaces`
and need to be deleted separately if desired.

### EVPN-VPLS

Delete all EVPN-VPLS:
```
no network-services evpn-vpls
```

Delete specific instance:
```
network-services evpn-vpls
  no instance INSTANCE-NAME
!
```

### Multihoming (ESI)

Delete all multihoming:
```
no network-services multihoming
```

Delete specific ESI:
```
network-services multihoming
  no es ES-NAME
!
```

## Combined Service + Interface Deletion

When services reference interfaces that are ALSO defined under `interfaces`:

1. **Delete services first** (removes references)
2. **Delete interfaces second** (removes definitions)

Correct order:
```
no network-services evpn-vpws-fxc
no interfaces pwhe-1.1
no interfaces pwhe-1.2
no interfaces pwhe-1.3
```

## Hierarchy Delete Commands Reference

| Target | Command |
|--------|---------|
| All interfaces | `no interfaces` |
| Single interface | `no interfaces <name>` |
| Network services | `no network-services` |
| BGP | `no protocols bgp` |
| ISIS | `no protocols isis` |
| OSPF | `no protocols ospf` |
| System | `no system` |
