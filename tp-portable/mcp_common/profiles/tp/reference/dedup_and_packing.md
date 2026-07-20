# Dedup and Multi-Category Packing

The merged `/TP` pipeline generates more granular TCs than the old `/TP`.
This file prevents duplicate inflation while preserving traceability.

## Dedup Fingerprint

Build a fingerprint from normalized fields:

- `trigger_type`
- `source_role`
- `topology_shape`
- `data_plane_behavior`
- `expected_behavior`
- `verification_surface`
- `failure_mode`
- `management_surface`

Normalize by lowercasing, removing punctuation, replacing concrete device names
with roles, and stripping incidental wording.

## Collapse Rules

Collapse into one TC when all are true:

- Same trigger.
- Same expected behavior.
- Same verification command surface.
- Same topology role.
- Same pass/fail assertion.

Keep as separate TCs when any of these changes:

- Topology or source role.
- HA trigger, process, container, or restart type.
- Datapath behavior.
- Control-plane behavior.
- Management plane: CLI vs NETCONF vs gNMI vs RESTCONF.
- Scale dimension.
- Failure mode or negative case.
- Timer boundary or dynamic timer behavior.

## Multi-Category Packing

One TC may cover multiple categories only when:

- Each category has at least one explicit pass criterion.
- The TC manifest lists `covers_categories`.
- The quality audit lists why packing is legitimate.
- `/TEST` automation can still map the TC to one primary `automation_type`.

Example: one EVPN-SI IRB MAC-IP move TC may cover `Sanity`, `Counters`, and
`Logs/Traces` if it verifies user-visible state, datapath counters, and logs in
one coherent flow.

Do NOT pack when the category requires a different setup or trigger. Example:
`HA`, `Scale`, and `Upgrade/Downgrade` are usually separate TCs, even if they
verify the same final show command.

## Variants Are Not Coverage

Costake's rule wins:

- If a scenario changes topology, trigger event, process, or datapath behavior,
  it is a standalone TC.
- Variants are only for trivial parameter substitutions, such as IPv4 vs IPv6
  in an otherwise identical test.

## Audit Output

`quality_audit.md` must include:

- duplicate fingerprints that were collapsed
- TCs packed across multiple categories
- categories that were intentionally not packed
- scenarios promoted from variants to standalone TCs
