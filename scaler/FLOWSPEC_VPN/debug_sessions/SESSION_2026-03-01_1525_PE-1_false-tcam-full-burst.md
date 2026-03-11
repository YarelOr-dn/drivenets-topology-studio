# Debug Session: PE-1 — False TCAM-Full During FlowSpec-VPN Burst Injection
Started: 2026-03-01 15:25:00 UTC | Device: YOR_PE-1_priv_26.1.0.3
Image: 26.1.0.3
Topic: NCP reports "No more space left in TCAM" during SAFI 134 burst injection when TCAM has spare capacity. 400 rules per family stuck as "Not Installed, out of resources". 4112 IPv4 + 38 IPv6 silently dropped by HandleRuleFailedWrite threshold.
Session mode: INVESTIGATE

---

## Phase 0: Pre-Flight Health Check

### [15:16:19] [show] show system npu-resources resource-type flowspec
```
Flowspec usage:

| NCP   | IPv4 Received rules   | IPv4 Rules installed   | IPv4 HW entries used/total   | IPv6 Received rules   | IPv6 Rules installed   | IPv6 HW entries used/total   |
|-------+-----------------------+------------------------+------------------------------+-----------------------+------------------------+------------------------------|
| 0     | 7888                  | 7488                   | 7488/12000                   | 3962                  | 3562                   | 3562/4000                    |
```

### [15:16:21] [show] show bgp summary | include 100.64.6.134
```
  100.64.6.134    4      65200     221249        178    0     0       0 00:02:26                   0
  100.64.6.134    4      65200     221249        178    0     0       0 00:02:26                   0
  100.64.6.134    4      65200     221249        178    0     0       0 00:02:26               12000
  100.64.6.134    4      65200     221249        178    0     0       0 00:02:26  (NoNeg)
  100.64.6.134    4      65200     221249        178    0     0       0 00:02:26                   0
  100.64.6.134    4      65200     221249        178    0     0       0 00:02:26                4000
```

### [15:17:12] [show] show dnos-internal routing rib-manager database flowspec
```
VRF: default

IPv4 Flowspec table (total size: 12000):
-------------------------------

IPv6 Flowspec table (total size: 4000):
-------------------------------
```

### [15:17:19] [show] show flowspec ncp 0 | tail 30
```
	Flow: DstPrefix:=2001:db8:f70::/48,SrcPrefix:=*
		Actions: Traffic-rate: 0 bps
		Status: Not Installed, out of resources
	(... 400 IPv4 + 400 IPv6 rules with this status ...)
```

### [15:18:05] [show] show bgp ipv4 flowspec-vpn summary
```
  Neighbor        V         AS    MsgRcvd    MsgSent  InQ  OutQ  AdjOut  Up/Down   State/PfxAccepted
  2.2.2.2         4    1234567        944      13654    0     0   12000 02:35:13                   0
  100.64.6.134    4      65200     221251        180    0     0       0 00:04:09               12000
```

### [15:18:08] [show] show bgp ipv6 flowspec-vpn summary
```
  Neighbor        V         AS    MsgRcvd    MsgSent  InQ  OutQ  AdjOut  Up/Down   State/PfxAccepted
  2.2.2.2         4    1234567        944      13654    0     0    4000 02:35:16                   0
  100.64.6.134    4      65200     221251        180    0     0       0 00:04:12                4000
```

### [15:20:40] [config] show config network-services vrf instance ZULU
```
network-services
  vrf
    instance ZULU
      interface ge400-0/0/5.2
      interface lo5
      protocols
        bgp 1234567
          route-distinguisher 1.1.1.1:200
          router-id 1.1.1.1
          address-family ipv4-flowspec
            export-vpn route-target 1234567:301
            import-vpn route-target 300:300,1234567:301
          !
          address-family ipv6-flowspec
            export-vpn route-target 1234567:401
            import-vpn route-target 1234567:401
          !
```

### [15:21:31] [show] show file traces routing_engine/fibmgrd_traces | include FLOWSPEC | tail 30
```
2026-03-01T15:15:21.674787 +02:00 [DEBUG] [MessageParser.cpp:280:HandleMessageFromZebra] Got protobuf: FLOWSPEC_RULE_ADD flowspec_add { key { afi: IPV6 nlri: "\0010\000 \001\r\270\017\226" bgp_as: 1234567 vrf_id: 4 } action { type: TRAFFIC_RATE traffic_rate: 0 } }
(... continued IPv6 rules through 2001:db8:f9f ...)
2026-03-01T15:15:21.721864 +02:00 [DEBUG] [FpmNcp.cpp:5574:operator()] Sending to FIB 0: FLOWSPEC [iid=157355]
```

### [15:22:35] [show] show file ncp 0 traces datapath/wb_agent.flowspec | tail 30
```
2026-03-01T15:15:21.722720 +02:00 [WARNING] [FlowspecRuleData.cpp:319 WriteToTcam()] Flowspec: No more space left in TCAM for new rules
2026-03-01T15:15:21.722736 +02:00 [ERROR] [FlowspecTable.cpp:121 InternalAddRule()] Flowspec: Failed to add rule to TCAM
2026-03-01T15:15:21.722752 +02:00 [DEBUG] [FlowspecTable.cpp:521 SendUnsupportedSystemEvent()] Flowspec: Sending flowspec unsupported rule system event, reason lack of resources, address family IPv6, rule DstPrefix:=2001:db8:f9f::/48,SrcPrefix:=*
2026-03-01T15:15:21.722760 +02:00 [DEBUG] [FlowspecTcamManager.cpp:146 RollbackRule()] Flowspec: Rollback rule 01300020010db80f9f in BCM
2026-03-01T15:15:21.722778 +02:00 [ERROR] [FlowspecTable.cpp:358 HandleRuleFailedWrite()] Flowspec: Too many unwritten rules, not adding to table
2026-03-01T15:15:21.722803 +02:00 [ERROR] [FlowspecManager.cpp:215 AddRuleInternal()] Flowspec: Unable to add IPv6 flowspec rule with length=9
```

## Phase 3: NCP Trace Analysis

Trace buffer severely rotated by 16K rule burst. Only the LAST failure event per keyword survives:
- 1x WriteToTcam WARNING
- 1x HandleRuleFailedWrite ERROR
- 1x AddRuleInternal ERROR
- 1x ReserveQualifiers DEBUG
- 1x Rollback DEBUG

Earlier IPv4 failures and first IPv6 failures are lost. No reproduction needed — code analysis reveals the mechanism.

## Phase 5: Code Analysis

### Source Files Analyzed
- `cheetah_26_1/src/wbox/src/flowspec/FlowspecTcamManager.cpp`
- `cheetah_26_1/src/wbox/src/flowspec/FlowspecRuleData.cpp`
- `cheetah_26_1/src/wbox/src/flowspec/FlowspecTable.cpp`
- `cheetah_26_1/src/wbox/src/flowspec/FlowspecTable.hpp`
- `cheetah_26_1/src/wbox/src/flowspec/FlowspecManager.cpp`

### Root Cause: `m_reserved` Leak in FlowspecTcamManager

`ReserveQualifiers()` at line 307 increments `m_reserved` on success:
```
m_reserved += to_reserve;
```

`m_reserved` is only decremented on SUCCESSFUL TCAM write (line 288-293):
```
m_numberOfEntries += writeRes.written - writeRes.deleted;
m_reserved -= flowspecRuleData.GetNumberOfTcamRules();
```

`RollbackRule()` (called on write failure) does NOT decrement `m_reserved`.
`DeleteRuleInternal()` does NOT release `m_reserved` for unwritten rules.

**Effect:** During bulk injection, in-flight reservations + any failed-write phantom reservations inflate `m_reserved`. The capacity check `(m_numberOfEntries + m_reserved + to_reserve) <= m_totalCapacity` then fails even when actual TCAM usage is well below capacity.

### Constants
- `FLOWSPEC_MAX_UNWRITTEN_IN_TABLE = 400` (hardcoded, FlowspecTable.hpp line 24)
- `EXTERNAL_FLOWSPEC_IPV4_MINIMUM_CAPACITY = 12000` (bcm_wrap_pmf.h line 30)
- `EXTERNAL_FLOWSPEC_IPV6_MINIMUM_CAPACITY = 4000` (bcm_wrap_pmf.h line 31)
- IPv4 and IPv6 have SEPARATE TCAM managers and PMF groups

### No Recovery
`ReshuffleRules()` skips rules with `!IsInstalled()` (line 386-389). Failed rules are never retried.

---

## Session Conclusion
Ended: 2026-03-01 15:35:00 UTC
Verdict: BUG FOUND
Bug file: ~/SCALER/FLOWSPEC_VPN/bug_evidence/BUG_FLOWSPEC_TCAM_RESERVED_LEAK_BURST.md

Root cause: `FlowspecTcamManager::RollbackRule()` does not release `m_reserved` entries that were incremented by `ReserveQualifiers()`. During bulk injection, phantom reservations inflate the capacity check, causing false "No more space left in TCAM" errors. Combined with the hardcoded 400 unwritten threshold and no retry mechanism, this causes permanent rule loss of up to 34% of injected rules.
