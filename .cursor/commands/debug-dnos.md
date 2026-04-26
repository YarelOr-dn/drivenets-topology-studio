---
description: DNOS CLI debugging methodology
---
# DNOS Multi-Layer Debug Session

Start a systematic debug investigation on a DNOS device, or quickly recall saved findings.

## Intent Detection (CRITICAL — do this FIRST)

Parse the user's message to determine which mode to use:

| User says... | Mode | Action |
|-------------|------|--------|
| `/debug-dnos` (no args) | **INVESTIGATE** | Start full investigation (Session Startup below) |
| `/debug-dnos` + device + problem | **INVESTIGATE** | Skip questions, go straight to Phase 0 |
| `/debug-dnos` + "summary", "findings", "recall", "bug", "show me the bug", "give me the proof", "bug description" | **RECALL** | Read saved bug evidence, present summary immediately. **"Bug description" = raw CLI outputs with timestamps as proof** |
| `/debug-dnos` + "retest" or "is it fixed?" | **RETEST** | Re-run key show commands against saved bug, compare |
| `/debug-dnos` + show command request (e.g., "show flowspec ncp 0 on PE-1") | **QUICK** | Run the specific command(s) directly, no investigation |
| `/debug-dnos verify SW-XXXXX` or `verify SW-XXXXX on <Device>` | **VERIFY** | Verify single bug fix on device |
| `/debug-dnos verify epic SW-XXXXX on <Device>` | **VERIFY** | Verify all closed children of epic on device |
| `/debug-dnos verify build on <Device>` | **VERIFY** | Auto-discover which bugs are verifiable on device's build |
| Device + Bug provided, verifiability question (e.g. "SW-XXXXX on PE-1", "is SW-XXXXX verifiable on PE-1?", "can I verify SW-XXXXX on PE-1?") | **BUILD_CHECK** | **Immediate** — run build check, report VERIFIABLE / NOT VERIFIABLE / UNKNOWN / SKIP. No wizard, no follow-up. Use when user wants to *know* if verifiable, not necessarily to *run* verification. |
| `/debug-dnos` + "learn", "what did you learn", "update knowledge" | **LEARN** | Self-learn from session: use `SKILL.md` Learning Routing Table to update the correct section file, plus `VERIFY_RECIPES.md` and `debug-dnos.md`. If learning also affects /BGP, /XRAY, /HA, update their JSON store + run sync. |

**RECALL mode is instant** — no device questions, no Phase 0. Read from `~/SCALER/FLOWSPEC_VPN/bug_evidence/` and present.

---

## Mode: RECALL (summary / findings / bug proof)

When user asks for bug summary, findings, proof, or saved info:

1. **Scan** `~/SCALER/FLOWSPEC_VPN/bug_evidence/BUG_*.md` for all saved bugs
2. **If one bug:** Read it and present the full summary with all raw traces, CLI outputs, timestamps, comparison table, and root cause
3. **If multiple bugs:** AskQuestion — "Which bug?" with options listing each bug title
4. **Present as-is** — the bug evidence file IS the deliverable. Include all sections: symptom, NH resolution, traces with timestamps, protobuf messages, comparison table, code-level root cause
5. **Present Expected/Actual/Steps as generic** — these sections MUST NOT mention specific topology device names or IPs. They describe the general problem pattern, not the specific test setup.
6. **"Bug description" = raw CLI proof** — when the user asks for "the bug description", they want raw `show` command outputs and trace lines with timestamps as evidence. NOT a code-level analysis summary. Deliver: (a) raw show outputs, (b) raw trace lines, (c) comparison tables, (d) specification/RFC quote. Code analysis is supplementary — put it last.
7. **Never re-run commands in RECALL mode** — the evidence file has everything. Only re-run if user explicitly says "retest" or "is it still there?"
7. **Topology JSON** — mention it's available via "Topologies → Load Debug-DNOS..." in the topology app, or via "File → Load" with the `.topology.json` file path
8. **Session log** — if the BUG_*.md header references a session log file, mention it: "Full raw outputs available in `<session log path>`"

---

## Mode: RETEST (is the bug fixed?)

When user asks to retest a known bug:

1. Read the bug evidence file to get the key verification commands
2. Run them on the device(s) and compare with saved evidence
3. Append a new row to the Retest History table
4. Report: `BUG PRESENT`, `FIX CONFIRMED`, or `STALE STATE`

---

## Mode: QUICK (run specific commands)

When user asks for a specific show command or a small set of outputs:

1. Parse the device and command from the user's message
2. Run via `run_show_command` directly
3. Present the raw output — no investigation, no phases

---

## Mode: BUILD_CHECK (immediate verifiability answer)

**When user provides Device + Bug** — answer immediately whether the closed bug is verifiable on that device's build. No wizard, no session log, no follow-up questions.

### Flow (single tool call)

1. **Parse** — Extract `SW-XXXXX` (or BUG-XXX) and device name from user message
2. **Resolve device** — `list_devices` (Network Mapper) or `~/SCALER/db/devices.json` fallback. Match by partial hostname. If not found, report "Device not found" and stop
3. **Run build check** — `python3 ~/SCALER/FLOWSPEC_VPN/bug_evidence/build_check.py --device <device> --bug SW-XXXXX --json`
4. **Report immediately** — Parse JSON and present:

| Result | Meaning | Report |
|--------|---------|--------|
| `FIX IN BUILD` | Fix is ancestor of device build | **VERIFIABLE** — you can run full verification |
| `LIKELY IN BUILD` | Version-based heuristic | **LIKELY VERIFIABLE** — proceed with caution |
| `FIX NOT IN BUILD` | Fix not in build, or excluded branch | **NOT VERIFIABLE** — need a build that includes the fix |
| `SKIP` | No fix exists (open bug) | **SKIP** — no fix to verify |
| `UNKNOWN` | Fix commit unknown | **UNKNOWN** — cannot determine |

### Output format (compact)

Parse JSON from `build_check.py --json`. Include branch info from the recipe:

```
## Build Check: SW-XXXXX on <Device>

| Field | Value |
|-------|-------|
| Device | <device> |
| Build | <commit>... (branch: <build_branch>) |
| Bug | SW-XXXXX |
| Fix commit | <sha>... (source: recipes) |
| **Valid branches for verification** | <fix_branch> (NOT <excluded_branches> if any) |
| **Result** | **VERIFIABLE** / NOT VERIFIABLE / SKIP / UNKNOWN |
```

**Valid branches for verification** — derived from the recipe's Fix branch and Excluded branches (which branches got the PR):
- **fix_branch** — branch(es) where the fix was merged (e.g. `easraf/flowspec_vpn/wbox_side`, or `rel_v26_1, rel_v25_4`)
- **excluded_branches** — branch(es) that do NOT have the fix (e.g. `dev_v26_2` for SW-238966)
- Report as: `rel_v26_1, rel_v25_4 (NOT dev_v26_2)` or `easraf/flowspec_vpn/wbox_side` when no exclusions
- When **NOT VERIFIABLE**: tell the user "Use a build from: &lt;valid branches&gt;" so they know which image to load

If user wants to run full verification after a VERIFIABLE result, they can say "verify it" or "run verification" — that triggers VERIFY mode.

---

## Mode: INVESTIGATE (full debug session)

## DNOS Command Syntax Validation (MANDATORY)

Before running ANY `run_show_command` that is not in the hardcoded lists below (Phase 0, Phase 3),
**validate it exists** using the Network Mapper MCP CLI documentation tools:

| Tool | When to use | Example |
|---|---|---|
| `search_cli_docs(keyword)` | Find all commands related to a feature or keyword | `search_cli_docs("show flowspec")` |
| `get_cli_doc_section(doc, term)` | Get full syntax details for a specific command | `get_cli_doc_section("SHOW_COMMANDS", "flowspec")` |
| `get_cli_guidelines()` | Get style rules and known error patterns before generating config | `get_cli_guidelines()` |

**When to validate:**
- QUICK mode: always validate the user's requested command before running it
- INVESTIGATE: any show command not already listed in Phase 0 or Phase 3 tables
- VERIFY: any command from a recipe you haven't seen before
- Any command with dynamic arguments (process names, VRF names, NCP IDs)

**For dynamic arguments** (e.g., which process names work with `show system process <name>`):
check `~/.cursor/dnos-cli-completions.json` first, then query the device if not cached.

**Full protocol:** `~/.cursor/rules/dnos-cli-completion-protocol.mdc`

---

## Required Context

Load these files for full methodology:
- **Rules:** `~/.cursor/rules/debug-dnos.mdc`
- **Skill:** `~/.cursor/skills/dnos-debug-methodology/SKILL.md`
- **Known Gotchas** quick-reference: `~/.cursor/skills/dnos-debug-methodology/sections/gotchas.md`

## Agent Reading Pattern

**Always read first:**
1. `~/.cursor/rules/debug-dnos.mdc`
2. `~/.cursor/skills/dnos-debug-methodology/SKILL.md`

**Read as needed:**
3. `~/.cursor/skills/dnos-debug-methodology/sections/gotchas.md` -- fast triage, post-ISSU retest flow, workflow lessons
4. `~/.cursor/skills/dnos-debug-methodology/sections/phase-procedures.md` -- phase workflow, session logging, verification, learning
5. `~/.cursor/skills/dnos-debug-methodology/sections/trace-patterns.md` -- trace files, pipe filters, feature keywords, proven grep patterns
6. `~/.cursor/skills/dnos-debug-methodology/sections/flowspec-behavior.md` -- FlowSpec / FlowSpec-VPN action rules, TCAM, local-policy semantics
7. `~/.cursor/skills/dnos-debug-methodology/sections/code-navigation.md` -- source-file map, branch-aware code search, config-desync analysis

## Session Startup

Ask the user:
1. **Which device?** (use `list_devices` to show available devices)
2. **What feature/problem?** (e.g., "FlowSpec rule not in datapath", "route missing from VRF", "EVPN not working")
3. **What's the expected vs actual behavior?**
4. **Which code branch for investigation?** (default: `easraf/flowspec_vpn/wbox_side` for FlowSpec, or "current branch" to use whatever is checked out in `cheetah_26_1/`)

---

## Session Logging Protocol (MANDATORY for INVESTIGATE and VERIFY modes)

Every INVESTIGATE and VERIFY session persists ALL raw `run_show_command` outputs to a session log file. This ensures no data is lost if the chat ends, and provides raw evidence for bug filing.

**QUICK mode does NOT create a session log** (too lightweight).

### Step 1: Create Session File

Immediately after Session Startup (before Phase 0), create the session log:

- **Path:** `~/SCALER/FLOWSPEC_VPN/debug_sessions/SESSION_<YYYY-MM-DD>_<HHMM>_<DEVICE>_<short-topic>.md`
- **short-topic:** 2-4 word slug from the problem description (e.g., `flowspec-missing`, `redirect-unreachable`, `tcam-overflow`)
- Use the Write tool to create the file with this header:

```markdown
# Debug Session: <DEVICE> -- <short description>
Started: <YYYY-MM-DD HH:MM:SS> UTC | Device: <DEVICE>
Image: (filled after Phase 0)
Topic: <user's problem description>
Session mode: INVESTIGATE | VERIFY

---

```

Store the session file path in your working memory as `SESSION_LOG_PATH`.

### Step 2: Append Every Device Command Output

**After every device interaction**, immediately append the output to the session log. This includes:

| Tool / Method | Log it? | Prefix in log |
|---------------|---------|---------------|
| `run_show_command` | YES | `[show]` |
| `device_shell_execute` | YES | `[shell]` |
| `get_device_config` | YES | `[config]` |
| `get_device_interfaces` | YES (if used for diagnosis) | `[interfaces]` |
| `get_device_lldp` | YES (if used for diagnosis) | `[lldp]` |
| Local `Shell` tool (Python scripts, git, grep on device data) | YES (if output is diagnostic evidence) | `[local]` |
| `validate_config` | YES | `[validate]` |

Format (use StrReplace to append at end of file):

```markdown

### [HH:MM:SS] [show] <full show command>
```
<raw output exactly as returned>
```

```

For shell/local commands:

```markdown

### [HH:MM:SS] [shell] cat /.gitcommit
```
<raw output>
```

```

- Use the actual wall-clock time (UTC) when the command was run
- Include the FULL raw output -- never truncate, never summarize
- Group under Phase headers when transitioning between phases (e.g., `## Phase 0: Pre-Flight`, `## Phase 3: Traces`)
- After Phase 0, update the `Image:` line in the header with the discovered image version
- Skip logging for routine tool calls that don't produce device evidence (e.g., `list_devices` for device discovery)

### Step 3: Conclude the Session

At Phase 6 (conclusion), append a conclusion block to the session log:

```markdown

---

## Session Conclusion
Ended: <YYYY-MM-DD HH:MM:SS> UTC
Verdict: BUG FOUND | NO BUG | INCONCLUSIVE
Bug file: <BUG_*.md path or "none">
```

### Step 4: Keep or Delete

- **Bug found:** Auto-keep the session log. Add `Session log: ~/SCALER/FLOWSPEC_VPN/debug_sessions/<filename>` to the BUG_*.md header section.
- **No bug found:** Ask the user: "No bug was found. Keep the session log (<filename>) or delete it?"
  - If keep: review the session log and propose which sections contain useful reference data vs routine outputs. Remove the routine sections with user approval.
  - If delete: delete the session file.

### Session Log Directory

```
~/SCALER/FLOWSPEC_VPN/debug_sessions/
  SESSION_2026-02-26_1234_PE-1_flowspec-missing.md
  SESSION_2026-02-25_0900_PE-4_tcam-overflow.md
```

---

## Investigation Flow

### Phase 0: Pre-Flight Health Check

Run before trace analysis (~30s):
- **Image version**: `show system image` — check FULL path (base version + build suffix, e.g. `26.1.0.22_priv...wbox_side_24`). **Never rely on hostname** — it may show the old base version after ISSU.
- **BGP state**: `show bgp summary`, `show bgp ipv4 flowspec summary`
- **FlowSpec NCP**: `show flowspec ncp 0`, `show flowspec-local-policies ncp 0`
- **TCAM capacity**: `show system npu-resources resource-type flowspec`
- **Zebra FlowSpec DB**: `show dnos-internal routing rib-manager database flowspec`
- **Optional (NCP shell)**: `xraycli /wb_agent/flowspec/hw_counters`, `xraycli /wb_agent/flowspec/info`

**Post-ISSU retest?** If retesting a known bug after image upgrade, follow the protocol in `~/.cursor/skills/dnos-debug-methodology/sections/gotchas.md`. Key: ISSU preserves in-memory state (same PID, same NH objects). You MUST trigger a fresh event (withdraw/re-inject, clear BGP) and verify new traces exist before concluding "bug persists."

**Automated alternative**: `python3 ~/SCALER/FLOWSPEC_VPN/fsvpn_wizard.py` — 20+ step diagnostic (BGP, VRF, NCP, HW counters, local policies, IPv6, capacity). Output: pass/fail/warning + flowchart + snapshot. README: `~/SCALER/FLOWSPEC_VPN/FSVPN_WIZARD_README.md`. When wizard finds an issue, use /debug-dnos for deep trace analysis.

### Phase 0.5: Packet Analysis (traffic-not-matched cases)

When debugging "traffic not matched" by FlowSpec or "packets dropped/forwarded wrong":

1. **Capture live traffic** with `/XRAY`:
   ```bash
   python3 ~/live_capture.py -s <interface> -o pcap -f /tmp/debug.pcap -t 30 -y
   ```
2. **Decode packet** with `/SNIFF` to extract FlowSpec-matchable fields:
   ```bash
   python3 ~/.cursor/tools/packet_decoder.py --pcap /tmp/debug.pcap --count 50
   ```
3. Pull installed rules: `show flowspec ncp 0` / `show flowspec-local-policies ncp 0`
4. Cross-match packet fields vs each rule's NLRI; report per-field match/mismatch
5. Check zebra DB: `show dnos-internal routing rib-manager database flowspec` to verify rules reached zebra

### Phase 1: Establish the Symptom
- Run relevant `show` commands on the device to confirm control plane state
- If datapath issue: access NCP traces/xraycli to confirm datapath state
- Document the gap: "Control plane has X, datapath has Y"

### Phase 2: Trigger a Clean Event
- Run `clear bgp neighbor <peer>` or equivalent to create a known timestamp
- Note the exact time for trace correlation

### Phase 3: Trace Every Layer (the core method)
Follow the DNOS pipeline, tracing the data through each component:

```
bgpd ──► zebra (rib-manager) ──► fib-manager ──► NCP wb_agent ──► BCM TCAM
                 │
                 └──► flowspec tracking table (vtysh: show flowspec db)
```

For each layer, use the trace commands:

| Layer | Trace Command |
|-------|--------------|
| bgpd | `show file traces routing_engine/bgpd_traces \| include <keyword>` |
| **zebra DB** | **vtysh**: `show flowspec db` or `show flowspec db vrf <name>` |
| **zebra DB** | **DNOS CLI**: `show dnos-internal routing rib-manager database flowspec` |
| rib-manager | `show file traces routing_engine/rib-manager_traces \| include <keyword>` |
| fib-manager | `show file traces routing_engine/fibmgrd_traces \| include <keyword>` |
| NCP wb_agent | `show file ncp 0 traces datapath/wb_agent.<feature> \| include <keyword>` |
| **vtysh** | `show file traces routing_engine/vtysh_traces \| include <keyword>` |

#### vtysh_traces: First Check for CLI-vtysh Misalignment

For config desync bugs (DNOS `show config` has settings but `show bgp` doesn't reflect them), check `vtysh_traces` FIRST:
```
show file traces routing_engine/vtysh_traces | include "Command not found"
```
This log (added in build 24+) tells you WHICH command was not registered in WHICH AF node, causing the premature `exit-address-family`. One grep = root cause. See `~/.cursor/skills/dnos-debug-methodology/sections/trace-patterns.md` for the focused `vtysh_traces` workflow.

#### FlowSpec Redirect-IP NH: Best Single Grep
```
show file traces routing_engine/fibmgrd_traces | include is_flowspec
```
Shows ALL redirect-IP NH protobuf messages. If `ADD_NEXTHOP` has NO `nexthops` array, NO `vrf_id`, only bare `address` + `is_flowspec: true` + `UNKNOWN_PROTO` — that confirms the VRF-local redirect-IP bug.

#### Zebra FlowSpec DB Check (critical for "rule missing" debugging)

The zebra flowspec tracking table sits between bgpd and fib-manager. This is where bgpd's routes are held before being pushed to FPM/fib-manager:

```bash
# DNOS CLI (no VRF filter, shows all):
show dnos-internal routing rib-manager database flowspec

# vtysh (supports per-VRF filter):
# Enter vtysh: run start shell → password: dnroot → vtysh
show flowspec db                    # all VRFs
show flowspec db vrf <vrf-name>     # specific VRF (e.g., "default", "vrf_customer1")
# Note: "vrf all" is NOT supported — use specific VRF names
```

**Decision tree:**
- Route in bgpd but NOT in zebra DB → problem is bgpd→zebra handoff
- Route in zebra DB but NOT in fib-manager traces → problem is zebra→FPM path
- Route in fib-manager but NOT in NCP → problem is fib-manager→NCP path

**Feature-specific keywords:**

| Feature | bgpd | rib-manager | fib-manager | NCP |
|---------|------|-------------|-------------|-----|
| FlowSpec | `announce_flowspec`, `withdraw_flowspec` | `FIB Flowspec`, `lowspec` | `FLOWSPEC_RULE_ADD`, `FLOWSPEC_RULE_DELETE` | `AddRuleInternal`, `DeleteRuleInternal`, `redirect` |
| Routes | `zebra_announce`, `zebra_withdraw` | `FIB Route Add`, `FIB Route Del` | `ROUTE_ADD`, `ROUTE_DELETE` | varies |
| BGP Session / NOTIFICATION | `NOTIFICATION`, `ADJCHANGE`, `Established`, `Clearing` | N/A | N/A | N/A |
| FlowSpec chain / advertise | `Chain is done`, `Flowspec-VPN`, `send EoR` | N/A | N/A | N/A |

**CRITICAL: `| include` is CASE-SENSITIVE.** `NOTIFICATION` works, `notification` does NOT. See `~/.cursor/skills/dnos-debug-methodology/sections/trace-patterns.md` for tested keywords.

#### DNOS Pipe Filter Reference (confirmed on live devices)

All `show` commands support these pipe operators:

| Operator | Sub-option | Syntax | Description |
|----------|-----------|--------|-------------|
| `include` | `<text>` | `\| include <text>` | Include lines matching plain text |
| `include` | `regex` | `\| include regex <pattern>` | Include lines matching regex |
| `exclude` | `<text>` | `\| exclude <text>` | Exclude lines matching plain text |
| `exclude` | `regex` | `\| exclude regex <pattern>` | Exclude lines matching regex |
| `find` | `<text>` | `\| find <text>` | Find first occurrence of plain text |
| `find` | `regex` | `\| find regex <pattern>` | Find first occurrence matching regex |
| `count` | — | `\| count` | Show number of lines in output |
| `tail` | `<N>` | `\| tail <N>` | Show last N lines |
| `no-more` | — | `\| no-more` | Disable output paging |
| `monitor` | — | `\| monitor` | Refresh and compare to previous output |

**Chaining**: Multiple pipes work left-to-right as AND: `| include X | include Y | exclude Z`

**Regex examples**:
```
show file traces routing_engine/bgpd_traces | include regex "NOTIF.*3/9"
show logging | include regex "Neighbor.*IDLE"
show bgp summary | exclude regex "Idle|Active"
```

**WARNING — ANSI color codes in traces**: Trace output on some devices contains ANSI escape codes (e.g., `\033[91m16:20\033[0m`) that **break pattern matching**. On PE-1, `include 16:20:34` returns EMPTY because the colon between MM and SS falls outside the ANSI-wrapped text. Workaround: **use `HH:MM` (not `HH:MM:SS`) as the timestamp filter**, then narrow with a second `| include`.

**Efficient grep strategy (do NOT guess keywords):**

1. **Start with timestamp (HH:MM only):** `include HH:MM` is safest — `HH:MM:SS` can fail due to ANSI codes on some devices
2. **Then narrow:** `include HH:MM | include NOTIFICATION` for precision
3. **Use regex for complex patterns:** `include regex "NOTIF.*neighbor"` when plain text won't work
4. **Never try:** `notify`, `unsupported`, `Optional`, `unknown`, `malformed` — these return EMPTY (syslog terms, not trace keywords)
5. **If buffer rotated** (empty results for a known event timestamp): stop searching that device, reproduce the bug for fresh traces

**Double-pipe filtering** to narrow by timestamp AND keyword:
```
show file traces routing_engine/bgpd_traces | include 12:24 | include flowspec
```

**No context lines (leading/trailing):** DNOS pipes have NO `-A`/`-B`/`-C` equivalent. `| include` returns matching lines only. `| find` returns from the first match onward (unlimited trailing, no leading, no line count). For surrounding context, use the Linux shell:

```
run start shell
# password: dnroot
grep -B 5 -A 5 "pattern" /core/traces/routing_engine/bgpd_traces
exit; exit   # back to DNOS CLI
```

| grep flag | Meaning | Example |
|---|---|---|
| `-B N` | N lines before (leading) | `grep -B 5 "treat" /core/traces/routing_engine/bgpd_traces` |
| `-A N` | N lines after (trailing) | `grep -A 10 "NOTIFICATION" /core/traces/routing_engine/bgpd_traces` |
| `-C N` | N lines before AND after | `grep -C 3 "bgp_flowspec" /core/traces/routing_engine/bgpd_traces` |

Trace file paths: `bgpd_traces` = `/core/traces/routing_engine/bgpd_traces`, `fibmgrd_traces` = `/core/traces/routing_engine/fibmgrd_traces`, etc. NCP traces: `run start shell ncp <id>` then `/core/traces/datapath/wb_agent*`.

### Phase 3.5: Active Debug on Device (when traces are not enough)

When Phase 3 traces lack detail (e.g., UPDATE content not logged, NLRI bytes not visible), the agent **MUST enable debug flags on the device**, reproduce, collect, then clean up.

**When to use:** Traces show the event (NOTIFICATION, ERROR) but not the payload that caused it. For example: "prefix length 0" but you can't see the actual UPDATE bytes.

**Safety rules:**
- **Always AskQuestion before enabling debug** — "Phase 3 traces show [symptom] but not the payload. I need to enable `debug bgp updates-in` on [device] to capture the UPDATE content. This increases trace verbosity. OK to proceed?"
- **Always clean up after** — remove debug config before finishing, even if the investigation fails
- **Never leave debug enabled** — the agent MUST track what it enabled and remove it
- **Commit is required** — debug config lives under `configure → debug → ...` and needs `commit`
- **Prefer targeted debugs** — use specific flags (e.g., `bgp updates-in`) over broad ones (e.g., `bgp`)

**Available DNOS debug commands** (under `configure → debug`):

| Debug Flag | What It Adds to Traces | When to Use |
|-----------|----------------------|-------------|
| `bgp updates-in` | Incoming UPDATE content (NLRI, attributes, ext-communities) | See what peer sent that caused NOTIFICATION |
| `bgp updates-out` | Outgoing UPDATE content | See what device advertises to peer |
| `bgp fsm` | FSM state transitions (Connect→OpenSent→Established→Clearing) | Session flap timing |
| `bgp events` | General BGP events | Broad BGP investigation |
| `bgp filters` | Route-map/filter decisions | Route not accepted/advertised |
| `bgp policy` | Policy evaluation | Policy not matching |
| `bgp rib` | BGP-RIB install/withdraw messages | Route not installed in RIB |
| `bgp nht` | Next-hop tracking events | Next-hop unreachable |
| `bgp best-path` | Best-path selection | Wrong route selected |
| `bgp keepalives` | Keepalive send/receive | Hold timer expiry |
| `bgp import` | VPN import into VRF | FlowSpec-VPN not imported |
| `bgp export` | VPN export from VRF | Route not exported |

**Workflow:**

```
1. Enable:
   validate_config(device, "debug\n  bgp updates-in\n!\n")
   → If valid, apply via SSH: configure → debug → bgp updates-in → commit → exit

2. Reproduce:
   clear bgp neighbor <peer>   (or wait for next flap)
   Note exact timestamp

3. Collect:
   show file traces routing_engine/bgpd_traces | include <HH:MM>

4. Clean up (MANDATORY):
   configure → debug → no bgp updates-in → commit → exit

5. Verify cleanup:
   show config debug   (should show no bgp debug flags)
```

**Implementation — enable debug via `run_show_command` is NOT possible** (it's config mode). Use `validate_config` to verify syntax, then apply via SSH session using the Network Mapper MCP tools or direct paramiko.

**Tracking:** The agent MUST maintain a mental list of `(device, debug_flag)` pairs enabled during the session and clean ALL of them in Phase 6 or on error.

### Phase 4: Build the Timeline
Cross-correlate all 4 layers by timestamp. Present as a unified timeline showing exactly where data is lost or corrupted.

### Phase 4b: Multi-Device Correlation (VPN routes)
For VPN routes: trace PE-originator → RR → PE-receiver. Use `show bgp ipv4 vpn neighbors <RR> advertised-routes` / `received-routes` per hop. Watch ORIGINATOR_ID, CLUSTER_LIST, VPN labels.

### Phase 5: Code Analysis (branch-aware)
- Checkout the investigation branch in `cheetah_26_1/` (from Session Startup question 4)
- Launch 2 parallel explore sub-agents: control-plane source + datapath source
- Search for the function from the ERROR trace; look at data structures, keys, comparators
- Check Jira epics: find the parent epic + DP enabler sub-epic

### Phase 6: Learn + Produce Deliverables

**BEFORE writing deliverables, update the split debug skill files** (mandatory -- see `SKILL.md` Learning Routing Table for the exact file-to-discovery mapping):

1. Add every grep keyword that **returned results** --> `sections/trace-patterns.md` "Proven Trace Grep Patterns (RETURN)"
2. Add every grep keyword that **returned EMPTY** --> `sections/trace-patterns.md` "Proven Trace Grep Patterns (EMPTY)"
3. New gotcha / false alarm / by-design behavior --> `sections/gotchas.md`
4. New syslog pattern or trace file location --> `sections/trace-patterns.md`
5. New source-file path or code search pattern --> `sections/code-navigation.md`
6. New FlowSpec action / TCAM rule --> `sections/flowspec-behavior.md`
7. New workflow improvement --> `sections/phase-procedures.md`
8. If learning also affects /BGP, /XRAY, /HA --> update their JSON store + run sync

Then produce deliverables:

1. **Short trace-based summary** -- raw timestamps from all layers (as-is, no translation), showing the data flow and where it breaks
2. **Root cause** -- which component, which logic, why
3. **Bug reproduction recipe** -- minimum steps to reproduce with verification commands
4. **Epic context** -- parent epic, DP enabler status, fix ownership (control plane vs datapath)
5. **Bug evidence file** -- save to `~/SCALER/FLOWSPEC_VPN/bug_evidence/BUG_<NAME>.md` with:
   - **Session log**: `~/SCALER/FLOWSPEC_VPN/debug_sessions/<SESSION_FILE>` — link to the full raw session log
   - **Image (discovered)**: FULL path from `show system image` (e.g. `26.1.0.22_priv.easraf_flowspec_vpn_wbox_side_24`)
   - **Retest History table**: `| Date | Image (full path) | Build | Result | Notes |` — append a new row each time the bug is retested after an upgrade. Result = `BUG PRESENT`, `FIX CONFIRMED`, or `STALE STATE` (ISSU, no fresh event triggered).
   - **Expected Results**: One generic sentence — no specific device names/IPs
   - **Actual Results**: One generic sentence — no specific device names/IPs
   - **Steps to Reproduce**: Numbered list with generic terms ("any non-default VRF", "a reachable IP") — never reference specific topology device names, IPs, or VRF names
   - **Jira ticket**: SW-XXXXX (if filed) — link to the Jira ticket
6. **Jira-ready description** -- generate a separate Jira description following the SW-253359 canonical format (see `sections/gotchas.md` "Jira Bug Description Format"):
   - Quote documentation FIRST (README, design doc, RFC)
   - Before/After structure with identical show commands, device prompts, timestamps
   - Traces grouped by NCC/process identity + PID
   - Environment section with full `show system` table
   - NO code-level analysis (no function names, source files, line numbers)
   - Expected/Actual/Steps generic
   - Tech-support tarball link if available
   - Present to user as a ready-to-paste Jira description
7. **Topology JSON** -- generate a topology editor JSON file from the investigation:
   - Save as `~/SCALER/FLOWSPEC_VPN/bug_evidence/BUG_<NAME>.topology.json`
   - Reference the `.topology.json` file in the bug evidence `.md` under a collapsible section (do NOT embed the full JSON inline)
   - Use the Topology JSON Template below — follow ALL visual standards (z-order, VRF panels, IP TBs, no BUG: labels)
   - **Topology app**: Run `python3 ~/CURSOR/serve.py` and open http://localhost:8080 → Topologies → Load Debug-DNOS... to see all bug topologies. Or use File → Load from File... with the .json path.

### Topology JSON Template and Layout Conventions

**Format:** Compatible with `~/CURSOR/` topology editor. Structure: `{ "version": "1.0", "objects": [...], "metadata": {...} }`.

#### Pre-Creation Checklist (MANDATORY — do BEFORE writing any topology JSON)

**Failure to follow this checklist caused incorrect topologies in the past. Every step is required.**

1. **Identify the PRIMARY bug** — ask: "What is the ONE thing that is broken?" If the bug has multiple gates/checks in code, the topology must describe the one the user reports. Example: "redirect target excluded due to missing RD" is the primary bug; "VPN import rejected" is a secondary effect of the same underlying check — do NOT put the secondary effect in the topology.
2. **Re-read the bug evidence `.md` file** — specifically the Expected/Actual sections. The VRF panel text in the topology JSON MUST describe the exact same symptom as the `.md` file. If they diverge, the topology is wrong.
3. **Use `show` command language, not code internals** — VRF panel text should describe what the user would see in `show` command output. Good: "Redirect target: selected", "No flows found in VRF". Bad: "BGP_CONFIG_RD not set", "match_vrf_from_rt returns NULL", "Cancel import due to invalid service state".
4. **For comparison bugs** (A works, B doesn't): both panels must show (a) what configuration differs (e.g., "RD configured" vs "No RD"), (b) the result from the user's perspective (e.g., "Redirect target: selected" vs "Redirect target: excluded"), and (c) the route info box must include the action that triggers the comparison (e.g., `redirect 888:888`).
5. **Verify no code-level leakage** — scan the JSON for function names, file names, line numbers, protobuf fields, BGP_CONFIG flags, vrf_ids. If any appear, remove them. The topology is a network diagram, not a code report.

#### Supported Object Types

| Type | Purpose | Key Properties |
|------|---------|---------------|
| `device` | Network devices | `deviceType`, `visualStyle`, `label`, `color`, `radius` |
| `link` | Connections between devices | `device1`, `device2`, `style`, `linkDetails` |
| `text` | Labels, annotations, info boxes | `text`, `fontSize`, `showBackground`, `linkId` |
| `shape` | Visual markers (cross, checkmark, rectangle, arrow, cloud) | `shapeType`, `fillColor`, `strokeColor` |

#### Device Visual Styles

| Style | Use For |
|-------|---------|
| `classic` | PEs, RRs (3D cylinder) |
| `server` | ExaBGP, test tools |
| `simple` | CEs, leaf nodes |
| `circle` | Default |
| `hex` | Special nodes |

#### Device Labels = Name Only, IP as Separate TB

**CRITICAL:** Device label is ONLY the device name. IP address goes in a separate text object positioned below the device label:
```json
{ "label": "PE-1" }
```
Then a separate text:
```json
{ "type": "text", "x": 350, "y": 370, "text": "1.1.1.1", "fontSize": 10, "color": "#85929e", "showBackground": false }
```
Position the IP text at `y = device_y + device_radius + 30` to sit below the label without overlap.

#### Link Styles

| Style | Use For |
|-------|---------|
| `arrow` | Primary route injection path (ExaBGP → PE) — width 3 |
| `solid` | iBGP sessions — width 2 |
| `dashed` | CE-PE eBGP, secondary paths — width 2 |
| `dotted` | Optional/inactive paths |

#### Text on Links (TB with No Background)

**MANDATORY:** Every link MUST have a text box attached at its midpoint showing the protocol. Use these properties to create a TB with no background on the link:

```json
{
  "id": "text_X", "type": "text",
  "x": 250, "y": 275,
  "text": "eBGP FlowSpec-VPN\nSAFI 133 + 134",
  "fontSize": 11, "color": "#2ecc71",
  "linkId": "link_0",
  "position": "middle",
  "_onLinkLine": true,
  "showBackground": false
}
```

- `linkId` — references the link this text belongs to
- `position: "middle"` — positions at link midpoint
- `_onLinkLine: true` — creates a gap in the link line where text sits
- `showBackground: false` — transparent background (TB style)
- Text content: protocol type, AFI/SAFI, ASN info (e.g. "iBGP FlowSpec-VPN", "eBGP ipv4-unicast\nAS 65100")

#### VRF Panels (Rectangle Shape + Text)

VRFs are represented as **rectangle shapes** (visual containers) with text on top. The rectangle goes in the mid-layer (between links and text), text sits on top of it:

Rectangle shape (container):
```json
{ "type": "shape", "shapeType": "rectangle", "x": 350, "y": 185, "width": 260, "height": 88,
  "fillColor": "#e74c3c", "fillOpacity": 0.05, "fillEnabled": true,
  "strokeColor": "#c0392b", "strokeWidth": 1.5, "strokeEnabled": true, "cornerRadius": 10 }
```

Text on top (no showBackground — the shape IS the background):
```json
{ "type": "text", "x": 350, "y": 185,
  "text": "VRF ALPHA on PE-1\nRD 1.1.1.1:100  RT 100:100\n10.0.0.230 reachable via CE\nRedirect NH: (unreachable)",
  "fontSize": 10, "color": "#e74c3c", "showBackground": false }
```

Same x,y for both so text is centered inside the rectangle. Use green (`#2ecc71`) for passing VRFs, red (`#e74c3c`) for failing.

#### Route Info Box (Near ExaBGP)

The injected route — concise match/action, subtle bordered box:

```json
{
  "type": "text", "x": 100, "y": 180,
  "text": "dst 100.100.100.1/32\nsrc 16.16.16.0/30\nredirect-ip 10.0.0.230",
  "fontSize": 10, "color": "#f0b27a",
  "showBackground": true, "backgroundColor": "rgba(230,126,34,0.08)",
  "backgroundOpacity": 60, "showBorder": true, "borderColor": "rgba(230,126,34,0.4)", "borderWidth": 1
}
```

**Must include "Route Injected:" header** so the user knows what this box represents. Include NLRI match fields, action, RD, RT.

#### NO "BUG:" Annotation in Topology

**Do NOT add a "BUG:" text label to the topology JSON.** The topology shows the setup and the symptom visually — VRF info boxes with colored borders and cross/checkmark shapes convey pass/fail. The bug analysis belongs only in the `.md` file.

**NEVER include in topology JSON:** "BUG:" labels, function names, file names, protobuf fields, vrf_ids, code-level root cause.

#### Shape Markers (MUST Be LAST in Objects Array)

**CRITICAL: Shapes must be the LAST objects in the array for highest z-order (drawn on top of everything).**

| Shape | Use For | Color |
|-------|---------|-------|
| `cross` (X) | Bug failure point | `#e74c3c` red, opacity 1.0 |
| `checkmark` | Working/passing element | `#2ecc71` green, opacity 1.0 |

Shape example (always at end of objects array):
```json
{ "id": "shape_0", "type": "shape", "shapeType": "cross", "x": 640, "y": 85, "width": 26, "height": 26, "rotation": 0, "fillColor": "#e74c3c", "fillOpacity": 1.0, "fillEnabled": true, "strokeColor": "#c0392b", "strokeWidth": 2, "strokeEnabled": true }
```

Position shapes in clear space next to their referenced element, not overlapping text.

#### Layout Rules

- Horizontal flow: ExaBGP left → PEs center → RR/downstream right
- Spacing: 250px between devices horizontally
- **IP text:** `y = device_y + radius + 30` (below device label)
- VRF text: ~85px above device center, no background
- CE devices: 210px below their PE
- Bug annotation: top area (y=80–100), no background, bold
- Route info: near ExaBGP, y=170–180, subtle border
- **No overlap:** ensure minimum 40px vertical gap between text elements

#### Object Array Order (Z-Order)

**Objects are drawn in array order — later = on top.** Always use this layered order:

1. **Devices** (bottom layer)
2. **Links**
3. **Container shapes** — rectangle shapes for VRF panels and route box (mid layer, behind text)
4. **Text objects** — IPs, link protocols, VRF info, route info (on top of container shapes)
5. **Marker shapes LAST** — cross/checkmark (highest layer, always visible on top of everything)

#### Color Scheme

| Element | Color | Hex |
|---------|-------|-----|
| DUT (PE) | Blue | `#3498db` |
| Test tools (ExaBGP) | Orange | `#e67e22` |
| Route Reflectors | Purple | `#9b59b6` |
| CEs | Green | `#2ecc71` |
| Bug annotation | Red bold | `#e74c3c` |
| IP addresses | Muted gray | `#85929e` |
| VRF info | Light gray | `#d5dbdb` |
| Link-on-text (iBGP) | Light blue | `#85c1e9` |
| Link-on-text (eBGP) | Green | `#2ecc71` or `#58d68d` |

#### What NOT to Include in Topology JSON

The topology is a visual diagram, not a code report:
- **NO** function names, file names, line numbers
- **NO** protobuf field names (vrf_id, nexthops[], ADD_NEXTHOP)
- **NO** internal IDs (vrf_id, inst_id, BGP_CONFIG flags)
- **NO** code-level root cause analysis
- **YES** device names + IPs, protocols, VRF/RD/RT, the route, the symptom

#### Complete Example

```json
{
  "version": "1.0",
  "objects": [
    { "id": "device_0", "type": "device", "deviceType": "router", "x": 120, "y": 300, "radius": 30, "color": "#e67e22", "label": "ExaBGP", "locked": false, "visualStyle": "server" },
    { "id": "device_1", "type": "device", "deviceType": "router", "x": 420, "y": 300, "radius": 40, "color": "#3498db", "label": "PE-1", "locked": false, "visualStyle": "classic" },

    { "id": "link_0", "type": "link", "originType": "QL", "device1": "device_0", "device2": "device_1", "start": {"x": 150, "y": 300}, "end": {"x": 380, "y": 300}, "color": "#2ecc71", "style": "arrow", "width": 3 },

    { "id": "text_0", "type": "text", "x": 120, "y": 358, "text": "100.64.6.134", "fontSize": 10, "color": "#85929e", "showBackground": false },
    { "id": "text_1", "type": "text", "x": 420, "y": 368, "text": "1.1.1.1", "fontSize": 10, "color": "#85929e", "showBackground": false },
    { "id": "text_2", "type": "text", "x": 270, "y": 278, "text": "eBGP FlowSpec-VPN", "fontSize": 10, "color": "#2ecc71", "linkId": "link_0", "position": "middle", "_onLinkLine": true, "showBackground": false },
    { "id": "text_3", "type": "text", "x": 120, "y": 155, "text": "Route Injected:\ndst 1.2.3.0/24\nredirect-ip 10.0.0.1\nRD 1.1.1.1:100  RT 100:100", "fontSize": 10, "color": "#f0b27a", "showBackground": true, "backgroundColor": "rgba(230,126,34,0.08)", "backgroundOpacity": 60, "showBorder": true, "borderColor": "rgba(230,126,34,0.4)", "borderWidth": 1 },
    { "id": "text_4", "type": "text", "x": 600, "y": 185, "text": "VRF ALPHA on PE-1\nRD 1.1.1.1:100  RT 100:100\n10.0.0.1 reachable via CE\nRedirect NH: (unreachable)", "fontSize": 10, "color": "#e74c3c", "showBackground": true, "backgroundColor": "rgba(231,76,60,0.06)", "backgroundOpacity": 50, "showBorder": true, "borderColor": "rgba(231,76,60,0.35)", "borderWidth": 1 },

    { "id": "shape_0", "type": "shape", "shapeType": "cross", "x": 730, "y": 148, "width": 26, "height": 26, "fillColor": "#e74c3c", "fillOpacity": 1.0, "fillEnabled": true, "strokeColor": "#c0392b", "strokeWidth": 2, "strokeEnabled": true }
  ],
  "metadata": { "deviceIdCounter": 2, "linkIdCounter": 1, "textIdCounter": 5, "shapeIdCounter": 1, "description": "ExaBGP → PE-1, VRF ALPHA redirect-ip unreachable" }
}
```

Links require `originType: "QL"`, `device1`, `device2`, `start`, `end`.

## FlowSpec-VPN Action Quick Reference

Before investigating a "rule not installed" or "wrong action" issue, check if the behavior is **by design**:

| If you see... | It means... | Not a bug? |
|---------------|-------------|------------|
| RT-Redirect + Redirect-IP both in rule | Only RT-Redirect applied, Redirect-IP silently ignored | Yes (SW-206876) |
| Drop (rate=0) + RT-Redirect both in rule | DP rejects entire rule as unsupported | Yes (SW-48486) |
| Redirect-IP via 0x010c (ext-community) | DNOS only supports 0x08 (NH in MP_REACH_NLRI) | Yes — deferred |
| Multiple VRFs match redirect RT | First VRF alphabetically selected | Yes (SW-61695) |
| Redirect to default VRF from NDVRF | Not supported | Yes (SW-206889) |
| Redirect-IP NH resolves via MPLS tunnel | NCP skips redirect action, shows `Redirect-ip-nh: N/A` | Yes (SW-41148) — redirect-ip only supports direct L3 NH, per draft-02 |
| Stale redirect target after VRF RT change | Known bug — `clear bgp neighbor` to force re-eval | Bug (SW-240206) |
| NOTIFICATION 3/9 flap loop after FlowSpec-VPN UPDATE | PE rejects `0x01 0x0c` ext-community in SAFI 134 (kills session), but accepts it in SAFI 133 (logs "unknown") | Bug — SAFI 134 parsing path missing graceful handling (2026-02-12) |

**Full reference**: See `~/.cursor/skills/dnos-debug-methodology/sections/flowspec-behavior.md` for complete rules, supported drafts, and combination matrix.

## CLI Audit Trail (Who Changed the Config?)

When config is mysteriously missing or the candidate is dirty, use the CLI trace log to find who did it:

```bash
# Show ALL non-show commands (the real audit trail):
show file traces routing_engine/cli | include regex "Execute command" | exclude show

# Search for specific config changes:
show file traces routing_engine/cli | include regex "Execute command.*protocols"
show file traces routing_engine/cli | include delete
show file traces routing_engine/cli | include regex "no isis|no bgp|no interfaces"
show file traces routing_engine/cli | include commit
show file traces routing_engine/cli | include rollback
show file traces routing_engine/cli | include load
show file traces routing_engine/cli | include configure

# From Linux shell (more flexible grep):
cat /core/traces/routing_engine/cli | grep "Execute command"
```

**What the trace shows:**
- `User-id: <user>` — who ran the command
- `MainThread: <PID>` — session PID (same PID = same CLI session)
- Timestamp — when the command ran
- Full command text — exactly what was typed

**Common patterns:**
- `configure` → `save` → `request file upload` → `exit` = automated config backup (e.g., monitorAPP)
- `configure` → `no <feature>` = someone deleted config from candidate
- `configure` → `commit` = config was committed to running
- `configure` with no matching `exit` = session still in config mode (candidate may be dirty)

**Tip**: Use `| include regex "Execute command" | exclude show` to filter out show commands and see only actual operations.

## Key Principles

- **Never assume where the bug is** -- prove it with traces from EVERY layer
- **Start at both ends** (bgpd + NCP), then narrow the middle
- **ERROR logs are gold** -- they mark the exact failure point
- **Count and compare** -- if bgpd sends 2 but NCP receives 1, something dropped one
- **VRF IDs may differ** between control plane and datapath -- correlate by NLRI and timestamp
- **Check the DP enabler** -- if NCP already has the fields, the bug is upstream in control plane

## Execution Strategy: Direct Parallel Calls vs Sub-Agents

**Key rule: Use `run_show_command` directly from the parent agent. Do NOT launch sub-agents for device commands.**

The parent agent can call multiple `run_show_command` MCP tools in a single message batch. This is faster and cheaper than sub-agents because: no startup overhead, no context duplication, results come back directly.

**Sub-agents are ONLY for Phase 5 (code analysis)** — they need multi-step reasoning across files.

| Phase | How to Execute | Why |
|-------|---------------|-----|
| Phase 0 (Pre-Flight) | **Direct**: batch 4 `run_show_command` calls in one message | No reasoning needed, just collect output |
| Phase 0.5 (Packet) | **Direct**: `run_show_command` or Shell for pcap decode | Single device, single task |
| Phase 3 (Traces) | **Direct**: batch 2-4 `run_show_command` calls per device | Grep is just pattern matching, no reasoning |
| Phase 4b (Multi-Device) | **Direct**: batch `run_show_command` calls across devices | Same — just collecting output from multiple devices |
| Phase 5 (Code Analysis) | **Sub-agent**: 1-2 `explore` agents (default model) | Needs multi-step reasoning about data structures and logic |

### Phase 0: Pre-Flight (4 parallel direct calls)

Call all 4 in ONE message batch:

```
run_show_command(device, "show bgp summary")
run_show_command(device, "show bgp ipv4 flowspec summary")
run_show_command(device, "show flowspec ncp 0")
run_show_command(device, "show system npu-resources resource-type flowspec")
```

Then in a second batch if needed:
```
run_show_command(device, "show flowspec-local-policies ncp 0")
run_show_command(device, "show dnos-internal routing rib-manager database flowspec")
```

For per-VRF zebra inspection (vtysh `show flowspec db vrf <name>`), use interactive SSH:
`run start shell` → password `dnroot` → `vtysh` → `show flowspec db vrf <name>` → `exit` × 3.
Only needed when Phase 0 finds a VRF-specific discrepancy.

### Phase 3: Trace Greps (2-4 parallel direct calls)

Call `run_show_command` with trace grep commands in parallel. **Use proven keywords only** (see `~/.cursor/skills/dnos-debug-methodology/sections/trace-patterns.md`):

```
run_show_command(device, "show file traces routing_engine/bgpd_traces | include HH:MM")
run_show_command(device, "show file traces routing_engine/rib-manager_traces | include HH:MM | include FIB")
run_show_command(device, "show file traces routing_engine/fibmgrd_traces | include HH:MM | include FLOWSPEC")
run_show_command(device, "show file ncp 0 traces datapath/wb_agent.flowspec | include HH:MM")
```

### Phase 5: Code Analysis (sub-agents — only phase that needs them)

Launch 1-2 `explore` sub-agents at default model:

| Agent | Search Scope | What to Find |
|-------|-------------|--------------|
| Control-plane | `cheetah_26_1/services/control/quagga/` | Function from ERROR trace, data structures, comparators |
| Datapath | `cheetah_26_1/src/wbox/src/flowspec/` | TCAM programming logic, rule add/delete, VRF handling |

**Optimization:** If Phase 3 already identified which side lost the data, launch only 1 agent.

**Efficiency rules:**
- Check early-exit rules after Phase 0 and Phase 3 (TCAM full / BGP down = stop early)
- Never re-run a show command already executed in an earlier phase
- **NEVER guess trace keywords.** Only use keywords from `~/.cursor/skills/dnos-debug-methodology/sections/trace-patterns.md`. If unsure, grep by timestamp first (`include HH:MM`), then narrow.
- **One smart grep > five blind greps.** A single `include 12:24:02` returns the full picture.
- **Trace output is raw — present it as-is.** Never translate, simplify, or strip metadata from trace lines. The user needs source file, function name, PID, and sequence numbers.

Phases 1, 2, 4, 6-7 remain sequential (require user input or synthesis of prior results).

## Branch Context

- Investigation branch is set during Session Startup (question 4)
- Default for FlowSpec: `easraf/flowspec_vpn/wbox_side`
- Before Phase 5, ensure `cheetah_26_1/` is on the correct branch: `git fetch origin <branch> && git checkout <branch>`
- If user skips or says "current", use whatever is already checked out

---

## Mode: VERIFY (Bug Fix Verification)

When the user asks to verify a bug fix, verify on a device, or verify a build:

### Step 1: Parse + Resolve Targets

- **Single bug**: Extract `SW-XXXXX`. Ask user for device if not specified.
- **Epic**: `atlassian_jira_search` with JQL `parent = SW-XXXXX AND status = Closed AND resolution = Fixed`. Collect all matching bug keys.
- **Build**: Run `build_check.py --device <device> [--bug SW-XXXXX | --all-recipes]` to get build commit and filter bugs by ancestry. Or use `device_shell_execute(device, "cat /.gitcommit")` + `git merge-base --is-ancestor` manually.

### Step 2: Build Compatibility Check

For each bug, determine if the fix is in the device's running build using the **exact git commit** from the device.

#### Preferred: Use build_check.py (automated)

```bash
python3 ~/SCALER/FLOWSPEC_VPN/bug_evidence/build_check.py --device <device> --bug SW-XXXXX --json
```

Returns JSON with: `result`, `build`, `build_branch`, `fix_commit`, `fix_branch`, `excluded_branches`, `fix_versions`. Use `fix_branch` and `excluded_branches` to report **Valid branches for verification** to the user.

For all recipes at once: `--all-recipes`

The script fetches the device's `/.gitcommit`, resolves the fix from VERIFY_RECIPES.md or git log, and runs `git merge-base --is-ancestor`. Use this as the first step in VERIFY mode.

**SW-238966 caveat:** The recipe formerly listed `ffa5846` as the fix commit; that is SW-230334 (disk usage), not SW-238966. The script now uses version + branch check: fix is in rel_v25_4 (v25.4.13+) and rel_v26_1 (v26.1+). Builds on dev_v26_2 do NOT have the fix (verified 2026-03-07 via bgp_nsr.c source inspection). Do not rely on ancestry check for SW-238966.

#### Manual fallback (if build_check.py unavailable)

**Get the device's build commit** (do this ONCE per device per session):

```
device_shell_execute(device, "cat /.gitcommit")
```
Returns: `<commit_hash>-<branch_name>` (e.g., `302f8d9908a793fdcf90e8f29e68164fba33819d-easraf/flowspec_vpn/wbox_side`)

**Fallback** (if port 2222 fails): SSH port 22 → `run start shell` → password `dnroot` → `cat /.gitcommit` → `exit`

**Check if a fix is in the build** (per bug):

1. Get fix commit hash from `VERIFY_RECIPES.md`, or search local git: `git log --oneline --grep="SW-XXXXX"` in `cheetah_26_1/`
2. Run ancestry check:
   ```bash
   cd ~/cheetah_26_1 && git merge-base --is-ancestor <fix_commit> <build_commit>
   echo $?   # 0 = fix IS in build, 1 = fix is NOT in build
   ```

This is **deterministic** — no date guessing. The fix commit is either an ancestor of the build commit or it isn't.

#### Decision per bug

| Status | Condition | Action |
|--------|-----------|--------|
| **VERIFIABLE** | `git merge-base --is-ancestor` returns 0 | Proceed with recipe |
| **SKIP (no fix)** | Recipe says `Fix commit: not yet fixed` or `open bug` | **Auto-skip — do NOT run verification** |
| **SKIP (newer build needed)** | `git merge-base --is-ancestor` returns 1 (fix not in build) | Skip, tell user which build they need |
| **UNKNOWN** | No fix commit found in recipe, git, or Jira | Ask user before proceeding |

**CRITICAL: Never verify bugs with no fix.** If `VERIFY_RECIPES.md` says `not yet fixed` or `open bug`, skip immediately with one line: `SW-XXXXX: SKIP (no fix exists)`. Do not waste device commands on known-unfixed bugs.

**Immediate stop:** When build check returns `FIX NOT IN BUILD`, `SKIP`, or `UNKNOWN` (and no fix commit), report the result and **stop**. Do not proceed to recipe loading or execution. The user gets an immediate answer.

**Always include valid branches:** When reporting build compatibility, include **Valid branches for verification** from the recipe (Fix branch + Excluded branches). Example: "Valid for verification: rel_v26_1, rel_v25_4 (NOT dev_v26_2)". When NOT VERIFIABLE, tell the user: "Use a build from: &lt;valid branches&gt;".

**Proceed only when:** Result is `FIX IN BUILD` or `LIKELY IN BUILD`. Then present the compatibility table (if multiple bugs) or proceed directly to Step 3.

### Step 3: Load or Build Verification Recipe

**Priority order** (first match wins):

1. **VERIFY_RECIPES.md** (`~/SCALER/FLOWSPEC_VPN/bug_evidence/VERIFY_RECIPES.md`) — saved recipe with exact show commands + pass/fail patterns. Instant replay.
2. **BUG_*.md evidence file** — extract "Verification Commands" or "Steps to Reproduce" + "Expected/Actual Results" sections.
3. **Jira description** — parse reproduction steps, extract show commands from description/comments via `atlassian_jira_get_issue`.
4. **Auto-infer from component** — use `~/.cursor/skills/dnos-debug-methodology/sections/gotchas.md` plus `~/.cursor/skills/dnos-debug-methodology/sections/trace-patterns.md` to generate show commands based on bug component.

If no recipe can be built from any source, **ask the user**: "I found no saved recipe for SW-XXXXX. The Jira description mentions [X]. What show commands should I run to verify the fix?"

### Step 4: Pre-Flight

Before executing the recipe:

1. **Create session log** — follow the Session Logging Protocol (same as INVESTIGATE). Path: `SESSION_<date>_<device>_verify-SW-XXXXX.md`
2. Confirm device is reachable: `run_show_command(device, "show system")`
3. Confirm build matches (from Step 2)
4. If recipe requires config, run `validate_config` first. **Ask user permission** before applying any config.

### Step 5: Execute Recipe

Run recipe steps using **direct parallel `run_show_command` calls** (same as INVESTIGATE Phase 0):

- Batch 3-4 show commands per message for speed
- If config is required and user approved: apply config, wait, then run verification show commands
- For config-based verifications, prefer a single comprehensive paramiko script over iterative manual steps
- Collect raw output per step — this is the proof

**Config-based verification rules (learned from SW-239537, SW-242121):**

- **Per-AF checks**: Always use `show bgp neighbors X | include regex "address family:|<keyword>"` with section headers. NEVER trust `show bgp ipv4 <af> neighbors X | include <keyword>` alone — it shows ALL AFs.
- **clear bgp syntax**: `clear bgp ipv4 flowspec-vpn neighbor X` does NOT work. Use `clear bgp neighbor X` (hard) or `clear bgp neighbor X soft in` (soft).
- **excess-discard**: Requires hard BGP reset to trigger. Soft reconfig does NOT re-evaluate already-accepted routes.
- **New route-policy**: Must attach with `()` — `policy NAME() in`, not `policy NAME in`.
- **Script template**: See `VERIFY_RECIPES.md` "Verification Script Best Practices" section for paramiko template.
- **One script, one run**: Write one comprehensive script covering apply → verify → trigger → check → cleanup. Iterative rewrites waste 5+ minutes each.

### Step 6: Verdict

For each step, apply pass/fail criteria from the recipe:

| Verdict | Condition |
|---|---|
| **FIX CONFIRMED** | All pass criteria met, no fail criteria triggered |
| **BUG PRESENT** | Any fail criterion triggered |
| **INCONCLUSIVE** | Pass criteria not met but fail criteria also not triggered (e.g., feature not configured on device, stale state from ISSU) |

### Step 7: Present Proof in Chat + Generate Jira Comment

**Two outputs are always produced:**

1. **Chat summary** — concise markdown for the user in chat
2. **Jira comment** — Jira wiki markup ready to paste, following the standard in `~/.cursor/rules/jira-verification-comment-format.mdc`

**Chat summary (single bug):**

```
### SW-XXXXXX: Short Title — FIX CONFIRMED

Device: PE-1 | Image: 26.1.0.24_...build_26

Step 1: show bgp ipv4 flowspec summary
  Result: PASS — "Established" found
  [raw output snippet]

Step 2: show flowspec ncp 0
  Result: PASS — no "(unreachable)" found
  [raw output snippet]

Verdict: FIX CONFIRMED (2/2 steps passed)
```

**Chat summary (multi-bug):**

```
Verification Results on PE-1 (build 26):
- SW-211921: FIX CONFIRMED (IRB flap twice)
- SW-222730: BUG PRESENT (vtysh ambiguous in VRF scope)
- SW-240206: SKIP (fix not in build)
- SW-248123: INCONCLUSIVE (feature not configured)
```

**Jira comment (MANDATORY for every verified bug):**

After the chat summary, generate the Jira wiki markup inside a **plain markdown code block**
(triple backticks, no language tag) so the user can copy the entire block and paste it
directly into Jira's comment editor. The content renders identically to the SW-243977
canonical comment (Yarel Or, focusedCommentId=903241).

Follow the exact format in `~/.cursor/rules/jira-verification-comment-format.mdc`:

- `h3.` headings for each Proof section (numbered: Proof 1, Proof 2, Proof 3...)
- `{noformat}...{noformat}` touching the first/last line of raw CLI output
- `||double pipes||` for table headers, `|single pipes|` for data rows
- `{{double braces}}` for inline code
- `*asterisks*` for bold (Device, Image, Overall, verdict)
- Verdict Table always last: `||Criterion||Expected (PASS)||Observed||Result||`
- Final row: `|*Overall*| | |*FIX CONFIRMED*|` or `|*Overall*| | |*BUG PRESENT*|`
- NO cleanup, NO script details, NO analysis paragraphs -- factual sentences only

### Step 8: Self-Learn (Mandatory)

After each verification:

1. **Save/update recipe** in `VERIFY_RECIPES.md` — append history row if recipe exists, create new entry if first time
2. **Update BUG_*.md** Retest History table if an evidence file exists for this bug
3. **Update the relevant split debug skill file** if a new trace keyword or gotcha was discovered during verification
4. **If recipe was auto-inferred** (from Jira/git/component), save it to `VERIFY_RECIPES.md` so next time it's instant replay

### Key Principles

- **No guessing** — if no recipe source exists, ask the user
- **Config-optional** — many bugs verifiable via show commands alone
- **Idempotent** — never change device state unless recipe requires config + cleanup, and always ask permission first
- **Build-aware** — always check if fix is in the running build before executing
- **Fast** — parallel `run_show_command` calls, no sub-agents for device commands
- **Self-learning** — every verification saves its recipe for instant replay next time

---

## Bug Evidence Directory

All saved bug findings live in `~/SCALER/FLOWSPEC_VPN/bug_evidence/`.

**Naming convention:** `BUG_<SHORT_NAME>.md`

**Required sections in every bug evidence file:**
1. Header: title, date, devices, image, branch, severity, component
2. Retest History table (append-only)
3. One-Line Summary
4. **Expected Results** (generic, no topology-specific details)
5. **Actual Results** (generic, no topology-specific details)
6. **Steps to Reproduce** (generic minimum steps, no mention of specific device names/IPs)
7. VRF / Test Setup configuration
8. Symptom: raw `show` command outputs with timestamps
9. NH Resolution / Route checks with timestamps
10. BGP table outputs with timestamps
11. Topology diagram (ASCII) AND Topology JSON (separate .json file)
12. Raw Trace Evidence: per-device, per-layer, with full timestamps and source file references
13. Comparison table (all tested scenarios side-by-side)
14. Code-Level Root Cause: file, function, line, what's missing
15. Related Bugs

### Expected / Actual / Steps to Reproduce — Rules

These three sections are **MANDATORY** and must be **generic** (no mention of specific topology, device names, or IPs):

**Expected Results:** One sentence. What SHOULD happen. Reference the show command that would confirm it.
> Example: "FlowSpec redirect-ip next-hop is marked (reachable) when the target IP exists as best, fib in the VRF routing table."

**Actual Results:** One sentence. What ACTUALLY happens. State the symptom clearly.
> Example: "FlowSpec redirect-ip next-hop is always marked (unreachable) in any non-default VRF, regardless of SAFI or NH resolution method."

**Steps to Reproduce:** Numbered list. Minimum steps. Use generic terms ("any non-default VRF", "a reachable IP", "a FlowSpec rule") — NOT specific device names, IPs, or VRF names from the test topology.
> Example:
> 1. Configure any non-default VRF with a reachable route to an IP
> 2. Inject a FlowSpec rule with redirect-ip targeting that IP
> 3. Verify `show route vrf <name> <IP>` returns best, fib
> 4. Observe `show flowspec ncp <id>` shows (unreachable)

**Phase 6 must always save to this directory.** RECALL mode reads from it.

**Current bugs:**

| File | Title | Status |
|------|-------|--------|
| `BUG_FLOWSPEC_REDIRECT_IP_UNREACHABLE_VRF.md` | Redirect-IP NH always unreachable in non-default VRF | **Fixed** (SW-242876) — rib-manager protobuf now includes VRF + nexthops. Datapath confirmed on PE-1 build 28. |
| `BUG_FLOWSPEC_REDIRECT_IP_MPLS_NH_SKIPPED.md` | Redirect-IP action skipped when NH resolves via MPLS tunnel | **By Design** — SW-41148 scopes redirect-ip to direct L3 NH only (draft-02: tunnel types "outside its scope"). Reclassified 2026-03-02. |
| `BUG_FLOWSPEC_VPN_VRF_LITE_NO_IMPORT.md` | FlowSpec redirect-to-rt cannot target VRF without RD (VRF-Lite) | Open — `match_vrf_from_rt` excludes VRF-Lite |
| `BUG_CONFIG_DESYNC_BGP_NETWORK_SERVICES.md` | BGP/network-services config desync after commit | Open |
| `BUG_FLOWSPEC_TCAM_RESERVED_LEAK_BURST.md` | TCAM m_reserved leak on burst injection | Open |
| `BUG_FLOWSPEC_TCAM_OVERFLOW_NO_RECOVERY.md` | TCAM overflow with no recovery | Open |
| `BUG_FLOWSPEC_LOCAL_POLICY_RESOURCE_LEAK.md` | Local policy resource leak | Open |
| `BUG_FLOWSPEC_VPN_IPV4_IMPORT_RT_BITMAP.md` | IPv4 import RT bitmap bug | Open |
| `BUG_VPLS_LABEL_POOL_FIB_PRESERVED_CLUSTER.md` | bgp-vpls label pool not carved on cluster -- no operational fix | **Open** (SW-253359) |

---

## Called by /HA (Cross-Command Integration)

When /HA detects an unexpected result during HA testing (routes lost, sessions not recovering,
process restarts), it may invoke /debug-dnos with pre-filled context to skip the startup questions.

Read `~/.cursor/rules/cross-command-integration.mdc` for the shared protocol.

### Pre-Filled Context from /HA

When called from /HA, the following context is already known:

| Field | Source | Example |
|---|---|---|
| Device | /HA locked device | YOR_CL_PE-4 |
| Feature | /HA test scenario | FlowSpec-VPN |
| Timestamp | /HA event trigger time | 11:30 (HH:MM for trace greps) |
| Symptom | /HA diff result | "200 FlowSpec-VPN rules before, 150 after NCC switchover" |
| Expected | /HA known-behaviors.md | "Rules retained in NCP TCAM during NCC switchover" |
| Actual | /HA after-snapshot | "50 rules missing from NCP, BGP session recovered" |

### Skip Session Startup

When invoked from /HA with pre-filled context:
1. **Skip questions 1-3** (device, feature, expected/actual already provided)
2. **Use question 4 default** (branch = "current" unless specified)
3. **Go straight to Phase 0** with the /HA-provided device
4. **Start trace greps at the /HA timestamp** (Phase 3 uses the event time directly)

### Report Findings Back

After investigation:
1. Save findings to bug evidence file as usual
2. Append summary to /HA session log at `~/SCALER/HA/active_ha_session.json`
3. If root cause found: /HA records it in the test result as `FAIL -- <root cause from /debug-dnos>`

### Device Identity Check

When called from /HA, the device is already identity-validated by /HA's Device Lock.
/debug-dnos should still verify the device name matches before running trace greps.
