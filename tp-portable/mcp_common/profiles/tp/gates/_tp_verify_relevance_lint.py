#!/usr/bin/env python3
"""
_tp_verify_relevance_lint.py - flag procedure steps whose Verification command
cannot actually PROVE the step's Expected Result.

Read-only. Parses each TC's rendered Procedure table out of manifest.json
(the single source of truth) and classifies every step's Expected assertion
into an "evidence need", then checks whether the paired Verification command(s)
can supply that evidence. Emits categorized findings with a confidence level.

This does NOT mutate artifacts. Fixes are applied by the generator's
apply_config_default_verification() pass (HIGH) and companion-append passes
(MED/LOW); this lint is the auditor/gate.

Usage:
    python3 _tp_verify_relevance_lint.py --epic SW-XXXXX [--min-conf HIGH|MED|LOW]
    python3 _tp_verify_relevance_lint.py --epic SW-XXXXX --json
Exit code: 0 always (advisory); use --strict to exit 1 when HIGH findings exist.
"""
import argparse, json, re, sys
from pathlib import Path
from collections import Counter

from _tp_paths import resolve_data_dir, default_data_dir



def load_manifest(epic):
    p = resolve_data_dir(getattr(args, 'dir', None)) / epic / "manifest.json"
    return json.loads(p.read_text())


def parse_steps(body):
    """Yield (step, dev, action, verif, ie, expected) tuples from the Procedure table."""
    m = re.search(r'h3\. Procedure\n(.*?)(?:\nh3\. |\Z)', body, re.S)
    if not m:
        return
    header_cols = None
    for row in m.group(1).splitlines():
        if row.startswith('||'):
            header_cols = [c.strip().strip('*') for c in row.strip('|').split('||')]
            continue
        if not row.startswith('|'):
            continue
        cells = [c.strip() for c in row.strip('|').split('|')]
        has_ie = header_cols and any('Ingress' in c for c in header_cols)
        if has_ie:
            if len(cells) < 6:
                continue
            yield cells[0], cells[1], cells[2], cells[3], cells[4], cells[5]
        else:
            if len(cells) < 5:
                continue
            yield cells[0], cells[1], cells[2], cells[3], "", cells[4]


# ---- evidence classifiers on the Expected text -----------------------------
# a genuine "verify a configured DEFAULT" assertion (value/knob), NOT a feature
# name that merely contains the word "default".
DEFAULT_RE = re.compile(r'defaults? to|at their platform default|'
                        r'off \(default\)|on \(default\)', re.I)
DEFAULT_FEATURE_NAME = re.compile(r'default-selective|default-gateway|default mode|'
                                  r'default-originate', re.I)
# RT emission = THIS box originates/advertises/emits an RT-N. Receive/schedule/
# hold/treat-as-withdraw/relearn are proven by the group-DB, not a route show.
RT_EMIT_RE = re.compile(r'(emit|emitted|emits|advertis\w+|originat\w+)\b[^.]*\bRT-[34678]\b|'
                        r'\bRT-[34678]\b[^.]*(emit|emitted|emits|advertis\w+|originat\w+)', re.I)
RT_RECV_RE = re.compile(r'receiv|import|schedul|treat-as-withdraw|relearn|holds|about to send',
                        re.I)
WIRE_RE = re.compile(r'(send|emit)\w*.*\b(query|report|general query|group-specific)\b.*\b(out|toward|on)\b',
                     re.I)
LOSS_RE = re.compile(r'0% loss|no loss|traffic (is )?(delivered|forwarded|received)|'
                     r'receiver gets the stream|line-rate', re.I)

# ---- capability classifiers on the Verification command(s) -----------------
HAS_CONFIG = re.compile(r'show config|flatten|display set', re.I)
HAS_OPERDETAIL = re.compile(r'show evpn instance \S+ detail', re.I)
HAS_RUNTIME_DB = re.compile(r'multicast-db|show igmp interfaces', re.I)
HAS_BGP_ROUTE = re.compile(r'show bgp l2vpn evpn|route-type|show evpn .*route', re.I)
HAS_CAPTURE = re.compile(r'tcpdump|xray|capture|monitor traffic|spirent|stc |wireshark|pcap', re.I)
HAS_TRAFFIC_STATS = re.compile(r'spirent|stc |ixia|traffic (stat|counter)|rx-rate|tx-rate|'
                               r'stream (stat|result)|loss', re.I)
# forwarding is also legitimately provable by OIF-install + per-hop counters
HAS_FWD_EVIDENCE = re.compile(r'multicast-db|counter|statistics|show interfaces|'
                              r'oif|replication|clear .*counter|forwarding-table|'
                              r'multicast forwarding|multicast route|'
                              r'show evpn instance \S+ detail', re.I)

BENIGN_EMPTY = re.compile(r'driver running|verified in the following|verified next|'
                          r'stimulus|inject|failure injected|no verification', re.I)


def classify(verif, expected):
    """Return list of (rule, confidence, why) findings for one step."""
    v, e = verif.lower(), expected
    out = []
    # M1 config default proven by a runtime show only (skip feature-name "default")
    if DEFAULT_RE.search(e) and not DEFAULT_FEATURE_NAME.search(e) \
            and HAS_RUNTIME_DB.search(v) \
            and not HAS_CONFIG.search(v) and not HAS_OPERDETAIL.search(v):
        out.append(("CONFIG_DEFAULT", "HIGH",
                    "asserts a configured DEFAULT/knob value but verifies only a runtime show"))
    # M2 THIS box originates an RT-N but has no BGP/evpn route show or capture
    # (receive/schedule/hold/treat-as-withdraw are correctly proven by group-DB)
    if RT_EMIT_RE.search(e) and not RT_RECV_RE.search(e) \
            and HAS_RUNTIME_DB.search(v) \
            and not HAS_BGP_ROUTE.search(v) and not HAS_CAPTURE.search(v):
        out.append(("RT_EMISSION", "MED",
                    "asserts THIS box originates an RT-x but has no BGP/EVPN route show or capture"))
    # M3 wire packet emission with neither a capture nor the oper-detail TX
    # counter block (the tool-agnostic, capture-free proof the packet left)
    if WIRE_RE.search(e) and not HAS_CAPTURE.search(v) and not HAS_OPERDETAIL.search(v):
        out.append(("WIRE_PACKET", "LOW",
                    "asserts a packet is sent on-wire but has no capture or oper-detail "
                    "TX-counter proof it left the box"))
    # M4 traffic/loss outcome with NO evidence at all (no traffic stats AND no
    # OIF/counter forwarding proof). Forwarding proven by OIF+counters is fine.
    if LOSS_RE.search(e) and not HAS_TRAFFIC_STATS.search(v) \
            and not HAS_FWD_EVIDENCE.search(v) and verif != "-":
        out.append(("TRAFFIC_LOSS", "MED",
                    "asserts a data-plane forwarding/loss outcome with no traffic stats "
                    "and no OIF/counter forwarding evidence"))
    # M5 empty verification with a positive assertion
    if verif == "-" and len(e) > 15 and not BENIGN_EMPTY.search(e):
        out.append(("EMPTY_VERIF", "MED",
                    "no verification command for a positive expected result"))
    return out


CONF_ORDER = {"HIGH": 3, "MED": 2, "LOW": 1}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epic", required=True)
    ap.add_argument("--dir", default=default_data_dir())
    ap.add_argument("--min-conf", default="LOW", choices=["HIGH", "MED", "LOW"])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()

    mf = load_manifest(a.epic)
    thresh = CONF_ORDER[a.min_conf]
    findings = []
    for tc in mf["test_cases"]:
        for step, dev, action, verif, ie, exp in parse_steps(tc["jira_wiki_body"]):
            for rule, conf, why in classify(verif, exp):
                if CONF_ORDER[conf] >= thresh:
                    findings.append({"tc": tc["id"], "step": step, "rule": rule,
                                     "conf": conf, "why": why,
                                     "verif": verif, "expected": exp})

    if a.json:
        print(json.dumps({"epic": a.epic, "count": len(findings),
                          "findings": findings}, indent=2))
    else:
        by_rule = Counter(f["rule"] for f in findings)
        by_conf = Counter(f["conf"] for f in findings)
        print(f"verification-relevance findings for {a.epic}: {len(findings)}")
        print(f"  by confidence: {dict(by_conf)}")
        print(f"  by rule:       {dict(by_rule)}\n")
        for f in sorted(findings, key=lambda x: -CONF_ORDER[x["conf"]]):
            print(f"[{f['conf']:4}] {f['rule']:14} {f['tc']} (step {f['step']})")
            print(f"        why : {f['why']}")
            print(f"        verif: {f['verif'][:72]!r}")
            print(f"        exp  : {f['expected'][:80]!r}")
    if a.strict and by_conf.get("HIGH"):
        sys.exit(1)


if __name__ == "__main__":
    main()
