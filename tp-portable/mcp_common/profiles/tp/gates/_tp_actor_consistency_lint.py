#!/usr/bin/env python3
"""
_tp_actor_consistency_lint.py - epic-agnostic gate that enforces ACTOR-NAME
consistency across the three places a traffic actor appears in a /TP TC
(anchor: tp:actor-name-consistency):

  (a) the "Traffic Actors" list        (who sources / receives / queries)
  (b) the "Topology Illustration"       (diagram + notes labels)
  (c) the Procedure Dev / step namings  (per-step actor + location)

They must all use the SAME canonical actor tokens (RCVR-1, RCVR-2, SRC,
MROUTER, EMU-PEER) with no drift. The gate holds the sane invariant TRIANGLE:

  procedure-Dev actor  =>  Traffic Actors list  =>  depicted in Topology

so a Procedure step can never name an actor the list omits, and a listed actor
is always drawn in the topology. The topology template MAY depict optional/idle
actors as a superset (topology -> list is therefore advisory, not a hard fail).

Read-only. Exits 1 when any HARD mismatch is found (a real gate); INFO/advisory
lines never fail. Reads the epic's full_result.json (structured steps).

Usage:
    python3 _tp_actor_consistency_lint.py --epic SW-XXXXX [--json] [--strict]
"""
import argparse, json, re, sys
from pathlib import Path

from _tp_paths import resolve_data_dir, default_data_dir


CANON = ("RCVR-1", "RCVR-2", "SRC", "MROUTER", "EMU-PEER")
# How each canonical actor may be DEPICTED in the topology illustration
# (case-insensitive) - the exact token OR a role keyword, so 'RCVR-2' matches a
# 'rcvr/idle' label and 'EMU-PEER' matches a 'remote peer via RR' label.
ROLE = {
    "RCVR-1": ("rcvr", "receiver"),
    "RCVR-2": ("rcvr", "receiver"),
    "SRC": ("src", "source"),
    "MROUTER": ("mrouter", "querier", "pim"),
    "EMU-PEER": ("emu-peer", "emu", "remote", "peer", "rr"),
}


def tokens_in(text):
    out = set()
    for c in CANON:
        if re.search(r"\b" + re.escape(c) + r"\b", str(text)):
            out.add(c)
    return out


def list_tokens(tc):
    toks = set()
    for a in (tc.get("traffic_actors") or []):
        head = str(a).split(" -", 1)[0].strip()
        toks |= tokens_in(head)
    return toks


def depicted(tok, topo_text):
    tl = topo_text.lower()
    return any(r in tl for r in ROLE[tok])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epic", required=True)
    ap.add_argument("--dir", default=default_data_dir())
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true",
                    help="accepted for CLI parity; the gate fails on any hard "
                         "mismatch regardless")
    a = ap.parse_args()

    fr_path = resolve_data_dir(getattr(a, 'dir', None)) / a.epic / "full_result.json"
    fr = json.loads(fr_path.read_text())
    tcs = fr.get("test_cases") or []

    proc_not_list = []   # (id, [tokens], listed)   HARD  procedure -> list
    list_not_topo = []   # (id, [tokens])           HARD  list -> topology
    topo_not_list = []   # (id, [tokens])           INFO  topology -> list (superset)

    for t in tcs:
        alist = list_tokens(t)
        dev_toks = set()
        for s in (t.get("steps") or []):
            dev_toks |= tokens_in(s.get("dev", ""))
        topo = (str(t.get("topology_diagram", "")) + " "
                + " ".join(t.get("topology_notes") or []))
        topo_toks = tokens_in(topo)

        miss_a = sorted(dev_toks - alist)
        if miss_a:
            proc_not_list.append((t.get("id"), miss_a, sorted(alist)))
        miss_b = sorted(x for x in alist if not depicted(x, topo))
        if miss_b:
            list_not_topo.append((t.get("id"), miss_b))
        miss_c = sorted(topo_toks - alist)
        if miss_c:
            topo_not_list.append((t.get("id"), miss_c))

    hard = len(proc_not_list) + len(list_not_topo)

    if a.json:
        print(json.dumps({
            "epic": a.epic, "tcs": len(tcs),
            "procedure_actor_not_in_list": proc_not_list,
            "list_actor_not_in_topology": list_not_topo,
            "topology_actor_not_in_list_advisory": topo_not_list,
            "hard_mismatches": hard,
        }, indent=2))
    else:
        print(f"actor-name consistency lint -- {a.epic} ({len(tcs)} TC(s))")
        print(f"  [{'OK  ' if not proc_not_list else 'FAIL'}] A  every Procedure Dev actor is in the Traffic Actors list")
        for tid, toks, listed in proc_not_list[:12]:
            print(f"         {tid}: Dev names {toks} not in list {listed}")
        print(f"  [{'OK  ' if not list_not_topo else 'FAIL'}] B  every Traffic Actors list actor is depicted in the Topology")
        for tid, toks in list_not_topo[:12]:
            print(f"         {tid}: listed {toks} not depicted in topology")
        print(f"  [INFO] C  topology depicts {len(topo_not_list)} TC(s) with a superset actor "
              f"(optional/idle) not in the per-TC list (allowed)")
        if hard == 0:
            print("\n[PASS] actor names are consistent across Traffic-Actors / Topology / Procedure "
                  "(0 mismatches).")
        else:
            print(f"\n[FAIL] {hard} hard actor-name mismatch(es). "
                  "Fix: name only listed actors in Dev cells (enforce_actor_consistency) "
                  "and depict every listed actor in the topology template (see tp:actor-name-consistency).")

    if hard:
        sys.exit(1)


if __name__ == "__main__":
    main()
