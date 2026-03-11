# FlowSpec VPN Scale Test Report (SW-234480)

Device: YOR_CL_PE-4
Run: 2026-03-02T09:34:58.706599
ExaBGP session: pe_1
RT: 1234567:301 | RD: 1.1.1.1:100

## Results Summary

| Test | Name | BGP Routes | DP Installed | Convergence | Verdict |
|------|------|-----------|-------------|-------------|---------|
| test_12 | Session Flap Recovery at Scale (20K < 90s) | 20000 | 11 | 5.3s | FAIL |

**Result: 0 PASS / 1 FAIL / 0 SKIP / 0 ERROR (out of 1 tests)**

### test_12: Session Flap Recovery at Scale (20K < 90s)

- **Verdict**: FAIL
- **Reason**: DP not restored: 11/12000
- **Recovery**: 5.3s
- **BGP PfxRcd**: 20000
- **DP Installed**: 11
- **TCAM**: {'installed': 12000, 'total': 12000, 'percent': 100.0, 'ipv6_installed': 21, 'ipv6_total': 4000}
