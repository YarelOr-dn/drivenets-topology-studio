#!/usr/bin/env python3
"""Tests for /TP syntax source-of-truth binding (harvester + gate)."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

GATES_ROOT = Path(__file__).resolve().parents[1] / "gates"
MCP_ROOT = Path(__file__).resolve().parents[1] / "mcp" / "tp_agent_mcp"
sys.path.insert(0, str(GATES_ROOT))
sys.path.insert(0, str(MCP_ROOT))

import _tp_cli_spec_harvester as harvester  # noqa: E402
import _tp_spec_binding_gate as spec_gate  # noqa: E402
import _tp_syntax_common as syntax  # noqa: E402


class TestStoryHarvester(unittest.TestCase):
    def test_story_cmd_syntax_hit(self):
        text = """
## SW-999001 [To Do] demo

**cmd syntax:**  admin-state <enabled/disabled>

**cmd level: configure network-services evpn instance <name> protocols igmp-snooping**
"""
        rows = syntax.parse_story_cmd_blocks(text)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["sw_key"], "SW-999001")
        self.assertIn("admin-state", rows[0]["full"])


class TestRstHarvester(unittest.TestCase):
    def test_rst_syntax_regex(self):
        text = "**Command syntax: show evpn summary**\n"
        out = syntax.parse_rst_syntax(text, "show/evpn summary.rst")
        self.assertEqual(out, ["show evpn summary"])


class TestSpecBindingGate(unittest.TestCase):
    def _fixture_tp(self, tmp: Path, *, fr_tcs: list[dict], inventory: list[dict]) -> Path:
        epic = "FIX-SPEC"
        tp = tmp / epic
        tp.mkdir()
        (tp / "epic_version.json").write_text(
            json.dumps({
                "epic": epic,
                "fix_version": "v26.4",
                "implementation_status": "pending_build",
                "blocker": {"message": "test blocker"},
            }),
            encoding="utf-8",
        )
        (tp / "cli_spec_inventory.json").write_text(
            json.dumps({"entries": inventory}),
            encoding="utf-8",
        )
        (tp / "full_result.json").write_text(
            json.dumps({"test_cases": fr_tcs}),
            encoding="utf-8",
        )
        return tp

    def test_bind_story_spec(self):
        inv = [{
            "cmd": "configure network-services evpn instance <name> protocols igmp-snooping admin-state <enabled/disabled>",
            "kind": "config",
            "source": "SPEC_USER_STORY:SW-999001",
            "raw": "admin-state <enabled/disabled>",
            "syntax_only": "admin-state <enabled/disabled>",
            "level": "configure network-services evpn instance <name> protocols igmp-snooping",
            "norm": syntax.normalize_cmd(
                "configure network-services evpn instance <name> protocols igmp-snooping admin-state <enabled/disabled>"
            ),
            "norm_syntax": syntax.normalize_cmd("admin-state <enabled/disabled>"),
        }]
        fr = [{
            "id": "TC-1",
            "steps": [{
                "command": "configure network-services evpn instance SVC-1 protocols igmp-snooping admin-state enabled",
            }],
        }]
        with tempfile.TemporaryDirectory() as td:
            tp = self._fixture_tp(Path(td), fr_tcs=fr, inventory=inv)
            report = spec_gate.bind_all(tp, "FIX-SPEC", write=False)
            self.assertTrue(str(report["bindings"][0]["state"]).startswith("SPEC_USER_STORY"))

    def test_unbound_strict_fails(self):
        fr = [{"id": "TC-BAD", "steps": [{"command": "configure invented-knob foo bar"}]}]
        with tempfile.TemporaryDirectory() as td:
            tp = self._fixture_tp(Path(td), fr_tcs=fr, inventory=[])
            # No blocker -> true UNBOUND
            (tp / "epic_version.json").write_text(
                json.dumps({
                    "epic": "FIX-SPEC",
                    "fix_version": "v26.2",
                    "implementation_status": "pending_build",
                    "rst_root": "/tmp",
                    "blocker": None,
                }),
                encoding="utf-8",
            )
            rc = spec_gate.run_gate(tp, "FIX-SPEC", strict=True, write=False)
            self.assertEqual(rc, 1)

    def test_drift_warn_finding(self):
        findings = [{
            "kind": "spec-binding",
            "target_id": "TC-1",
            "what_missing": "DRIFT live != SPEC: show foo",
            "severity": "warn",
        }]
        # Direct collect_findings drift path via report file
        with tempfile.TemporaryDirectory() as td:
            tp = Path(td)
            (tp / "spec_binding_report.json").write_text(
                json.dumps({
                    "bindings": [{
                        "tc_id": "TC-1",
                        "command": "show foo",
                        "state": "DRIFT",
                        "drift": True,
                        "spec_source": "SPEC_USER_STORY:SW-1",
                    }],
                }),
                encoding="utf-8",
            )
            out = spec_gate.collect_findings(tp, "X")
            self.assertEqual(out[0]["severity"], "warn")


class TestHarvesterIntegration(unittest.TestCase):
    def test_harvest_writes_inventory(self):
        with tempfile.TemporaryDirectory() as td:
            epic = "FIX-HARV"
            tp = Path(td) / epic
            tp.mkdir()
            (tp / "epic_version.json").write_text(
                json.dumps({"fix_version": "v26.4", "blocker": {"message": "x"}}),
                encoding="utf-8",
            )
            (tp / "user_story_bodies.md").write_text(
                "## SW-1 [x] y\n\n**cmd syntax:**  proxy <enabled>\n\n"
                "**cmd level: configure network-services evpn instance <name> protocols igmp-snooping**\n",
                encoding="utf-8",
            )
            out = harvester.harvest_inventory(tp, epic, write=True)
            self.assertGreaterEqual(out["story_count"], 1)
            self.assertTrue((tp / "cli_spec_inventory.json").is_file())


if __name__ == "__main__":
    unittest.main()
