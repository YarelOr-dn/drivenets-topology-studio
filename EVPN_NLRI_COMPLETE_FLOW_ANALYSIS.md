# EVPN NLRI Complete Flow: From BGP Packet to FIB Programming

## Overview

This document traces the complete flow of an EVPN NLRI (Network Layer Reachability Information) from when it's received as a BGP UPDATE packet through all system components, containers, and daemons until it's programmed into the Forwarding Information Base (FIB).

---

## System Architecture Overview

### Containers/Daemons Involved

1. **bgpd** (BGP Daemon) - Control Plane Container
2. **zebra** (RIB Manager) - Control Plane Container  
3. **fibmgrd** (FIB Manager Daemon) - Control Plane Container
4. **Element Manager (EM)** - Management Plane Container
5. **WBox** (White Box) - Data Plane Container
6. **FPM Communicator** - Interface between Control and Data Plane

---

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. BGP PACKET RECEPTION (bgpd)                                  │
│    - TCP socket receives BGP UPDATE packet                      │
│    - bgp_read_packet() → bgp_update_receive()                   │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. BGP UPDATE PROCESSING (bgpd)                                 │
│    - Parse NLRI and attributes                                  │
│    - Validate route                                              │
│    - Apply import policies                                      │
│    - Next-hop resolution check                                  │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. NEXT-HOP RESOLUTION (bgpd + zebra)                          │
│    - bgp_nexthop_reachability_check()                          │
│    - bgp_find_or_add_nexthop()                                  │
│    - Query RIB for next-hop route                               │
│    - Check MPLS reachability (for EVPN)                        │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. SERVICE IMPORT (bgpd)                                       │
│    - bgp_service_import_handler_evpn()                         │
│    - Check RT (Route Target) import policy                     │
│    - Import route to service instance (EVI)                    │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. EVPN SERVICE MANAGER (zebra/evpn)                            │
│    - EvpnServiceManager receives route notification            │
│    - EvpnServiceBuilder creates/updates service               │
│    - EvpnEthTagService processes route                         │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. FPM INSTALLATION (zebra)                                     │
│    - EvpnFpmInstaller.install()                                 │
│    - Create zebra_fpm_evpn_object                               │
│    - Send to FPM via protobuf                                   │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. FPM COMMUNICATOR (libdatapath)                               │
│    - Receive protobuf message                                   │
│    - Parse EVPN route information                               │
│    - Forward to Element Manager                                 │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. ELEMENT MANAGER (EM)                                         │
│    - Process EVPN route update                                  │
│    - Validate and transform data                                 │
│    - Send to WBox (White Box)                                   │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ 9. WBOX / DATAPATH (Data Plane)                                 │
│    - Receive route programming request                           │
│    - Program hardware FIB                                       │
│    - Install MPLS labels                                        │
│    - Update forwarding tables                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Detailed Component Flow

### Phase 1: BGP Packet Reception (bgpd)

**File**: `services/control/quagga/bgpd/bgp_packet.c`

**Function Flow**:
```2794:2894:services/control/quagga/bgpd/bgp_packet.c
bgp_update_receive (struct peer *peer, bgp_size_t size)
{
  // Parse BGP UPDATE packet
  // Extract NLRI and attributes
  // Validate packet format
  // Process withdraw routes
  // Process path attributes
  // Call bgp_update_main() for route processing
}
```

**Key Steps**:
1. **Packet Reception**: TCP socket receives BGP UPDATE packet
2. **Parsing**: Extract NLRI, path attributes, withdraw routes
3. **Validation**: Check packet format, attribute validity
4. **Route Processing**: Call `bgp_update_main()` to process routes

**Container**: `bgpd` daemon in control plane container

---

### Phase 2: BGP Route Processing (bgpd)

**File**: `services/control/quagga/bgpd/bgp_route.c`

**Function Flow**:
```
bgp_update_main()
  → bgp_update_receive()
    → bgp_attr_parse()          // Parse path attributes
    → bgp_nlri_parse()          // Parse NLRI
    → bgp_update()              // Process route update
      → bgp_process()           // Main route processing
        → bgp_path_info_new()   // Create route info
        → bgp_nexthop_reachability_check()  // Check next-hop
```

**Key Steps**:
1. **Attribute Parsing**: Parse BGP path attributes (AS_PATH, Communities, RT, etc.)
2. **NLRI Parsing**: Parse EVPN NLRI (Type 1, ESI, Eth-Tag, etc.)
3. **Route Validation**: Validate route format and attributes
4. **Import Policy**: Apply import route-maps and filters
5. **Next-Hop Resolution**: Check if next-hop is reachable

**Container**: `bgpd` daemon

---

### Phase 3: Next-Hop Resolution (bgpd + zebra)

**File**: `services/control/quagga/bgpd/bgp_route.c`  
**File**: `services/control/quagga/bgpd/bgp_nht.c`

**Function Flow**:
```8847:8887:services/control/quagga/bgpd/bgp_route.c
void bgp_nexthop_reachability_check(struct peer *peer,
                                     afi_t orig_afi,
                                     safi_t orig_safi,
                                     struct bgp_info *ri,
                                     struct attr *intern_attr,
                                     struct bgp *bgp_of_ri,
                                     bgp_rmap_set_flags *flags,
                                     const char *nh_vrf_name)
{
    // Check if next-hop is directly connected
    // Call bgp_find_or_add_nexthop() to resolve next-hop
    // Set BGP_INFO_VALID flag if next-hop is reachable
}
```

**Next-Hop Resolution Logic**:
```1015:1020:services/control/quagga/bgpd/bgp_nht.c
if (BGP_AF_OPS(bgp_of_ri, afi_dst_safi).bgp_info_is_mpls_reachability_needed(ri))
{
    /* MPLS route is valid if its nexthop is either MPLS reachable, or connected*/
    mpls_valid = (CHECK_FLAG(bnc->flags, BGP_NEXTHOP_MPLS_REACHABLE)
                | CHECK_FLAG(bnc->flags, BGP_NEXTHOP_CONNECTED));
}
```

**For EVPN Routes**:
```822:850:services/control/quagga/bgpd/bgp_mpls.c
bool bgp_info_is_mpls_reachability_needed_evpn(const struct bgp_info *info)
{
    // EVPN routes require MPLS reachability (unless VXLAN/SRv6)
    if (bgp_info_has_remote_label(info))
    {
        return true;  // MPLS label present → requires MPLS reachability
    }
    return true;  // Default: MPLS reachability required
}
```

**Key Steps**:
1. **Next-Hop Lookup**: Query RIB (via zebra) for route to next-hop
2. **MPLS Check**: For EVPN, verify next-hop has MPLS label (LDP/SR)
3. **Validation**: Route is valid only if:
   - Next-hop is MPLS reachable (has label), OR
   - Next-hop is directly connected
4. **Flag Setting**: Set `BGP_INFO_VALID` if reachable, unset if not

**Containers**: 
- `bgpd` (BGP daemon) - initiates check
- `zebra` (RIB manager) - provides RIB lookup

**Communication**: Unix socket IPC between bgpd and zebra

---

### Phase 4: Service Import (bgpd)

**File**: `services/control/quagga/bgpd/bgp_service.c`

**Function Flow**:
```1451:1454:services/control/quagga/bgpd/bgp_service.c
void bgp_service_import_handler_evpn(struct bgp *bgp, afi_t afi, safi_t safi, struct bgp_node *rn)
{
    bgp_service_import_handler_common(bgp, afi, safi, SAFI_EVI, rn);
}
```

**Key Steps**:
1. **RT Check**: Verify Route Target (RT) matches import policy
2. **Service Instance**: Identify target EVI (Ethernet VPN Instance)
3. **Route Import**: Import route from global BGP table to service instance
4. **Notification**: Notify EVPN service manager of new route

**Container**: `bgpd` daemon

**Trigger**: Route becomes valid and matches import RT

---

### Phase 5: EVPN Service Manager (zebra/evpn)

**File**: `services/control/quagga/zebra/evpn/EvpnServiceManager.cpp`

**Function Flow**:
```
EvpnServiceManager::OnBgpRouteUpdate()
  → EvpnServiceBuilder::build()
    → EvpnEthTagService::processRoute()
      → EvpnServiceVpws::update()
        → EvpnFpmInstaller::install()
```

**Key Components**:

1. **EvpnServiceManager**: Main service manager
   - Receives BGP route notifications
   - Manages service lifecycle
   - Coordinates service components

2. **EvpnServiceBuilder**: Service construction
   - Creates/updates EVPN service objects
   - Handles service configuration

3. **EvpnEthTagService**: Route processing
   - Processes EVPN routes by Eth-Tag
   - Manages attachment circuits (AC)
   - Handles pseudowire (PW) state

4. **EvpnServiceVpws**: VPWS-specific logic
   - VPWS service implementation
   - FXC (Flexible Cross-Connect) support
   - DF (Designated Forwarder) election

**Key Steps**:
1. **Route Notification**: Receive route update from BGP
2. **Service Lookup**: Find or create service instance
3. **Route Processing**: Process route based on type (AD, MAC/IP, etc.)
4. **State Update**: Update service operational state
5. **FPM Notification**: Trigger FPM installation

**Container**: `zebra` daemon (RIB manager)

**Communication**: 
- BGP → Zebra: Via `bgp_service_import_handler_evpn()`
- Internal: C++ object method calls

---

### Phase 6: FPM Installation (zebra)

**File**: `services/control/quagga/zebra/evpn/EvpnFpmInstaller.cpp`  
**File**: `services/control/quagga/zebra/zebra_fpm_protobuf.c`

**Function Flow**:
```
EvpnFpmInstaller::install()
  → sendToFpm()
    → zebra_fpm_evpn_object_create()
    → zfpm_evpn_route_add()
      → zebra_fpm_protobuf_encode_evpn()
        → create_cheetah_message()
          → fpm__message__pack()
            → Send via FPM socket
```

**Protobuf Encoding**:
```73:94:services/control/quagga/zebra/zebra_fpm_protobuf.c
static Cheetah__CheetahMessage *create_cheetah_message(qpb_allocator_t *allocator)
{
    Fpm__Message  *msg;
    Cheetah__CheetahMessage *encap;

    msg = QPB_ALLOC(allocator, typeof(*msg));
    encap  = QPB_ALLOC(allocator, typeof(*encap));
    
    cheetah__cheetah_message__init(encap);
    fpm__message__init(msg);

    encap->fpm_message = msg;
    encap->message_case = CHEETAH__CHEETAH_MESSAGE__MESSAGE_FPM_MESSAGE;
    msg->has_type = 1;

    return encap;
}
```

**Key Steps**:
1. **Object Creation**: Create `zebra_fpm_evpn_object` with route information
2. **Protobuf Encoding**: Encode route data into protobuf format
3. **Message Packaging**: Package into Cheetah message format
4. **Socket Send**: Send to FPM socket (Unix socket or TCP)

**Container**: `zebra` daemon

**Communication**: Unix socket or TCP to FPM communicator

---

### Phase 7: FPM Communicator (libdatapath)

**File**: `src/libdatapath/fpm_communicator/fpm_communicator.c`  
**File**: `src/libdatapath/fpm_communicator/fpm_evpn_vpws_service_handler.cpp`

**Function Flow**:
```
fpm_communicator_receive()
  → fpm_message_parse()
    → fpm_evpn_vpws_service_handler()
      → Process EVPN route
        → Forward to Element Manager
```

**Key Steps**:
1. **Message Reception**: Receive protobuf message from zebra
2. **Parsing**: Parse protobuf message
3. **Route Processing**: Extract EVPN route information
4. **Validation**: Validate route data
5. **Forwarding**: Forward to Element Manager

**Container**: Part of `wbox` or separate process in data plane container

**Communication**: 
- From: Unix socket/TCP from zebra
- To: Element Manager via internal messaging

---

### Phase 8: Element Manager (EM)

**File**: `src/element_manager/`

**Function Flow**:
```
EM receives FPM message
  → Process EVPN route update
    → Validate route data
      → Transform to WBox format
        → Send to WBox
```

**Key Steps**:
1. **Message Reception**: Receive route update from FPM communicator
2. **Validation**: Validate route data and configuration
3. **Transformation**: Transform to WBox-specific format
4. **Routing**: Route to appropriate WBox component
5. **Forwarding**: Send to WBox for FIB programming

**Container**: `element_manager` daemon in management plane

**Communication**: Internal messaging to WBox

---

### Phase 9: WBox / Datapath (Data Plane)

**File**: `src/wbox/`

**Function Flow**:
```
WBox receives route programming request
  → Validate route
    → Program hardware FIB
      → Install MPLS labels
        → Update forwarding tables
          → Acknowledge completion
```

**Key Steps**:
1. **Route Reception**: Receive route programming request
2. **Hardware Programming**: Program route into hardware FIB
3. **Label Installation**: Install MPLS labels for EVPN
4. **Table Update**: Update forwarding tables (MAC, MPLS, etc.)
5. **Acknowledgment**: Send acknowledgment back to control plane

**Container**: `wbox` daemon in data plane container

**Hardware**: Direct interface to NPU (Network Processing Unit)

---

## Inter-Component Communication

### Communication Mechanisms

1. **Unix Sockets**: 
   - bgpd ↔ zebra (zserv protocol)
   - zebra ↔ FPM communicator

2. **TCP Sockets**:
   - BGP peer connections
   - FPM connections (optional)

3. **Protocol Buffers**:
   - zebra → FPM communicator
   - FPM communicator → Element Manager

4. **Internal Messaging**:
   - Element Manager ↔ WBox
   - Inter-process communication

5. **Shared Memory**:
   - Fast path data sharing
   - Statistics and counters

---

## Data Structures Flow

### 1. BGP Route Info (`struct bgp_info`)
- **Location**: `bgpd`
- **Contains**: Route attributes, next-hop, labels, communities
- **Lifetime**: Until route is withdrawn or invalidated

### 2. EVPN Service Object (`EvpnService`)
- **Location**: `zebra/evpn`
- **Contains**: Service configuration, AC state, PW state
- **Lifetime**: Service lifetime

### 3. FPM EVPN Object (`zebra_fpm_evpn_object`)
- **Location**: `zebra`
- **Contains**: Route information for FIB programming
- **Lifetime**: Until route is programmed

### 4. Protobuf Message (`Fpm__Message`)
- **Location**: `zebra` → `FPM communicator`
- **Contains**: Serialized route data
- **Lifetime**: Message transmission

### 5. Hardware FIB Entry
- **Location**: NPU hardware
- **Contains**: Forwarding table entry
- **Lifetime**: Until route is removed

---

## Error Handling and Failure Points

### Failure Point 1: Next-Hop Unreachable
- **Location**: Phase 3 (Next-Hop Resolution)
- **Symptom**: Route marked as `(inaccessible)`
- **Result**: Route not imported to service, not installed in FIB

### Failure Point 2: RT Import Mismatch
- **Location**: Phase 4 (Service Import)
- **Symptom**: Route not imported to service instance
- **Result**: Route in global table but not in service

### Failure Point 3: Service Not Configured
- **Location**: Phase 5 (EVPN Service Manager)
- **Symptom**: No service instance found
- **Result**: Route not processed by service manager

### Failure Point 4: FPM Communication Failure
- **Location**: Phase 6-7 (FPM Installation/Communication)
- **Symptom**: Route not sent to data plane
- **Result**: Route in control plane but not in hardware FIB

### Failure Point 5: Hardware Programming Failure
- **Location**: Phase 9 (WBox/Datapath)
- **Symptom**: Route not programmed in hardware
- **Result**: Route in software but not forwarding

---

## Debugging and Tracing

### Trace Files

| Component | Trace File | Location |
|-----------|-----------|----------|
| bgpd | `bgpd_traces` | `/var/log/` |
| zebra | `rib-manager_traces` | `/var/log/` |
| FPM | `fpm_traces` | `/var/log/` |
| WBox | `wbox_traces` | `/var/log/` |

### Key Debug Commands

```bash
# BGP route debugging
show bgp l2vpn evpn detail
show bgp l2vpn evpn rd <rd> nlri <nlri> detail

# Next-hop debugging
show bgp nexthop
show bgp nexthop <ip> detail

# EVPN service debugging
show evpn-vpws-fxc instance <name> detail
show evpn service <name> detail

# FIB debugging
show route forwarding-table mpls in-label <label>
show route forwarding-table evpn
```

---

## Performance Considerations

### Optimization Points

1. **Batch Processing**: Multiple routes processed together
2. **Async Processing**: Non-blocking I/O for socket communication
3. **Caching**: Next-hop resolution cached in BGP NHT
4. **Protobuf**: Efficient binary serialization
5. **Hardware Offload**: Routes programmed directly to hardware

### Bottlenecks

1. **Next-Hop Resolution**: RIB lookup can be slow
2. **Service Processing**: Complex service logic
3. **FPM Communication**: Socket I/O overhead
4. **Hardware Programming**: NPU programming latency

---

## Summary

The complete flow of an EVPN NLRI involves:

1. **9 Major Phases** across multiple containers/daemons
2. **5 Communication Mechanisms** (Unix sockets, TCP, protobuf, messaging, shared memory)
3. **5 Data Structure Transformations** (BGP route → Service → FPM → Protobuf → Hardware)
4. **5 Potential Failure Points** requiring monitoring

The flow ensures:
- Route validation at each stage
- Proper next-hop resolution
- Service-aware processing
- Efficient data plane programming
- Hardware FIB synchronization

---

*Based on DriveNets cheetah_25_4 codebase analysis*  
*Date: December 10, 2025*






