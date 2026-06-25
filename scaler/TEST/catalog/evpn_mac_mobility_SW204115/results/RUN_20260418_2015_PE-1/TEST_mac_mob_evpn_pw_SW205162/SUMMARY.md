# TEST_mac_mob_evpn_pw_SW205162

**Device:** PE-1
**Mode:** execute
**Time:** 2026-04-18T20:21:05+00:00
**Overall:** FAIL
**Elapsed:** 350.3s

## Test Verdict: TEST_mac_mob_evpn_pw_SW205162 on PE-1
**Overall: FAIL** | Elapsed: 350.3s

| Scenario | Overall | Layers | Convergence | Debug Hint |
|----------|---------|--------|-------------|------------|
| SC01_evpn_to_pw | WARN | trigger=PASS, mac_flags=PASS, forwarding=PASS, mobility_counter=WARN, ghost_macs=PASS, cross_layer=PASS, bgp_session=PASS, traces=SKIP, timing=PASS | 9.73s | -- |
| SC02_pw_to_evpn | PASS | trigger=PASS, mac_flags=PASS, forwarding=PASS, ghost_macs=PASS, cross_layer=PASS, bgp_session=PASS, traces=SKIP, timing=PASS | 17.85s | -- |
| SC03_sticky_evpn_to_pw | FAIL | trigger=PASS, mac_flags=PASS, forwarding=PASS, ghost_macs=PASS, cross_layer=PASS, bgp_session=FAIL, traces=PASS, timing=WARN | 110.60s | Layer 'bgp_session' failed. No trace hits near 20:18. Trace buffer may have rotated or timestamp mismatch. | Action: Reproduce the failure for fresh traces. Check trace buffer size: show file traces routing_engine/bgpd_traces | tail 5 |
| SC04_pw_to_sticky_evpn | FAIL | trigger=FAIL | -- | -- |

### SC01_evpn_to_pw: Non-sticky: remote EVPN -> PW; no RT change; not counted

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| trigger | PASS | EVPN->PW move via RT-2 inject + PW VLAN 1010 | 0.00s |
| mac_flags | PASS | Flags ['L', 'K', 'M', 'P'] | 0.25s |
| forwarding | PASS | NCP state: forwarding (expected forwarding) | 0.20s |
| mobility_counter | WARN | Mobility counter 1 -> 1 (delta 0) | 0.25s |
| ghost_macs | PASS | No stale/ghost MACs | 0.25s |
| cross_layer | PASS | Cross-layer check PASS: 6 layers consistent for 00:de:ad:ff:ff:01 | 0.00s |
| bgp_session | PASS | 1/3 ESTABLISHED | 0.25s |
| traces | SKIP | Skipped trace check (infra failure detected) | 0.00s |
| timing | PASS | 9.73s <= 90.0s threshold | 0.00s |

### SC02_pw_to_evpn: PW -> EVPN; accept; static entry

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| trigger | PASS | PW->EVPN move via PW VLAN 1010 + RT-2 inject | 0.00s |
| mac_flags | PASS | Flags ['L', 'K', 'M', 'P'] | 0.25s |
| forwarding | PASS | NCP state: forwarding (expected forwarding) | 0.15s |
| ghost_macs | PASS | No stale/ghost MACs | 0.25s |
| cross_layer | PASS | Cross-layer check PASS: 6 layers consistent for 00:de:ad:ff:ff:01 | 0.00s |
| bgp_session | PASS | 1/3 ESTABLISHED | 0.25s |
| traces | SKIP | Skipped trace check (infra failure detected) | 0.00s |
| timing | PASS | 17.85s <= 90.0s threshold | 0.00s |

### SC03_sticky_evpn_to_pw: Sticky EVPN RT-2 -> PW; IGNORE move (blackholing risk)

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| trigger | PASS | sticky EVPN->PW move via RT-2 inject + PW VLAN 1010 | 0.00s |
| mac_flags | PASS | Flags ['L', 'R', 'K', 'M'] | 0.25s |
| forwarding | PASS | NCP state: forwarding (expected forwarding) | 0.20s |
| ghost_macs | PASS | No stale/ghost MACs | 0.25s |
| cross_layer | PASS | Cross-layer check PASS: 6 layers consistent for 00:de:ad:ff:ff:01 | 0.00s |
| bgp_session | FAIL | 0/3 ESTABLISHED | 0.25s |
| traces | PASS | No ERROR lines near 20:18 | 1.86s |
| timing | WARN | 110.60s > 90.0s (within 2x) | 0.00s |

**Debug:** Layer 'bgp_session' failed. No trace hits near 20:18. Trace buffer may have rotated or timestamp mismatch. | Action: Reproduce the failure for fresh traces. Check trace buffer size: show file traces routing_engine/bgpd_traces | tail 5

### SC04_pw_to_sticky_evpn: PW -> Sticky EVPN; accept; datapath static sticky

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| trigger | FAIL | EVPN BGP peer 19.19.19.2 not ESTABLISHED -- cannot inject RT-2. Run: spirent_tool.py protocol-start --device-name EVPN_RT2_Peer | 0.00s |


## Observability Summary

- **Commands executed:** 65
- **Anomalies detected:** 0
- **Scenarios:** 4
- **Commands per phase:**
  - snapshot: 1
  - mac_cleanup: 6
  - trigger: 6
  - verify: 37
  - auto_diagnose: 6