---
name: tp-agent-queue-routing
description: "/TP queue vs user-test-mcp ownership split"
---

# TP Agent Queue Routing

The `user-tp-agent-mcp` server owns TP production, queueing, review artifacts,
and status. The `user-test-mcp` server owns consuming saved TP artifacts into
runnable TEST recipes, compiling phases, validating syntax, prerequisites, and
execution.

## Ownership Split

| Need | First server/tool family | Stop or next step |
|---|---|---|
| Generate or revise a TP from Jira/Confluence/spec text | `user-tp-agent-mcp` TP create/generate tool | Stop after artifact path and queue id unless user asks to run it. |
| Check queued TP generation progress | `user-tp-agent-mcp` queue/status tool | Poll only by returned job/queue id. |
| Inspect produced TP artifacts | `user-tp-agent-mcp` artifact/list/read tool | Return artifact path and summary. |
| Convert a saved TP into a runnable recipe | `user-test-mcp.test_create_from_tp` | Then `test_phase_compile`. |
| Validate executable DNOS syntax from TP steps | `user-test-mcp.test_syntax_validate_live` | Uses knowledge-first resolver; do not re-run TP generation. |
| Run or report the test | `user-test-mcp.test_run_gated` / `test_report` / `test_proof_path` | TEST owns verdict and proof. |

## Natural Language Triggers

| User says | First tool family |
|---|---|
| `/TP`, "generate test plan", "build TP for SW-..." | `user-tp-agent-mcp` create/generate |
| "what is the TP queue doing", "status of TP generation" | `user-tp-agent-mcp` queue/status |
| "show the generated TP artifacts", "where is the TP output" | `user-tp-agent-mcp` artifact/list/read |
| "turn this TP into a TEST", "run this TP", "compile this TP recipe" | `user-test-mcp.test_create_from_tp`, then `test_phase_compile` |
| "validate commands from this TP", "wrong DNOS syntax in TP" | `user-test-mcp.test_syntax_validate_live` |

## Rules

1. Do not make both servers produce the same artifact. TP creates the plan;
   TEST consumes it.
2. Do not jump from TP generation directly to device config or Spirent traffic.
   TEST must compile, validate syntax, check prerequisites, and own execution.
3. Use TEST's knowledge-first resolver for executable DNOS syntax. TP text is a
   requirement source, not command truth.
4. For category or multi-TP execution, use TEST background job semantics and
   poll by job id; do not hold one synchronous MCP call open for a long run.
