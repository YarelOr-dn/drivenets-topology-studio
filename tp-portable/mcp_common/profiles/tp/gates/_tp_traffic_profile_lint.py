#!/usr/bin/env python3
"""Per-TC background-traffic profile gate (anchor: tp:traffic-profile-topology-match).

Every `requires_traffic` TC MUST carry a machine-consumable `traffic_profile` that:
  1. exists and is not a NEEDS_TOPOLOGY_PROFILE placeholder;
  2. is TOPOLOGY-MATCHED - its topology_ref equals the TC's topology_ref, and every
     device referenced by the source + interested OIFs is a PE that appears in the
     TC's own topology (the topology-illustration / prereq), so the traffic can't be
     for a device the TC doesn't test;
  3. respects the /SDK Spirent rail - rate_mbps < 10 (hard cap);
  4. declares a direction and at least one interested OIF + at least one dark port.

Exit 0 = all requires_traffic TCs have a valid, topology-matched, capped profile.
Exit 1 = >=1 hard gap. Usage: python3 _tp_traffic_profile_lint.py --epic SW-XXXXX [--json]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from _tp_paths import default_data_dir, resolve_data_dir

RATE_CAP = 10  # /SDK: no Spirent stream >= 10 Mbps

# IRB-correctness: an L3->L2 leg is valid ONLY with an IRB in the EVI+IGMP/PIM.
# L2-only topologies have no IRB; and a TC that explicitly runs the No-IRB /
# IRB-not-in-multicast / snooping-disabled variant has no L3->L2 leg either.
L2_ONLY_TOPOS = {"T1", "T4", "T5", "T6"}
NO_IRB_TC_SIGNALS = ("no-irb", "not-in-igmp-pim", "snoop-disabled", "snooping-disabled")


def _pes_in_topology(tc):
    """Set of PE tokens the TC actually depicts (topology diagram + prereq + devices)."""
    blob = " ".join([
        tc.get("topology_diagram", "") or "",
        " ".join(tc.get("topology_notes", []) or []),
        " ".join(str(x) for row in (tc.get("devices") or []) for x in row),
        tc.get("jira_wiki_body", "") or "",
    ])
    return set(re.findall(r"PE-[A-Z0-9-]+", blob))


def _profile_pes(prof):
    out = set()
    src = (prof.get("source") or {}).get("pe", "")
    for tok in re.findall(r"PE-[A-Z0-9-]+", str(src)):
        out.add(tok)
    for oif in prof.get("interested_oifs", []) or []:
        for tok in re.findall(r"PE-[A-Z0-9-]+", str(oif.get("pe", ""))):
            out.add(tok)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--epic", required=True)
    ap.add_argument("--dir", default=default_data_dir())
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    epic_dir = resolve_data_dir(a.dir) / a.epic
    man = json.load(open(epic_dir / "manifest.json", encoding="utf-8"))
    fr = json.load(open(epic_dir / "full_result.json", encoding="utf-8"))
    fr_by_id = {t["id"]: t for t in (fr.get("test_cases") or fr if isinstance(fr, list) else fr["test_cases"])}

    hard, ok = [], 0
    for t in man["test_cases"]:
        if not bool((t.get("test_hints") or {}).get("requires_traffic")):
            continue
        tid = t["id"]
        prof = t.get("traffic_profile")
        frt = fr_by_id.get(tid, {})
        problems = []
        if not prof:
            problems.append("no traffic_profile")
        elif prof.get("NEEDS_TOPOLOGY_PROFILE"):
            problems.append(f"NEEDS_TOPOLOGY_PROFILE (topology_ref={prof.get('topology_ref')})")
        else:
            if str(prof.get("topology_ref", "")).upper() != str(t.get("topology_ref", "")).upper():
                problems.append(
                    f"topology_ref mismatch (profile={prof.get('topology_ref')} vs tc={t.get('topology_ref')})"
                )
            depicted = _pes_in_topology({**t, **frt})
            if depicted:
                stray = sorted(p for p in _profile_pes(prof) if p not in depicted)
                if stray:
                    problems.append(f"profile references PE(s) not in the TC topology: {stray}")
            dirn = str(prof.get("direction", ""))
            claims_l3 = dirn.upper().startswith("L3->L2") or "via irb" in dirn.lower()
            ref = str(t.get("topology_ref", "")).upper()
            idl = tid.lower()
            no_irb_tc = ref in L2_ONLY_TOPOS or any(s in idl for s in NO_IRB_TC_SIGNALS)
            if claims_l3 and no_irb_tc:
                problems.append(
                    f"direction claims L3->L2 but TC has NO IRB path "
                    f"(topology={ref}, no-irb-variant={any(s in idl for s in NO_IRB_TC_SIGNALS)}) "
                    f"- L3->L2 impossible in the EVI"
                )
            rate = prof.get("rate_mbps")
            if not isinstance(rate, (int, float)) or rate >= RATE_CAP:
                problems.append(f"rate_mbps={rate} violates /SDK cap (<{RATE_CAP})")
            if not prof.get("direction"):
                problems.append("no direction")
            if not prof.get("interested_oifs"):
                problems.append("no interested OIFs")
            if not prof.get("dark_ports"):
                problems.append("no dark ports")
        if problems:
            hard.append((tid, t.get("topology_ref", ""), problems))
        else:
            ok += 1

    if a.json:
        print(json.dumps({
            "epic": a.epic,
            "ok": ok,
            "hard": [{"tc": i, "topology": r, "problems": p} for i, r, p in hard],
        }, indent=2))
    else:
        print(f"traffic-profile topology-match gate -- {a.epic}: valid {ok} | HARD gaps {len(hard)}")
        for tid, ref, probs in hard:
            print(f"  [FAIL] {tid} ({ref})")
            for p in probs:
                print(f"         - {p}")
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
