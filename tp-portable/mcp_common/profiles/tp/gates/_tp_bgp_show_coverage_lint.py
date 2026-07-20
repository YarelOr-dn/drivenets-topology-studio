#!/usr/bin/env python3
"""
_tp_bgp_show_coverage_lint.py - epic-agnostic gate that teaches /TP the BGP
"needs" of any BGP-related feature.

When an epic INTRODUCES or AFFECTS a BGP route-type / AFI (detected from the
generated plan), the CLI category MUST exercise the full BGP operational
surface for those route-types - not just the route-type list. This lint checks
that surface is present and flags the gaps, so a future BGP epic inherits the
SW-211037 coverage automatically instead of relying on the agent to remember.

The required surface (per the dnos-cli-discoveries "three operational layers"
model + guardrails), for each route-type/AFI the epic touches:
  L1 route-type list          show bgp l2vpn evpn route-type <N>
  L2 neighbor decoded NLRI     neighbors <ip> advertised-routes / received-routes
  L3 single-NLRI full attrs    neighbors <ip> received-routes nlri <nlri>
  RD  RD-scoped view           show bgp l2vpn evpn rd <rd>
  CNT per-neighbor accounting  neighbors <ip> prefix-counts
  ITM per-route-type itemize   received-routes | include "type:=<N>"
  BP  bestpath tie-break       bestpath-compare rd <rd> nlri <nlri>   (MH RT-7/8)
  PM  PMSI attribute           (RT-3 IMET single-NLRI detail)         (if RT-3)
  MAX guardrail                neighbor ... address-family <afi> maximum-prefix

Read-only. Advisory by default; --strict exits 1 when a REQUIRED layer is
missing for a BGP-relevant epic. A non-BGP epic is a no-op PASS (not applicable).

Usage:
    python3 _tp_bgp_show_coverage_lint.py --epic SW-XXXXX [--strict]
"""
import argparse, json, re, sys
from pathlib import Path

from _tp_paths import resolve_data_dir, default_data_dir



def cli_bodies(mf):
    out = []
    for tc in mf["test_cases"]:
        cat = tc.get("jira_category") or tc.get("category") or ""
        if cat == "CLI" or "CLI" in (tc.get("covers_categories") or []):
            out.append((tc["id"], tc["jira_wiki_body"]))
    return out


def all_bodies(mf):
    return "\n".join(tc["jira_wiki_body"] for tc in mf["test_cases"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epic", required=True)
    ap.add_argument("--dir", default=default_data_dir())
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    mf = json.loads((resolve_data_dir(getattr(a, 'dir', None)) / a.epic / "manifest.json").read_text())
    blob = all_bodies(mf)

    # (1) Is this a BGP-relevant epic, and which route-types does it touch?
    rts = set(re.findall(r'\bRT-([1-8])\b', blob)) | set(re.findall(r'route-type ([1-8])\b', blob)) \
        | set(re.findall(r'type:=([1-8])\b', blob))
    rts = sorted(int(x) for x in rts)
    bgp_relevant = bool(rts) or ("l2vpn evpn" in blob.lower())
    if not bgp_relevant:
        print(f"[N/A] {a.epic}: no BGP route-type / l2vpn-evpn surface detected -> BGP-show-coverage lint not applicable.")
        return

    cli = cli_bodies(mf)
    cli_blob = "\n".join(b for _, b in cli)

    def present(pat, scope=cli_blob):
        return bool(re.search(pat, scope, re.I))

    # route-types the epic introduces beyond the always-present base (1/2/3/4 are
    # base EVPN; 6/7/8 are the multicast/IGMP-proxy additions). We require the
    # full surface for EVERY referenced type, but BP/PMSI are conditional.
    checks = []  # (code, label, required, covered, detail)
    checks.append(("L1", "route-type list (show ... route-type <N>)", True,
                   present(r'route-type [1-8]\b'), ""))
    checks.append(("L2", "neighbor decoded NLRI (advertised-routes / received-routes)", True,
                   present(r'advertised-routes') and present(r'received-routes'), ""))
    checks.append(("L3", "single-NLRI full attrs (received-routes nlri / advertised-routes nlri)", True,
                   present(r'(received|advertised)-routes nlri'), ""))
    checks.append(("RD", "RD-scoped view (show ... rd <rd>)", True,
                   present(r'evpn rd <'), ""))
    checks.append(("CNT", "per-neighbor accounting (prefix-counts)", True,
                   present(r'prefix-counts'), ""))
    checks.append(("ITM", "per-route-type itemization (received-routes | include type:=<N>)", True,
                   present(r'type:=[1-8]'), ""))
    # conditional layers
    mh = any(n in rts for n in (7, 8))
    checks.append(("BP", "bestpath tie-break (bestpath-compare) [MH RT-7/8]", mh,
                   present(r'bestpath-compare'),
                   "required because the epic touches multihoming RT-7/RT-8" if mh else "not applicable (no RT-7/8)"))
    imet = 3 in rts
    checks.append(("PM", "PMSI attribute (RT-3 IMET single-NLRI detail)", imet,
                   present(r'\bpmsi\b'),
                   "required because the epic touches RT-3 IMET" if imet else "not applicable (no RT-3)"))
    # guardrail: maximum-prefix on the AFI carrying the new route-types. This is
    # a behavioral/scale test, so it may live in the Scale category (not CLI) -
    # check the WHOLE plan, not just the CLI category.
    checks.append(("MAX", "AFI guardrail (neighbor ... maximum-prefix on the l2vpn-evpn AFI) [CLI or Scale]", True,
                   present(r'maximum-prefix', scope=blob), ""))

    gaps = [c for c in checks if c[2] and not c[3]]
    if a.json:
        print(json.dumps({"epic": a.epic, "route_types": rts,
                          "checks": [{"code": c[0], "label": c[1], "required": c[2],
                                      "covered": c[3], "detail": c[4]} for c in checks],
                          "gaps": [c[0] for c in gaps]}, indent=2))
    else:
        print(f"BGP-show-coverage lint -- {a.epic} (route-types touched: {rts or '[AFI-only]'})")
        for code, label, req, cov, detail in checks:
            if not req:
                mark = "n/a "
            else:
                mark = "OK  " if cov else "GAP "
            extra = f"  ({detail})" if detail else ""
            print(f"  [{mark}] {code:3} {label}{extra}")
        if gaps:
            print(f"\n[FAIL] {len(gaps)} required BGP show layer(s) missing from the CLI category: "
                  f"{', '.join(c[0] for c in gaps)}")
            print("  Fix: extend the CLI route-type show-TCs with the missing layer(s) using "
                  "live cmd_search-verified syntax (see tp:bgp-feature-show-coverage).")
        else:
            print("\n[PASS] all required BGP show layers are covered in the CLI category.")

    if a.strict and gaps:
        sys.exit(1)


if __name__ == "__main__":
    main()
