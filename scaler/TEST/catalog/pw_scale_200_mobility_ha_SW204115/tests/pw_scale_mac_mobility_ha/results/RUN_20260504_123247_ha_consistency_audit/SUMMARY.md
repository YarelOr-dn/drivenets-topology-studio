# HA Consistency Audit Summary

- HA exit code: 1
- HA result directory: /home/dn/drivenets-topology-studio/scaler/TEST/catalog/pw_scale_200_mobility_ha_SW204115/tests/pw_scale_mac_mobility_ha/results/RUN_ha_safe_no_bgp_moved_20260504_PE4_RRSA2
- Audit directory: /home/dn/drivenets-topology-studio/scaler/TEST/catalog/pw_scale_200_mobility_ha_SW204115/tests/pw_scale_mac_mobility_ha/results/RUN_20260504_123247_ha_consistency_audit
- Consistency verdict: FAIL
- Total inconsistencies: 1600

## Counts By Category
- missing_mac_or_sequence: 800
- moved_state_ownership_mismatch: 800

## First 10 Samples
- {'category': 'missing_mac_or_sequence', 'device': 'YOR_CL_PE-4', 'service': 'EVPN_PW_S001', 'role': 'pe4_source', 'mac': '00:de:ad:01:00:01', 'detail': {'missing': False, 'sequence': None}}
- {'category': 'moved_state_ownership_mismatch', 'device': 'YOR_CL_PE-4', 'service': 'EVPN_PW_S001', 'role': 'pe4_source', 'mac': '00:de:ad:01:00:01', 'detail': {'expected': 'pw', 'actual': 'unknown', 'interface': None}}
- {'category': 'missing_mac_or_sequence', 'device': 'YOR_CL_PE-4', 'service': 'EVPN_PW_S001', 'role': 'rr_source', 'mac': '00:de:be:01:00:01', 'detail': {'missing': False, 'sequence': None}}
- {'category': 'moved_state_ownership_mismatch', 'device': 'YOR_CL_PE-4', 'service': 'EVPN_PW_S001', 'role': 'rr_source', 'mac': '00:de:be:01:00:01', 'detail': {'expected': 'local', 'actual': 'unknown', 'interface': None}}
- {'category': 'missing_mac_or_sequence', 'device': 'YOR_CL_PE-4', 'service': 'EVPN_PW_S002', 'role': 'pe4_source', 'mac': '00:de:ad:01:00:02', 'detail': {'missing': False, 'sequence': None}}
- {'category': 'moved_state_ownership_mismatch', 'device': 'YOR_CL_PE-4', 'service': 'EVPN_PW_S002', 'role': 'pe4_source', 'mac': '00:de:ad:01:00:02', 'detail': {'expected': 'pw', 'actual': 'unknown', 'interface': None}}
- {'category': 'missing_mac_or_sequence', 'device': 'YOR_CL_PE-4', 'service': 'EVPN_PW_S002', 'role': 'rr_source', 'mac': '00:de:be:01:00:02', 'detail': {'missing': False, 'sequence': None}}
- {'category': 'moved_state_ownership_mismatch', 'device': 'YOR_CL_PE-4', 'service': 'EVPN_PW_S002', 'role': 'rr_source', 'mac': '00:de:be:01:00:02', 'detail': {'expected': 'local', 'actual': 'unknown', 'interface': None}}
- {'category': 'missing_mac_or_sequence', 'device': 'YOR_CL_PE-4', 'service': 'EVPN_PW_S003', 'role': 'pe4_source', 'mac': '00:de:ad:01:00:03', 'detail': {'missing': False, 'sequence': None}}
- {'category': 'moved_state_ownership_mismatch', 'device': 'YOR_CL_PE-4', 'service': 'EVPN_PW_S003', 'role': 'pe4_source', 'mac': '00:de:ad:01:00:03', 'detail': {'expected': 'pw', 'actual': 'unknown', 'interface': None}}
