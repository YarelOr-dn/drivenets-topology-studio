# TEST_mac_mob_basic_SW205160 — MAC Mobility | Basic Learning

Human-readable companion to `recipe.json`. Every layer, step, and command this
test runs is documented here. The `recipe.json` is the executable form of this
same content; if the two ever drift, the recipe wins (it is what runs) and this
README must be updated to match.

## At a glance

| Field | Value |
|-------|-------|
| Test ID | `TEST_mac_mob_basic_SW205160` |
| Jira | [SW-205160](https://drivenets.atlassian.net/browse/SW-205160), parent epic SW-204115 |
| Type | Functional |
| Feature | EVPN MAC mobility |
| Knowledge revision | 2026-04-30-mcp-dnaas-source-qualified |
| MCP-validated | Yes — every show command live-fired against PE-1 (0 syntax fails) |
| Ready to run | Yes |

## What this test proves

EVPN MAC learning works correctly across the three legitimate sources DNOS can
learn from, and the table-level invariants (count, ghost cleanliness, BGP
stability) hold throughout.

| Scenario | Source of MAC | What we assert |
|---|---|---|
| **SC01** Local AC | DUT learns the MAC from a local Spirent AC | MAC table shows `Local`; RT-2 advertised; NCP forwarding points to local AC; no ghost / suppression |
| **SC02** Remote EVPN | DUT receives MAC via remote PE's RT-2 | MAC table shows `bgp/evpn/remote`; RT-2 present with sane sequence/origin; local AC does not falsely own it |
| **SC03** VPLS PW | DUT learns MAC over a VPLS PW (dynamic) | MAC table shows `pw/pseudo/vpls`; RT-2 NOT advertised from PW learning; forwarding uses PW label |
| **SC04** Stability | Suite-level invariants | MAC count does not regress; forwarding table stable; BGP stays up; ghost table clean |

## Layer-by-layer execution map

`/TEST run TEST_mac_mob_basic_SW205160` walks these layers in order. Every
device-touching step routes through the **`dnos-config` MCP** automatically
(Strategy 0 in `shared/device_runner.py`).

### Layer 0 — MCP wiring (automatic, no user action)

| Step | What happens | Where |
|---|---|---|
| 0.1 | Probe `http://localhost:9300/health` | `device_runner._probe_mcp()` |
| 0.2 | If healthy: route every show command via `dnos_run_show_commands` | `device_runner._mcp_run_show()` |
| 0.3 | If unhealthy: fall through to helper / SSH chain | logged, no failure |

**Opt-out (debug only):** `TEST_DISABLE_MCP=1`.

### Layer 1 — Prerequisite gate (mandatory; never skipped)

Every prerequisite below runs against the live device. The test does not
proceed to scenarios until every entry is green.

| # | ID | What it proves | Check command / MCP tool |
|---|---|---|---|
| 1 | `bgp_evpn` | BGP L2VPN EVPN session is Established | `show bgp l2vpn evpn summary \| no-more` |
| 2 | `evpn_instance` | The EVPN instance under test exists | `show evpn instance {evpn_name} detail \| no-more` |
| 3 | `seamless_integration` | SI is enabled and there is **no** `router-interface` (rejected for ELAN+SI) | `show config network-services evpn instance {evpn_name} \| flatten \| no-more` |
| 4 | `spirent_dnaas_diagnose` | DNAAS path for the chosen outer VLAN has `overall_verdict=pass` and `fault_count=0` | MCP `dnos_dnaas_diagnose` |
| 5 | `spirent_ac_teach_plan` | DNAAS returns a usable `frame_recipe` (no recipe blockers) — feeds into `active_test_session.expected_traffic` | MCP `dnos_dnaas_teach_plan` |
| 6 | `spirent_correlation` | `frame_recipe.ownership_tag` appears on Spirent streams/devices AND in the DUT-side description | inspection of Spirent + DNOS desc |
| 7 | `pw_instance_for_sc03` | PW EVI is **Installed** with a non-zero ingress label (only required for SC03) | `show evpn vpls-pw \| no-more` |
| 8 | `mac_learned` | A `test_mac` is reachable on the AC (Spirent stream is sending or has just sent) | `/SPIRENT L2` using the MCP `frame_recipe.spirent_flags` |

**Auto-fix policy** (from the prerequisite gate flow):

- `prerequisite.fix_via_mcp` set → call that MCP tool directly (`dnos_atomic_commit`, `dnos_dnaas_*`, …) and re-check.
- `prerequisite.fix_via` set → call the named sub-command (`/BGP`, `/SPIRENT`, `/debug-dnos`) and re-check.
- DNOS bug → invoke `/debug-dnos`, document, ask user.
- Unknown syntax → run `/search-company-knowledge` AND `validate_config` in parallel; never write unvalidated syntax.
- Truly unfixable → ask the user `[Skip | Abort | Manual fix]`.

### Layer 2 — Scenario phases (per scenario)

Every scenario has the same four-phase shape:

| Phase | Purpose | Tool |
|---|---|---|
| `snapshot` | Take a baseline of MAC / BGP / forwarding / ghost tables before the trigger | `mcp` (show only) |
| `trigger` | Cause the MAC to be learned (local AC traffic, remote PE traffic, or PW traffic) | `mcp` for static; `python` only for polling/conditional logic |
| `verify` | Re-read the same tables and assert the expected state | `mcp` (show + parsers) |
| `health` | Process status / crashes / alarms | `mcp` (show) |

#### SC01 — Local AC learning (`test_mac` = `00:DE:AD:00:01:01`)

Snapshot commands:
1. `show evpn instance {evpn_name} detail | no-more`
2. `show evpn mac-table detail instance {evpn_name} | no-more`
3. `show evpn mac-table instance {evpn_name} mac {test_mac} | no-more`
4. `show bgp l2vpn evpn summary | no-more`
5. `show evpn forwarding-table mac-address-table instance {evpn_name} mac {test_mac} | no-more`
6. `show dnos-internal routing evpn instance {evpn_name} mac-table-ghost detail | no-more`

Trigger: `traffic_on_ac1` (Spirent stream toward DUT AC).

Verify commands:
1. `show evpn mac-table mac {test_mac} | no-more`
2. `show evpn mac-table detail instance {evpn_name} | no-more`
3. `show evpn instance {evpn_name} detail | no-more`
4. `show bgp l2vpn evpn route-type 2 | include {test_mac} | no-more`
5. `show evpn forwarding-table mac-address-table instance {evpn_name} mac {test_mac} | no-more`
6. `show dnos-internal routing evpn instance {evpn_name} mac-table-ghost detail | no-more`

Expected:
- `source_contains` ⊇ `["local", "ac"]`
- `rt2_advertised: true`
- `forbidden_flags`: `F` (frozen), `D` (duplicate) — neither present
- `sequence_consistent`, `check_forwarding`, `check_ghost_macs`, `no_stuck_blackhole`, `cross_layer_check` — all true

#### SC02 — Remote EVPN learning (`test_mac` = `00:DE:AD:00:02:02`)

Same shape as SC01 but trigger is `remote_pe_traffic` and `source_contains` ⊇
`["bgp", "evpn", "remote"]`. RT-2 must still be present (received-routes
column) but local AC must NOT show as the owner.

#### SC03 — VPLS PW learning (`test_mac` = `00:DE:AD:00:03:03`)

Adds five extra prerequisites on top of Layer 1:

| # | ID | Note |
|---|---|---|
| 1 | `si_evpn_instance` | VPLS RTs ONLY valid under SI subtree |
| 2 | `isis_adjacency` | Convergence budget: 45 s |
| 3 | `ldp_session` | Convergence budget: 10 s |
| 4 | `spirent_vpls_peer` | BGP-VPLS session up; budget 10 s |
| 5 | `pw_installed` | PW must be **Installed**, not Uninstalled/BNI |

Total convergence budget: **90 s**. Reference doc:
`~/.cursor/spirent-reference/vpls-pw-establishment.md`.

Trigger: `spirent_create_vpls_stream` (sends MPLS-labeled L2 frames via
`vpls-stream` using the PW ingress label).

Expected source: `["pw", "pseudo", "vpls"]`. RT-2 **withdrawn** is the key
positive assertion (RT-2 must NOT be advertised from PW-learned MACs).

#### SC04 — Table counts and forwarding continuity

Suite-level invariants only:
- `mac_count_stable_or_grows: true`
- `source_mac_flags`: exact SC01/SC02/SC03 MAC-to-source mapping must coexist on PE-4 (`L>`, `B>`, and `v>` respectively).
- `check_mac_flags`, `check_forwarding`, `check_ghost_macs`, `no_stuck_blackhole`, `cross_layer_check` — all true.

### Layer 3 — Counters (collected once before, once after each scenario)

| Label | Command | Parser | Rule |
|---|---|---|---|
| `mac_count` | `show evpn mac summary \| no-more` | first integer in output | `no_decrease` |
| `ghost_mac_count` | `show dnos-internal routing evpn instance {evpn_name} mac-table-ghost detail \| no-more` | real ghost/suppression parser | `zero` (active selected MACs in the diagnostic view do not count) |
| `fwd_table_count` | `show evpn forwarding-table mac-address-table instance {evpn_name} \| no-more` | line count | informational |

### Layer 4 — Event expectations (syslog scan around trigger windows)

| Event | Expectation | Why |
|---|---|---|
| `BGP_NOTIFICATION` | absent | no BGP session resets during the test |
| `L2_MAC_MOBILITY_MAC_ADDRESS_SUPPRESSED` | absent | suppression should not trigger on normal operations |

### Layer 5 — Health checks (run between scenarios)

- Process status: `routing:bgpd`, `routing:fibmgrd`, `routing:rib_manager`, `neighbour_manager` — all `running`.
- Crash check: `check_crashes: true`.
- Alarm check: `check_alarms: true`.

### Layer 6 — Bug Finding Guard

`bug_finding_guard.enabled: true`, `stop_after_first_functional_fail: true`.

If the infrastructure-correct checklist passes and any DNOS-facing assertion
still fails:

1. Stop the run immediately.
2. Save active context (device, EVI, MAC, expected vs observed source, stream
   ID, timestamp, results path).
3. Invoke `/debug-dnos` with this context:
   ```
   {feature: evpn-vpls-si, epic: SW-178648, dp_enabler: SW-183400, jira: SW-205160}
   ```
4. Collect multi-layer proof (CLI / forwarding / BGP-EVPN-VPLS / traces / code).
5. Write `BUG_*.md` evidence file before any workaround.

### Layer 7 — Cleanup (always runs, even on failure)

| Command | Purpose |
|---|---|
| `unset logging terminal` | turns off live syslog stream that was enabled at the start; DNOSSession must not append `| no-more` to `unset` commands |

(Removed from this recipe on 2026-04-30: `no debug evpn mac-mobility` was
flagged INVALID by MCP auto-investigation — DNOS has no `debug` operational
command. Replacement is the `set logging terminal` + file-based traces flow.)

### Layer 8 — Result artifacts

After every run:

```
~/SCALER/TEST/catalog/evpn_mac_mobility_SW204115/results/RUN_<ts>_<device>/
   TEST_mac_mob_basic_SW205160/
      SUMMARY.md                — one-page verdict: PASS / FAIL / WARN / INCONCLUSIVE per scenario
      EXECUTION_LOG.md          — human-readable transcript: every command + every output,
                                  grouped by phase + scenario, with timestamps, method tag,
                                  REJECTED markers, and elapsed-ms per command
      execution_log.jsonl       — machine-readable: one JSON record per command
      execution_log_stats.json  — quick stats: totals, by-method, verdict
      evidence.json             — raw outputs of every show command, per phase
      counters.json             — before/after numbers for each counter rule
      health.json               — process / crash / alarm snapshots
      events.json               — syslog matches for tracked events
      session.log               — legacy helper/SSH session log
```

**EXECUTION_LOG.md format** (auto-generated by `shared/run_transcript.py`,
hooked into the `device_runner.run_show` choke point so every command is
captured regardless of which strategy executed it -- MCP, helper, SSH, or
agent callback):

```markdown
# Execution Log -- TEST_mac_mob_basic_SW205160

Run started: 2026-04-30T... | Primary DUT: PE-1 | Dry run: False | Verdict: PASS

## Totals
- Total commands issued: 47
- DNOS-rejected commands: 0
- By method: dnos_config_mcp=47

## Commands per DUT
| Device | Commands |
|---|---|
| PE-1 | 47 |

## Phase: prerequisite_gate
_8 command(s) in this phase._

### 1. [2026-04-30T...] PE-1 via dnos_config_mcp -- 1772 ms
**Command:** show bgp l2vpn evpn summary | no-more
**Output:** (full output here, fenced)

## Phase: SC01_learn_local_ac -- scenario SC01_learn_local_ac
_12 command(s) in this phase._
...
```

## How to read the recipe.json

If you prefer the executable form, here is the field map:

| `recipe.json` key | Purpose |
|---|---|
| `prerequisites[]` | Layer 1 — checked before any scenario runs |
| `scenarios[]` | Layer 2 — each scenario has `phases.{snapshot,trigger,verify}` |
| `counter_commands[]` + `counter_expectations[]` | Layer 3 — counter rules |
| `event_expectations[]` | Layer 4 — syslog scan rules |
| `health_checks` | Layer 5 |
| `bug_finding_guard` | Layer 6 |
| `cleanup_commands` | Layer 7 |
| `runtime_parameters` | Resolved per-run (e.g. `{evpn_name}` is read from `show evpn summary`) |
| `show_commands_validated` | Catalog of canonical show commands with one-line doc per command |
| `invalid_commands` | Catalog of commands DNOS rejects, with the recommended replacement |
| `verdict.layers: 14` | Number of verdict gates (full taxonomy in `~/.cursor/rules/dnos-test-automation-blueprint.mdc`) |

## How to run

```bash
# Standalone (single test)
python3 ~/SCALER/TEST/catalog/evpn_mac_mobility_SW204115/mac_mobility_orchestrator.py \
    --device PE-1 --test TEST_mac_mob_basic_SW205160

# Suite-batch (skip already-passing tests)
python3 ~/SCALER/TEST/catalog/evpn_mac_mobility_SW204115/mac_mobility_runner.py \
    --device PE-1 --only TEST_mac_mob_basic_SW205160

# Or via the meta-orchestrator
/TEST run TEST_mac_mob_basic_SW205160 on PE-1
```

## Validation history

| Date | Action | Result |
|---|---|---|
| 2026-04-30 | MCP auto-investigation of all 25 commands via `dnos_cmd_search` + `dnos_run_show_commands` | 7/9 reported MISSes were **false negatives**; 1/9 (`debug evpn mac-mobility`) confirmed INVALID and removed |
| 2026-04-30 | End-to-end live-device validation against PE-1 | 23 commands → **0 syntax fails** (19 PASS-LIVE + 3 PASS-LIVE-EMPTY + 1 DEFERRED config-mode) |
| 2026-04-30 | `/TEST run` MCP wiring (Strategy 0) added to `shared/device_runner.py` | smoke test green: every show routes through `dnos_config_mcp` |

## See also

- Suite-level: `~/SCALER/TEST/catalog/evpn_mac_mobility_SW204115/README.md`
- Development: `~/SCALER/TEST/catalog/evpn_mac_mobility_SW204115/DEVELOPMENT_GUIDELINES.md`
- Sibling test types: `tests/ac_evpn`, `tests/ac_pw`, `tests/ha_mac_mobility`, `tests/multihoming`, `tests/sticky_modes`, `tests/withdraw_flush`
- Verdict layer taxonomy: `~/.cursor/rules/dnos-test-automation-blueprint.mdc`
- MCP auto-investigation rule: `~/.cursor/rules/test-mcp-auto-investigate-miss.mdc`
- DNOS CLI completion / `cmd search` rule: `~/.cursor/rules/dnos-cli-completion-protocol.mdc`
