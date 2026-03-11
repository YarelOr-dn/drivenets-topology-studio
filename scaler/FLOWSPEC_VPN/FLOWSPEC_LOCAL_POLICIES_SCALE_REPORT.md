# FlowSpec Local Policies — Scale and Behavior Report

**Device:** PE-4 (YOR_CL_PE-4_priv_26.1.0.24)
**NCPs:** 6, 18
**TCAM Capacity:** 12,000 IPv4 + 4,000 IPv6
**YANG Limits:** 8,000 IPv4 + 4,000 IPv6
**Date:** 2026-02-23

**BGP FlowSpec Baseline (always present):** IPv4: 14 received / 13 installed; IPv6: 2 received / 2 installed

---

## Section 1: Baseline — Simple Criteria, No VRF, All-Drop

**Config:** `s1_baseline.cfg` — 100 IPv4 MCs + 50 IPv6 MCs
**Match:** `dest-ip/32` + `protocol tcp/udp` + `dest-ports` (exact single value)
**Action:** `rate-limit 0` (drop)
**VRF:** none

### Results

| Metric | NCP 6 | NCP 18 |
|--------|-------|--------|
| IPv4 Received | 114 (100 local + 14 BGP) | 114 |
| IPv4 Installed | 113 (100 local + 13 BGP) | 113 |
| IPv4 HW entries | 113/12000 | 113/12000 |
| IPv6 Received | 52 (50 local + 2 BGP) | 52 |
| IPv6 Installed | 52 | 52 |
| IPv6 HW entries | 52/4000 | 52/4000 |

**TCAM Expansion:** 1:1 — each simple rule maps to exactly 1 HW entry
**Vrf field:** `Vrf: all` for all local-policy rules (no VRF specified = applies globally)
**Not Installed count:** 0 (for local-policies)
**Status:** PASS

---

## Section 2: VRF Behavior — ALPHA, No-VRF, Mixed, Nonexistent

### 2a: VRF ALPHA on all MCs

- **TCAM:** IPv4 113/12000 (100 local), IPv6 52/4000 (50 local) — identical to no-VRF
- **Vrf field:** `Vrf: ALPHA` on all local-policy rules
- **Not Installed:** 0
- **Finding:** VRF does NOT cause TCAM expansion. Same 1:1 ratio.

### 2b: No VRF (same as Section 1)

- **TCAM:** IPv4 113/12000 (100 local), IPv6 52/4000 (50 local)
- **Vrf field:** `Vrf: all`
- **Not Installed:** 0

### 2c: Mixed — half ALPHA, half ZULU

- **TCAM:** IPv4 113/12000, IPv6 52/4000 — identical to single-VRF
- **Vrf field:** Shows both `Vrf: ALPHA` and `Vrf: ZULU` correctly per match-class
- **Not Installed:** 0
- **Finding:** Mixed VRFs within one policy work correctly with no TCAM overhead.

### 2d: VRF NONEXISTENT

- **Paste:** No errors during config paste
- **Commit Check:** FAILS with `'vrf NONEXISTENT' is configured ... but it doesn't exist.`
- **Finding:** DNOS validates VRF references at commit time. Non-existent VRF is rejected.

### Section 2 Summary

| Test | VRF | Commits? | TCAM IPv4 | TCAM IPv6 | Vrf Field |
|------|-----|----------|-----------|-----------|-----------|
| 2a | ALPHA | Yes | 100/12000 | 50/4000 | ALPHA |
| 2b | none | Yes | 100/12000 | 50/4000 | all |
| 2c | ALPHA+ZULU | Yes | 100/12000 | 50/4000 | ALPHA/ZULU |
| 2d | NONEXISTENT | No (commit fail) | N/A | N/A | N/A |

**Key findings:**
1. VRF has zero TCAM overhead — no expansion
2. Mixed VRFs in one policy are supported
3. Non-existent VRF names are caught at commit check (not paste)
4. `Vrf: all` is the default when no VRF is configured

---

## Section 3: TCAM Expansion Map — Which Match Fields Cause >1:1

10 IPv4 MCs per variant, all with `rate-limit 0`, clean-slate per variant.

| Variant | Match Criteria | HW entries / 10 rules | Ratio | Status |
|---------|---------------|----------------------|-------|--------|
| 3a | dest-ip only | 10 | 1.0:1 | All installed |
| 3b | dest-ip + protocol tcp | 10 | 1.0:1 | All installed |
| 3c | dest-ip + protocol + dest-ports | 10 | 1.0:1 | All installed |
| 3d | dest-ip + protocol + dest-ports + dscp | 10 | 1.0:1 | All installed |
| 3e | dest-ip + src-ip | 10 | 1.0:1 | All installed |
| 3f | dest-ip + src-ports (single value) | 10 | 1.0:1 | All installed |
| 3g | dest-ip + src-ports (range 1024-2048) | 10 | 1.0:1 | All installed |
| 3h | dest-ip + packet-length (single value 64) | 10 | 1.0:1 | All installed |
| **3i** | **dest-ip + packet-length (range 64-1500)** | **0** | **FAIL** | **ALL 10 NOT INSTALLED** |
| 3j | dest-ip + tcp-flag syn | 10 | 1.0:1 | All installed |
| 3k | dest-ip + tcp-flag syn,ack | 10 | 1.0:1 | All installed |
| 3l | dest-ip + fragmented | 10 | 1.0:1 | All installed |
| 3m | dest-ip + icmp echo-request | 10 | 1.0:1 | All installed |
| **3n** | **Combined: dest-ip + src-ip + src-ports range + packet-length range + tcp-flag** | **0** | **FAIL** | **ALL 10 NOT INSTALLED** |

### Key Findings

1. **All single-value match criteria are 1:1** — no TCAM expansion for FlowSpec local policies
2. **src-ports range is 1:1** — unlike BGP FlowSpec, local policy port ranges do NOT cause expansion
3. **BUG: packet-length RANGE causes complete installation failure** — `packet-length 64` works (1:1), but `packet-length 64-1500` causes ALL rules in the policy to NOT install
4. **Combined worst-case fails** — because it includes packet-length range
5. **tcp-flag combinations are 1:1** — `syn,ack` does not expand unlike BGP FlowSpec
6. **fragmented is 1:1** — no expansion

### BUG: packet-length range (3i, 3n)

- **Symptom:** Rules with `packet-length <range>` (e.g., `64-1500`) are received by NCP but show "Not Installed"
- **Workaround:** Use single packet-length values only (e.g., `packet-length 64`)
- **Severity:** High — this silently fails with no commit error
- **Impact:** Any policy containing a packet-length range match-class will have those rules silently dropped

---

## Section 4: BUG-2 — NCP Resource Leak on Create/Delete Cycles

**Test Date:** 2026-02-24
**Config:** 100 IPv4 MCs with simple criteria (dest-ip/32, protocol, dest-port), `action rate-limit 0`
**Procedure:** After ~15 create/delete cycles on the same device from prior testing

### Results

| Test | Config | Installed / Loaded | Failed | TCAM |
|------|--------|--------------------|--------|------|
| Load MC4-BUG2 (dirty NCP) | 10.2.0.x, ports 5xxx | 84/100 | 16 | 97/12000 |
| retry-install | — | 84/100 | 16 | 97/12000 |
| Delete + Load MC4-S1 (dirty NCP) | 10.1.0.x, ports 6xxx | 84/100 | 16 | 97/12000 |
| **After NCP restart** | same MC4-S1 | **100/100** | **0** | **113/12000** |

### Key Findings

1. **Resource leak confirmed:** Same 100-rule config installs 100/100 on fresh NCP, 84/100 on dirty NCP
2. **Not config-dependent:** Two completely different configs hit the same 84-rule ceiling
3. **Not recoverable without restart:** `request retry-install` does not help — NCP genuinely believes resources are exhausted
4. **NCP restart recovers:** All 100 rules install after NCP restart with zero config changes
5. **Leaked resource is NOT TCAM:** TCAM at 0.8% capacity (97/12000) when failures occur
6. **`rate-limit 0` involved:** Even drop actions (no policer) trigger the leak

### Bug Evidence File

Full details: `bug_evidence/BUG_FLOWSPEC_LOCAL_POLICY_RESOURCE_LEAK.md`

---

