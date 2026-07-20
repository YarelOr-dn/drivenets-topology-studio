---
name: knowledge-first-mcp-routing
description: "Knowledge-first MCP routing for /TEST /TP /debug"
---

# Knowledge-First MCP Routing

For DNOS syntax, `/TEST`, `/TP`, `/CCIE`, `/debug-dnos`, and any agent flow that
turns Jira/Confluence/TP prose into executable commands, the agent must use
proven local knowledge before live discovery.

## Intent Router: Pick One Primary Tool First

Classify the user's request before calling tools. Do not fan out across MCPs
from loose keywords.

| User intent | First native MCP tool | Stop / next step |
|---|---|---|
| List runnable tests / catalog | `project-0-drivenets-topology-studio-user-test-mcp.test_catalog_list` | Stop after catalog summary unless user asks to run/create. |
| Find tests by category, TC, Jira task/category | `project-0-drivenets-topology-studio-user-test-mcp.test_category_find` | Use matches to plan or run. |
| Convert TP/Jira TC to runnable recipe | `project-0-drivenets-topology-studio-user-test-mcp.test_create_from_tp` | Then `test_phase_compile`. |
| Compile / inspect recipe phases | `project-0-drivenets-topology-studio-user-test-mcp.test_phase_compile` | Then syntax/prereq gates. |
| Validate DNOS syntax | `project-0-drivenets-topology-studio-user-test-mcp.test_syntax_validate_live` | It uses knowledge-first resolver before live discovery. |
| Check prerequisites | `project-0-drivenets-topology-studio-user-test-mcp.test_prerequisites_live_check` or `test_prerequisites_batch` | Missing config returns dry-run dnos-config commit plan. |
| Run one TEST recipe | `project-0-drivenets-topology-studio-user-test-mcp.test_run_gated` | Use returned job/result/proof path. |
| Run TEST category | `project-0-drivenets-topology-studio-user-test-mcp.test_category_run` | Must return `job_id`; poll `test_category_status`. |
| Show running category progress | `project-0-drivenets-topology-studio-user-test-mcp.test_category_status` | Continue polling until completed. |
| Explain proof / evidence | `project-0-drivenets-topology-studio-user-test-mcp.test_proof_path` then `test_report` | Read raw evidence if auditing PASS/FAIL. |
| DNOS path / Spirent frame recipe | `project-0-drivenets-topology-studio-dnos-config.dnos_dnaas_spirent_preflight` | Only after TEST gate asks for path/traffic readiness. |
| Create/start/measure traffic | `project-0-drivenets-topology-studio-user-spirent-mcp` via TEST phase | Do not call directly before TEST/DNAAS gates. |
| Packet proof | `project-0-drivenets-topology-studio-user-xray-mcp` | Only after counter proof or explicit packet-proof request. |
| DNOS bug diagnosis | `project-0-drivenets-topology-studio-user-debug-dnos-mcp` | Only after TEST proves infrastructure is clean. |

If the native MCP reports `Not connected`, `Tool not found`, invalid request, or
transport failure, retry once, then repair/rebind. CLI fallback is allowed only
as a logged temporary bridge.

## Required Lookup Order

1. Catalog recipe memory: `metadata.syntax_validation`,
   `metadata.knowledge_resolution`, and saved `compiled_phases`.
2. Global TEST corrections: `~/.cursor/test_knowledge/corrections.json`.
3. Shared TEST syntax cache:
   `~/SCALER/TEST/_shared/knowledge/by_protocol/*/{validated_commands,known_invalid,completion_menus}.json`.
4. Feature knowledge cache:
   `~/.cursor/knowledge_base/<feature_id>/`, accepting both legacy `command`
   and canonical `cmd` show-command fields.
5. Static DNOS command knowledge from dnos-config / Network Mapper command docs.
6. Live dnos-config MCP fallback:
   `dnos_cmd_search`, `dnos_run_show_commands`, and only then dry-run
   `dnos_atomic_commit` when explicitly allowed.

## Rules

- Never trust Jira, Confluence, TP markdown, or LLM text as executable DNOS
  syntax until it has passed the lookup order above.
- If live MCP proves a command correction, persist both the wrong and correct
  forms so later chats and category runs do not rediscover the same error.
- If a command is known invalid and has no correction, block the run as
  `UNTRUSTED_SYNTAX` / `SYNTAX_UNVALIDATED` instead of trying it anyway.
- `/CCIE` is a topology and prerequisite blueprint cache, not durable syntax
  memory. It may shorten prerequisite discovery, but command truth still comes
  from the knowledge-first resolver.
- Use `test_dnos_live_wait` or equivalent condition polling for convergence.
  Do not add blind sleeps when a show command, MCP job state, stream counter, or
  trace marker can be polled directly.
- Every wait/check/test phase should expose elapsed milliseconds, poll count,
  and the condition that ended the wait.
- VERIFY the cache before trusting a handoff/gate that claims it is EMPTY.
  A stale "knowledge cache empty, do not assert" gate can force an unnecessary
  capture detour. Actually list `~/.cursor/knowledge_base/<feature_id>/` (and
  grep for the epic/SW key across sibling feature dirs) before concluding the
  cache is empty; a related feature dir often already holds live-validated
  behavior. (Learned 2026-07-08: SW-277948 proxy-NDP was cached under
  `evpn_si_vpls_proxy_arp_ndp` + `sw194912_vpls_pw_arp_ndp_proxy_arp_irb` even
  though a prior handoff gate said "cache EMPTY".)
- `test_verdict_layers` is built for COMPILED-TP recipes. A no-recipe/agentic
  run (no `compile` object, ad-hoc phases) will hard-fail the `tp_substeps` and
  `phase_execution` layers and return an overall FAIL even when every
  `step_result` is PASS. That overall FAIL is a payload-shape artifact, NOT a
  test failure. For agentic runs: report the per-`step_result` verdicts as the
  truth, state the artifact explicitly, and do not force a green. (Ideal tool
  fix: mark `tp_substeps`/`phase_execution` NOT_APPLICABLE when `compile` is
  absent.)
