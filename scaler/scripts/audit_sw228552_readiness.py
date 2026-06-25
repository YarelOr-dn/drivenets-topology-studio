#!/usr/bin/env python3
"""Offline readiness audit for SW-228552 TEST recipes."""

from __future__ import annotations

import collections
import json
from pathlib import Path


CATALOG = Path("/home/dn/SCALER/TEST/catalog")


def main() -> int:
    paths = sorted(
        p
        for p in CATALOG.glob("TEST_SW-228552*/recipe.json")
        if ".backup_" not in p.parts
    )
    counts: collections.Counter[str] = collections.Counter()
    buckets: dict[str, list[str]] = collections.defaultdict(list)
    stale_needles = (
        "matching RT-2 MAC-IP behavior",
        "populate EVPN mac-ip-table + advertise RT-2",
        "RT-2 MAC-IP behavior matches the IPv4 PW ARP reference",
    )

    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        text = path.read_text(encoding="utf-8")
        test_id = data.get("id", path.parent.name)
        recipe_type = data.get("type", "<missing>")
        counts[recipe_type] += 1

        phases = data.get("phases") or []
        has_phase_traffic = any(
            isinstance(phase, dict) and phase.get("traffic_contract")
            for phase in phases
        )
        lower_text = text.lower()

        if not data.get("feature_id"):
            buckets["no_feature_id"].append(test_id)
        if not data.get("traffic_contract") and not has_phase_traffic:
            buckets["no_traffic_contract"].append(test_id)
        if not phases:
            buckets["no_phases"].append(test_id)
        if not data.get("prerequisites"):
            buckets["no_prerequisites"].append(test_id)
        if any(needle in text for needle in stale_needles):
            buckets["stale_behavior_text"].append(test_id)
        if "<service_name>" in text or "<vrf-name>" in text or "<DUT" in text:
            buckets["placeholder_text"].append(test_id)
        if "migration" in (recipe_type.lower() + " " + data.get("name", "").lower()):
            buckets["migration"].append(test_id)
        if "counter" in (recipe_type.lower() + " " + data.get("name", "").lower() + " " + lower_text):
            buckets["counter_related"].append(test_id)
        if recipe_type == "scale" or "scale" in data.get("name", "").lower():
            buckets["scale"].append(test_id)

    print(f"recipes={len(paths)}")
    print(f"types={dict(counts)}")
    for name in sorted(buckets):
        values = buckets[name]
        preview = ", ".join(values[:12])
        suffix = "" if len(values) <= 12 else f" ... +{len(values) - 12}"
        print(f"{name}={len(values)} {preview}{suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
