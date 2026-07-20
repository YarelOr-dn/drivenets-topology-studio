#!/usr/bin/env python3
"""
_tp_counter_coverage_lint.py - epic-agnostic gate that teaches /TP the COUNTER
"needs" of any feature that introduces or affects counters/statistics.

A feature that adds or touches counters is not covered by "a show renders a
number" - the counters must be proven to move correctly and reset. When the
generated plan is counter-relevant (detected below), this lint checks the plan
exercises the counter contract and flags the gaps, so a future counter-bearing
epic inherits the SW-211037 rigor automatically.

Required counter contract (when relevant):
  DELTA  before/after correctness  the counter INCREASES by exactly the driven
                                   events (after-minus-before == stimulus count)
  CLEAR  reset semantics           `clear ... counters` returns the counter to 0
                                   (and never negative / no stale)
  SCOPE  correct granularity       per-instance AND/OR per-neighbor/per-interface
                                   counters (whichever the feature exposes)
Conditional:
  ENABLE opt-in counters           if the counters are opt-in (enable/admin-state),
                                   a TC proves enable-then-count and off-then-frozen

Read-only. Advisory by default; --strict exits 1 when a REQUIRED counter check is
missing for a counter-relevant epic. A non-counter epic is a no-op PASS.

Usage:
    python3 _tp_counter_coverage_lint.py --epic SW-XXXXX [--strict]
"""
import argparse, json, re, sys
from pathlib import Path

from _tp_paths import resolve_data_dir, default_data_dir


# ---- relevance + contract signals -----------------------------------------
COUNTER_TOKEN = re.compile(r'\bcounter[s]?\b|\bstatistics\b|TX \w+ Packets|'
                           r'RX \w+ Packets|prefix-counts|packets/bytes', re.I)
CLEAR_ZERO = re.compile(r'clear\b[^.]*counter[^.]*(zero|reset|back to 0|to 0\b|=\s*0)|'
                        r'counter[^.]*(reset to|returns to|back to)\s*(zero|0)', re.I)
CLEAR_ANY = re.compile(r'clear\b[^.]*counter', re.I)
DELTA = re.compile(r'increase[sd]?\b|after minus before|\bdelta\b|increment[s]?\b[^.]*=='
                   r'|==\s*the (transmitted|driven|number|count)|by exactly', re.I)
SCOPE_INST = re.compile(r'per-instance|per instance|instance <?\w+ (detail|counter)', re.I)
SCOPE_PEER = re.compile(r'per-neighbor|per neighbor|per-interface|per interface|per-port', re.I)
ENABLE_OPTIN = re.compile(r'counter[s]? (enable|admin-state|enabled)|enable[^.]*counter|'
                          r'statistics enable|counters? (on|off) \(', re.I)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epic", required=True)
    ap.add_argument("--dir", default=default_data_dir())
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    mf = json.loads((resolve_data_dir(getattr(a, 'dir', None)) / a.epic / "manifest.json").read_text())
    bodies = [(tc["id"], tc["jira_wiki_body"]) for tc in mf["test_cases"]]
    blob = "\n".join(b for _, b in bodies)

    counter_tc_ct = sum(1 for _, b in bodies if COUNTER_TOKEN.search(b))
    relevant = counter_tc_ct >= 3 or bool(CLEAR_ANY.search(blob)) \
        or bool(re.search(r'TX \w+ Packets|prefix-counts', blob, re.I))
    if not relevant:
        print(f"[N/A] {a.epic}: no counter/statistics surface detected "
              f"({counter_tc_ct} counter-token TC(s)) -> counter-coverage lint not applicable.")
        return

    def any_tc(pat):
        return [tid for tid, b in bodies if pat.search(b)]

    delta_tcs = any_tc(DELTA)
    clear_zero_tcs = [tid for tid, b in bodies if CLEAR_ZERO.search(b)]
    # fall back: a TC that both clears counters and mentions zero/reset anywhere
    if not clear_zero_tcs:
        clear_zero_tcs = [tid for tid, b in bodies
                          if CLEAR_ANY.search(b) and re.search(r'\b(zero|reset|to 0)\b', b, re.I)]
    scope_inst = any_tc(SCOPE_INST)
    scope_peer = any_tc(SCOPE_PEER)
    optin = bool(ENABLE_OPTIN.search(blob))
    enable_tcs = any_tc(ENABLE_OPTIN)

    checks = [
        ("DELTA", "before/after delta correctness (counter increases by the driven events)",
         True, bool(delta_tcs), delta_tcs[:3]),
        ("CLEAR", "reset semantics (clear counters -> zero; no stale/negative)",
         True, bool(clear_zero_tcs), clear_zero_tcs[:3]),
        ("SCOPE", "counter granularity (per-instance and/or per-neighbor/per-interface)",
         True, bool(scope_inst or scope_peer),
         (scope_inst[:2] + scope_peer[:2])),
        ("ENABLE", "opt-in counters proven (enable-then-count / off-then-frozen)",
         optin, bool(enable_tcs),
         enable_tcs[:2] if optin else ["not applicable (counters not opt-in)"]),
    ]
    gaps = [c for c in checks if c[2] and not c[3]]

    if a.json:
        print(json.dumps({"epic": a.epic, "counter_relevant": True,
                          "counter_token_tcs": counter_tc_ct,
                          "checks": [{"code": c[0], "label": c[1], "required": c[2],
                                      "covered": c[3], "examples": c[4]} for c in checks],
                          "gaps": [c[0] for c in gaps]}, indent=2))
    else:
        print(f"counter-coverage lint -- {a.epic} ({counter_tc_ct} counter-bearing TC(s))")
        for code, label, req, cov, ex in checks:
            mark = "n/a " if not req else ("OK  " if cov else "GAP ")
            print(f"  [{mark}] {code:6} {label}")
        if gaps:
            print(f"\n[FAIL] {len(gaps)} required counter check(s) missing: "
                  f"{', '.join(c[0] for c in gaps)}")
            print("  Fix: add/extend a dedicated counter-verification TC "
                  "(baseline -> drive event -> delta increment -> clear -> zero), "
                  "at the right scope (see tp:counter-coverage).")
        else:
            print("\n[PASS] counter contract covered (delta + clear-to-zero + scope"
                  + (" + opt-in" if optin else "") + ").")

    if a.strict and gaps:
        sys.exit(1)


if __name__ == "__main__":
    main()
