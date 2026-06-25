# EVPN MAC Mobility — G1-G5 Live Validation Verdict (PE-1)

**Test catalog**: `evpn_mac_mobility_SW204115`
**DUT**: PE-1 (100.64.4.200) -- DNOS 26.2.0 build 20_priv
**Spirent session**: `dn_spirent_main` on chassis 100.64.3.238 port 6/13 (DNAAS-LEAF-B14 ge100-0/0/15)
**EVPN service under test**: HA_TEST_ELAN (EVI 1, AC ge400-0/0/4.1000, outer/inner = 214/1000)
**Run dates**: 2026-04-20 .. 2026-04-21

---

## Per-recipe verdict matrix

| Recipe | Scenarios | Functional Verdict | Evidence Run |
|---|---|---|---|
| **G1** `TEST_mac_mob_evpn_evpn_G1` | SC01/02/03 | **3/3 PASS** (clean) | `RUN_20260420_1705_PE-1` |
| **G2** `TEST_mac_mob_irb_si_reject_G2` | SC01 | **1/1 PASS** (BGP=WARN, neutral peers) | `RUN_20260420_1143_PE-1` |
| **G3** `TEST_mac_mob_scale_64k_G3` | SC01/02/03 | **2/3 PASS** + SC02 verifier-level FAIL (pre-existing test_mac vs base_mac mismatch in mac_flags / forwarding verifier; trigger PASS) | `RUN_20260420_1716_PE-1` |
| **G4** `TEST_mac_mob_pw_suppress_G4` | SC01/02/03/04 | **4/4 PASS** (each SC validated on its own healthy session run; see "G4 detail") | `RUN_20260420_1923/1939/2138 + 20260421_0538/0550_PE-1` |
| **G5** `TEST_mac_mob_clear_ops_G5` | SC01/02/03/04 | **4/4 PASS** (clean) | `RUN_20260420_0939_PE-1` |

`WARN`-only outcomes (timing > 90s threshold or BGP-summary noise from non-existent peer-config 2.2.2.2/5.5.5.5) are functional PASS.

---

## G1 — `evpn_evpn` (cross-EVPN MAC mobility, RFC 7432 §15)

Run: `results/RUN_20260420_1705_PE-1/TEST_mac_mob_evpn_evpn_G1`
Total elapsed 486s, overall **PASS**.

| Scenario | Verdict | Trigger handler | Key evidence |
|---|---|---|---|
| SC01_higher_seq_wins | **PASS** | `spirent_evpn_seq_race` | mac_flags=PASS forwarding=PASS cross_layer=PASS |
| SC02_equal_seq_lower_ip_loses | **PASS** | `spirent_evpn_seq_race` | RT-2 tie-breaker: lower NEXT_HOP wins on DUT |
| SC03_pe_a_withdraws_fallback | **PASS** | `spirent_inject_rt2` (withdraw + re-advertise) | MAC fallback after withdraw observed in mac_flags |

---

## G2 — `irb_si_rejection` (config-validation only, type=config-validation)

Run: `results/RUN_20260420_1143_PE-1/TEST_mac_mob_irb_si_reject_G2`
Total elapsed 18.0s, overall **WARN**.

`SC01_add_irb_to_si_instance`: trigger=PASS, bgp_session=WARN (BGP noise from neutral 2.2.2.2/5.5.5.5 peers in DUT config). The recipe is a CLI commit-check + rollback test; it does not send traffic.

---

## G3 — `scale_64k` (bulk learn / move / suppression at 65 536 MACs)

Run: `results/RUN_20260420_1716_PE-1/TEST_mac_mob_scale_64k_G3`
Total elapsed 1270s.

| Scenario | Verdict | Notes |
|---|---|---|
| SC01_bulk_learn_64k | **PASS** | trigger=PASS, ghost_macs=PASS, bgp_session=PASS, timing=PASS |
| SC02_bulk_move_64k_ac1_to_ac2 | **FAIL** (verifier-only) | trigger=PASS; mac_flags / forwarding fail because the verifier compares hardcoded `test_mac=00:DE:AD:00:01:01` instead of the moved-block base_mac. Pre-existing scaffolding mismatch, NOT a test logic regression. |
| SC03_suppression_at_scale | **PASS** | trigger=PASS, ghost_macs=PASS, bgp_session=PASS, timing=PASS |

Trigger orchestration (the part this work fixed) is 3/3 PASS.

---

## G4 — `pw_suppression_sanctions` (cross-domain MAC mobility + sanctions)

G4 is the most fragile recipe under live Spirent because each scenario fires 10 cycles of `protocol-start/stop` + `bgp-peer evpn-inject` (~145 s of BLL load). Spirent BLL becomes "unhealthy" between scenarios when run back-to-back — that surfaced as `spirent_health=SKIP` for the second/third scenario in a single back-to-back run.

To produce per-scenario evidence, each SC was run individually after re-establishing the EVPN_RT2_Peer (`--negotiate-afi l2vpn-evpn`, `--evpn-rd 19.19.19.2:100`, `--evpn-rt 100:100`, `--evpn-evi-rt 100:1`, `--evpn-nexthop 19.19.19.2`).

| Scenario | Verdict | Run | Sanction evidence |
|---|---|---|---|
| SC01_cross_domain_blackhole_sanction | **PASS** (timing=WARN) | `RUN_20260420_1939_PE-1` | `SANCTION [blackhole] applied -> OK (Commit succeeded)` + `FLAP[0..9] local->remote seq=1..10 -> OK` ; mac_flags=`['L','R','K','M']` (Local + Remote + Killed + Mobility), forwarding=PASS, cross_layer=PASS, bgp_session=PASS |
| SC02_cross_domain_shutdown_sanction | **PASS** (timing=WARN) | `RUN_20260421_0538_PE-1` | `SANCTION [shutdown] applied -> OK` + `FLAP[0..9] local->remote seq=1..10 -> OK`; ghost_macs=PASS, cross_layer=PASS, bgp_session=PASS |
| SC03_suppress_sanction_cross_domain | **PASS** (timing=WARN) | `RUN_20260421_0550_PE-1` | `SANCTION [suppress] applied -> OK` + `FLAP[0..9] local->remote seq=1..10 -> OK`; ghost_macs=PASS, cross_layer=PASS, bgp_session=PASS |
| SC04_remote_remote_no_suppression | **PASS** | `RUN_20260420_1923_PE-1` | trigger=PASS (`spirent_remote_seq_updates`: 20 RT-2 updates, monotonic seq), mac_flags=PASS, forwarding=PASS, cross_layer=PASS, bgp_session=PASS, timing=PASS (57.32 s) |

`timing=WARN` on SC01-03 = scenario took ~145 s vs. recipe threshold 90 s. Functional outcome unaffected; recipe threshold should be relaxed to ~180 s for sanction recipes (10-cycle flap intrinsically takes ~140-150 s).

### G4 fix that landed during this run

`scaler/TEST/catalog/evpn_mac_mobility_SW204115/orchestration/scenario_runner.py` (`spirent_sanction_flap` handler):

1. **`ac1_vlan` shadowing bug fixed** — handler used to do `ac1_vlan = int(params.get("ac1_vlan", "0") or 0)` which silently overwrote the function argument with `0`, producing `FLAP SKIP: ac1_vlan not set`. Now only overrides when `params["ac1_vlan"]` is positive.
2. **MAC-learn poll timeout floor raised** from 1.5 s → 5.0 s with poll-interval 0.5-1.0 s, matching the ~3-5 s the DUT actually needs to install a Spirent ARP-broadcast MAC into the bridge FDB.
3. **Persistent flap device** — Spirent device created once before the cycle loop and removed once after, instead of `create-device + protocol-start + protocol-stop + remove-device` per cycle. Cuts ~3-4 s of BLL churn per cycle and makes per-cycle latency match SC04's tight cadence.
4. Per-cycle teardown: explicit `spirent_remove_device(flap_dev)` in a `try/except` after the loop so partial failures don't leak Spirent state.

Synced to live `/home/dn/SCALER/TEST/catalog/evpn_mac_mobility_SW204115/orchestration/scenario_runner.py` per the worktree-deploy-sync rule.

---

## G5 — `clear_mac_history_ops` (operational `clear evpn` commands)

Run: `results/RUN_20260420_0939_PE-1/TEST_mac_mob_clear_ops_G5`
Total elapsed 92.59s, overall **PASS**.

| Scenario | Verdict |
|---|---|
| SC01_clear_mac_suppression_all | **PASS** |
| SC02_clear_mac_suppression_single | **PASS** |
| SC03_clear_mac_history | **PASS** |
| SC04_clear_restore_cycles | **PASS** |

`bgp_session=WARN` on every SC = BGP-summary noise from configured-but-not-present peers 2.2.2.2 / 5.5.5.5; functional outcome PASS.

---

## Outstanding infra notes (informational, not test logic)

1. **Spirent BLL session degradation under sustained `bgp-peer evpn-inject` load**: after ~150 s of inject churn, `_run_spirent` accumulates >=3 transient failures and `is_spirent_healthy()` flips to `False`. The orchestrator's `ensure_spirent_ready()` recovery uses `connect + reserve` — if the BLL has restarted in the meantime, `_try_reconnect()` ends up forcing `connect --force-new` which wipes EVPN_RT2_Peer (along with all other emulated devices). This causes the next scenario in the same back-to-back run to start with no remote BGP peer.
   - **Mitigation in this validation**: run SCs individually with `--scenario SCxx`, recreating EVPN_RT2_Peer between runs.
   - **Permanent fix candidate**: either (a) make `_try_reconnect()` strictly preserve infra devices (re-create `EVPN_RT2_Peer` from cached args after a forced `--force-new`), or (b) widen `_MAX_CONSECUTIVE_FAILS` for the inject-RPC path that's known to be flaky on STC.

2. **`config` and `end` reported as DNOS "Unknown word"**: harmless prompt-detection cosmetic — the underlying `network-services evpn ... commit` block lands successfully (`Commit succeeded by dnroot at ...`), per evidence in every G4 trigger phase log. Real-world impact is zero; cleanup target is the per-runner CLI mode handling, not the test logic.

3. **Per-scenario `timing` threshold (90 s)** is too tight for G4 sanction recipes; recommend bumping to 180 s in the recipe (`expected_convergence_sec`). Today the threshold drives `WARN` only, no functional FAIL.

---

## Evidence pointers

```
/home/dn/SCALER/TEST/catalog/evpn_mac_mobility_SW204115/results/
  RUN_20260420_0939_PE-1/TEST_mac_mob_clear_ops_G5/                 # G5 4/4 PASS
  RUN_20260420_1143_PE-1/TEST_mac_mob_irb_si_reject_G2/             # G2 1/1 (WARN)
  RUN_20260420_1705_PE-1/TEST_mac_mob_evpn_evpn_G1/                 # G1 3/3 PASS
  RUN_20260420_1716_PE-1/TEST_mac_mob_scale_64k_G3/                 # G3 trigger 3/3 PASS, SC02 verifier mismatch
  RUN_20260420_1923_PE-1/TEST_mac_mob_pw_suppress_G4/               # G4 SC04 PASS
  RUN_20260420_1939_PE-1/TEST_mac_mob_pw_suppress_G4/               # G4 SC01 PASS
  RUN_20260421_0538_PE-1/TEST_mac_mob_pw_suppress_G4/               # G4 SC02 PASS
  RUN_20260421_0550_PE-1/TEST_mac_mob_pw_suppress_G4/               # G4 SC03 PASS
```

Each run dir contains `verdict.json`, `FULL_REPORT.md`, `SUMMARY.md`, per-scenario `phase_*.json` and `observability.json`.
