# PW Scale MAC Mobility HA Result

- Verdict: PASS
- Run directory: `/home/dn/drivenets-topology-studio/scaler/TEST/catalog/pw_scale_200_mobility_ha_SW204115/tests/pw_scale_mac_mobility_ha/results/RUN_mass_mobility_200_before_restart_PE4_RRSA2/TEST_pw_scale_mac_mobility_ha_SW204115`
- Services: 200
- StreamBlocks: 2
- Inner VLAN window: 3101..3300
- Label budget per device: 1600 slots

| Phase | Result | Detail |
|---|---|---|
| `mass_mobility_streams_create` | PASS | created 2 reverse modifier StreamBlocks for 400 logical flows |
| `mass_mobility_stream_activation` | PASS | started 2 reverse modifier StreamBlocks |
| `verify_mass_mobility` | PASS | all service MACs moved to opposite DUT |
