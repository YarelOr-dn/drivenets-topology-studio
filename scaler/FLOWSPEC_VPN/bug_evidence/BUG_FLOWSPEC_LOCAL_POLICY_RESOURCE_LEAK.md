# BUG: FlowSpec Local Policy NCP Resource Leak on Create/Delete Cycles

| Field | Value |
|-------|-------|
| **Date Discovered** | 2026-02-24 |
| **Device** | YOR_CL_PE-4_priv_26.1.0.24 |
| **NCPs** | 6, 18 |
| **Image** | 26.1.0.24 (private build) |
| **Severity** | High |
| **Component** | NCP / wb_agent FlowSpec |
| **Status** | Open |

## Retest History

| Date | Image | Build | Result | Notes |
|------|-------|-------|--------|-------|
| 2026-02-24 | 26.1.0.24 (priv) | 24 | BUG PRESENT | Initial discovery. NCP restart recovers leaked resources. |
| 2026-02-25 | 26.1.0.24 (priv) | 24 | BUG PRESENT — SEVERE | After aggressive stress test (TCAM-fill + heavy rules + rapid cycles), m_reserved leaked to ~10,976. 2000 simple rules → only 1024 installed, 976 "out of resources" at 1024/12000 TCAM. Techsupport `ts_dp_bug_21_26_08` captured at 21:34 — rotated traces confirm BCM Num entries: 1024 at deletion, and 1437-entry TCAM amplification per PacketLen rule. |

## One-Line Summary

After repeated create/delete cycles of FlowSpec local policies, the NCP permanently leaks internal resources, causing subsequent rules to fail with "lack of resources" even though TCAM is nearly empty — only recoverable by NCP restart.

## Expected Results

All 100 FlowSpec local policy rules with `rate-limit 0` (drop) action should install successfully on every load, regardless of how many prior create/delete cycles have occurred, as confirmed by `show system npu-resources resource-type flowspec` showing "Rules installed" equal to "Received rules" minus any legitimately unsupported rules.

## Actual Results

After multiple create/delete cycles of FlowSpec local policies, only 84 out of 100 identical `rate-limit 0` rules install; 16 rules fail with "lack of resources" syslog warnings. TCAM usage is 97/12000 (0.8%). The `request retry-install flowspec-local-policy-rules ipv4` command does not recover the failed rules. Only an NCP restart recovers the leaked resources and allows all 100 rules to install.

## Steps to Reproduce

1. Configure 100 FlowSpec local policy match-classes with simple criteria (dest-ip/32, protocol, dest-port) and `action rate-limit 0`
2. Apply the policy via `forwarding-options flowspec-local ipv4 apply-policy-to-flowspec`
3. Commit and verify all 100 rules install (`show system npu-resources resource-type flowspec`)
4. Delete all FlowSpec local policies and the forwarding-options application, commit
5. Repeat steps 1-4 approximately 10-15 times (create/delete cycles)
6. Load the same 100 rules one final time and commit
7. Observe that only 84 rules install; 16 fail with syslog `FLOWSPEC_LOCAL_UNSUPPORTED_RULE: ... lack of resources`
8. Run `request retry-install flowspec-local-policy-rules ipv4` — failures persist
9. Restart the NCPs (`request system restart ncp <id>`) — all 100 rules install successfully

---

## Topology Diagram

<details>
<summary>Topology JSON (click to expand path)</summary>

`~/SCALER/FLOWSPEC_VPN/bug_evidence/BUG_FLOWSPEC_LOCAL_POLICY_RESOURCE_LEAK.topology.json`

Load via: Topology app → Topologies → Load Debug-DNOS..., or File → Load from File...
</details>

---

## Evidence

### Test Timeline (24-Feb-2026, PE-4)

| Time (IST) | Action | IPv4 Received | IPv4 Installed | Result |
|-------------|--------|---------------|----------------|--------|
| ~08:51 | Prior testing (many create/delete cycles) | — | — | NCP state dirty |
| 11:00 | Load 100 MC4-BUG2-xxxx rules (rate-limit 0) | 114 | 97 | 16 FAILED |
| 11:10 | `request retry-install flowspec-local-policy-rules ipv4` | 114 | 97 | Still 16 FAILED |
| 11:11 | Delete all local policies, commit | 14 | 13 | Back to BGP baseline |
| 11:13 | Load 100 MC4-S1-xxxx rules (rate-limit 0, different IPs/ports) | 114 | 97 | Same 16 FAILED |
| ~14:00 | Restart NCP 6 and NCP 18 | — | — | NCPs rebooting |
| 14:15 | NCPs back up, same config still loaded | 114 | **113** | **ALL 100 INSTALLED** |

### Key Observation

The same 16-rule failure occurred with TWO completely different configurations:
- **Config A (BUG2):** MC4-BUG2-0001..0100, dest-ip 10.2.0.x, ports 5001-5100
- **Config B (S1):** MC4-S1-0001..0100, dest-ip 10.1.0.x, ports 6001-6100

Both hit the exact same ceiling: 84 local + 13 BGP = 97 total. This proves the leak is in the NCP's internal resource tracking, not tied to specific rule content.

### Syslog Warnings (at commit, 11:00:58 IST)

```
FLOWSPEC_LOCAL_UNSUPPORTED_RULE:Flowspec Local IPv4 rule cannot be applied due to lack of resources. Rule NLRI: DstPrefix:=10.2.0.85/32,SrcPrefix:=*,Protocol:=6,DstPort:=5085, Actions: traffic rate
FLOWSPEC_LOCAL_UNSUPPORTED_RULE:Flowspec Local IPv4 rule cannot be applied due to lack of resources. Rule NLRI: DstPrefix:=10.2.0.86/32,SrcPrefix:=*,Protocol:=17,DstPort:=5086, Actions: traffic rate
... (16 total, rules 85-100 all failed)
```

### Before NCP Restart (dirty state, 11:00 IST)

```
show system npu-resources resource-type flowspec

| NCP | IPv4 Received rules | IPv4 Rules installed | IPv4 HW entries used/total |
|-----+---------------------+----------------------+----------------------------|
| 6   | 114                 | 97                   | 97/12000                   |
| 18  | 114                 | 97                   | 97/12000                   |
```

### After retry-install (11:10 IST) — no change

```
request retry-install flowspec-local-policy-rules ipv4
→ Same 16 syslog warnings, count stays at 97/97
```

### After NCP Restart (clean state, 14:15 IST)

```
show system npu-resources resource-type flowspec

| NCP | IPv4 Received rules | IPv4 Rules installed | IPv4 HW entries used/total |
|-----+---------------------+----------------------+----------------------------|
| 6   | 114                 | 113                  | 113/12000                  |
| 18  | 114                 | 113                  | 113/12000                  |
```

### show flowspec-local-policies ncp 6 (post-restart, 14:17 IST)

All 100 rules show `Status: Installed`, including the previously failing rules 85-100:

```
Flow: DstPrefix:=10.1.0.85/32,SrcPrefix:=*,Protocol:=6,DstPort:=6085
    Vrf: all
    Actions: Traffic-rate: 0 bps
    Status: Installed

Flow: DstPrefix:=10.1.0.100/32,SrcPrefix:=*,Protocol:=17,DstPort:=6100
    Vrf: all
    Actions: Traffic-rate: 0 bps
    Status: Installed
```

### show flowspec-local-policies counters (post-restart, 14:17 IST)

All 100 match-classes listed under policy `POL-S1-DROP` with `Actions: Traffic-rate: 0 kbps (drop)` and `Match packets: 0`.

### Comparison Table

| Condition | Local Rules Loaded | Local Rules Installed | Failed | TCAM Used | Recovery |
|-----------|-------------------|-----------------------|--------|-----------|----------|
| Fresh NCP (Section 1 historical) | 100 | 100 | 0 | 113/12000 | N/A |
| After ~15 create/delete cycles | 100 | 84 | 16 | 97/12000 | retry-install: NO |
| After ~15 cycles + different config | 100 | 84 | 16 | 97/12000 | retry-install: NO |
| After NCP restart | 100 | 100 | 0 | 113/12000 | NCP restart: YES |

---

## Root Cause (Code-Level, Confirmed)

### The Leaking Resource: `m_reserved` in `FlowspecTcamManager`

**File:** `src/wbox/src/flowspec/FlowspecTcamManager.cpp`
**Variable:** `FlowspecTcamManager::m_reserved` (int, initialized to 0 in constructor, line 23)

The `FlowspecTcamManager` maintains three counters for TCAM capacity management:
- `m_numberOfEntries` — actual entries written to BCM TCAM (shown by `show system npu-resources`)
- `m_reserved` — slots reserved by rules pending write (deferred during priority reshuffle)
- `m_totalCapacity` — maximum TCAM entries (12000 for IPv4, const)

The capacity check in `ReserveQualifiers()` (line 315) uses ALL THREE:
```
if ((m_numberOfEntries + m_reserved + to_reserve) <= m_totalCapacity)
```

### How the Leak Happens

**Normal rule-add flow:**
1. `ReserveQualifiers(1)` → `m_reserved += 1` (line 317)
2. `WriteRuleInTcam()` succeeds → `m_reserved -= 1`, `m_numberOfEntries += 1` (line 291-292)
3. Net: `m_reserved` returns to 0

**Priority reshuffle deferral flow (triggered when >~20 rules are added in a batch due to binary priority splitting exhausting the integer priority space):**
1. `ReserveQualifiers(1)` → `m_reserved += 1`
2. `IsWriteMode()` returns false (reshuffle paused writes, line 324) → `WriteToTcam()` returns true without writing
3. Rule is "deferred" — `m_reserved` stays incremented
4. Later, `ReshuffleRules()` writes the deferred rule → `m_reserved -= 1` on success

**LEAK PATH — when deferred rule fails during reshuffle:**
1. `ReserveQualifiers(1)` → `m_reserved += 1` (**incremented**)
2. Rule deferred (IsWriteMode=false)
3. During `ReshuffleRules()` (line 427): `ReshuffleWriteToTcam()` → `WriteRuleInTcam()` FAILS
4. `HandleRuleFailedWrite()` called (line 431) → calls `RollbackRule()` (line 353)
5. `RollbackRule()` (FlowspecTcamManager.cpp:144) only deletes partial BCM entries — **does NOT decrement `m_reserved`**
6. Rule stays in table as "unwritten"
7. Later deleted via `DeleteRuleInternal()` (line 249): `IsWritten()` = false → `EraseFromTcam()` NOT called → **`m_reserved` never decremented**

**LEAK PATH — direct write failure (HandleRuleFailedWrite in InternalAddRule):**
1. `ReserveQualifiers(1)` → `m_reserved += 1` (**incremented**)
2. `PerformWriteToTcam()` → `WriteRuleInTcam()` FAILS (any BCM error)
3. `HandleRuleFailedWrite()` → `RollbackRule()` — **does NOT decrement `m_reserved`**
4. Rule later deleted → `IsWritten()` = false → **`m_reserved` never decremented**

### Why the Leak Grows Over Cycles

Each batch of 100 rules triggers a priority reshuffle (priority space 0–1999999 is exhausted after ~21 sequential binary insertions). During reshuffle, if ANY rule fails to write (BCM error, timing, resource contention), `m_reserved` permanently increases. Over ~15 create/delete cycles, the cumulative leaked `m_reserved` reaches a threshold where `m_numberOfEntries + m_reserved + 1 > m_totalCapacity`, and `ReserveQualifiers()` starts rejecting new rules.

### wb_agent Trace Evidence (NCP 6, 24-Feb-2026)

**Successful rule (10.2.0.1, rule 34057):**
```
11:00:58.589056  UpdateRateLimitPolicerIfNeeded: traffic rate is 0.000000. Will not initialize policer.
11:00:58.589067  ReserveQualifiers: local_config_flowspec_should_validate_resources: 1
11:00:58.589078  DeterminePriority: Adding rule between priority 0 to priority 1999999
11:00:58.589088  WriteRuleInTcam: Adding rule with priority 999999
11:00:58.599070  Succeeded to add rule in BCM
11:00:58.599117  Succeeded to write 1 rules in TCAM for rule id 34057
```

**Reshuffle trigger (10.2.0.22, rule 34078 — priority space exhausted):**
```
11:00:58.603829  ReserveQualifiers: local_config_flowspec_should_validate_resources: 1
11:00:58.603838  DeterminePriority: Adding rule between priority 1999998 to priority 1999999
11:00:58.603848  InitiateReshuffle: Disabling TCAM writes      ← IsWriteMode = false
11:00:58.603868  Succeeded to add IPv4 flowspec rule            ← deferred, m_reserved += 1
```

**Deferred rules (10.2.0.23–10.2.0.84, rules after reshuffle — no TCAM write):**
```
11:00:58.604013  ReserveQualifiers: local_config_flowspec_should_validate_resources: 1
11:00:58.604023  Succeeded to add IPv4 flowspec rule            ← deferred, m_reserved += 1 each
```

**Failed rules (10.2.0.85–10.2.0.100, 16 rules — ReserveQualifiers FAILS):**
```
11:00:58.612068  WARNING: No more space left in TCAM for new rules   ← m_numberOfEntries + m_reserved + 1 > m_totalCapacity
11:00:58.612087  ERROR: Failed to add rule to TCAM
11:00:58.612139  ERROR: Unable to add IPv4 flowspec rule with length=13
```

**Reshuffle execution (after all 100 adds attempted):**
```
11:00:58.615501  Reshuffle local rules called for IPv4
11:00:58.615511  Reshuffling 84 supported local ipv4 rules      ← only 84 (16 failed ones excluded)
11:00:58.615521  Min: 0, Max: 1999999, Interval:23529
```

**retry-install attempt (11:10 — same NCP, same leaked m_reserved):**
```
11:10:22.385389  ERROR: Failed to update rule in TCAM           ← 16 times, m_reserved still leaked
```

### Key Code References

| File | Line | Function | Role |
|------|------|----------|------|
| `FlowspecTcamManager.cpp` | 315-317 | `ReserveQualifiers()` | Capacity check: `m_numberOfEntries + m_reserved + to_reserve <= m_totalCapacity`. Increments `m_reserved` |
| `FlowspecTcamManager.cpp` | 291-292 | `WriteRuleInTcam()` | **Only place** `m_reserved` is decremented — requires successful write AND `!update` |
| `FlowspecTcamManager.cpp` | 144-154 | `RollbackRule()` | Deletes partial BCM entries but **never adjusts `m_reserved`** |
| `FlowspecTcamManager.cpp` | 60-86 | `DeleteRule()` | Adjusts `m_numberOfEntries -= n_deleted` but **never adjusts `m_reserved`** |
| `FlowspecTable.cpp` | 350-363 | `HandleRuleFailedWrite()` | Calls `RollbackRule()` — **does not release reservation** |
| `FlowspecTable.cpp` | 249-279 | `DeleteRuleInternal()` | For unwritten rules (`IsWritten()=false`): skips `EraseFromTcam()` — **`m_reserved` never decremented** |
| `FlowspecRuleData.cpp` | 315-322 | `WriteToTcam()` | `ReserveQualifiers()` called, but if `IsWriteMode()=false`, returns true without consuming the reservation |
| `FlowspecRuleData.hpp` | 270-273 | `IsInstalled()` | `return IsSupported() && !m_tcam_error` — rules with TCAM errors excluded from reshuffle |

### Shared TcamManager Architecture

Both BGP and Local FlowSpec tables share the SAME `FlowspecTcamManager` instance per AFI:
```
m_ipv4TcamManager → shared by m_ipv4BGPTable AND m_ipv4LocalTable
m_ipv6TcamManager → shared by m_ipv6BGPTable AND m_ipv6LocalTable
```
This means leaked `m_reserved` from ANY source (BGP or local, any prior configuration) affects ALL subsequent rule installations.

### Why NCP Restart Fixes It

The `FlowspecTcamManager` constructor initializes `m_reserved(0)` (line 23). An NCP restart re-initializes all wb_agent data structures, resetting `m_reserved` to 0.

### Suggested Fix

Add `m_reserved` cleanup in the failure/delete paths:
1. In `HandleRuleFailedWrite()`: after `RollbackRule()`, call `m_flowspecTcamManager->ReleaseReserved(ruleData->GetNumberOfTcamRules())` to decrement `m_reserved`
2. In `DeleteRuleInternal()`: for rules where `!IsWritten()` but reservation was taken, release the reserved slots
3. Alternatively, add an `UnreserveQualifiers(int count)` method to `FlowspecTcamManager` that does `m_reserved -= count` under lock

---

## Evidence (2026-02-25): Severe Leak After Aggressive Stress Test

### Trigger Scenario

An automated stress test (`run_aggressive.py`) ran 15 scenarios including:
- S1-S4: Loading 500/1000/2000/3000 simple rules
- S5: Filling TCAM to absolute max with `packet-length range` rules (8 PL rules × ~1437 TCAM entries each)
- S7: 500 heavy rules (6 match criteria)
- S12: 10 rapid 500-rule load/delete cycles

After these scenarios, the m_reserved leak had accumulated massively.

### Smoking Gun: 2000 Simple Rules → 1024 Installed (20:55 IST)

```
show system npu-resources resource-type flowspec

| NCP | IPv4 Received | IPv4 Installed | IPv4 HW used/total | IPv6 Received | IPv6 Installed | IPv6 HW used/total |
|-----|---------------|----------------|---------------------|---------------|----------------|---------------------|
| 6   | 2000          | 1024           | 1024/12000          | 4000          | 4000           | 4000/4000           |
| 18  | 2000          | 1024           | 1024/12000          | 4000          | 4000           | 4000/4000           |
```

- **2000 simple rules** (1 TCAM entry each) loaded
- **Only 1024 installed** — TCAM has **10,976 free entries**
- **976 rules** explicitly marked `Status: Not Installed, out of resources`
- **1024 = 2^10** — the leaked m_reserved consumed exactly 10,976 phantom entries

### Status Breakdown from `show flowspec-local-policies ncp 6`

| Status | Count |
|--------|-------|
| Total rules (2000 received) | 2000 |
| Status: Installed | 1024 |
| Status: Not Installed, out of resources | 976 |

Rules 1-1024 (DstPrefix 10.30.0.1..10.30.4.8): Installed
Rules 1025-2000 (DstPrefix 10.30.4.9..10.30.7.208): Not Installed, out of resources

### Sample "Not Installed" entries

```
Flow: DstPrefix:=10.30.4.9/32,SrcPrefix:=*,Protocol:=6,DstPort:=4025
    Vrf: ALPHA
    Actions: Traffic-rate: 500000 bps
    Status: Not Installed, out of resources

Flow: DstPrefix:=10.30.4.10/32,SrcPrefix:=*,Protocol:=17,DstPort:=4026
    Vrf: ALPHA
    Actions: Traffic-rate: 500000 bps
    Status: Not Installed, out of resources
```

### m_reserved Leak Calculation

For exactly 1024 rules to install in a 12,000-entry TCAM:
- ReserveQualifiers check: `m_numberOfEntries + m_reserved + to_reserve <= m_totalCapacity`
- Rule 1024: `1023 + leaked + 1 <= 12000` → passes when `leaked <= 10,976`
- Rule 1025: `1024 + leaked + 1 > 12000` → fails when `leaked >= 10,976`
- **Leaked m_reserved = exactly 10,976 entries** (91.5% of TCAM capacity)

### How 10,976 Entries Leaked

Previous stress test cycles included TCAM-fill scenarios with `packet-length range` rules:
- Each `packet-length range` rule expands to ~1,437 TCAM entries (ternary range expansion)
- 8 PL rules × 1,437 = 11,496 TCAM entries reserved
- When TCAM was near capacity (11,996/12,000), some ReserveQualifiers succeeded but WriteRuleInTcam failed
- Failed writes: m_reserved never decremented (code paths confirmed in Root Cause section)
- Subsequent delete/cleanup: m_reserved still not decremented
- Accumulated leaked m_reserved from multiple cycles = ~10,976

### NCP Trace Evidence (NCP 6, 25-Feb-2026)

Last rule successfully installed with priority 1997824:
```
2026-02-25T20:54:58.693641 [INFO] FlowspecTcamManager.cpp:241 WriteRuleInTcam() Flowspec: Adding rule with priority 1997824
2026-02-25T20:54:58.693654 [DEBUG] FlowspecTcamManager.cpp:102 _FillAction() Flowspec: Action traffic rate is 62500.000000
2026-02-25T20:54:58.693667 [INFO] FlowspecTcamManager.cpp:195 operator()() Flowspec: Succeeded to add rule in BCM
2026-02-25T20:54:58.693686 [INFO] FlowspecTcamManager.cpp:283 WriteRuleInTcam() Flowspec: Succeeded to write 1 rules in TCAM for rule id 251844
```

Then IPv6 reshuffle triggered (NOT IPv4 — wrong AF):
```
2026-02-25T20:54:58.693754 [DEBUG] FlowspecManager.cpp:346 ReshuffleLocal() Flowspec: Reshuffle local rules called for IPv6
```

No ERROR/WARNING/Failed messages in buffer — rotated before we could capture them.

### Techsupport Trace Evidence (ts_dp_bug_21_26_08, captured 21:34:41)

Techsupport captured at 21:34:41 IST preserved **rotated trace files** that were no longer available on the live device:

**Rotated trace files recovered:**

| File | Timestamp Range | Lines | Key Content |
|------|----------------|-------|-------------|
| `wb_agent.flowspec-20260225_20:53:49.gz` | Before 20:53:49 | 10,051 | Deletion of user's 1024 installed rules |
| `wb_agent.flowspec-20260225_21:02:33.gz` | 20:53-21:02 | 21,310 | Rule additions with ReserveQualifiers |
| `wb_agent.flowspec-20260225_21:05:22.gz` | 21:02-21:05 | 7,322 | Heavy rules with PacketLen TCAM amplification |

**Evidence A — BCM confirms exactly 1024 HW entries at deletion time (fs2053, 20:53:48):**

```
2026-02-25T20:53:48.166707 [FlowspecTcamManager.cpp:63 DeleteRule()] Deleting rule with priority 1951
2026-02-25T20:53:48.167366 [FlowspecTcamManager.cpp:50 DeleteTcamRule()] Succeeded to delete rule in BCM. Num entries: 1024
2026-02-25T20:53:48.167952 [FlowspecTcamManager.cpp:63 DeleteRule()] Deleting rule with priority 3902
2026-02-25T20:53:48.167986 [FlowspecTcamManager.cpp:50 DeleteTcamRule()] Succeeded to delete rule in BCM. Num entries: 1023
2026-02-25T20:53:48.168554 [FlowspecTcamManager.cpp:63 DeleteRule()] Deleting rule with priority 5853
2026-02-25T20:53:48.168605 [FlowspecTcamManager.cpp:50 DeleteTcamRule()] Succeeded to delete rule in BCM. Num entries: 1022
```

BCM hardware counter starts at **1024** and counts down (1024, 1023, 1022...) as each rule is deleted. This is **hardware-level proof** that only 1024 entries existed in the physical TCAM when `show system npu-resources` reported 1024/12000. The other 10,976 capacity was consumed by leaked `m_reserved`.

Total deletes in this file: **3024** (including IPv6 reshuffle deletes). IPs are `10.30.0.x` series (user's manual 2000-rule test).

**Evidence B — TCAM Amplification: 1 rule = 1437 HW entries (fs2105, 21:05:22):**

```
2026-02-25T21:05:22.391114 [FlowspecManager.cpp:151 AddRuleInternal()] Received local IPv4 NLRI: ...DstPrefix:=10.60.0.3/32,SrcPrefix:=172.16.0.3/32,Protocol:=6,DstPort:=3003,SrcPort:=5003,PacketLen:>=64&<=1500
2026-02-25T21:05:22.391208 [FlowspecTcamManager.cpp:309 ReserveQualifiers()] local_config_flowspec_should_validate_resources: 1
2026-02-25T21:05:22.391221 [FlowspecTcamManager.cpp:241 WriteRuleInTcam()] Adding rule with priority 1749999
  <...1437 consecutive "Succeeded to add rule in BCM" at line 195...>
2026-02-25T21:05:22.475913 [FlowspecTcamManager.cpp:283 WriteRuleInTcam()] Succeeded to write 1437 rules in TCAM for rule id 256331
```

Three such rules in this file, each consuming **1437 TCAM entries**:

| Rule ID | TCAM Entries | Match Criteria |
|---------|-------------|----------------|
| 256331 | 1437 | DstPrefix + SrcPrefix + Proto + DstPort + SrcPort + **PacketLen:>=64&<=1500** |
| 256334 | 1437 | Same criteria pattern, different IPs |
| 256337 | 1437 | Same criteria pattern, different IPs |

Total from 3 rules: **4311 TCAM entries** reserved via `ReserveQualifiers()`. When deleted, `DeleteRule()` frees the BCM entries but `m_reserved` retains all 4311 — permanent phantom capacity loss.

**Evidence C — Keyword summary across all trace files:**

| Keyword | fs2053 | fs2102 | fs2105 | fs_current |
|---------|--------|--------|--------|------------|
| ReserveQualifiers | 0 | **1261** | **15** | 0 |
| WriteRuleInTcam | 0 | **6000** | **29** | 0 |
| Succeeded to write | 0 | **3000** | **14** | 0 |
| AddRuleInternal | 0 | **5296** | **59** | 0 |
| DeleteRule() | **3024** | 0 | **1** | **5** |
| Succeeded to delete | **3024** | **21** | **2** | **6** |
| Reshuffle | **2** | **4** | **2** | **2** |
| WARNING | 0 | 0 | 0 | 0 |
| No more space | 0 | 0 | 0 | 0 |
| Failed | 0 | 0 | 0 | 0 |

Note: No WARNING/Failed messages captured — the "No more space left in TCAM" WARNING at line 321 of `FlowspecTcamManager.cpp` likely rotated out before the techsupport was taken, or the trace level wasn't sufficient. The leak is **silent** — it does not produce ERROR/WARNING messages.

### Priority Space Analysis (confirmed from code)

| Priority Range | Value |
|----------------|-------|
| Local minimum | 0 |
| Local maximum | 1,999,999 |
| Spacing at 1024 rules | ~1,951 (1,999,999 / 1025) |
| Last observed priority | 1,997,824 |

Priority space is NOT the issue — 2M range supports thousands of rules. The bottleneck is m_reserved consuming the TCAM capacity counter.

### Complete Stress Test Timeline (25-Feb-2026)

| Time | Scenario | Rules Loaded | Rules Installed | HW Used/Total | Result | Leak? |
|------|----------|-------------|-----------------|---------------|--------|-------|
| 18:46 | Baseline | 0 | 0 | 0/12000 | Clean start | No |
| 18:47 | PROBE #0 | 498 (8 PL + 490 simple) | 498 | 11986/12000 | PROBE OK (490/490 simple) | No |
| 18:47 | S1: 500 simple | 500 | **500** | 500/12000 | All installed | No |
| 18:48 | S2: 1000 simple | 1000 | **1000** | 1000/12000 | All installed | No |
| 18:49 | S3: 2000 simple | 2000 | **1024** | 1024/12000 | **976 FAILED "out of resources"** | **YES — m_reserved ~10,976** |
| 19:00 | S4: 3000 simple | 3000 | **3000** | 3000/12000 | All installed | Recovered |
| 19:03 | S5: TCAM fill (8 PL + simple) | 508 | **508** | 11996/12000 | Near-full (legitimate) | No |
| 19:04 | S6: Rollback test | 0 | **0** | 0/12000 | Rollback clean | N/A |
| 19:04 | S7: 500 heavy (6 criteria) | 500 | **342** | 11830/12000 | TCAM full (34.6x amplification) | Legitimate |
| 19:10 | S8: 5000 simple | 5000 | **5000** | 5000/12000 | All installed | No |
| 19:15 | S9: 7000 heavy | 7000 | **512** | 12000/12000 | TCAM full (23.4x amplification) | Legitimate |
| 19:27 | PROBE #1 | 498 (8 PL + 490 simple) | 498 | 11986/12000 | PROBE OK (490/490 simple) | No |
| 19:28 | S10: 7000 heavy rollback | 0 | **0** | 0/12000 | Rollback clean | N/A |
| 19:33 | S11: 500 → 7000 overwrite | 500 | **500** | 500/12000 | Phase 1 OK | No |
| 20:55 | User manual test | 2000 | **1024** | 1024/12000 | **976 FAILED "out of resources"** | **YES — m_reserved ~10,976** |

### Leak Accumulation Analysis

The leak appears at **S3 (2000 rules → 1024 installed)** and reappears in the **user's manual test (20:55)**. Key observations:

1. **S1 (500) and S2 (1000)**: All rules install — no leak yet
2. **S3 (2000)**: Only 1024 install — leak suddenly appears
3. **S4 (3000)**: All 3000 install — leak apparently recovered during S3→S4 cleanup
4. **PROBE #1 (after S9)**: 490/490 — no leak detected

This suggests the leak is **condition-dependent** rather than permanently accumulating:
- Triggered under specific batch size / reshuffle timing conditions
- May recover when all rules are successfully deleted from the table
- But can reappear when the triggering conditions recur

The fact that it appeared TWICE (S3 and user's test at 20:55) with the exact same result (1024/2000) confirms it is reproducible under specific conditions.

### Diagnostic Limitations

**m_reserved is invisible** (confirmed via code analysis):
- NOT exposed in `show system npu-resources`
- NOT exposed via `xraycli /wb_agent/flowspec/info`
- NOT exposed via any CLI show command
- The variable exists ONLY in `FlowspecTcamManager` memory

**Indirect detection**: The only way to detect the leak is through its EFFECTS:
- Rules fail with "Not Installed, out of resources" when TCAM has ample space
- `hw_rules_write_fail` xraycli counter (under `/wb_agent/flowspec/hw_counters`) tracks failed writes — non-zero confirms the leak trigger occurred

### Suggested Verification Steps

1. Enter NCP shell: `request system shell ncp 6`
2. Run: `xraycli /wb_agent/flowspec/hw_counters` — check `hw_rules_write_fail` counter
3. If non-zero: proves writes failed, which is the precondition for m_reserved leak
4. Load 2000 simple rules → if only 1024 install: leak is active
5. Restart NCP: `request system restart ncp 6`
6. Reload same 2000 rules → if all 2000 install: confirms m_reserved was the leak

### Secondary Finding: Stale IPv6 FlowSpec Rules

4000 IPv6 FlowSpec rules persist in NCP across ALL test scenarios despite:
- `show config routing-policy flowspec-local-policies ipv6` → EMPTY
- `show bgp ipv6 flowspec summary` → PfxAccepted: 0
- IPv6 TCAM: 4000/4000 (completely full throughout all 11 scenarios + 2 probes)
- Rules show VRF: ZULU, DstPrefix: 2001:db8:*/48, action: rate-limit 0

These are orphaned rules — config was deleted but NCP retained the rules. Separate cleanup issue. The IPv6 rules use a **separate TCAM** (4000 capacity vs 12000 for IPv4) and separate `FlowspecTcamManager` instance. They do NOT affect IPv4 rule installation.

### Updated Comparison Table

| Condition | Rules Loaded | Rules Installed | Failed | TCAM Used | m_reserved (est.) |
|-----------|-------------|-----------------|--------|-----------|-------------------|
| Fresh NCP (2026-02-24) | 100 | 100 | 0 | 113/12000 | 0 |
| After ~15 create/delete cycles (2026-02-24) | 100 | 84 | 16 | 97/12000 | ~16 |
| After NCP restart (2026-02-24) | 100 | 100 | 0 | 113/12000 | 0 (reset) |
| After aggressive stress test (2026-02-25) | 2000 | 1024 | 976 | 1024/12000 | ~10,976 |
| After aggressive + heavy rules (2026-02-25) | 500 | 342 | 158 | 11830/12000 | Unknown (mixed heavy/simple) |

---

## Related Bugs

- **BUG-1 (packet-length range):** Documented in FLOWSPEC_LOCAL_POLICIES_SCALE_REPORT.md Section 3i — separate issue, not related to create/delete cycles
- **BUG-3 (stale NCP state on action update):** Not yet tested — rules that initially fail due to policer exhaustion may not recover when action is changed to `rate-limit 0`
- **Stale IPv6 NCP rules:** Config deleted but 4000 IPv6 FlowSpec rules persist in NCP (4000/4000 TCAM). Separate from m_reserved leak — indicates NCP does not clean up rules when local-policy config is removed.
