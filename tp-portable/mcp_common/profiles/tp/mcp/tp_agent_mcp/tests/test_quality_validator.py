"""Unit tests for TP quality validator (no Jira, no network)."""

import unittest

from tp_agent_mcp.quality_validator import (
    extract_tc_blocks,
    summarize_coverage,
    validate_structured_result,
    validate_test_plan_markdown,
)


MINIMAL_TP = """## Test Cases

### **TC-001: Example**

1. **Test Name:** Foo Positive

2. **Test Description:** Does thing

3. **Test Steps:**

   1. Step one
   2. Step two

4. **Pass Criteria:**

   1. Criterion one
   2. Criterion two

5. **Variants:** none
"""


class TestQualityValidator(unittest.TestCase):
    def test_extract_blocks(self):
        blocks = extract_tc_blocks(MINIMAL_TP)
        self.assertIn("TC-001", blocks)

    def test_validate_markdown_ok(self):
        ok, errs = validate_test_plan_markdown(MINIMAL_TP)
        self.assertTrue(ok, errs)

    def test_validate_structured_v2_requires_fields(self):
        ok, errs = validate_structured_result({"schema_version": 2, "test_count": 1})
        self.assertFalse(ok)
        self.assertTrue(any("quality_gate" in e for e in errs))

    def test_validate_structured_v2_ok(self):
        body = {
            "schema_version": 2,
            "test_count": 1,
            "quality_gate": {"verdict": "pass"},
            "artifacts": {},
        }
        ok, errs = validate_structured_result(body)
        self.assertTrue(ok, errs)

    def test_summarize_coverage(self):
        epic = {"user_stories": [{"key": "SW-1"}, {"key": "SW-2"}]}
        result = {"test_plan_markdown": "Cover SW-1 only"}
        s = summarize_coverage(epic, result)
        self.assertEqual(s["user_stories_mentioned_in_plan"], ["SW-1"])
        self.assertEqual(s["user_stories_not_mentioned_in_plan"], ["SW-2"])


if __name__ == "__main__":
    unittest.main()
