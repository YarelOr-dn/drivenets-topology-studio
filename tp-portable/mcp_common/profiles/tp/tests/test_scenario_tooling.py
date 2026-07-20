#!/usr/bin/env python3
"""Regression tests for /TP scenario extractor + coverage gate + MCP rule."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

GATES_ROOT = Path(__file__).resolve().parents[1] / "gates"
MCP_ROOT = Path(__file__).resolve().parents[1] / "mcp" / "tp_agent_mcp"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(GATES_ROOT))
sys.path.insert(0, str(MCP_ROOT))

import _tp_scenario_extract as extract  # noqa: E402
import _tp_scenario_coverage_gate as covgate  # noqa: E402
from quality_validator import check_scenario_coverage, SCENARIO_COVERAGE_HARD_FAIL  # noqa: E402


class TestScenarioExtract(unittest.TestCase):
    def test_hld_minimal_yields_expected_ids(self):
        text = (FIXTURES / "hld_minimal.md").read_text(encoding="utf-8")
        items = extract.extract_from_hld_markdown(text)
        ids = {s["scenario_id"] for s in items}
        self.assertIn("A1", ids)
        self.assertIn("A2", ids)
        self.assertIn("G1", ids)
        waived = [s for s in items if s["status"] == "waived"]
        self.assertTrue(waived, "expected at least one waived scenario (TBD/no need)")

    def test_no_hld_jira_rfc_only_does_not_false_fail(self):
        with tempfile.TemporaryDirectory() as td:
            tp = Path(td) / "FIX-NOHLD"
            tp.mkdir()
            (tp / "must_requirements.json").write_text(
                (FIXTURES / "must_only.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            rc = extract.run_extract(tp, "FIX-NOHLD")
            self.assertEqual(rc, 0)
            inv = json.loads((tp / "scenario_inventory.json").read_text())
            self.assertGreaterEqual(inv["scenario_count"], 1)
            # Empty inventory must INFO-skip, not false-FAIL (no full_result needed)
            self.assertEqual(inv["needs_coverage_count"], 1)


class TestUserStories(unittest.TestCase):
    def test_user_story_file_yields_us_items(self):
        with tempfile.TemporaryDirectory() as td:
            tp = Path(td)
            (tp / "jira_user_stories.json").write_text(
                json.dumps({
                    "user_stories": [
                        {"key": "SW-1001", "summary": "Support SMET", "status": "In Progress"},
                        {"key": "SW-1002", "summary": "Rejected idea", "status": "Rejected"},
                        {"key": "SW-1003", "summary": "MLD out of scope", "status": "Done"},
                    ]
                }),
                encoding="utf-8",
            )
            items = extract.extract_from_user_stories(tp / "jira_user_stories.json")
            ids = {s["scenario_id"]: s for s in items}
            self.assertIn("US-SW-1001", ids)
            self.assertNotIn("US-SW-1002", ids)  # rejected dropped
            self.assertEqual(ids["US-SW-1001"]["status"], "needs-coverage")
            self.assertEqual(ids["US-SW-1003"]["status"], "waived")  # out of scope

    def test_user_story_from_must_provenance(self):
        with tempfile.TemporaryDirectory() as td:
            tp = Path(td)
            (tp / "must_requirements.json").write_text(
                json.dumps({"must_requirements": [
                    {"id": "MUST-001", "text": "do a thing", "source": "epic/SW-2001"},
                    {"id": "MUST-002", "text": "another", "source_story": "SW-2002"},
                ]}),
                encoding="utf-8",
            )
            items = extract.extract_from_must_source_stories(tp / "must_requirements.json")
            ids = {s["scenario_id"] for s in items}
            self.assertIn("US-SW-2001", ids)
            self.assertIn("US-SW-2002", ids)


class TestAgentLayer(unittest.TestCase):
    def test_valid_agent_file_merges(self):
        with tempfile.TemporaryDirectory() as td:
            tp = Path(td)
            (tp / "scenario_inventory_agent.json").write_text(
                json.dumps({"scenarios": [
                    {"scenario_id": "AGENT-1", "text": "missed HLD case", "kind": "hld_group_item"},
                ]}),
                encoding="utf-8",
            )
            items = extract.extract_from_agent_file(tp / "scenario_inventory_agent.json")
            self.assertEqual(items[0]["scenario_id"], "AGENT-1")
            self.assertEqual(items[0]["source"], "agent")

    def test_agent_missing_field_raises(self):
        with tempfile.TemporaryDirectory() as td:
            tp = Path(td)
            (tp / "scenario_inventory_agent.json").write_text(
                json.dumps({"scenarios": [{"scenario_id": "AGENT-2"}]}),
                encoding="utf-8",
            )
            with self.assertRaises(extract.AgentScenarioError):
                extract.extract_from_agent_file(tp / "scenario_inventory_agent.json")

    def test_agent_waived_without_reason_raises(self):
        with tempfile.TemporaryDirectory() as td:
            tp = Path(td)
            (tp / "scenario_inventory_agent.json").write_text(
                json.dumps({"scenarios": [
                    {"scenario_id": "AGENT-3", "text": "x", "kind": "k", "status": "waived"},
                ]}),
                encoding="utf-8",
            )
            with self.assertRaises(extract.AgentScenarioError):
                extract.extract_from_agent_file(tp / "scenario_inventory_agent.json")

    def test_bad_agent_file_makes_run_extract_exit_3(self):
        with tempfile.TemporaryDirectory() as td:
            tp = Path(td) / "FIX-BADAGENT"
            tp.mkdir()
            (tp / "scenario_inventory_agent.json").write_text(
                json.dumps([{"scenario_id": "X"}]), encoding="utf-8",
            )
            self.assertEqual(extract.run_extract(tp, "FIX-BADAGENT"), 3)


class TestValidationMining(unittest.TestCase):
    def test_mutual_exclusion_mined_from_body(self):
        body = (
            "## CLI igmp-snooping\n"
            "A commit validation shall check that there are no seamless-integration "
            "site-ids together with igmp-snooping. VPLS and Proxy-IGMP snooping are "
            "mutually exclusive on the same EVPN instance.\n"
        )
        items = extract.extract_validation_scenarios(body)
        self.assertTrue(items, "expected at least one VAL-* commit-validation scenario")
        self.assertTrue(all(s["kind"] == "commit_validation" for s in items))
        self.assertTrue(all(s["scenario_id"].startswith("VAL-") for s in items))

    def test_plain_prose_yields_nothing(self):
        body = "This section describes the general architecture of the proxy.\n"
        self.assertEqual(extract.extract_validation_scenarios(body), [])


class TestHldAudit(unittest.TestCase):
    def test_zero_yield_heading_flagged(self):
        hld = (
            "## Group A\n- **A1** join case\n\n"
            "## Hidden Section\nThis paragraph describes a special scenario we "
            "want to verify, but it uses no bullet and no normative keyword so "
            "the deterministic parser turns it into nothing at all really.\n"
        )
        # Only A1 gets extracted; the "Hidden Section" (has must/verify) is a blind spot.
        scen = extract.extract_from_hld_markdown(hld)
        audit = extract.audit_hld_blind_spots(hld, scen)
        titles = {h["heading"] for h in audit["headings_with_zero"]}
        self.assertIn("Hidden Section", titles)


class TestCoverageGate(unittest.TestCase):
    def test_complete_fixture_passes(self):
        with tempfile.TemporaryDirectory() as td:
            tp = Path(td) / "FIX-COMPLETE"
            tp.mkdir()
            (tp / "scenario_inventory.json").write_text(
                (FIXTURES / "scenario_inventory_complete.json").read_text(),
                encoding="utf-8",
            )
            (tp / "full_result.json").write_text(
                (FIXTURES / "full_result_complete.json").read_text(),
                encoding="utf-8",
            )
            self.assertEqual(covgate.run_gate(tp, "FIX-COMPLETE", verbose=False), 0)

    def test_incomplete_fixture_fails(self):
        with tempfile.TemporaryDirectory() as td:
            tp = Path(td) / "FIX-INCOMPLETE"
            tp.mkdir()
            inv = json.loads((FIXTURES / "scenario_inventory_complete.json").read_text())
            inv["epic"] = "FIX-INCOMPLETE"
            (tp / "scenario_inventory.json").write_text(json.dumps(inv), encoding="utf-8")
            (tp / "full_result.json").write_text(
                (FIXTURES / "full_result_incomplete.json").read_text(),
                encoding="utf-8",
            )
            self.assertEqual(covgate.run_gate(tp, "FIX-INCOMPLETE", verbose=False), 1)


class TestMcpScenarioRule(unittest.TestCase):
    def test_mcp_warn_mode_on_incomplete(self):
        inv = json.loads((FIXTURES / "scenario_inventory_complete.json").read_text())
        res = json.loads((FIXTURES / "full_result_incomplete.json").read_text())
        hard, warn, summary = check_scenario_coverage(res, inv)
        if SCENARIO_COVERAGE_HARD_FAIL:
            self.assertTrue(hard)
            self.assertIn("G1", hard[0])
        else:
            self.assertEqual(hard, [])
            self.assertTrue(warn)
        self.assertGreater(summary["mapped"], 0)
        self.assertLess(summary["mapped"], summary["needs_coverage"])

    def test_mcp_pass_on_complete(self):
        inv = json.loads((FIXTURES / "scenario_inventory_complete.json").read_text())
        res = json.loads((FIXTURES / "full_result_complete.json").read_text())
        hard, warn, summary = check_scenario_coverage(res, inv)
        self.assertEqual(hard, [])
        self.assertEqual(warn, [])
        self.assertEqual(summary["mapped"], summary["needs_coverage"])


if __name__ == "__main__":
    unittest.main()
