# DNOS CLI Documentation Index - v26.1 Complete

Complete CLI documentation for DriveNets Network Operating System (DNOS) v26.1

**Total Files:** 4,246 RST files across 674 directories

---

## 📁 Configuration Hierarchies

### Core Configuration

| Category | Files | Description |
|----------|-------|-------------|
| [Interfaces/](./Interfaces/) | 160 | Physical, sub-interfaces, bundles, VLANs, MTU, ACLs, QoS, flow-monitoring |
| [Network-services/](./Network-services/) | 576 | EVPN, EVPN-VPWS, EVPN-VPWS-FXC, VRF, Multihoming, NAT, IPsec, Bridge-domain |
| [System/](./System/) | 571 | Profile, SSH, Login, SNMP, NTP, Management, AAA, TACACS |
| [Protocols/](./Protocols/) | 1,306 | BGP, IS-IS, OSPF, OSPFv3, LDP, MPLS, LACP, BFD, VRRP, PIM, MSDP, IGMP |
| [QoS/](./QoS/) | 159 | Quality of Service, traffic classes, policies, ECN, WRED, port-mirroring |
| [Services/](./Services/) | 213 | Flow monitoring, sFlow, DHCP, OAM, TWAMP, L2-cross-connect |

### Network Services Hierarchies

| Service | Path | Description |
|---------|------|-------------|
| **EVPN** | `Network-services/evpn/` | EVPN service with router-interface, interface, mac-handling |
| **EVPN-VPWS** | `Network-services/evpn-vpws/` | EVPN VPWS point-to-point L2 service |
| **EVPN-VPWS-FXC** | `Network-services/evpn-vpws-fxc/` | Flexible Cross-connect with interface hierarchy |
| **VRF** | `Network-services/vrf/` | L3 VPN with full BGP, VRRP, static protocols |
| **Multihoming** | `Network-services/multihoming/` | ESI, designated-forwarder, redundancy-mode |
| **Bridge-domain** | `Network-services/bridge-domain/` | L2 bridging with router-interface |
| **NAT** | `Network-services/nat/` | SNAT44, DNAT44, SNAPT44, NAPT44 rules |
| **IPsec** | `Network-services/ipsec/` | IKE maps, tunnels, encryption |

### Key Hierarchies (User Requested)

#### EVPN Router-Interface
```
Network-services/evpn/instance/router-interface/
└── router-interface.rst    # IRB configuration for EVPN
```

#### EVPN Interface Inside Network-services
```
Network-services/evpn/instance/interface/
├── interface.rst
├── e-tree.rst
├── sticky-interface.rst
├── sticky-mac.rst
├── invert-preference-algorithm.rst
└── storm-control/
```

#### Multihoming (PWHE) Interface
```
Network-services/multihoming/interface/
├── interface.rst           # PWHE interface configuration
├── esi.rst                 # ESI configuration
├── esi_arbitrary.rst       # Arbitrary ESI
├── esi_lacp.rst           # LACP-based ESI
├── redundancy-mode.rst
├── no-startup-delay.rst
└── designated-forwarder/
    ├── algorithm.rst
    ├── algorithm_mod.rst
    ├── algorithm_highest_preference.rst
    ├── df-propagation.rst
    ├── election-time.rst
    └── no-preemption.rst
```

#### VRF Protocols Hierarchy
```
Network-services/vrf/instance/protocols/
├── bgp/                    # Full BGP with neighbor, address-family
│   ├── neighbor/
│   ├── neighbor-group/
│   ├── afi_ipv4-unicast/
│   ├── afi_ipv6-unicast/
│   └── graceful-restart/
├── static/                 # Static routes with BFD
└── vrrp/                   # VRRP with IPv4/IPv6 AFI
```

### Access Control Lists

| Category | Files | Description |
|----------|-------|-------------|
| [Access-lists/](./Access-lists/) | 22 | IPv4/IPv6 ACLs with rules |
| [AS-path Access-list/](./AS-path%20Access-list/) | - | BGP AS-path filtering |
| [Community-list/](./Community-list/) | 6 | BGP community filtering |

#### ACL Rule Options
```
Access-lists/access-lists rule*.rst
├── src-ip, dest-ip         # Source/Destination IP
├── src-ports, dest-ports   # TCP/UDP ports
├── protocol                # IP protocol matching
├── icmp, ipv6-icmp        # ICMP type/code
├── dscp                    # DSCP marking
├── tcp-flag               # TCP flags
├── fragmented             # Fragment matching
├── packet-length          # Packet size
├── next-hop, next-table   # PBR actions
├── set-qos                # QoS actions
└── vrf                    # VRF matching
```

### Routing & Policy

| Category | Files | Description |
|----------|-------|-------------|
| [Routing-options/](./Routing-options/) | 37 | Router-ID, load-balancing, next-hop resolution |
| [Routing-policy/](./Routing-policy/) | 76 | Route maps, community-list, prefix-list |
| [Policy/](./Policy/) | 42 | Hierarchical policies |
| [Prefix-list/](./Prefix-list/) | 3 | IPv4/IPv6 prefix lists |
| [Segment-routing/](./Segment-routing/) | 1 | SR-MPLS configuration |

---

## 🚀 Transport-Protocol Options (Updated from drivenets/cheetah)

The transport-protocol hierarchy now includes documentation for all options:

### Available Transport Protocols

| Transport | Status | Location |
|-----------|--------|----------|
| **MPLS** | ✅ Complete | `transport-protocol/mpls/` with `control-word`, `fat-label` |
| **VXLAN** | ✅ Complete | `transport-protocol/vxlan/` with `vni`, `vtep-source-if` |
| **SRv6** | ✅ Complete | `transport-protocol/srv6/` with `locator` |
| **MPLS-SRv6-Migration** | ✅ Available | For transitioning from MPLS to SRv6 |

### VXLAN Configuration (for EVPN)

```
Network-services/evpn/instance/transport-protocol/vxlan/
├── vxlan.rst           # Enable VXLAN transport
├── vni.rst             # VXLAN Network Identifier (1-16777215)
└── vtep-source-if.rst  # VTEP source interface (loopback)
```

**Example:**
```bash
network-services evpn instance EVPN-1 {
    transport-protocol vxlan {
        vni 10001;
        vtep-source-if lo0;
    }
}
```

### SRv6 Configuration (for EVPN-VPWS/FXC)

```
Network-services/evpn-vpws-fxc/instance/transport-protocol/srv6/
├── srv6.rst            # Enable SRv6 transport
└── locator.rst         # SRv6 locator name

Network-services/evpn-vpws/instance/transport-protocol/srv6/
├── srv6.rst            # Enable SRv6 transport
└── locator.rst         # SRv6 locator name
```

**Example:**
```bash
network-services evpn-vpws-fxc FXC-1 {
    instance 1 {
        transport-protocol srv6 {
            locator MAIN_LOC;
        }
    }
}
```

**Note:** VXLAN and SRv6 documentation sourced from `drivenets/cheetah` main repository (v26.1).

### Protocol-Specific

| Category | Files | Description |
|----------|-------|-------------|
| [BFD/](./BFD/) | 9 | Bidirectional Forwarding Detection |
| [LDP/](./LDP/) | 25 | Label Distribution Protocol |
| [MPLS/](./MPLS/) | 2 | Multiprotocol Label Switching |
| [Multicast/](./Multicast/) | 3 | PIM, IGMP, MSDP |
| [Traffic Engineering/](./Traffic%20Engineering/) | 40 | MPLS-TE, PCEP, DiffServ-TE |

---

## 📋 Operational Commands

| Category | Files | Description |
|----------|-------|-------------|
| [Show Commands/](./Show%20Commands/) | 442 | Device status, routing tables, counters |
| [Clear Commands/](./Clear%20Commands/) | - | Statistics and session management |
| [Request Commands/](./Request%20Commands/) | 57 | Operational requests |
| [Run Commands/](./Run%20Commands/) | 30 | Execute operations |
| [Set Commands/](./Set%20Commands/) | 14 | Terminal settings |

---

## 🔧 CLI Usage

| Category | Files | Description |
|----------|-------|-------------|
| [CLI Guidelines/](./CLI%20Guidelines/) | - | Usage, navigation, shortcuts |
| [Transactions/](./Transactions/) | 8 | Commit, rollback, load, save |
| [Accessing the CLI Terminal/](./Accessing%20the%20CLI%20Terminal/) | - | SSH, console access |
| [Main Menu Commands/](./Main%20Menu%20Commands/) | - | Top-level navigation |
| [GI Mode Commands/](./GI%20Mode%20Commands/) | - | Generic Interface mode |
| [Recovery Mode Commands/](./Recovery%20Mode%20Commands/) | 8 | System recovery |
| [Debug log Commands/](./Debug%20log%20Commands/) | - | Debug and logging |

---

## 🔒 Security & Advanced

| Category | Files | Description |
|----------|-------|-------------|
| [nacm/](./nacm/) | 10 | NETCONF Access Control Model |
| [forwarding-options/](./forwarding-options/) | 13 | Forwarding plane options |
| [tracking-policy/](./tracking-policy/) | 11 | Interface/route tracking |
| [High-availability/](./High-availability/) | 9 | HA configuration |

---

## 📊 Quick Reference

### Essential Show Commands
```bash
show config | no-more              # Full configuration
show system | no-more              # System info, Router ID
show interfaces | no-more          # All interfaces
show interfaces brief              # Interface summary
show isis | no-more                # IS-IS status
show ospf | no-more                # OSPF status
show bgp summary | no-more         # BGP neighbors
show ldp summary | no-more         # LDP sessions
show segment-routing | no-more     # SR-MPLS
show evpn-vpws-fxc | no-more       # FXC services
show network-services | no-more    # All services
show access-lists | no-more        # ACL configuration
show multihoming | no-more         # MH status
```

### Configuration Workflow
```bash
configure                          # Enter config mode
set interfaces ge100-0/0/1 admin-state enabled
set network-services evpn-vpws-fxc FXC-1 admin-state enabled
show | compare                     # Review changes
commit check                       # Validate
commit                             # Apply
```

### Network Service Examples

#### EVPN with Router-Interface (IRB)
```
network-services {
    evpn EVPN-1 {
        instance 1 {
            interface ge100-0/0/1.100 { }
            router-interface irb100 { }
            evpn-protocols {
                bgp {
                    route-distinguisher 1.1.1.1:1;
                    export-l2vpn-evpn-route-target 65000:1;
                    import-l2vpn-evpn-route-target 65000:1;
                }
            }
        }
    }
}
```

#### Multihoming with ESI
```
network-services {
    multihoming {
        interface bundle1 {
            esi arbitrary 00:11:22:33:44:55:66:77:88:99;
            redundancy-mode all-active;
            designated-forwarder {
                algorithm mod;
            }
        }
    }
}
```

#### EVPN-VPWS-FXC with Interface
```
network-services {
    evpn-vpws-fxc FXC-1 {
        instance 1 {
            admin-state enabled;
            fxc-mode vlan-unaware;
            interface ge100-0/0/1.100 { }
            transport-protocol mpls { }
            evpn-vpws-fxc-protocols {
                bgp {
                    route-distinguisher 1.1.1.1:1;
                    export-l2vpn-evpn-route-target 65000:100;
                    import-l2vpn-evpn-route-target 65000:100;
                }
            }
        }
    }
}
```

---

## 📈 Documentation Coverage

| Category | RST Files | Status |
|----------|-----------|--------|
| Protocols | 1,306 | ✅ Complete |
| Network-services | 576 | ✅ Complete |
| System | 571 | ✅ Complete |
| Show Commands | 442 | ✅ Complete |
| Services | 213 | ✅ Complete |
| Interfaces | 160 | ✅ Complete |
| QoS | 159 | ✅ Complete |
| Routing-policy | 76 | ✅ Complete |
| Request Commands | 57 | ✅ Complete |
| Policy | 42 | ✅ Complete |
| Traffic Engineering | 40 | ✅ Complete |
| Routing-options | 37 | ✅ Complete |
| Run Commands | 30 | ✅ Complete |
| LDP | 25 | ✅ Complete |
| Access-lists | 22 | ✅ Complete |
| Set Commands | 14 | ✅ Complete |
| forwarding-options | 13 | ✅ Complete |
| tracking-policy | 11 | ✅ Complete |
| nacm | 10 | ✅ Complete |
| BFD | 9 | ✅ Complete |
| High-availability | 9 | ✅ Complete |
| Transactions | 8 | ✅ Complete |
| Recovery Mode Commands | 8 | ✅ Complete |
| debug | 7 | ✅ Complete |
| Community-list | 6 | ✅ Complete |
| Multicast | 3 | ✅ Complete |
| Prefix-list | 3 | ✅ Complete |
| MPLS | 2 | ✅ Complete |
| Segment-routing | 1 | ✅ Complete |

**Total: 4,246 RST files** | All hierarchies complete

---

*Fetched from DriveNets askai-poc repository - December 2024*
*DNOS Version: v26.1*

```

### Routing & Policy

| Category | Files | Description |
|----------|-------|-------------|
| [Routing-options/](./Routing-options/) | 37 | Router-ID, load-balancing, next-hop resolution |
| [Routing-policy/](./Routing-policy/) | 76 | Route maps, community-list, prefix-list |
| [Policy/](./Policy/) | 42 | Hierarchical policies |
| [Prefix-list/](./Prefix-list/) | 3 | IPv4/IPv6 prefix lists |
| [Segment-routing/](./Segment-routing/) | 1 | SR-MPLS configuration |

---

## 🚀 Transport-Protocol Options (Updated from drivenets/cheetah)

The transport-protocol hierarchy now includes documentation for all options:

### Available Transport Protocols

| Transport | Status | Location |
|-----------|--------|----------|
| **MPLS** | ✅ Complete | `transport-protocol/mpls/` with `control-word`, `fat-label` |
| **VXLAN** | ✅ Complete | `transport-protocol/vxlan/` with `vni`, `vtep-source-if` |
| **SRv6** | ✅ Complete | `transport-protocol/srv6/` with `locator` |
| **MPLS-SRv6-Migration** | ✅ Available | For transitioning from MPLS to SRv6 |

### VXLAN Configuration (for EVPN)

```
Network-services/evpn/instance/transport-protocol/vxlan/
├── vxlan.rst           # Enable VXLAN transport
├── vni.rst             # VXLAN Network Identifier (1-16777215)
└── vtep-source-if.rst  # VTEP source interface (loopback)
```

**Example:**
```bash
network-services evpn instance EVPN-1 {
    transport-protocol vxlan {
        vni 10001;
        vtep-source-if lo0;
    }
}
```

### SRv6 Configuration (for EVPN-VPWS/FXC)

```
Network-services/evpn-vpws-fxc/instance/transport-protocol/srv6/
├── srv6.rst            # Enable SRv6 transport
└── locator.rst         # SRv6 locator name

Network-services/evpn-vpws/instance/transport-protocol/srv6/
├── srv6.rst            # Enable SRv6 transport
└── locator.rst         # SRv6 locator name
```

**Example:**
```bash
network-services evpn-vpws-fxc FXC-1 {
    instance 1 {
        transport-protocol srv6 {
            locator MAIN_LOC;
        }
    }
}
```

**Note:** VXLAN and SRv6 documentation sourced from `drivenets/cheetah` main repository (v26.1).

### Protocol-Specific

| Category | Files | Description |
|----------|-------|-------------|
| [BFD/](./BFD/) | 9 | Bidirectional Forwarding Detection |
| [LDP/](./LDP/) | 25 | Label Distribution Protocol |
| [MPLS/](./MPLS/) | 2 | Multiprotocol Label Switching |
| [Multicast/](./Multicast/) | 3 | PIM, IGMP, MSDP |
| [Traffic Engineering/](./Traffic%20Engineering/) | 40 | MPLS-TE, PCEP, DiffServ-TE |

---

## 📋 Operational Commands

| Category | Files | Description |
|----------|-------|-------------|
| [Show Commands/](./Show%20Commands/) | 442 | Device status, routing tables, counters |
| [Clear Commands/](./Clear%20Commands/) | - | Statistics and session management |
| [Request Commands/](./Request%20Commands/) | 57 | Operational requests |
| [Run Commands/](./Run%20Commands/) | 30 | Execute operations |
| [Set Commands/](./Set%20Commands/) | 14 | Terminal settings |

---

## 🔧 CLI Usage

| Category | Files | Description |
|----------|-------|-------------|
| [CLI Guidelines/](./CLI%20Guidelines/) | - | Usage, navigation, shortcuts |
| [Transactions/](./Transactions/) | 8 | Commit, rollback, load, save |
| [Accessing the CLI Terminal/](./Accessing%20the%20CLI%20Terminal/) | - | SSH, console access |
| [Main Menu Commands/](./Main%20Menu%20Commands/) | - | Top-level navigation |
| [GI Mode Commands/](./GI%20Mode%20Commands/) | - | Generic Interface mode |
| [Recovery Mode Commands/](./Recovery%20Mode%20Commands/) | 8 | System recovery |
| [Debug log Commands/](./Debug%20log%20Commands/) | - | Debug and logging |

---

## 🔒 Security & Advanced

| Category | Files | Description |
|----------|-------|-------------|
| [nacm/](./nacm/) | 10 | NETCONF Access Control Model |
| [forwarding-options/](./forwarding-options/) | 13 | Forwarding plane options |
| [tracking-policy/](./tracking-policy/) | 11 | Interface/route tracking |
| [High-availability/](./High-availability/) | 9 | HA configuration |

---

## 📊 Quick Reference

### Essential Show Commands
```bash
show config | no-more              # Full configuration
show system | no-more              # System info, Router ID
show interfaces | no-more          # All interfaces
show interfaces brief              # Interface summary
show isis | no-more                # IS-IS status
show ospf | no-more                # OSPF status
show bgp summary | no-more         # BGP neighbors
show ldp summary | no-more         # LDP sessions
show segment-routing | no-more     # SR-MPLS
show evpn-vpws-fxc | no-more       # FXC services
show network-services | no-more    # All services
show access-lists | no-more        # ACL configuration
show multihoming | no-more         # MH status
```

### Configuration Workflow
```bash
configure                          # Enter config mode
set interfaces ge100-0/0/1 admin-state enabled
set network-services evpn-vpws-fxc FXC-1 admin-state enabled
show | compare                     # Review changes
commit check                       # Validate
commit                             # Apply
```

### Network Service Examples

#### EVPN with Router-Interface (IRB)
```
network-services {
    evpn EVPN-1 {
        instance 1 {
            interface ge100-0/0/1.100 { }
            router-interface irb100 { }
            evpn-protocols {
                bgp {
                    route-distinguisher 1.1.1.1:1;
                    export-l2vpn-evpn-route-target 65000:1;
                    import-l2vpn-evpn-route-target 65000:1;
                }
            }
        }
    }
}
```

#### Multihoming with ESI
```
network-services {
    multihoming {
        interface bundle1 {
            esi arbitrary 00:11:22:33:44:55:66:77:88:99;
            redundancy-mode all-active;
            designated-forwarder {
                algorithm mod;
            }
        }
    }
}
```

#### EVPN-VPWS-FXC with Interface
```
network-services {
    evpn-vpws-fxc FXC-1 {
        instance 1 {
            admin-state enabled;
            fxc-mode vlan-unaware;
            interface ge100-0/0/1.100 { }
            transport-protocol mpls { }
            evpn-vpws-fxc-protocols {
                bgp {
                    route-distinguisher 1.1.1.1:1;
                    export-l2vpn-evpn-route-target 65000:100;
                    import-l2vpn-evpn-route-target 65000:100;
                }
            }
        }
    }
}
```

---

## 📈 Documentation Coverage

| Category | RST Files | Status |
|----------|-----------|--------|
| Protocols | 1,306 | ✅ Complete |
| Network-services | 576 | ✅ Complete |
| System | 571 | ✅ Complete |
| Show Commands | 442 | ✅ Complete |
| Services | 213 | ✅ Complete |
| Interfaces | 160 | ✅ Complete |
| QoS | 159 | ✅ Complete |
| Routing-policy | 76 | ✅ Complete |
| Request Commands | 57 | ✅ Complete |
| Policy | 42 | ✅ Complete |
| Traffic Engineering | 40 | ✅ Complete |
| Routing-options | 37 | ✅ Complete |
| Run Commands | 30 | ✅ Complete |
| LDP | 25 | ✅ Complete |
| Access-lists | 22 | ✅ Complete |
| Set Commands | 14 | ✅ Complete |
| forwarding-options | 13 | ✅ Complete |
| tracking-policy | 11 | ✅ Complete |
| nacm | 10 | ✅ Complete |
| BFD | 9 | ✅ Complete |
| High-availability | 9 | ✅ Complete |
| Transactions | 8 | ✅ Complete |
| Recovery Mode Commands | 8 | ✅ Complete |
| debug | 7 | ✅ Complete |
| Community-list | 6 | ✅ Complete |
| Multicast | 3 | ✅ Complete |
| Prefix-list | 3 | ✅ Complete |
| MPLS | 2 | ✅ Complete |
| Segment-routing | 1 | ✅ Complete |

**Total: 4,246 RST files** | All hierarchies complete

---

*Fetched from DriveNets askai-poc repository - December 2024*
*DNOS Version: v26.1*
