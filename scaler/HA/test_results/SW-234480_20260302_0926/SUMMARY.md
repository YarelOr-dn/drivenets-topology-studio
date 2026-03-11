# FlowSpec VPN Scale Test Report (SW-234480)

Device: YOR_CL_PE-4
Run: 2026-03-02T09:29:44.433271
ExaBGP session: pe_1
RT: 1234567:301 | RD: 1.1.1.1:100

## Results Summary

| Test | Name | BGP Routes | DP Installed | Convergence | Verdict |
|------|------|-----------|-------------|-------------|---------|
| test_12 | Session Flap Recovery at Scale (20K < 90s) | 0 | 0 | 5.4s | FAIL |

**Result: 0 PASS / 1 FAIL / 0 SKIP / 0 ERROR (out of 1 tests)**

### test_12: Session Flap Recovery at Scale (20K < 90s)

- **Verdict**: FAIL
- **Reason**: DP not restored: 0/12000
- **Recovery**: 5.4s
- **TCAM**: {'installed': 0, 'total': 12000, 'percent': 0.0, 'ipv6_installed': 0, 'ipv6_total': 4000}
