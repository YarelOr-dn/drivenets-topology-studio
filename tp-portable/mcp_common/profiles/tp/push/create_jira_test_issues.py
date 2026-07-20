#!/usr/bin/env python3
"""
Create Jira Test Category + Testing Task issues from a markdown test plan.

Parses TC-NNN blocks from a generate-qa-test-plan style markdown file,
groups them into user-defined categories, and creates issues via the
Jira Cloud REST API v2.

Hierarchy:
  Epic (user-supplied) -> Test Category (one per --category) -> Testing Task (one per TC)

Usage:
  python3 create_jira_test_issues.py test_plans/SW-211690/test_plan_SW-211690.md \\
    --epic SW-211690 \\
    --category "Sanity: TC-001-002, TC-008" \\
    --category "HA: TC-009-016" \\
    --category "Scale: TC-018-019"

  python3 create_jira_test_issues.py test_plans/SW-211690/test_plan_SW-211690.md \\
    --epic SW-211690 \\
    --category "Sanity: TC-001-002, TC-008" \\
    --priority High \\
    --dry-run

Requires: Python 3.8+ (stdlib only, no pip).
Auth: JIRA_USERNAME and JIRA_API_TOKEN environment variables.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

JIRA_BASE_URL = "https://drivenets.atlassian.net"
JIRA_API = f"{JIRA_BASE_URL}/rest/api/2"

PROJECT_KEY = "SW"
TEST_CATEGORY_TYPE_ID = "10200"
TESTING_TASK_TYPE_ID = "10379"

# /TP-owned ADF pusher (Cloud-native collapsible per-device config, REST v3).
# Imported by file path for the opt-in --adf-config path; never duplicated here.
ADF_PUSH_PATH = os.path.expanduser("~/SCALER/TEST/tp/_tp_jira_push_adf.py")


def _load_adf_module():
    """Import the /TP-owned ADF pusher (_tp_jira_push_adf.py) by file path."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_tp_jira_push_adf", ADF_PUSH_PATH
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load ADF pusher at {ADF_PUSH_PATH}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

# Jira issue-link type used by the opt-in --link-covers provenance linker.
DEFAULT_LINK_TYPE = "Relates"
# SW-<digits> keys, scanned ONLY from a TC block's provenance lines (Covers /
# Stories / source_story / enabler_epic) so we never link an out-of-scope or
# placeholder ref.
SW_KEY_RE = re.compile(r"\bSW-\d+\b", re.IGNORECASE)
PROVENANCE_LINE_RE = re.compile(
    r"(?i)\b(covers?|stor(?:y|ies)|source[_ ]story|enabler(?:[_ ]epic)?)\b"
)

TC_HEADER_RE = re.compile(
    r"^### \*\*(TC-\d+[A-Z]?):\s*([^\n*]+)\*\*\s*$", re.MULTILINE
)
TC_RANGE_RE = re.compile(r"^TC-(\d+)-(\d+)$", re.IGNORECASE)
TC_SINGLE_RE = re.compile(r"^TC-(\d+)([A-Z]?)$", re.IGNORECASE)
EPIC_RE = re.compile(r"^SW-\d+$", re.IGNORECASE)

# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------


def _auth_header() -> str:
    user = os.environ.get("JIRA_USERNAME")
    token = os.environ.get("JIRA_API_TOKEN")
    if not user or not token:
        raise SystemExit(
            "error: JIRA_USERNAME and JIRA_API_TOKEN environment variables are required"
        )
    cred = base64.b64encode(f"{user}:{token}".encode()).decode()
    return f"Basic {cred}"


# ---------------------------------------------------------------------------
# Jira REST helpers
# ---------------------------------------------------------------------------


def jira_post(endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
    """POST JSON to Jira and return the parsed response."""
    url = f"{JIRA_API}{endpoint}"
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": _auth_header(),
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"  ERROR {exc.code}: {body}", file=sys.stderr)
        raise


def jira_create_issue_link(
    from_key: str, to_key: str, link_type: str = DEFAULT_LINK_TYPE
) -> None:
    """Create a directional issue link (POST /issueLink). The endpoint returns
    201/204 with an empty body, so we do not parse a JSON response. Raises on a
    non-2xx HTTP status (the caller warns and continues)."""
    payload = {
        "type": {"name": link_type},
        "inwardIssue": {"key": to_key},
        "outwardIssue": {"key": from_key},
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        f"{JIRA_API}/issueLink",
        data=data,
        headers={
            "Authorization": _auth_header(),
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        resp.read()  # drain; body is empty on success


def extract_covers_keys(text: str) -> list[str]:
    """Resolve the SW-<digits> provenance keys a TC 'Covers' - its story /
    source_story / enabler_epic references. Deterministic + conservative: only
    lines that name a provenance label (Covers / Stories / source_story /
    enabler_epic) are scanned, so out-of-scope refs (e.g. 'out of scope SW-...')
    and 'SW-______' bug placeholders are NOT linked. De-duplicated, order-stable."""
    keys: list[str] = []
    seen: set[str] = set()
    for line in (text or "").splitlines():
        if not PROVENANCE_LINE_RE.search(line):
            continue
        for m in SW_KEY_RE.finditer(line):
            k = m.group(0).upper()
            if k not in seen:
                seen.add(k)
                keys.append(k)
    return keys


# ---------------------------------------------------------------------------
# Markdown parser
# ---------------------------------------------------------------------------


def _tc_sort_key(tc_id: str) -> tuple[int, str]:
    m = TC_SINGLE_RE.match(tc_id)
    if not m:
        return (0, tc_id)
    return (int(m.group(1)), (m.group(2) or "").upper())


def expand_tc_token(tok: str) -> list[str]:
    """Expand 'TC-001-015' into ['TC-001', ..., 'TC-015'], or return ['TC-042']."""
    t = tok.strip().upper()
    if not t:
        return []
    m = TC_RANGE_RE.match(t)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        if b < a:
            raise ValueError(f"invalid range (end < start): {tok}")
        return [f"TC-{i:03d}" for i in range(a, b + 1)]
    m = TC_SINGLE_RE.match(t)
    if m:
        num = int(m.group(1))
        suf = (m.group(2) or "").upper()
        return [f"TC-{num:03d}{suf}"]
    raise ValueError(f"invalid TC token: {tok!r}")


def split_tc_blocks(text: str) -> dict[str, tuple[str, str]]:
    """Return {tc_id: (title_from_header, body_after_header)}."""
    matches = list(TC_HEADER_RE.finditer(text))
    blocks: dict[str, tuple[str, str]] = {}
    for i, m in enumerate(matches):
        tc_id = m.group(1).upper()
        title = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        if tc_id in blocks:
            raise ValueError(f"duplicate TC header: {tc_id}")
        blocks[tc_id] = (title, text[start:end])
    return blocks


def _extract_numbered(blob: str | None) -> list[str]:
    if not blob:
        return []
    return [ln for ln in blob.strip().splitlines() if re.match(r"^\s*\d+\.\s", ln)]


SECTION_SPLIT_RE = re.compile(r"^\d+\.\s*\*\*[^*]+:\*\*", re.MULTILINE)


def parse_tc_body(body: str) -> dict[str, Any]:
    """Parse a TC block by splitting on positional bold-header boundaries.

    Sections are identified by position (1st through 6th), not by name,
    so typos in section labels don't break extraction.
    """
    markers = list(SECTION_SPLIT_RE.finditer(body))
    sections: list[str] = []
    for i, m in enumerate(markers):
        start = m.end()
        end = markers[i + 1].start() if i + 1 < len(markers) else len(body)
        sections.append(body[start:end])

    def _get(idx: int) -> str:
        return sections[idx].strip() if idx < len(sections) else ""

    test_name = _get(0)
    test_desc = _get(1)
    steps_blob = _get(2)
    pass_blob = _get(3)
    var_blob = _get(4)
    auto_text = _get(5)

    steps_lines = _extract_numbered(steps_blob)
    pass_lines = _extract_numbered(pass_blob)
    var_lines = [ln for ln in var_blob.splitlines() if re.match(r"^\s*-\s", ln)]

    if not auto_text or auto_text.lower() in ("none", "n/a"):
        auto_text = "N/A"

    return {
        "test_name": test_name,
        "test_description": test_desc,
        "test_steps": steps_lines,
        "pass_criteria": pass_lines,
        "variants": var_lines,
        "automation_reference": auto_text,
    }


def _strip_step_prefix(line: str) -> str:
    """Remove leading whitespace + '1. ' numbering from a step line."""
    return re.sub(r"^\s*\d+\.\s+", "", line).rstrip()


def _strip_bullet_prefix(line: str) -> str:
    return re.sub(r"^\s*-\s+", "", line).rstrip()


def _escape_wiki(text: str) -> str:
    """Escape characters that conflict with Jira wiki markup.

    Backtick-quoted fragments are converted to Jira {{monospace}} markup.
    """
    parts: list[str] = []
    pos = 0
    for m in re.finditer(r"`([^`]+)`", text):
        if m.start() > pos:
            parts.append(text[pos:m.start()])
        parts.append("{{" + m.group(1) + "}}")
        pos = m.end()
    if pos < len(text):
        parts.append(text[pos:])
    return "".join(parts) if parts else text


def build_wiki_markup(sections: dict[str, Any]) -> str:
    """Build Jira wiki markup for customfield_11772 (Test Description)."""
    lines: list[str] = []

    lines.append("h3. +Test Steps+:")
    lines.append("")
    for step in sections["test_steps"]:
        lines.append(f"# {_escape_wiki(_strip_step_prefix(step))}")
    if not sections["test_steps"]:
        lines.append("# N/A")

    lines.append("")
    lines.append("h3. +Pass Criteria+:")
    lines.append("")
    for crit in sections["pass_criteria"]:
        lines.append(f"# {_escape_wiki(_strip_step_prefix(crit))}")
    if not sections["pass_criteria"]:
        lines.append("# N/A")

    lines.append("")
    lines.append("h3. +Variants+:")
    lines.append("")
    if sections["variants"]:
        for v in sections["variants"]:
            lines.append(f"* {_escape_wiki(_strip_bullet_prefix(v))}")
    else:
        lines.append("N/A")

    lines.append("")
    lines.append("h3. +Automation Reference+:")
    lines.append("")
    lines.append(_escape_wiki(sections["automation_reference"]))

    return "\n".join(lines)


def parse_test_plan(path: str) -> dict[str, dict[str, Any]]:
    """Parse all TC blocks from a test plan file.

    Returns {tc_id: {test_name, test_description, summary, description, wiki_markup}}.
    """
    with open(path, encoding="utf-8") as f:
        text = f.read()

    raw = split_tc_blocks(text)
    result: dict[str, dict[str, Any]] = {}

    for tc_id in sorted(raw, key=_tc_sort_key):
        title, body = raw[tc_id]
        parsed = parse_tc_body(body)
        wiki = build_wiki_markup(parsed)
        summary = f"{tc_id}: {parsed['test_name']}".strip()
        description = (
            f"{parsed['test_description']}\n\n"
            f"Source: {path} | {tc_id}"
        )
        result[tc_id] = {
            "test_name": parsed["test_name"],
            "summary": summary,
            "description": description,
            "wiki_markup": wiki,
            # Provenance for the opt-in --link-covers Relates linker. Scan the
            # header title + raw body so 'Covers / Stories / source_story /
            # enabler_epic' SW keys are captured wherever the plan renders them.
            "covers_keys": extract_covers_keys(f"{title}\n{body}"),
        }
    return result


# ---------------------------------------------------------------------------
# Category parsing (from CLI --category args)
# ---------------------------------------------------------------------------


def parse_category_arg(arg: str) -> tuple[str, list[str]]:
    """Parse 'Category Name: TC-001-005, TC-008' into (name, [expanded tc ids])."""
    if ":" not in arg:
        raise ValueError(
            f"invalid --category format (expected 'Name: TC-NNN-NNN, ...'): {arg!r}"
        )
    name, tc_part = arg.split(":", 1)
    name = name.strip()
    if not name:
        raise ValueError(f"empty category name in: {arg!r}")

    tokens = [t.strip() for t in tc_part.split(",") if t.strip()]
    if not tokens:
        raise ValueError(f"no TC ids in category {name!r}: {arg!r}")

    expanded: list[str] = []
    for tok in tokens:
        expanded.extend(expand_tc_token(tok))
    return name, expanded


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_inputs(
    epic: str,
    categories: list[tuple[str, list[str]]],
    all_tcs: dict[str, Any],
) -> None:
    if not EPIC_RE.match(epic):
        raise SystemExit(f"error: epic must be SW-<digits>, got: {epic!r}")

    seen: dict[str, str] = {}
    for cat_name, tc_ids in categories:
        for tc in tc_ids:
            if tc in seen:
                raise SystemExit(
                    f"error: {tc} assigned to both '{seen[tc]}' and '{cat_name}'"
                )
            seen[tc] = cat_name
            if tc not in all_tcs:
                raise SystemExit(
                    f"error: {tc} (in category '{cat_name}') not found in test plan"
                )

    unassigned = sorted(set(all_tcs) - set(seen), key=_tc_sort_key)
    if unassigned:
        print(f"WARNING: {len(unassigned)} TCs not assigned to any category:")
        for tc in unassigned:
            print(f"  {tc}: {all_tcs[tc]['test_name']}")
        print()


# ---------------------------------------------------------------------------
# Jira issue creation
# ---------------------------------------------------------------------------


PRIORITY_NAME_TO_ID = {
    "highest": "1",
    "high": "2",
    "medium": "3",
    "low": "4",
    "lowest": "5",
}


def create_test_category(
    epic_key: str,
    summary: str,
    priority: str,
) -> str:
    """Create a Test Category issue. Returns the new issue key."""
    priority_id = PRIORITY_NAME_TO_ID.get(priority.lower(), "3")
    payload: dict[str, Any] = {
        "fields": {
            "project": {"key": PROJECT_KEY},
            "issuetype": {"id": TEST_CATEGORY_TYPE_ID},
            "parent": {"key": epic_key},
            "summary": summary,
            "priority": {"id": priority_id},
        }
    }
    resp = jira_post("/issue", payload)
    return resp["key"]


def create_testing_task(
    parent_key: str,
    summary: str,
    description: str,
    wiki_markup: str,
    priority: str,
) -> str:
    """Create a Testing Task issue under a Test Category. Returns the new issue key."""
    priority_id = PRIORITY_NAME_TO_ID.get(priority.lower(), "3")
    payload: dict[str, Any] = {
        "fields": {
            "project": {"key": PROJECT_KEY},
            "issuetype": {"id": TESTING_TASK_TYPE_ID},
            "parent": {"key": parent_key},
            "summary": summary,
            "description": description,
            "priority": {"id": priority_id},
            "customfield_11772": wiki_markup,
        }
    }
    resp = jira_post("/issue", payload)
    return resp["key"]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Create Jira Test Category + Testing Task issues from a test plan.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            'Example:\n'
            '  %(prog)s test_plans/SW-211690/test_plan_SW-211690.md \\\n'
            '    --epic SW-211690 \\\n'
            '    --category "Sanity: TC-001-002, TC-008" \\\n'
            '    --category "HA: TC-009-016"'
        ),
    )
    ap.add_argument("test_plan", help="Path to the markdown test plan file")
    ap.add_argument("--epic", required=True, help="Parent epic key (SW-<digits>)")
    ap.add_argument(
        "--category",
        action="append",
        required=True,
        dest="categories",
        metavar='"Name: TC-NNN-NNN, TC-NNN"',
        help="Category name and TC assignments (repeatable)",
    )
    ap.add_argument(
        "--priority",
        default="Medium",
        help='Priority for all created issues (default: Medium)',
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and validate only; do not create issues",
    )
    ap.add_argument(
        "--link-covers",
        action="store_true",
        help=(
            "OPT-IN: after creating each Testing Task, add a Jira issue link "
            "(default type 'Relates') from it to every SW-<digits> story the TC "
            "Covers (its story / source_story / enabler_epic provenance). OFF by "
            "default; the parent epic and self-links are skipped and keys are "
            "de-duplicated. A link failure warns and continues (never aborts the push)."
        ),
    )
    ap.add_argument(
        "--link-type",
        default=DEFAULT_LINK_TYPE,
        help=f"Issue-link type name for --link-covers (default: {DEFAULT_LINK_TYPE}).",
    )
    ap.add_argument(
        "--adf-config",
        action="store_true",
        help=(
            "OPT-IN: after creating each Testing Task, set its DESCRIPTION to the "
            "TC's per-device Minimum Configuration rendered as REAL Jira ADF "
            "'expand' collapsibles (one per device) via _tp_jira_push_adf.py "
            "(REST v3, Cloud-native). Sourced from the epic manifest.json. OFF by "
            "default; the existing customfield_11772 push is unchanged. A failure "
            "warns and continues (never aborts the push)."
        ),
    )
    ap.add_argument(
        "--adf-manifest",
        default=None,
        help=(
            "Manifest.json path for --adf-config "
            "(default: ~/SCALER/TEST/tp/<EPIC>/manifest.json)."
        ),
    )
    args = ap.parse_args()

    epic_key = args.epic.strip().upper()
    plan_path = args.test_plan

    if not os.path.isfile(plan_path):
        print(f"error: test plan not found: {plan_path}", file=sys.stderr)
        return 1

    # --- Parse ---
    print(f"Parsing test plan: {plan_path}")
    all_tcs = parse_test_plan(plan_path)
    print(f"  Found {len(all_tcs)} test cases")

    # --- Parse categories ---
    categories: list[tuple[str, list[str]]] = []
    for raw in args.categories:
        name, tc_ids = parse_category_arg(raw)
        tc_ids.sort(key=_tc_sort_key)
        categories.append((name, tc_ids))

    # --- Validate ---
    validate_inputs(epic_key, categories, all_tcs)

    # --- Preview ---
    total_tasks = sum(len(tcs) for _, tcs in categories)
    print(f"\nPlan: {len(categories)} Test Categories, {total_tasks} Testing Tasks")
    print(f"Epic: {epic_key}  |  Priority: {args.priority}\n")
    for cat_name, tc_ids in categories:
        print(f"  [{cat_name}] ({len(tc_ids)} tasks)")
        for tc in tc_ids:
            line = f"    {tc}: {all_tcs[tc]['test_name']}"
            if args.link_covers:
                cov = [k for k in all_tcs[tc].get("covers_keys", []) if k != epic_key]
                line += f"   [{args.link_type} -> {', '.join(cov) if cov else 'none'}]"
            print(line)
    if args.link_covers:
        print(f"\n--link-covers ON: Testing Tasks will be '{args.link_type}'-linked to "
              f"their Covers story keys (epic {epic_key} + self-links skipped).")
    print()

    if args.dry_run:
        if args.adf_config:
            print("--adf-config ON: each Testing Task would also get REAL ADF "
                  "'expand' per-device config collapsibles (REST v3).")
        print("DRY RUN — no issues created.")
        return 0

    # --- OPT-IN: per-device config as ADF collapsibles (setup once) ---
    # ADDITIVE to the customfield_11772 push. Sources per-TC config from the epic
    # manifest and PUTs it as the Testing Task description via REST v3 ADF.
    adf = None
    adf_manifest = None
    adf_auth = None
    if args.adf_config:
        try:
            adf = _load_adf_module()
            manifest_path = args.adf_manifest or adf._manifest_path(epic_key)
            adf_manifest = json.load(open(manifest_path, encoding="utf-8"))
            a_email, a_token, a_src = adf.resolve_auth()
            adf_auth = adf._auth_header(a_email, a_token)
            print(f"--adf-config ON: per-device config from {manifest_path} "
                  f"(auth: {a_src}); ADF 'expand' collapsibles will be PUT to each "
                  f"Testing Task description.")
        except Exception as exc:  # noqa: BLE001 - setup failure must not create issues
            print(f"error: --adf-config setup failed: {exc}", file=sys.stderr)
            return 1

    # --- Create ---
    results: list[dict[str, str]] = []
    category_keys: dict[str, str] = {}

    for cat_name, tc_ids in categories:
        print(f"\nCreating Test Category: {cat_name}")
        try:
            cat_key = create_test_category(epic_key, cat_name, args.priority)
        except Exception as exc:
            print(f"  FAILED to create category '{cat_name}': {exc}", file=sys.stderr)
            return 1
        category_keys[cat_name] = cat_key
        print(f"  -> {cat_key}  {JIRA_BASE_URL}/browse/{cat_key}")

        for tc_id in tc_ids:
            tc = all_tcs[tc_id]
            print(f"  Creating Testing Task: {tc_id}")
            try:
                task_key = create_testing_task(
                    parent_key=cat_key,
                    summary=tc["summary"],
                    description=tc["description"],
                    wiki_markup=tc["wiki_markup"],
                    priority=args.priority,
                )
            except Exception as exc:
                print(f"    FAILED {tc_id}: {exc}", file=sys.stderr)
                results.append({"tc": tc_id, "key": "FAILED", "category": cat_name})
                continue
            results.append({"tc": tc_id, "key": task_key, "category": cat_name})
            print(f"    -> {task_key}  {JIRA_BASE_URL}/browse/{task_key}")

            # OPT-IN: set the new Testing Task's DESCRIPTION to its per-device
            # Minimum Configuration as REAL Jira ADF 'expand' collapsibles (one
            # per device), sourced from the epic manifest. Additive; a failure
            # warns and continues. SystemExit from the resolver is also caught so
            # a single unresolved TC never aborts the whole push.
            if args.adf_config and adf is not None:
                try:
                    tc_obj = adf.find_manifest_tc(adf_manifest, tc_id)
                    doc = adf.build_manifest_tc_adf(tc_obj)
                    exp = adf.collect_expand_nodes(doc)
                    if adf.put_description_adf(task_key, doc, adf_auth):
                        ok, titles = adf.verify_expand(
                            task_key, adf_auth, expected=len(exp)
                        )
                        print(f"      [{'OK' if ok else 'WARN'}] ADF config -> "
                              f"{task_key}: {len(titles)} expand(s) verified "
                              f"(expected {len(exp)})")
                    else:
                        print(f"      WARNING: ADF config PUT failed for "
                              f"{task_key}", file=sys.stderr)
                except (SystemExit, Exception) as exc:  # noqa: BLE001
                    print(f"      WARNING: ADF config for {tc_id} -> {task_key} "
                          f"skipped: {exc}", file=sys.stderr)

            # OPT-IN: link the Testing Task to each story it Covers. Skip the
            # parent epic + self; de-dup. A failure warns and continues.
            if args.link_covers:
                link_keys = [
                    k for k in tc.get("covers_keys", [])
                    if k != epic_key and k != task_key
                ]
                for target in link_keys:
                    try:
                        jira_create_issue_link(task_key, target, args.link_type)
                        print(f"      linked ({args.link_type}) {task_key} -> {target}")
                    except Exception as exc:  # noqa: BLE001 - never abort the push
                        print(
                            f"      WARNING: failed to link {task_key} -> {target}: {exc}",
                            file=sys.stderr,
                        )
            time.sleep(0.2)

    # --- Report ---
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Epic: {epic_key}")
    for cat_name, _ in categories:
        cat_key = category_keys.get(cat_name, "FAILED")
        print(f"\n  Test Category: {cat_key} — {cat_name}")
        for r in results:
            if r["category"] == cat_name:
                status = r["key"] if r["key"] != "FAILED" else "FAILED"
                print(f"    {r['tc']} -> {status}")

    failed = [r for r in results if r["key"] == "FAILED"]
    if failed:
        print(f"\n  {len(failed)} issue(s) FAILED to create.")
        return 1

    print(f"\nAll {len(results)} Testing Task(s) created successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
