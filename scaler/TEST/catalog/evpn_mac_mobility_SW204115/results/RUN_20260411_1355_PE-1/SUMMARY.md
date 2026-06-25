# AC_AC Test Results -- RUN 2026-04-11 13:55 on PE-1

**Test:** TEST_mac_mob_ac_ac_SW205161
**Device:** YOR_PE-1 (100.64.4.200)
**EVPN Instance:** HA_TEST_ELAN (EVI 1)
**Date:** 2026-04-11
**Overall:** ALL 5 SCENARIOS PASSED

## ACs Used

| AC | Interface | Outer VLAN | Inner VLAN | Role |
|----|-----------|------------|------------|------|
| AC1 | ge400-0/0/5.1000 | 214 | 1000 | Primary (sticky in SC04) |
| AC2 | ge400-0/0/5.1001 | 214 | 1001 | Secondary |
| AC3 | ge400-0/0/5.1002 | 214 | 1002 | Tertiary (created for SC05) |

## Loop Prevention Config

- LLP enabled, threshold=5, window=30s, action=ac-shutdown
- Remote LP enabled, action=suppress, window=180s

## Scenario Results

| Scenario | Description | Result | Details |
|----------|-------------|--------|---------|
| SC01 | Non-sticky AC1->AC2 move | PASS | MAC moved .1000->.1001, forwarding updated, flags L, 0 suppressed |
| SC02 | Rapid AC<->AC flap (6 moves) | PASS | LLP triggered (threshold=5), .1001 shutdown, restore timer 300s |
| SC03 | Local loop counter check | PASS | Counter incremented (1/5), simultaneous MAC presence detected |
| SC04 | Sticky AC enforcement | PASS | MAC stayed on .1000 (Lsi flags), move to .1002 rejected |
| SC05 | A->B->A->B->C sequencing | PASS | 5 moves all correct: .1000->.1001->.1000->.1001->.1002 |

## Timing

- Session reconnect: ~60s
- Port reserve: ~50s
- Each MAC learn/verify cycle: ~7s (create stream + start + 4s wait + stop + verify)
- SC02 rapid flap (6 moves): ~43s
- SC05 full sequence (5 moves): ~68s
- Total test time (including infra fixes): ~25 min

## Issues Encountered

1. **PW_TEST_ELAN blocking-all:** AC ge400-0/0/5.1011 in PW_TEST_ELAN was permanently
   blocking-all (SI-related). Switched to HA_TEST_ELAN which had all ACs forwarding-all.
2. **.2000/.2001 outer-tag 210:** Sub-interfaces used outer-tag 210 (no DNAAS BD), not 214.
   Fixed by using .1000/.1001/.1002 (all outer-tag 214).
3. **LLP ac-shutdown recovery:** After SC02/SC03, AC2 (.1001) was shut down by LLP.
   Required waiting for 300s restore timer. Admin-state bounce does NOT clear LLP shutdown.
4. **Spirent stream TX=0 after many remove/create cycles:** STC generator broke after ~28
   stream creates/removes in one session. Fixed by force-reconnecting the session.

## Learnings for Future Runs

- Use HA_TEST_ELAN (not PW_TEST_ELAN) for ac_ac tests -- no SI blocking issues
- All ACs must share the same outer-tag (214 for DNAAS BD path)
- LLP ac-shutdown persists through admin-state bounce -- must wait for restore timer
- Force-reconnect Spirent session if TX drops to 0 after many stream operations
- SC04 sticky: use `sticky-interface enabled/disabled`, NOT `no sticky-interface`
