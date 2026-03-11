# FlowSpec VPN Scale Test Report (SW-234480)

Device: YOR_CL_PE-4
Run: 2026-03-02T09:21:40.805201
ExaBGP session: pe_1
RT: 1234567:301 | RD: 1.1.1.1:100

## Results Summary

| Test | Name | BGP Routes | DP Installed | Convergence | Verdict |
|------|------|-----------|-------------|-------------|---------|
| test_03 | Route Churn -- Bulk Add/Remove x5 | - | - | - | PASS |
| test_08 | Exceed DP Limit -- Incremental (14K) | 13514 | 11 | - | PASS |
| test_09 | Exceed DP Limit -- Bulk (15K) | 14942 | 11 | - | PASS |
| test_12 | Session Flap Recovery at Scale (20K < 90s) | - | - | - | FAIL |

**Result: 3 PASS / 1 FAIL / 0 SKIP / 0 ERROR (out of 4 tests)**

### test_03: Route Churn -- Bulk Add/Remove x5

- **Verdict**: PASS
- **Churn Cycles**: 5 completed
- **Session Stable**: True

### test_08: Exceed DP Limit -- Incremental (14K)

- **Verdict**: PASS
- **BGP PfxRcd**: 13514
- **DP Installed**: 11
- **TCAM**: {'installed': 12000, 'total': 12000, 'percent': 100.0, 'ipv6_installed': 21, 'ipv6_total': 4000}

### test_09: Exceed DP Limit -- Bulk (15K)

- **Verdict**: PASS
- **BGP PfxRcd**: 14942
- **DP Installed**: 11
- **TCAM**: {'installed': 12000, 'total': 12000, 'percent': 100.0, 'ipv6_installed': 21, 'ipv6_total': 4000}

### test_12: Session Flap Recovery at Scale (20K < 90s)

- **Verdict**: FAIL
- **Reason**: preload_not_converged (got 2/20000)
