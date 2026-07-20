# Minimal synthetic HLD for extractor fixture tests
## Group A — Type-7 joins
- **A1** IGMPv2 join behind R1 → Type-7 appears ES-local.
- **A2** IGMPv2 join behind R2 as well → R2 also originates Type-7.

## Group G — Negative
- **G1** Invalid Type-6: v2 and v3 set → treat-as-withdraw.

## Operational Flow: ESI config change
#### Detach old ESI before attach
Changing ESI must detach old membership first.

## Use-case 0.1 — TBD
Placeholder — no need to test yet.