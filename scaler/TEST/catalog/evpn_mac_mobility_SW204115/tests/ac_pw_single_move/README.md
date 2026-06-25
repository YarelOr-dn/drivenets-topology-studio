# TEST_mac_mob_ac_pw_single_move_SW205198

Real-topology AC<->PW MAC mobility test derived from the passed
`TEST_mac_mob_basic_SW205160` run.

## What This Tests

This recipe uses one MAC, `00:de:ad:00:04:01`, and moves it through the real
`EVPN_SI_VPLS_1` service:

1. PE-4 local AC: untagged traffic to `ge100-18/0/1` must learn as `L>`.
2. RR-SA-2 remote AC: Q-in-Q `215/3001` traffic must move the same MAC to the
   VPLS PW, so PE-4 sees `v>` via peer `2.2.2.2`.
3. PE-4 local AC again: untagged traffic must move the MAC back to `L>` and
   re-advertise RT-2.

## No-Guessing Contract

The recipe declares strict `mcp_dnaas_teach_plan` prerequisites for both traffic
sources. The runner must consume the resulting frame recipes before traffic is
sent:

- PE-4 local AC: `--no-qinq`, no `--vlan`, no `--inner-vlan`.
- RR-SA-2 remote AC: `--vlan 215 --inner-vlan 3001`.

Move scenarios use `cleanup_scope: "preserve"` so the previous MAC source is not
cleared before the next trigger. Clearing would make the scenario fresh learning
instead of a real mobility event.
