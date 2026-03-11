# FlowSpec VPN Scale Test Report (SW-234480)

Device: YOR_CL_PE-4 (Cluster CL-16, NCP-6)
Software: 26.1.0.27
Date: 2026-03-02
ExaBGP session: pe_1 → PE-1 → RR (2.2.2.2) → PE-4
RT: 1234567:301 | RD: 1.1.1.1:100

## TCAM Limits (from limits.json)

| AFI | TCAM Limit | BGP Max |
|-----|-----------|---------|
| IPv4 FlowSpec | 12,000/NCP | 20,000 |
| IPv6 FlowSpec | 4,000/NCP | 20,000 |

## Results Summary

| Test | Name | BGP Routes | DP Installed | Convergence | Verdict |
|------|------|-----------|-------------|-------------|---------|
| test_01 | Max BGP Routes (20K) + Convergence | 20,000 | 12,000 | ~5s | **PASS** |
| test_03 | Route Churn -- Bulk Add/Remove x5 | 10,000/cycle | - | 4.5-7.7s/cycle | **PASS** |
| test_08 | Exceed DP Limit -- Incremental (14K) | 14,000 | 12,000 (100%) | 5.0s | **PASS** |
| test_09 | Exceed DP Limit -- Bulk (15K) | 15,000 | 12,000 (100%) | 4.6s | **PASS** |
| test_12 | Session Flap Recovery at Scale (20K) | 20,000 | 12,000 | 5.5s recovery | **PASS** |

**Quick-win: 5 PASS / 0 FAIL**

### Phase 2 Results (added 2026-03-02)

| Test | Name | BGP Routes | DP Installed | Convergence | Verdict |
|------|------|-----------|-------------|-------------|---------|
| test_10 | Withdraw All at Once | 20,000→0 | 0/12,000 → 0 | ~5s | **PASS** |
| test_11 | Exceed BGP Limit (25K) | 25,000 | 12,000 | 5.5s | **PASS** |
| test_02 | IPv4 + IPv6 Combined | 12K+4K | IPv4=12K, IPv6=4K | ~30s | **PASS** (after RT fix) |

**Phase 2: 3 PASS / 0 FAIL**

**Note on test_02**: Initially reported as FAIL (IPv6=0/4000). Root cause: test tooling RT
mismatch — ExaBGP used RT=1234567:300 for IPv6, but VRF imports IPv6-flowspec on RT=1234567:401.
After fixing bgp_tool.py parser and orchestrator rt_overrides, combined injection works perfectly:
IPv4=12K/12K + IPv6=4K/4K, ZERO NCP errors.

## Detailed Results

### test_01: Max BGP Routes (20K) + Convergence
- 20K IPv4 FlowSpec-VPN routes injected via ExaBGP in stress mode
- BGP converged to 20K PfxAccepted
- TCAM correctly capped at 12K (hardware limit)
- No session drops, no crashes

### test_03: Route Churn -- Bulk Add/Remove x5
- 5 cycles of inject 10K → converge → withdraw → repeat
- All cycles completed successfully, session stable throughout
- Convergence per cycle: 4.5s - 7.7s (avg ~5.2s)
- BGP session never dropped during churn

### test_08: Exceed DP Limit -- Incremental (14K)
- Phase 1: 12K routes filled TCAM (100%)
- Phase 2: 2K more routes accepted by BGP (14K total), TCAM stayed at 12K cap
- TCAM: 12,000/12,000 (100.0%)
- No crash, no session drop

### test_09: Exceed DP Limit -- Bulk (15K)
- 15K routes injected in single burst (stress mode)
- BGP accepted all 15K, TCAM capped at 12K
- Stability check passed (15s steady)

### test_12: Session Flap Recovery at Scale (20K < 90s)
- Pre-loaded 20K routes, TCAM at 12K capacity
- Session flapped via `clear bgp neighbor 2.2.2.2`
- **Recovery: 5.5 seconds** (limit: 90s) -- well within tolerance
- Post-recovery: BGP 20K PfxRcd, TCAM 12K installed

## Known Issues (not blocking)

| Issue | Impact | Reference |
|-------|--------|-----------|
| IPv6 FlowSpec TCAM leak | IPv6: only 21/4000 installed (bug) | BUG_FLOWSPEC_TCAM_RESERVED_LEAK_BURST |
| NCP counter truncation at scale | `show flowspec ncp X` output truncated over SSH for 12K+ rules | Fixed: use `\| include "status: installed" \| count` |

## Orchestrator Fixes Applied During Testing

1. **Filename sanitization** -- test names with `/` caused FileNotFoundError (e.g., "Bulk Add/Remove")
2. **TCAM parser rewrite** -- `parse_tcam_usage` now correctly parses multi-column NPU table
3. **NCP counter fix** -- `parse_flowspec_ncp_counters` switched to `count("status: installed")`
4. **Convergence tracking** -- `poll_bgp_convergence` now updates `last_count` before break
5. **Device-side NCP count** -- uses `| include "status: installed" | count` pipe for accuracy at scale
6. **TCAM programming wait** -- 10-30s delay after BGP convergence for TCAM catch-up
7. **IPv6 RT mismatch fix** -- bgp_tool.py `--rt` parser default changed to `None` so per-mode defaults work; orchestrator uses `rt_overrides` dict for mode-specific RTs (IPv6-flowspec → 1234567:401)

## Remaining Tests (SW-234480)

| Test | Name | Status | Notes |
|------|------|--------|-------|
| test_02 | IPv4 + IPv6 Combined | **PASS** | Fixed: RT mismatch in tooling |
| test_10 | Withdraw All at Once | **PASS** | |
| test_11 | Exceed BGP Limit (25K) | **PASS** | |
| test_04 | 12K DP + Traffic Enforcement | PENDING | Agent-driven with /SPIRENT + /XRAY |
| test_05 | Multi-VRF (8 VRFs x 1500) | PENDING | Needs VRF config |
| test_06 | Local Policy at Scale (20/AFI) | PENDING | |
| test_07 | Mixed Local + Remote | PENDING | |
