"""CLI for /TP — doctor, ingest, generate, gates, push (portable profile)."""
from __future__ import annotations

import argparse
import json
import sys


def _cmd_doctor(_args: argparse.Namespace) -> int:
    from mcp_common.profiles.tp.tp_env import portability_doctor

    out = portability_doctor()
    print(json.dumps(out, indent=2, default=str))
    if out.get("remediation"):
        print("\n[REMEDIATION]")
        for line in out["remediation"]:
            print(f"  - {line}")
    return 0 if out.get("go") else 1


def _cmd_knowledge(args: argparse.Namespace) -> int:
    from mcp_common.profiles.tp.knowledge import knowledge_list, knowledge_import

    if args.knowledge_cmd == "list":
        items = knowledge_list()
        print(json.dumps(items, indent=2))
        return 0
    if args.knowledge_cmd == "import":
        out = knowledge_import(force=args.force)
        print(json.dumps(out, indent=2))
        return 0 if out.get("ok") else 1
    return 1


def _cmd_ingest(args: argparse.Namespace) -> int:
    from mcp_common.profiles.tp.ingest import ingest_epic

    out = ingest_epic(args.epic, linked=args.linked or [])
    print(json.dumps(out, indent=2, default=str))
    return 0 if out.get("ok") else 1


def _cmd_generate(args: argparse.Namespace) -> int:
    from mcp_common.profiles.tp.generate import run_generate

    out = run_generate(
        args.epic,
        agent=args.agent,
        categories=args.categories,
        strict_knowledge=args.strict_knowledge,
    )
    if out.get("report_block"):
        print(out["report_block"])
        print()
    print(json.dumps({k: v for k, v in out.items() if k != "report_block"}, indent=2, default=str))
    return 0 if out.get("ok") else 1


def _cmd_selfcheck(args: argparse.Namespace) -> int:
    from mcp_common.profiles.tp.gates_runner import run_selfcheck

    return run_selfcheck(args.epic, skip_mcp_validate=args.skip_mcp_validate)


def _cmd_parity(args: argparse.Namespace) -> int:
    from mcp_common.profiles.tp.gates_runner import run_parity

    return run_parity(args.epic, strict=args.strict)


def _cmd_refine(args: argparse.Namespace) -> int:
    from mcp_common.profiles.tp.gates_runner import run_refine

    return run_refine(args.epic, max_iterations=args.max_iterations)


def _cmd_review(args: argparse.Namespace) -> int:
    from mcp_common.profiles.tp.gates_runner import run_review

    text = run_review(
        args.epic,
        tc=args.tc,
        category=args.category,
        list_all=args.list_all,
        fmt=args.format,
    )
    print(text)
    return 0


def _cmd_push(args: argparse.Namespace) -> int:
    from mcp_common.profiles.tp.push_runner import run_push

    out = run_push(
        args.epic,
        category=args.category,
        tc=args.tc,
        adf_config=args.adf_config,
        dry_run=args.dry_run,
    )
    print(json.dumps(out, indent=2, default=str))
    return 0 if out.get("ok") else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="/TP portable CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor", help="Portability doctor + go/no-go")

    p_know = sub.add_parser("knowledge", help="Knowledge seed management")
    know_sub = p_know.add_subparsers(dest="knowledge_cmd", required=True)
    know_sub.add_parser("list", help="List installed knowledge features")
    p_import = know_sub.add_parser("import", help="Import bundled knowledge_seed")
    p_import.add_argument("--force", action="store_true")

    p_ingest = sub.add_parser("ingest", help="Ingest epic + enablers from Jira")
    p_ingest.add_argument("epic")
    p_ingest.add_argument("--linked", nargs="*", default=[])

    p_gen = sub.add_parser("generate", help="Generate TP for epic")
    p_gen.add_argument("epic")
    p_gen.add_argument("--agent", choices=["sdk", "cursor", "none"], default="none")
    p_gen.add_argument("--categories", nargs="*")
    p_gen.add_argument("--strict-knowledge", action="store_true")

    p_sc = sub.add_parser("selfcheck", help="Run _tp_self_check gates")
    p_sc.add_argument("epic")
    p_sc.add_argument("--skip-mcp-validate", action="store_true")

    p_par = sub.add_parser("parity", help="Run parity gate")
    p_par.add_argument("epic")
    p_par.add_argument("--strict", action="store_true")

    p_ref = sub.add_parser("refine", help="Run Stage-7 refine loop")
    p_ref.add_argument("epic")
    p_ref.add_argument("--max-iterations", type=int, default=3)

    p_rev = sub.add_parser("review", help="Review TC render from manifest")
    p_rev.add_argument("epic")
    p_rev.add_argument("--tc")
    p_rev.add_argument("--category")
    p_rev.add_argument("--list", dest="list_all", action="store_true")
    p_rev.add_argument("--format", choices=["chat", "jira"], default="chat")

    p_push = sub.add_parser("push", help="Push TP to Jira")
    p_push.add_argument("epic")
    p_push.add_argument("--category")
    p_push.add_argument("--tc")
    p_push.add_argument("--adf-config", action="store_true")
    p_push.add_argument("--dry-run", action="store_true")

    args = parser.parse_args(argv)
    handlers = {
        "doctor": _cmd_doctor,
        "knowledge": _cmd_knowledge,
        "ingest": _cmd_ingest,
        "generate": _cmd_generate,
        "selfcheck": _cmd_selfcheck,
        "parity": _cmd_parity,
        "refine": _cmd_refine,
        "review": _cmd_review,
        "push": _cmd_push,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
