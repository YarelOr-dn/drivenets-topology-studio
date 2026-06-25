# TEST_mac_mob_irb_si_reject_G2

**Device:** PE-1
**Mode:** execute
**Time:** 2026-04-19T15:47:12+00:00
**Overall:** FAIL
**Elapsed:** 18.0s

## Test Verdict: TEST_mac_mob_irb_si_reject_G2 on PE-1
**Overall: FAIL** | Elapsed: 18.0s

| Scenario | Overall | Layers | Convergence | Debug Hint |
|----------|---------|--------|-------------|------------|
| SC01_add_irb_to_si_instance | FAIL | trigger=FAIL, bgp_session=WARN, traces=SKIP, timing=PASS | 11.78s | Infrastructure failure: MAC never appeared in mac-table. Check Spirent BGP peers (EVPN/VPLS), DNAAS path, and L2 traffic. |

### SC01_add_irb_to_si_instance: router-interface (IRB) on SI-enabled instance -> commit check must REJECT

| Layer | Status | Detail | Time |
|-------|--------|--------|------|
| trigger | FAIL | commit check did NOT reject as expected. failed=False regex_hit=False output[:300]='NOTICE: commit action is not applicable. no configuration changes were made' | 0.00s |
| bgp_session | WARN | 0/3 ESTABLISHED (not required for this test) | 0.25s |
| traces | SKIP | Skipped trace check (infra failure detected) | 0.00s |
| timing | PASS | 11.78s <= 90.0s threshold | 0.00s |

**Debug:** Infrastructure failure: MAC never appeared in mac-table. Check Spirent BGP peers (EVPN/VPLS), DNAAS path, and L2 traffic.


## Observability Summary

- **Commands executed:** 13
- **Anomalies detected:** 0
- **Scenarios:** 1
- **Commands per phase:**
  - snapshot: 1
  - mac_cleanup: 2
  - trigger: 7
  - verify: 3
  - auto_diagnose: 0