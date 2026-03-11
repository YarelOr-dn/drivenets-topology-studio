# BUG: FlowSpec TCAM `m_reserved` Leak Causes False "Out of Resources" During Bulk Injection

| Field | Value |
|-------|-------|
| **Date Discovered** | 2026-03-01 |
| **Device** | PE-1 |
| **Image (discovered)** | 26.1.0.3 |
| **Branch** | Release (not private branch) |
| **Severity** | Major — permanent rule loss during bulk FlowSpec injection; up to 34% of rules silently dropped |
| **Component** | NCP / wb_agent FlowSpec — `FlowspecTcamManager::ReserveQualifiers()` |
| **Jira** | TBD |
| **Related** | `BUG_FLOWSPEC_TCAM_OVERFLOW_NO_RECOVERY` (same 400-threshold mechanism, different trigger) |

## Retest History

| Date | Image (full path) | Build | Result | Notes |
|------|-------------------|-------|--------|-------|
| 2026-03-01 | 26.1.0.3 | release | BUG PRESENT | 12K IPv4 + 4K IPv6 FlowSpec-VPN via preload burst. IPv4: 7488/12000 installed (37.6% lost). IPv6: 3562/4000 installed (10.9% lost). |
| 2026-03-02 | PE-4 cluster (26.1.x) | release | BUG PRESENT | IPv6 on PE-4 (via RR): BGP=4000, NCP received=421, installed=21. Gap=400 (exact circuit breaker match). IPv4 unaffected at time of check. Indirect injection path (ExaBGP→PE-1→RR→PE-4). |
| 2026-03-02 | PE-4 26.1.0.27 | release | RETESTED: test_02 "failure" was RT mismatch | test_02 (IPv4+IPv6 combined) initially showed IPv6=0/4000. /debug-dnos traced: bgpd accepted 4000 IPv6, chain done, but zebra DB=0 — routes never imported into VRF. Root cause: ExaBGP used RT=1234567:300, but VRF IPv6-flowspec import expects RT=1234567:401. After fixing RT: IPv4=12K/12K + IPv6=4K/4K + ZERO NCP errors. The m_reserved leak bug was NOT reproduced in this test. |

## One-Line Summary

`FlowspecTcamManager::ReserveQualifiers()` never releases `m_reserved` entries when `WriteRuleInTcam()` or `PerformWriteToTcam()` fails, causing phantom TCAM consumption that triggers false "No more space left in TCAM" errors during bulk FlowSpec rule injection — even when actual TCAM usage is well below capacity.

## Expected Results

When FlowSpec-VPN rules are injected via BGP and the TCAM has sufficient capacity for all rules, all rules should be installed in hardware. `show system npu-resources resource-type flowspec` should show `IPv4 Rules installed` equal to `IPv4 Received rules`, and the same for IPv6.

## Actual Results

During bulk injection (e.g., 12,000+ rules arriving in a burst), the NCP's TCAM reservation counter (`m_reserved`) inflates with phantom entries from failed writes that are never released. This causes `ReserveQualifiers()` to falsely report TCAM as full. After 400 rules fail per address family, the `HandleRuleFailedWrite()` circuit breaker activates and permanently deletes all subsequent arriving rules. No retry mechanism exists.

## Steps to Reproduce

1. Configure any VRF with `import-vpn route-target` for FlowSpec-VPN (SAFI 134) for both IPv4 and IPv6
2. Inject FlowSpec-VPN rules at scale (e.g., 12,000 IPv4 + 4,000 IPv6) in a single burst via ExaBGP preload or rapid pipe injection
3. Wait for BGP to accept all routes: `show bgp ipv4 flowspec-vpn summary` shows full count
4. Check TCAM: `show system npu-resources resource-type flowspec`
5. Observe: `Received rules` < BGP accepted count, and `Received rules - Rules installed = 400` per family
6. Check NCP traces: `show file ncp 0 traces datapath/wb_agent.flowspec | include WriteToTcam` shows "No more space left in TCAM" even though TCAM has spare capacity
7. Rules cannot be recovered without withdrawing ALL routes and re-injecting

---

## Test Setup

- **Injector:** ExaBGP 5.0.1 on 100.64.6.134 peering with PE-1 (eBGP AS 65200 → AS 1234567)
- **Device:** PE-1 (YOR_PE-1_priv_26.1.0.3)
- **VRF:** ZULU on PE-1
  - `import-vpn route-target 300:300,1234567:301` under `address-family ipv4-flowspec`
  - `import-vpn route-target 1234567:401` under `address-family ipv6-flowspec`
- **Injection method:** ExaBGP `--preload` (process API — all routes sent in initial BGP burst)
- **TCAM capacity:** IPv4: 12,000 / IPv6: 4,000

| Route Set | Count | SAFI | Base Prefix | RD | RT | Action |
|-----------|-------|------|-------------|-----|-----|--------|
| IPv4 FlowSpec-VPN | 12,000 | 134 | 10.0.0.0/24 | 1.1.1.1:100 | 1234567:301 | rate-limit 0 |
| IPv6 FlowSpec-VPN | 4,000 | 134 | 2001:db8::/48 | 1.1.1.1:100 | 1234567:401 | rate-limit 0 |

---

## Symptom: NPU Resources

```
| NCP | IPv4 Received | IPv4 Installed | IPv4 HW used/total | IPv6 Received | IPv6 Installed | IPv6 HW used/total |
|-----|---------------|----------------|---------------------|---------------|----------------|---------------------|
| 0   | 7888          | 7488           | 7488/12000          | 3962          | 3562           | 3562/4000           |
```

**Gap analysis:**

| Family | BGP Accepted | NCP Received | NCP Installed | Unwritten (400 cap) | Silently Dropped |
|--------|-------------|--------------|---------------|---------------------|------------------|
| IPv4   | 12,000      | 7,888        | 7,488         | 400                 | 4,112            |
| IPv6   | 4,000       | 3,962        | 3,562         | 400                 | 38               |

- **400 per family**: Rules kept in NCP table as "unwritten" (up to `FLOWSPEC_MAX_UNWRITTEN_IN_TABLE` threshold)
- **4,112 + 38 silently dropped**: Rules arriving AFTER the 400 threshold → `DeleteRuleInternal()` → permanently lost

---

## NCP wb_agent Traces (tail of rotated buffer)

```
2026-03-01T15:15:21.722720 +02:00 [WARNING] [FlowspecRuleData.cpp:319 WriteToTcam()] Flowspec: No more space left in TCAM for new rules
2026-03-01T15:15:21.722736 +02:00 [ERROR  ] [FlowspecTable.cpp:121 InternalAddRule()] Flowspec: Failed to add rule to TCAM
2026-03-01T15:15:21.722752 +02:00 [DEBUG  ] [FlowspecTable.cpp:521 SendUnsupportedSystemEvent()] Flowspec: ...reason lack of resources, address family IPv6, rule DstPrefix:=2001:db8:f9f::/48
2026-03-01T15:15:21.722760 +02:00 [DEBUG  ] [FlowspecTcamManager.cpp:146 RollbackRule()] Flowspec: Rollback rule 01300020010db80f9f in BCM
2026-03-01T15:15:21.722778 +02:00 [ERROR  ] [FlowspecTable.cpp:358 HandleRuleFailedWrite()] Flowspec: Too many unwritten rules, not adding to table
2026-03-01T15:15:21.722803 +02:00 [ERROR  ] [FlowspecManager.cpp:215 AddRuleInternal()] Flowspec: Unable to add IPv6 flowspec rule with length=9
```

Trace buffer rotated during 16K rule burst — only the LAST failure event per keyword survives. Earlier IPv4 failures and initial IPv6 failures are overwritten.

---

## Code-Level Root Cause

### File: `FlowspecTcamManager.cpp` (cheetah_26_1/src/wbox/src/flowspec/)

**The reservation leak:**

```
// Line 307-322: ReserveQualifiers — INCREMENTS m_reserved
bool FlowspecTcamManager::ReserveQualifiers(int to_reserve) {
    if (!local_config_flowspec_should_validate_resources()) return true;
    std::lock_guard<std::mutex> lock(m_lock);
    if ((m_numberOfEntries + m_reserved + to_reserve) <= m_totalCapacity) {
        m_reserved += to_reserve;  // ← INCREMENTED HERE
        return true;
    }
    return false;
}

// Line 288-293: m_reserved ONLY decremented on SUCCESSFUL write
if (!update) {
    std::lock_guard<std::mutex> lock(m_lock);
    m_numberOfEntries += writeRes.written - writeRes.deleted;
    m_reserved -= flowspecRuleData.GetNumberOfTcamRules();  // ← ONLY ON SUCCESS
}

// Line 144-156: RollbackRule — called on FAILURE — does NOT release m_reserved
void FlowspecTcamManager::RollbackRule(FlowspecRuleData &flowspecRuleData) {
    // Deletes partial TCAM entries... but NO m_reserved adjustment
}
```

**Failure cascade during bulk injection:**

1. Rules arrive in rapid burst → each calls `ReserveQualifiers()` → `m_reserved` grows
2. TCAM writes are slower than reservations → `m_reserved` accumulates in-flight
3. Some writes fail (BCM contention, priority issues, or concurrent writes)
4. Failed writes → `RollbackRule()` → `m_reserved` NOT decremented → **phantom entries**
5. `m_numberOfEntries + m_reserved + to_reserve > m_totalCapacity` → false "no space"
6. Subsequent rules fail `ReserveQualifiers()` → `HandleRuleFailedWrite()` → `m_unwritten_in_table++`
7. After 400 unwritten: `DeleteRuleInternal()` → **permanent rule loss** for all subsequent rules
8. No recovery: `ReshuffleRules()` skips `!IsInstalled()` rules (line 386-389)

### Constants

| Constant | Value | File |
|----------|-------|------|
| `FLOWSPEC_MAX_UNWRITTEN_IN_TABLE` | 400 | `FlowspecTable.hpp:24` |
| `EXTERNAL_FLOWSPEC_IPV4_MINIMUM_CAPACITY` | 12,000 | `bcm_wrap_pmf.h:30` |
| `EXTERNAL_FLOWSPEC_IPV6_MINIMUM_CAPACITY` | 4,000 | `bcm_wrap_pmf.h:31` |

### Fix Required

`RollbackRule()` must release the reserved entries:

```cpp
void FlowspecTcamManager::RollbackRule(FlowspecRuleData &flowspecRuleData) {
    // ... existing rollback logic ...
    
    // FIX: Release the reservation that was made in ReserveQualifiers
    std::lock_guard<std::mutex> lock(m_lock);
    m_reserved -= flowspecRuleData.GetNumberOfTcamRules();
}
```

Additionally, `HandleRuleFailedWrite()` should release `m_reserved` when calling `DeleteRuleInternal()` for rules past the 400 threshold.

A retry mechanism for "unwritten" rules (when TCAM space becomes available) would also prevent permanent rule loss.

---

## Relationship to BUG_FLOWSPEC_TCAM_OVERFLOW_NO_RECOVERY

| Aspect | TCAM Overflow Bug | This Bug (Reservation Leak) |
|--------|------------------|-----------------------------|
| **Trigger** | SAFI 133 fills TCAM, SAFI 134 rejected | Pure SAFI 134 burst — no TCAM competition |
| **TCAM actually full?** | Yes (12000/12000) | No (7488/12000) |
| **400 threshold** | Same mechanism | Same mechanism |
| **No recovery** | Same mechanism | Same mechanism |
| **Root cause** | TCAM genuinely full | `m_reserved` leak → false capacity exhaustion |
| **Severity** | Only when competing SAFIs | Any bulk injection can trigger |

Both bugs share the same downstream mechanism (`HandleRuleFailedWrite` → 400 threshold → permanent deletion). This bug exposes a **deeper root cause**: the reservation accounting error that can trigger false TCAM exhaustion even without genuine capacity issues.

---

## Comparison Table

| Metric | Expected (16K rules, TCAM has capacity) | Actual (burst injection) |
|--------|----------------------------------------|--------------------------|
| IPv4 NCP Received | 12,000 | 7,888 |
| IPv4 NCP Installed | 12,000 | 7,488 |
| IPv4 Silently Dropped | 0 | 4,112 |
| IPv6 NCP Received | 4,000 | 3,962 |
| IPv6 NCP Installed | 4,000 | 3,562 |
| IPv6 Silently Dropped | 0 | 38 |
| TCAM "out of resources" errors | 0 | 800 (400/family) |
| NCP trace | No errors | "No more space left in TCAM" + "Too many unwritten rules" |

---

Session log: `~/SCALER/FLOWSPEC_VPN/debug_sessions/SESSION_2026-03-01_1525_PE-1_false-tcam-full-burst.md`
