# Expected Behavior -- `EVPN IGMP Proxy - CLI syntax divergence (snoop-DB show)`

- **feature_id:** `SW-211037`
- **epics:** SW-211037
- **captured at:** 2026-07-15T10:46:22Z

System-architect CLI story SW-251450 (owner Menachem Dodge, To Do) specifies 'show evpn igmp-snooping multicast-db' as the snoop-DB show; code on feature/evpn_igmp_proxy_integration_v1 registers 'show evpn igmp-snooping groups'/'interfaces'. SA story is the syntax source of truth pre-live; keep 'multicast-db' as spec (EXPECTED_LIVE_VALIDATE) until the first lab build resolves it. Do NOT rewrite the TP to match code.

## Show Commands (live-validated)

_Live Status legend: **LIVE_VALIDATED** = accepted + real data; **LIVE_VALID_NO_ENTRIES** = valid command, empty table / object-not-found now; **LIVE_EMPTY** = blank output; **LIVE_INCOMPLETE** = valid stem, missing argument (auto `?`-discovery ran -- see Syntax Discovery below); **LIVE_REJECTED** = wrong command (fix syntax); **LIVE_ERROR** = valid command, run failed (auth/transport/timeout/crash -- retry)._

| Command | Device Role | Expected Keywords | Live Status |
|---|---|---|---|
| show evpn igmp-snooping multicast-db | proxy PE | Source, Group, Originator, ESI, Flags | UNVALIDATED |
| show evpn igmp-snooping groups | proxy PE | Group | UNVALIDATED |

## Cross-Feature Interactions

| Scenario | Expected | Anti-Pattern |
|---|---|---|
| snoop-DB show command name (SW-251450 spec vs code) | SA story SW-251450 = 'show evpn igmp-snooping multicast-db' is the spec/authority pre-live; on first build run BOTH multicast-db and groups, whichever the CLI accepts is truth -> cache it and /TP improve SW-211037 | silently rewriting the TP from 'multicast-db' to 'groups' because code differs (record the divergence and keep SA syntax until live proves otherwise) |

## Sources

- **[jira]** [EVPN-IGMP Proxy: CLI | show evpn igmp-snooping multicast-db](https://drivenets.atlassian.net/browse/SW-251450) -- fetched None

