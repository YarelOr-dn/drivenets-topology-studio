# FlowSpec VPN Scale Test Report (SW-234480)

Device: YOR_CL_PE-4
Run: 2026-03-02T10:13:28.338319
ExaBGP session: pe_1
RT: 1234567:301 | RD: 1.1.1.1:100

## Results Summary

| Test | Name | BGP Routes | DP Installed | Convergence | Verdict |
|------|------|-----------|-------------|-------------|---------|
| test_02 | IPv4 + IPv6 Combined (12K + 4K) | - | - | - | FAIL |
| test_10 | Withdraw All at Once (20K bulk) | - | - | - | PASS |
| test_11 | Exceed BGP Limit (25K) | 25000 | 12000 | - | PASS |

**Result: 2 PASS / 1 FAIL / 0 SKIP / 0 ERROR (out of 3 tests)**

### test_02: IPv4 + IPv6 Combined (12K + 4K)

- **Verdict**: FAIL
- **Reason**: IPv6 TCAM: 0/4000

### test_10: Withdraw All at Once (20K bulk)

- **Verdict**: PASS
- **TCAM**: {'installed': 0, 'total': 12000, 'percent': 0.0, 'ipv6_installed': 0, 'ipv6_total': 4000}

### test_11: Exceed BGP Limit (25K)

- **Verdict**: PASS
- **BGP PfxRcd**: 25000
- **DP Installed**: 12000
- **TCAM**: {'installed': 12000, 'total': 12000, 'percent': 100.0, 'ipv6_installed': 0, 'ipv6_total': 4000}
