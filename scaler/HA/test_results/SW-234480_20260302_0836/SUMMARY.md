# FlowSpec VPN Scale Test Report (SW-234480)

Device: YOR_CL_PE-4
Run: 2026-03-02T08:39:56.055257
ExaBGP session: pe_1
RT: 1234567:301 | RD: 1.1.1.1:100

## Results Summary

| Test | Name | BGP Routes | DP Installed | Convergence | Verdict |
|------|------|-----------|-------------|-------------|---------|
| test_01 | Max BGP Routes (20K) + Convergence | 12000 | 0 | 182.3s | FAIL |

**Result: 0 PASS / 1 FAIL / 0 SKIP / 0 ERROR (out of 1 tests)**

### test_01: Max BGP Routes (20K) + Convergence

- **Verdict**: FAIL
- **Reason**: not_converged (got 12000/20000)
- **Convergence**: 182.3s
- **BGP PfxRcd**: 12000
- **TCAM**: {'installed': 0, 'total': 0, 'percent': 0.0}
