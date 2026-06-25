#!/usr/bin/env python3
"""Compile SW-228552 TEST recipes through TEST MCP without executing phases."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path


CATALOG = Path("/home/dn/SCALER/TEST/catalog")
MCP_CLI = Path("/home/dn/.cursor/tools/mcp_cli.py")
SUMMARY_PATH = Path("/home/dn/SCALER/TEST/catalog/.sw228552_compile_readiness_20260513.json")


def extract_json(markdown: str) -> dict:
    start = markdown.find("```json")
    if start < 0:
        raise ValueError("missing JSON fenced block")
    start = markdown.find("\n", start)
    end = markdown.find("```", start + 1)
    if start < 0 or end < 0:
        raise ValueError("unterminated JSON fenced block")
    return json.loads(markdown[start:end].strip())


def atomic_write_text(path: Path, body: str) -> None:
    try:
        prior_mode = os.stat(path).st_mode & 0o777
    except FileNotFoundError:
        prior_mode = 0o644
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp, prior_mode)
        os.replace(tmp, path)
    except BaseException:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass
        raise


def main() -> int:
    paths = sorted(
        p
        for p in CATALOG.glob("TEST_SW-228552*/recipe.json")
        if ".backup_" not in p.parts
    )
    results: list[dict] = []
    failures: list[dict] = []

    for index, path in enumerate(paths, start=1):
        recipe = json.loads(path.read_text(encoding="utf-8"))
        test_id = recipe.get("id", path.parent.name)
        payload = json.dumps({"test_id": test_id, "format": "json"})
        proc = subprocess.run(
            ["python3", str(MCP_CLI), "user-test-mcp", "test_phase_compile", payload],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
            check=False,
        )
        row = {
            "index": index,
            "test_id": test_id,
            "recipe_path": str(path),
            "returncode": proc.returncode,
        }
        if proc.returncode != 0:
            row["verdict"] = "CLI_FAILED"
            row["stderr"] = proc.stderr.strip()[-800:]
            failures.append(row)
        else:
            try:
                data = extract_json(proc.stdout)
                row["ok"] = data.get("ok")
                row["verdict"] = data.get("verdict")
                row["compiled_count"] = len(data.get("compiled_phases") or [])
                needs = [
                    phase
                    for phase in [
                        *(data.get("compiled_phases") or []),
                        *(data.get("missing_phase_wiring") or []),
                    ]
                    if isinstance(phase, dict)
                    and phase.get("status") == "NEEDS_PHASE_WIRING"
                ]
                row["needs_wiring_count"] = len(needs)
                row["missing_bindings"] = sorted(
                    {
                        binding
                        for phase in needs
                        for binding in (phase.get("missing_bindings") or [])
                    }
                )
                row["manual_review_steps"] = [
                    phase.get("original_step", {}).get("step")
                    for phase in needs
                    if phase.get("original_step")
                ]
                if not data.get("ok") or data.get("verdict") != "PHASES_COMPILED":
                    row["errors"] = data.get("errors")
                    failures.append(row)
            except Exception as exc:  # noqa: BLE001 - audit script reports parser failures.
                row["verdict"] = "PARSE_FAILED"
                row["error"] = str(exc)
                failures.append(row)
        results.append(row)
        print(
            f"[{index:03d}/{len(paths):03d}] {test_id}: "
            f"{row.get('verdict')} phases={row.get('compiled_count', 0)}"
        )

    summary = {
        "total": len(results),
        "passed": len(results) - len(failures),
        "failed": len(failures),
        "failures": failures,
    }
    atomic_write_text(SUMMARY_PATH, json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(f"summary_path={SUMMARY_PATH}")
    print("SUMMARY_JSON=" + json.dumps(summary, sort_keys=True))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
