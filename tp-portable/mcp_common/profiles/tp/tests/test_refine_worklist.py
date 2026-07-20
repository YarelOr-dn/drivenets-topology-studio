#!/usr/bin/env python3
"""Regression tests for Stage-7 refine worklist + loop driver."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

GATES_ROOT = Path(__file__).resolve().parents[1] / "gates"
sys.path.insert(0, str(GATES_ROOT))

import _tp_refine_loop as refine_loop  # noqa: E402
import _tp_refine_worklist as worklist  # noqa: E402
import _tp_tc_quality_gate as quality_gate  # noqa: E402
import _tp_traffic_matrix_audit as traffic_audit  # noqa: E402


def _minimal_fr(tcs: list[dict]) -> dict:
    return {"test_cases": tcs}


class TestWorklistBuilder(unittest.TestCase):
    def test_synthetic_e2_gap_yields_traffic_finding(self):
        with tempfile.TemporaryDirectory() as td:
            tp = Path(td) / "FIX-E2"
            tp.mkdir()
            (tp / "full_result.json").write_text(
                json.dumps(_minimal_fr([
                    {
                        "id": "TC-FIX-01",
                        "exec_tier": "E2",
                        "purpose": "forwarding test",
                        "steps": [
                            {"action": "stream", "command": "show multicast forwarding-table", "expected": "0% loss"},
                        ],
                        "pass_criteria": ["0% loss at egress"],
                    }
                ])),
                encoding="utf-8",
            )
            findings = traffic_audit.collect_findings(tp, "FIX-E2")
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0]["kind"], "traffic-matrix")
            self.assertIn("negative", findings[0]["what_missing"])

    def test_worklist_strict_exit_on_deliberate_fail(self):
        with tempfile.TemporaryDirectory() as td:
            tp = Path(td) / "FIX-FAIL"
            tp.mkdir()
            (tp / "full_result.json").write_text(
                json.dumps(_minimal_fr([
                    {
                        "id": "TC-BAD",
                        "exec_tier": "E2",
                        "purpose": "x",
                        "steps": [{"action": "a", "command": "", "expected": ""}],
                        "pass_criteria": ["only one"],
                    }
                ])),
                encoding="utf-8",
            )
            rc = worklist.run_worklist(tp, "FIX-FAIL", strict=True, write=False)
            self.assertEqual(rc, 1)

    def test_worklist_clean_fixture_exits_zero(self):
        with tempfile.TemporaryDirectory() as td:
            tp = Path(td) / "FIX-OK"
            tp.mkdir()
            tc = {
                "id": "TC-OK",
                "rich": True,
                "exec_tier": "E2",
                "purpose": "ok",
                "steps": [
                    {"dev": "#1 PE-X", "action": "fwd", "command": "show x", "expected": "delivered with 0% loss"},
                    {"dev": "#1 PE-X", "action": "neg", "command": "show y", "expected": "no flood to non-interested ports"},
                ],
                "pass_criteria": ["verify deliver ok", "verify no flood ok"],
            }
            (tp / "full_result.json").write_text(json.dumps(_minimal_fr([tc])), encoding="utf-8")
            (tp / "manifest.json").write_text(
                json.dumps({"test_cases": [tc], "tp_rules": {"rule_anchors": {}}}),
                encoding="utf-8",
            )
            (tp / "test_plan_FIX-OK.md").write_text("#### TC-OK - clean fixture\n_Test ID: `TC-OK`_\n")
            (tp / "sources_ingested.json").write_text(
                json.dumps({"epic": "FIX-OK", "ingested_epics": ["FIX-OK"], "ingested_confluence": [], "comments_scanned": True}),
                encoding="utf-8",
            )
            (tp / "spec_binding_report.json").write_text(
                json.dumps({"epic": "FIX-OK", "bindings": [], "blocker": None}),
                encoding="utf-8",
            )
            rc = worklist.run_worklist(tp, "FIX-OK", strict=True, write=False)
            self.assertEqual(rc, 0)


class TestStrictExitCodes(unittest.TestCase):
    def test_traffic_strict_nonzero_on_gap(self):
        with tempfile.TemporaryDirectory() as td:
            tp = Path(td)
            (tp / "full_result.json").write_text(
                json.dumps(_minimal_fr([{"id": "T", "exec_tier": "E2", "steps": [], "pass_criteria": []}])),
                encoding="utf-8",
            )
            self.assertEqual(traffic_audit.run_audit(tp, "X", strict=True), 1)
            self.assertEqual(traffic_audit.run_audit(tp, "X", strict=False), 0)

    def test_quality_strict_nonzero_on_gap(self):
        with tempfile.TemporaryDirectory() as td:
            tp = Path(td)
            (tp / "full_result.json").write_text(
                json.dumps(_minimal_fr([{"id": "T", "steps": [], "pass_criteria": ["x"]}])),
                encoding="utf-8",
            )
            self.assertEqual(quality_gate.run_gate(tp, "X", strict=True), 1)


class TestNoRegression(unittest.TestCase):
    def test_regression_detected_when_worklist_worsens(self):
        prev = {"e2_missing": 0, "below_floor": 0, "story_zero": 0, "story_thin": 0, "worklist_count": 0}
        curr = {"e2_missing": 1, "below_floor": 0, "story_zero": 0, "story_thin": 0, "worklist_count": 1}
        self.assertFalse(refine_loop._score_improved(prev, curr))

    def test_improvement_accepted(self):
        prev = {"e2_missing": 8, "below_floor": 2, "story_zero": 0, "story_thin": 0, "worklist_count": 11}
        curr = {"e2_missing": 0, "below_floor": 0, "story_zero": 0, "story_thin": 0, "worklist_count": 0}
        self.assertTrue(refine_loop._score_improved(prev, curr))


if __name__ == "__main__":
    unittest.main()
