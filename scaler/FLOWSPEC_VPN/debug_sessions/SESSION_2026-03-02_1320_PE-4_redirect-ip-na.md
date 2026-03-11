# Debug Session: PE-4 -- FlowSpec redirect-ip NH shows N/A in NCP
Started: 2026-03-02 13:19:00 UTC | Device: YOR_CL_PE-4
Image: (TBD)
Topic: FlowSpec redirect-ip rule installed in NCP but Redirect-ip-nh: N/A despite route being reachable via MPLS/VPN
Session mode: INVESTIGATE

---

## Phase 0: Pre-Flight

### [13:19:54] [show] show file traces routing_engine/fibmgrd_traces | include is_flowspec
```
2026-03-02T12:11:03.455445 +02:00 [DEBUG] [MessageParser.cpp:280:HandleMessageFromZebra] nexthop { type: ADD_NEXTHOP add_nexthop { oid: 61 is_support_indirection: true address { v4 { value: 167772390 } } is_flowspec: true } }
2026-03-02T12:11:08.456187 +02:00 [DEBUG] same broken protobuf (oid 61, no nexthops, no vrf_id)
2026-03-02T12:11:13.457048 +02:00 [DEBUG] same broken protobuf
2026-03-02T12:11:18.451105 +02:00 [DEBUG] same broken protobuf
2026-03-02T13:17:01.125031 +02:00 [DEBUG] nexthop { type: ADD_NEXTHOP add_nexthop { oid: 62 is_support_indirection: true nexthops { if_id { index: 14377 cheetah_index: 13353 } if_name: "ge100-18/0/0.14" address { v4 { value: 235802113 } } vrf_id: 0 mpls_labels: 1040385 ecmp_weight: 0 protocol: LDP } address { v4 { value: 167772390 } } is_flowspec: true protocol: BGP } }
```

### [13:20:15] [show] show file ncp 18 traces datapath/wb_agent.flowspec | include redirect
```
2026-03-02T13:17:01.126461 +02:00 [DEBUG] [FlowspecManager.cpp:161 AddRuleInternal()] Flowspec: actions - type: redirect-ip-nh(4)
```

