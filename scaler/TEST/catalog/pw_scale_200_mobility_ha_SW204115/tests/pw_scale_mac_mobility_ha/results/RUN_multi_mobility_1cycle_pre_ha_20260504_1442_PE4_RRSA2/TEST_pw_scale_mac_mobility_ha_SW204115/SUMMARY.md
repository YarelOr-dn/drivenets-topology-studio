# PW Scale MAC Mobility HA Result

- Verdict: PASS
- Run directory: `/home/dn/drivenets-topology-studio/scaler/TEST/catalog/pw_scale_200_mobility_ha_SW204115/tests/pw_scale_mac_mobility_ha/results/RUN_multi_mobility_1cycle_pre_ha_20260504_1442_PE4_RRSA2/TEST_pw_scale_mac_mobility_ha_SW204115`
- Services: 200
- StreamBlocks: 2
- Inner VLAN window: 3101..3300
- Label budget per device: 1600 slots

| Phase | Result | Detail |
|---|---|---|
| `multi_mobility_cycle_1_baseline_activation` | PASS | started 2 modifier StreamBlocks |
| `multi_mobility_cycle_1_baseline_verify` | PASS | all service MACs learned on both sides |
| `multi_mobility_cycle_1_moved_activation` | PASS | started 2 reverse modifier StreamBlocks |
| `multi_mobility_cycle_1_moved_verify` | PASS | all service MACs moved to opposite DUT |
