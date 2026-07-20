#!/usr/bin/env python3
"""Cited-story deliverable-coverage gate (anchor: tp:cited-story-deliverable-coverage).

For every user story a TC CITES (covers_user_stories), extract the story's CONCRETE
deliverable tokens - quoted column/field names ("..."/curly), <<<-marked sample-output
field labels, and backtick tokens - then assert that AT LEAST ONE citing TC actually
verifies those tokens in its body. Surfaces the class of miss where a story is cited
but its specific new column/field/behavior is never asserted (e.g. SW-260732's new
`SMET Type-6` / `Multicast (x,G)` columns on 2026-07-19).

Waivers (`<epic>/us_coverage_waivers.json`) exclude tokens that are legitimately not
CLI-assertable (dev-internal code symbols) or are covered by a sibling TC (cross-refs),
each with a documented reason. A gap counts as HARD only if it has non-waived tokens.

Exit 0 = no hard gaps (all waived or covered); exit 1 = >=1 hard gap.
Usage: python3 _tp_us_coverage_lint.py --epic SW-XXXXX [--json] [--advisory]
"""
import argparse, json, re, sys
from pathlib import Path

from _tp_paths import resolve_data_dir, default_data_dir


STOP = {x.lower() for x in (
    "enabled","disabled","root","leaf","yes","no","true","false","up","down",
    "mpls","evpn","igmp","state","note","todo","to do","done","na","n/a",
    "type","mode","count","label","address","interface","interfaces","table",
    "id","ip","mac","the","and","for","with","new","column","field","proxy",
)}

def norm(s):
    s = (s or "").replace("\u201c", '"').replace("\u201d", '"')
    s = s.replace("\u2018", "'").replace("\u2019", "'")
    return re.sub(r"\s+", " ", s).lower()

def deliverable_tokens(body):
    toks = set()
    for q in re.findall(r'[\u201c"]([^"\u201c\u201d\n]{2,60})[\u201d"]', body):
        toks.add(q.strip())
    for line in body.splitlines():
        if "<<<" in line:
            lab = line.split(":")[0].strip(" #|")
            if lab:
                toks.add(lab)
    for q in re.findall(r"`([^`\n]{2,50})`", body):
        toks.add(q.strip())
    for q in re.findall(r'[Aa]dd(?:ed)?\s+(?:the\s+)?(?:column|field)\s+["\u201c]?([A-Za-z0-9 ()/,\-]{2,40})', body):
        toks.add(q.strip())
    out = set()
    for t in toks:
        t = t.strip().strip('.,;:')
        if len(t) < 3 or norm(t) in STOP or re.fullmatch(r"[\d\s.:/-]+", t):
            continue
        low = t.lower()
        if re.fullmatch(r"id-\d+", low) or low == "smartlink" or \
           any(x in low for x in ("data-type", "data-id", "custom", "href", "http", "<", "=", "\u200c")):
            continue
        out.add(t)
    return out

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--epic", required=True)
    ap.add_argument("--dir", default=default_data_dir())
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--advisory", action="store_true", help="always exit 0 (report only)")
    a = ap.parse_args(argv)
    d = resolve_data_dir(getattr(a, 'dir', None)) / a.epic
    man = json.load(open(d / "manifest.json"))
    tcs = man["test_cases"]

    bodies = {}
    usb = d / "user_story_bodies.md"
    if usb.exists():
        cur, buf = None, []
        for line in usb.read_text().splitlines():
            m = re.match(r"^##\s+(SW-\d+)\b", line)
            if m:
                if cur:
                    bodies[cur] = "\n".join(buf)
                cur, buf = m.group(1), [line]
            elif cur:
                buf.append(line)
        if cur:
            bodies[cur] = "\n".join(buf)

    waivers = {}
    wf = d / "us_coverage_waivers.json"
    if wf.exists():
        waivers = json.load(open(wf))

    cite = {}
    for t in tcs:
        body = norm(t.get("jira_wiki_body", ""))
        for s in t.get("covers_user_stories", []) or []:
            m = re.search(r"SW-\d+", str(s))
            if m:
                cite.setdefault(m.group(0), []).append(body)

    hard, waived_only, ok = [], [], 0
    for story in sorted(bodies):
        toks = deliverable_tokens(bodies[story])
        citing = cite.get(story)
        if not citing:
            continue  # 0-citing handled as INFO (dev stories etc.), never a hard fail
        allbody = " ".join(citing)
        uncovered = [tk for tk in sorted(toks) if norm(tk) not in allbody]
        if not uncovered:
            ok += 1
            continue
        wspec = waivers.get(story, {})
        if wspec.get("waive_all"):
            waived_only.append((story, uncovered))
            continue
        wv = {norm(x) for x in (wspec.get("tokens") or [])}
        non_waived = [u for u in uncovered if norm(u) not in wv]
        if non_waived:
            hard.append((story, non_waived))
        else:
            waived_only.append((story, uncovered))

    title = lambda s: bodies[s].splitlines()[0].replace("## ", "")[:70]
    if a.json:
        print(json.dumps({"epic": a.epic, "fully_covered": ok,
                          "hard_gaps": [{"story": s, "missing": u} for s, u in hard],
                          "waived": [{"story": s} for s, _ in waived_only]}, indent=2))
    else:
        print(f"cited-story deliverable-coverage -- {a.epic}: "
              f"fully covered {ok} | waived {len(waived_only)} | HARD gaps {len(hard)}")
        for s, u in hard:
            print(f"  [FAIL] {s} ({title(s)})")
            for x in u[:8]:
                print(f"         MISSING: {x}")
        for s, _ in waived_only:
            print(f"  [WAIVED] {s} - {waivers.get(s, {}).get('reason', '')[:80]}")
    if hard and not a.advisory:
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
