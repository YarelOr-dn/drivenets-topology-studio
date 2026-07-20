#!/usr/bin/env python3
"""Apply portability patches to vendored gate scripts (run once after copy)."""
from __future__ import annotations

import re
from pathlib import Path

GATES = Path(__file__).resolve().parent

REPLACEMENTS = [
    ('sys.path.insert(0, "/home/dn")', "# portable: mcp_common on PYTHONPATH"),
    ('default="/home/dn/SCALER/TEST/tp"', 'default=default_data_dir()'),
    ('default=str(Path.home() / "SCALER/TEST/tp")', 'default=default_data_dir()'),
    ('Path("/home/dn/mcp_common/mcp_cli.py")', 'resolve_mcp_cli()'),
    ('MCP_ROOT = Path("/home/dn/qa_automation/ai_test_plan/tp_agent_mcp")',
     'MCP_ROOT = resolve_mcp_root()'),
    ('JIRA_BASE_URL = "https://drivenets.atlassian.net"',
     'JIRA_BASE_URL = resolve_jira_base_url()'),
    ('TP_ROOT = os.path.expanduser("~/SCALER/TEST/tp")',
     'TP_DATA_ROOT = default_data_dir()'),
]

LINT_SCRIPTS = [
    "_tp_actor_consistency_lint.py",
    "_tp_bgp_show_coverage_lint.py",
    "_tp_counter_coverage_lint.py",
    "_tp_topology_usage_lint.py",
    "_tp_traffic_profile_lint.py",
    "_tp_us_coverage_lint.py",
    "_tp_verify_relevance_lint.py",
]


def patch_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    orig = text

    for old, new in REPLACEMENTS:
        text = text.replace(old, new)

    if path.name == "_tp_syntax_common.py":
        text = re.sub(
            r"TP_CACHE_DIR = Path\.home\(\) / \"\.cursor\" / \"tp_cache\"",
            "TP_CACHE_DIR = resolve_cache_dir()",
            text,
        )
        text = re.sub(
            r"CHEETAH_GLOB = Path\.home\(\) / \"cheetah\*\"",
            'CHEETAH_GLOB = Path(resolve_cheetah_glob())',
            text,
        )
        if "from _tp_paths import" not in text:
            text = text.replace(
                "from pathlib import Path\n",
                "from pathlib import Path\n\nfrom _tp_paths import resolve_cache_dir, resolve_cheetah_glob\n",
                1,
            )

    if path.name == "_tp_live_syntax_probe.py":
        if "from _tp_paths import resolve_mcp_cli" not in text:
            text = text.replace(
                "from pathlib import Path\n",
                "from pathlib import Path\n\nfrom _tp_paths import resolve_mcp_cli\n",
                1,
            )
        text = text.replace("_MCP_CLI = resolve_mcp_cli()", "_MCP_CLI = resolve_mcp_cli()")

    if path.name in ("_tp_self_check.py", "_tp_refine_loop.py", "_tp_refine_worklist.py"):
        text = text.replace(
            "TP_ROOT = Path(__file__).resolve().parent",
            "from _tp_paths import GATES_DIR as TP_ROOT, default_data_dir, resolve_mcp_root\n\nGATES_DIR = TP_ROOT",
            1,
        )
        if path.name == "_tp_self_check.py" and "resolve_mcp_root" not in text.split("MCP_ROOT")[0]:
            pass

    if path.name == "_tp_parity_gate.py":
        if "from _tp_paths import default_data_dir" not in text:
            text = text.replace(
                "from pathlib import Path\n",
                "from pathlib import Path\n\nfrom _tp_paths import default_data_dir\n",
                1,
            )

    if path.name == "_tp_jira_push_adf.py":
        if "from _tp_paths import" not in text:
            insert = (
                "from _tp_paths import default_data_dir, resolve_jira_base_url\n\n"
                "JIRA_BASE_URL = resolve_jira_base_url()\n"
                "JIRA_API_V3 = f\"{JIRA_BASE_URL}/rest/api/3\"\n"
            )
            text = re.sub(
                r"JIRA_BASE_URL = resolve_jira_base_url\(\)\nJIRA_API_V3 = f\"\{JIRA_BASE_URL\}/rest/api/3\"\n",
                insert,
                text,
                count=1,
            )
            if "TP_DATA_ROOT" in text:
                text = text.replace(
                    'return os.path.join(TP_ROOT, epic.strip().upper(), "manifest.json")',
                    'return os.path.join(TP_DATA_ROOT, epic.strip().upper(), "manifest.json")',
                )

    if path.name in LINT_SCRIPTS:
        text = text.replace(
            "TP_ROOT = Path(__file__).resolve().parent",
            "from _tp_paths import resolve_data_dir, default_data_dir\n",
            1,
        )
        text = text.replace("TP_ROOT / a.epic", "resolve_data_dir(getattr(a, 'dir', None)) / a.epic")
        text = text.replace("TP_ROOT / epic", "resolve_data_dir(getattr(args, 'dir', None)) / epic")
        if 'ap.add_argument("--dir"' not in text:
            text = text.replace(
                'ap.add_argument("--epic", required=True)',
                'ap.add_argument("--epic", required=True)\n'
                '    ap.add_argument("--dir", default=default_data_dir())',
                1,
            )

    if path.name == "_tp_review.py":
        text = text.replace(
            "TP_ROOT = Path(__file__).resolve().parent\n\n\ndef _manifest_path(epic: str) -> Path:\n"
            "    return TP_ROOT / epic / \"manifest.json\"",
            "from _tp_paths import resolve_data_dir, default_data_dir\n\n\n"
            "def _manifest_path(epic: str, data_dir: str | None = None) -> Path:\n"
            '    return resolve_data_dir(data_dir) / epic / "manifest.json"',
        )
        text = text.replace(
            "def _load_tcs(epic: str):",
            "def _load_tcs(epic: str, data_dir: str | None = None):",
        )
        text = text.replace(
            "mp = _manifest_path(epic)",
            "mp = _manifest_path(epic, data_dir)",
        )
        text = text.replace(
            'ap.add_argument("--epic", required=True)',
            'ap.add_argument("--epic", required=True)\n'
            '    ap.add_argument("--dir", default=default_data_dir())',
            1,
        )
        text = text.replace(
            "tcs = _load_tcs(args.epic)",
            "tcs = _load_tcs(args.epic, args.dir)",
        )

    if path.name == "_tp_syntax_divergence.py":
        text = text.replace(
            "TP_ROOT = Path(__file__).resolve().parent",
            "from _tp_paths import resolve_data_dir, default_data_dir\n",
            1,
        )
        text = text.replace(
            "return TP_ROOT / epic / \"syntax_divergences.json\"",
            "return resolve_data_dir(data_dir) / epic / \"syntax_divergences.json\"",
        )

    if path.name == "_tp_push_category.py":
        text = text.replace(
            "TP_ROOT = Path(__file__).resolve().parent",
            "from _tp_paths import GATES_DIR as TP_ROOT, resolve_data_dir, default_data_dir\n",
            1,
        )
        text = text.replace("TP_ROOT / a.epic", "resolve_data_dir(a.dir) / a.epic")

    # Ensure files with default_data_dir() import it
    if "default_data_dir()" in text and "from _tp_paths import" not in text:
        if path.name not in ("_tp_paths.py",):
            text = "from _tp_paths import default_data_dir\n" + text

    if path.name == "_tp_self_check.py" and "resolve_mcp_root" not in text:
        text = text.replace(
            "from _tp_paths import GATES_DIR as TP_ROOT, resolve_mcp_root",
            "from _tp_paths import GATES_DIR as TP_ROOT, resolve_mcp_root",
        )

    if text != orig:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> int:
    changed = 0
    for path in sorted(GATES.glob("_tp_*.py")):
        if patch_file(path):
            changed += 1
            print(f"[OK] patched {path.name}")
    print(f"[INFO] {changed} files patched")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
