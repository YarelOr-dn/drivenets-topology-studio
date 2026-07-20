#!/usr/bin/env python3
"""Manifest-driven push of ONE TP category to Jira under a single Test Category,
with the operator naming scheme (2026-07-19):

    Test Category (parent = epic) : EVPN-IGMP Proxy | <Category>
    Testing Task  (parent = cat)  : EVPN-IGMP Proxy | <Category> | <sub-category> | <clean test name>

Body = full ADF (per-device config collapsibles + compact SW- links) built by the
/TP-owned _tp_jira_push_adf.py and set as the Testing Task DESCRIPTION at create.
Testing Tasks are created in manifest (tree) order, grouped by sub-category.

Why not create_jira_test_issues.py: that script names tasks `TC-NNN: name`, parses
a numeric-TC markdown plan (our ids are TC-IGMP-CLI-<slug>), and has no sub-category
level. This driver reads the manifest directly and builds the exact titles.

DEFAULT = --dry-run (no Jira writes). Use --push to actually create + verify.
Auth resolves from mcp.json (dn-mcp-server) via the ADF pusher - no env vars needed.
"""
import argparse, importlib.util, json, sys, urllib.parse
from pathlib import Path

from _tp_paths import GATES_DIR as TP_ROOT, resolve_data_dir, default_data_dir

PROJECT_KEY = "SW"
TEST_CATEGORY_TYPE_ID = "10200"   # from create_jira_test_issues.py (proven)
TESTING_TASK_TYPE_ID = "10379"

# testing_task -> sub-category label in the Jira title (operator rename 2026-07-19)
SUBCAT_RENAME = {
    "CLI - Feature config knobs": "New configuration commands",
    "CLI - Show & oper-DB": "New show commands",
    # 3rd: operator shortened to just "Config ops" (2026-07-19)
    "CLI - Config ops (rollback / commit / policy / IRB / clear)":
        "Config ops",
}

# Short, human-friendly <Test name> segment per TC id (operator: title too long,
# 2026-07-19). Keeps the knob/feature essence; drops the long parenthetical tails.
# Fallback = clean_name() if a TC id is missing here.
SHORT_NAME = {
    # New configuration commands
    "TC-IGMP-CLI-igmp-snooping-proxy-enable-across-hierarchies": "igmp-snooping / proxy enable",
    "TC-IGMP-CLI-static-multicast-router-mrouter-interface": "static multicast-router (mrouter)",
    "TC-IGMP-CLI-static-group-bindings-instance-interface": "static group bindings",
    "TC-IGMP-CLI-source-ipv4-optional-default-0-0": "source-ipv4 (default 0.0.0.0)",
    "TC-IGMP-CLI-immediate-leave-instance-port": "immediate-leave (instance + port)",
    "TC-IGMP-CLI-router-guard": "router-guard",
    "TC-IGMP-CLI-timers-parity-sw-172381-leave-sync": "querier timers + leave-sync-propagation-time",
    "TC-IGMP-CLI-replication-caps-max-sg-replications-max-evpn": "replication caps (max-sg / max-evpn)",
    "TC-IGMP-CLI-lmq-mode-leave-receiver-vs-df": "lmq-mode (leave-receiver | df)",
    "TC-IGMP-CLI-mrouter-timeout-dynamic-aging": "mrouter-timeout aging",
    "TC-IGMP-CLI-querier-enable-per-instance": "querier enable (per-instance)",
    "TC-IGMP-CLI-pim-admin-state-over-irb": "PIM admin-state over IRB",
    "TC-IGMP-CLI-v2-compatibility-mode-v2-only-mode": "v2-compatibility / v2-only mode",
    # Basic Functionality (concise; sub-category already conveys topology context)
    "TC-IGMP-SAN-per-service-igmp-snooping-proxy-enable-off": "per-service snooping/proxy enable (ON/OFF + default)",
    "TC-IGMP-SAN-basic-snoop-selective-forwarding-flood": "basic snoop + selective forwarding",
    "TC-IGMP-SAN-igmpv2-igmpv3-s-g-g-report-learning": "IGMPv2/v3 (S,G) and (*,G) report learning",
    "TC-IGMP-SAN-distributed-anycast-irb-basic-snoop-forward": "distributed anycast IRB - snoop + forward",
    "TC-IGMP-SAN-centralized-anycast-irb-basic-snoop-forward": "centralized anycast IRB - snoop + forward",
    # operator 2026-07-19: drop the redundant 4th segment (title ends at the sub-category)
    "TC-IGMP-SAN-no-irb-router-interface-ac-basic-snoop": "",
    "TC-IGMP-TOPO-bd-coexist-background-bum-regression": "background Bridge-Domain BUM coexistence (regression)",
    "TC-IGMP-TOPO-irb-in-evi-not-in-igmp-pim-snoop-onoff": "IRB in EVI, not in IGMP/PIM (snoop OFF vs ON)",
    "TC-IGMP-TOPO-irb-in-igmp-pim-snoop-disabled-flood-all": "IRB in IGMP+PIM, snooping disabled (flood-all)",
    "TC-IGMP-TOPO-evi-traffic-class-sweep-both-directions": "EVI traffic-class sweep (L2->L2 + L3->L2)",
    "TC-IGMP-SAN-cluster-multi-ncp-acs-same-group": "cluster: ACs on different NCPs - single-copy replication",
    # New show commands
    "TC-IGMP-CLI-show-evpn-igmp-snooping-multicast-db-fields": "show evpn igmp-snooping multicast-db",
    "TC-IGMP-CLI-show-bgp-l2vpn-evpn-route-type-6": "show bgp l2vpn evpn route-type 6 (SMET)",
    "TC-IGMP-CLI-show-bgp-l2vpn-evpn-route-type-7": "show bgp l2vpn evpn route-type 7 (Join Sync)",
    "TC-IGMP-CLI-show-bgp-l2vpn-evpn-route-type-8": "show bgp l2vpn evpn route-type 8 (Leave Sync)",
    "TC-IGMP-CLI-show-evpn-detail-summary-igmp-proxy-fields": "show evpn detail / summary",
    "TC-IGMP-CLI-show-evpn-inclusive-multicast-table-imet": "show evpn inclusive-multicast-table (IMET)",
    "TC-IGMP-CLI-show-evpn-igmp-snooping-remote-db-neighbor": "show evpn igmp-snooping remote-db",
    "TC-IGMP-CLI-consolidated-l3-datapath-multicast-shows-all": "consolidated L3 / datapath multicast shows",
    "TC-IGMP-CLI-full-counter-verification": "IGMP-proxy counter verification",
    "TC-IGMP-CLI-evpn-multicast-forwarding-table-route-counters-clear": "show evpn multicast forwarding-table",
    # Config ops
    "TC-IGMP-CLI-rollback-form-load-override-merge-commit": "rollback / no-form / load override-merge",
    "TC-IGMP-CLI-routing-policy-match-evpn-route-type-6": "routing-policy match evpn-route-type",
    "TC-IGMP-CLI-route-policy-evi-rt-rewrite-type-7-8": "route-policy EVI-RT rewrite (Type-7/8)",
    "TC-IGMP-CLI-igmp-snooping-evpn-interconnect-mutual-exclusion": "mutual-exclusion: igmp-snooping vs EVPN Interconnect",
    "TC-IGMP-CLI-clear-evpn-instance-svc-igmp-igmp-snooping": "clear evpn instance igmp-snooping",
    "TC-IGMP-CLI-clear-bgp-l2vpn-evpn-neighbor-hard-soft-nlri": "clear bgp neighbor (hard + soft in/out)",
    "TC-IGMP-CLI-cli-commit-negatives-reject-malformed-igmp": "commit negatives: reject malformed config",
    "TC-IGMP-CLI-vpls-si-igmp-snooping-mutual-exclusion": "mutual-exclusion: igmp-snooping vs VPLS-SI",
    "TC-IGMP-CLI-add-irb-into-igmp-pim-l3-multicast": "add IRB into IGMP + PIM (L3-multicast)",
}


def _load_adf():
    spec = importlib.util.spec_from_file_location(
        "_tp_jira_push_adf", str(TP_ROOT / "_tp_jira_push_adf.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def clean_name(n: str) -> str:
    import re
    n = (n or "").strip()
    n = re.sub(r"^CLI/Advanced:\s*", "", n)
    n = re.sub(r"^CLI:\s*", "", n)
    n = re.sub(r"^CLI\s+(commit negative)", r"\1", n)  # "CLI commit negative..." -> "commit negative..."
    # Basic Functionality name prefixes (drop the redundant lead-in; the sub-category
    # already conveys the context): "Use case:", "Topology:", "Topology (Regression/
    # sanity):", "Cluster:", "Cluster (...):".
    n = re.sub(r"^Use case:\s*", "", n)
    n = re.sub(r"^Topology(?:\s*\([^)]*\))?:\s*", "", n)
    n = re.sub(r"^Cluster(?:\s*\([^)]*\))?:\s*", "", n)
    return n.strip()


# Category FAMILY merge (operator 2026-07-19): fold several source categories that
# share a prefix into ONE pushed Test Category, each source category becoming a
# sub-category (its suffix after "<prefix> - "). Mirrors the CLI category shape.
CATEGORY_FAMILY = {
    # display name -> list of source category strings (in desired sub-category order)
    "Basic Functionality": [
        "Basic Functionality - Single-PE / Simulate-BD (core)",
        "Basic Functionality - Distributed Anycast IRB",
        "Basic Functionality - Centralized Anycast IRB",
        "Basic Functionality - L2 EVPN + External Router (No-IRB)",
    ],
}
# per-source-category -> sub-category label shown in the Jira title
FAMILY_SUBCAT = {
    "Basic Functionality - Single-PE / Simulate-BD (core)": "Single-PE / Simulate-BD (core)",
    "Basic Functionality - Distributed Anycast IRB": "Distributed Anycast IRB",
    "Basic Functionality - Centralized Anycast IRB": "Centralized Anycast IRB",
    "Basic Functionality - L2 EVPN + External Router (No-IRB)": "L2 EVPN + External Router (No-IRB)",
}


def build_plan(manifest: dict, category: str, epic: str):
    """Return (test_category_title, [ (subcat, [ (tc, long_title, short_title) ] ) ]) in tree order.

    Two modes:
    - SINGLE category (e.g. "CLI"): sub-category = each TC's testing_task (SUBCAT_RENAME).
    - FAMILY (category is a key of CATEGORY_FAMILY, e.g. "Basic Functionality"): fold the
      listed source categories into ONE pushed category; sub-category = FAMILY_SUBCAT[src].
    """
    if category in CATEGORY_FAMILY:
        srcs = CATEGORY_FAMILY[category]
        cat_title = f"EVPN-IGMP Proxy | {category}"
        out = []
        for src in srcs:
            sub = FAMILY_SUBCAT.get(src, src)
            rows = []
            for t in manifest["test_cases"]:
                if str(t.get("category", "")) != src:
                    continue
                head = f"EVPN-IGMP Proxy | {category} | {sub}"
                long_name = clean_name(t.get("name", ""))
                # explicit membership so an intentional empty "" short-name is honored
                short_name = SHORT_NAME[t["id"]] if t["id"] in SHORT_NAME else long_name
                long_t = f"{head} | {long_name}" if long_name else head
                short_t = f"{head} | {short_name}" if short_name else head
                rows.append((t, long_t, short_t))
            if rows:
                out.append((sub, rows))
        return cat_title, out

    tcs = [t for t in manifest["test_cases"] if str(t.get("category", "")) == category]
    cat_title = f"EVPN-IGMP Proxy | {category}"
    order, groups = [], {}
    for t in tcs:
        tt = t.get("testing_task", category)
        if tt not in groups:
            groups[tt] = []
            order.append(tt)
        groups[tt].append(t)
    out = []
    for tt in order:
        sub = SUBCAT_RENAME.get(tt, tt)
        rows = []
        for t in groups[tt]:
            base = f"EVPN-IGMP Proxy | {category} | {sub} | "
            long_t = base + clean_name(t.get("name", ""))
            short_t = base + (SHORT_NAME.get(t["id"]) or clean_name(t.get("name", "")))
            rows.append((t, long_t, short_t))
        out.append((sub, rows))
    return cat_title, out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--epic", required=True)
    ap.add_argument("--category", default="CLI")
    ap.add_argument("--push", action="store_true", help="actually create issues (default: dry-run)")
    ap.add_argument("--limit", type=int, default=0, help="push only the first N tasks (smoke)")
    ap.add_argument("--update-from", metavar="BASEKEY", default=None,
                    help="update summaries of ALREADY-created tasks to the SHORT title; "
                         "BASEKEY is the FIRST Testing Task key (e.g. SW-288730). Tasks are "
                         "BASEKEY..BASEKEY+N-1 in plan order; each is GET-verified before PUT.")
    ap.add_argument("--retitle-subcat", nargs=2, metavar=("OLD", "NEW"), default=None,
                    help="in-place: on every child of --parent-cat, replace the sub-category "
                         "segment ' | OLD | ' with ' | NEW | ' in the summary (GET-verify, PUT). "
                         "Only touches tickets whose title actually contains OLD.")
    ap.add_argument("--parent-cat", default=None,
                    help="Test Category key whose children to retitle (with --retitle-subcat)")
    a = ap.parse_args(argv)

    if a.retitle_subcat:
        adf = _load_adf()
        return _retitle_subcat(adf, a.parent_cat, a.retitle_subcat[0], a.retitle_subcat[1], a.push)

    adf = _load_adf()
    manifest = json.load(open(resolve_data_dir(a.dir) / a.epic / "manifest.json"))
    cat_title, groups = build_plan(manifest, a.category, a.epic)
    total = sum(len(rows) for _, rows in groups)

    if a.update_from:
        return _update_summaries(adf, groups, a.update_from)

    print(f"=== PUSH PLAN ({'PUSH' if a.push else 'DRY-RUN'}) ===")
    print(f"Epic (parent)        : {a.epic}")
    print(f"Test Category (new)  : {cat_title}   [issuetype {TEST_CATEGORY_TYPE_ID}, project {PROJECT_KEY}]")
    print(f"Testing Tasks        : {total} (issuetype {TESTING_TASK_TYPE_ID}), body = full ADF (SHORT titles), in tree order:\n")
    n = 0
    for sub, rows in groups:
        print(f"  +-- {sub}  ({len(rows)})")
        for t, long_t, short_t in rows:
            n += 1
            print(f"      {n:2}. {short_t}")
        print()

    # sample ADF body from the first TC (proves body renders)
    sample_tc = groups[0][1][0][0]
    doc = adf.build_full_tc_adf(sample_tc)
    counts = adf.count_node_types(doc)
    expands = [e.get("attrs", {}).get("title", "") for e in adf.collect_expand_nodes(doc)]
    print("--- sample Testing Task body (ADF) ---")
    print(f"  TC: {sample_tc['id']}")
    print(f"  node counts: expand={counts.get('expand',0)} codeBlock={counts.get('codeBlock',0)} "
          f"table={counts.get('table',0)} link={counts.get('link',0)} heading={counts.get('heading',0)} "
          f"inlineCard={counts.get('inlineCard',0)}")
    print(f"  per-device config expands: {expands}")

    if not a.push:
        print("\n[DRY-RUN] No Jira writes. Re-run with --push to create the Test Category + Testing Tasks.")
        return 0

    # ---- real push (v3 create; description=ADF at create time) ----
    email, token, src = adf.resolve_auth()
    auth = adf._auth_header(email, token)
    print(f"\n[PUSH] auth source: {src}")
    cat_key = _create_issue(adf, auth, {
        "project": {"key": PROJECT_KEY},
        "issuetype": {"id": TEST_CATEGORY_TYPE_ID},
        "parent": {"key": a.epic},
        "summary": cat_title,
    })
    print(f"[OK] Test Category {cat_key}: {cat_title}  {adf.JIRA_BASE_URL}/browse/{cat_key}")
    made = 0
    for sub, rows in groups:
        for t, long_t, short_t in rows:
            if a.limit and made >= a.limit:
                print(f"[INFO] --limit {a.limit} reached; stopping.")
                return 0
            doc = adf.build_full_tc_adf(t)
            key = _create_issue(adf, auth, {
                "project": {"key": PROJECT_KEY},
                "issuetype": {"id": TESTING_TASK_TYPE_ID},
                "parent": {"key": cat_key},
                "summary": short_t,
                "description": doc,
            })
            ok, titles = adf.verify_expand(key, auth)
            made += 1
            print(f"[OK] {key}  {short_t}  (expands={len(titles)})  {adf.JIRA_BASE_URL}/browse/{key}")
    print(f"\n[DONE] created Test Category {cat_key} + {made} Testing Task(s).")
    return 0


def _get_summary(adf, auth, key: str):
    _, parsed = adf._http("GET", f"{adf.JIRA_API_V3}/issue/{key}?fields=summary", auth)
    if not parsed:
        return None
    return (parsed.get("fields") or {}).get("summary")


def _put_summary(adf, auth, key: str, summary: str) -> bool:
    status, _ = adf._http("PUT", f"{adf.JIRA_API_V3}/issue/{key}", auth,
                          payload={"fields": {"summary": summary}})
    return 200 <= status < 300


def _update_summaries(adf, groups, base_key: str) -> int:
    """Update EXISTING Testing Task summaries to the SHORT title. Tasks are
    base_key..base_key+N-1 in plan order. Each key is GET-verified (its current
    summary must equal the known LONG title we pushed) before we PUT the short
    one - so a key mismatch WARNs and is skipped, never clobbered."""
    email, token, src = adf.resolve_auth()
    auth = adf._auth_header(email, token)
    proj, num = base_key.rsplit("-", 1)
    base = int(num)
    rows = [r for _, rows in groups for r in rows]  # flat, plan order
    print(f"[UPDATE] auth source: {src}; {len(rows)} tasks starting at {base_key}\n")
    updated = skipped = warned = 0
    for i, (t, long_t, short_t) in enumerate(rows):
        key = f"{proj}-{base + i}"
        cur = _get_summary(adf, auth, key)
        if cur is None:
            print(f"[WARN] {key}: could not read summary - skip"); warned += 1; continue
        if cur == short_t:
            print(f"[SKIP] {key}: already short"); skipped += 1; continue
        if cur != long_t:
            print(f"[WARN] {key}: current summary != expected long title - SKIP (no clobber)")
            print(f"        current : {cur}")
            print(f"        expected: {long_t}")
            warned += 1; continue
        if _put_summary(adf, auth, key, short_t):
            print(f"[OK] {key}  ->  {short_t}")
            updated += 1
        else:
            print(f"[WARN] {key}: PUT failed"); warned += 1
    print(f"\n[DONE] summaries updated={updated} skipped={skipped} warn={warned}")
    return 1 if warned else 0


def _retitle_subcat(adf, parent_cat: str, old: str, new: str, do_push: bool) -> int:
    """In place: for every child of parent_cat whose summary contains the sub-category
    segment ` | OLD | `, replace it with ` | NEW | `. GET-verify each before PUT; a
    ticket that does not contain OLD is skipped (never clobbered). DRY-RUN unless --push."""
    if not parent_cat:
        print("error: --parent-cat is required with --retitle-subcat"); return 1
    email, token, src = adf.resolve_auth()
    auth = adf._auth_header(email, token)
    old_seg, new_seg = f" | {old} | ", f" | {new} | "
    # fetch children
    jql = f"parent = {parent_cat} ORDER BY key ASC"
    _, parsed = adf._http("GET", f"{adf.JIRA_API_V3}/search/jql?jql={urllib.parse.quote(jql)}&fields=summary&maxResults=100", auth)
    issues = (parsed or {}).get("issues", [])
    print(f"[RETITLE] parent={parent_cat} children={len(issues)}  '{old}' -> '{new}'  ({'PUSH' if do_push else 'DRY-RUN'}); auth={src}\n")
    hit = miss = done = 0
    for it in issues:
        key = it.get("key"); cur = (it.get("fields") or {}).get("summary", "")
        if old_seg not in cur:
            miss += 1; continue
        newt = cur.replace(old_seg, new_seg)
        hit += 1
        if not do_push:
            print(f"[DRY] {key}\n    - {cur}\n    + {newt}")
            continue
        status, _ = adf._http("PUT", f"{adf.JIRA_API_V3}/issue/{key}", auth,
                              payload={"fields": {"summary": newt}})
        if 200 <= status < 300:
            print(f"[OK] {key}  ->  {newt}"); done += 1
        else:
            print(f"[WARN] {key}: PUT failed (status {status})")
    print(f"\n[{'DONE' if do_push else 'DRY-RUN'}] matched={hit} skipped(no-OLD)={miss} updated={done}")
    return 0


def _create_issue(adf, auth, fields: dict) -> str:
    status, parsed = adf._http("POST", f"{adf.JIRA_API_V3}/issue", auth, payload={"fields": fields})
    if not (parsed and parsed.get("key")):
        raise SystemExit(f"create failed (status {status}): {str(parsed)[:400]}")
    return parsed["key"]


if __name__ == "__main__":
    sys.exit(main())
