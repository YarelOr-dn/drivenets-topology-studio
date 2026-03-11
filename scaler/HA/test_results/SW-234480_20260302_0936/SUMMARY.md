# FlowSpec VPN Scale Test Report (SW-234480)

Device: YOR_CL_PE-4
Run: 2026-03-02T09:41:01.703554
ExaBGP session: pe_1
RT: 1234567:301 | RD: 1.1.1.1:100

## Results Summary

| Test | Name | BGP Routes | DP Installed | Convergence | Verdict |
|------|------|-----------|-------------|-------------|---------|
| test_12 | Session Flap Recovery at Scale (20K < 90s) | 20000 | 12000 | 5.5s | PASS |

**Result: 1 PASS / 0 FAIL / 0 SKIP / 0 ERROR (out of 1 tests)**

### test_12: Session Flap Recovery at Scale (20K < 90s)

- **Verdict**: PASS
- **Recovery**: 5.5s
- **BGP PfxRcd**: 20000
- **DP Installed**: 12000
- **TCAM**: {'installed': 12000, 'total': 12000, 'percent': 100.0, 'ipv6_installed': 21, 'ipv6_total': 4000}
