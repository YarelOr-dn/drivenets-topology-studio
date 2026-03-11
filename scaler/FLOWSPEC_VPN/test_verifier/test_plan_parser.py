#!/usr/bin/env python3
"""
Test Plan Parser - Parse test structure from Jira or markdown files

This module parses test plan data from Jira issue descriptions or
markdown files and converts them to structured TestCase objects.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

from .jira_fetcher import (
    fetch_issue, get_issue_description, JIRA_KEYS, MARKDOWN_FILES,
    get_all_test_categories, get_tests_for_category
)
from .test_cases import TestCase, TestStep

logger = logging.getLogger(__name__)


def parse_markdown_file(file_path: Path) -> str:
    """Load and return markdown file content"""
    if file_path.exists():
        with open(file_path, "r") as f:
            return f.read()
    return ""


def extract_test_cases_from_markdown(content: str, jira_key: str) -> List[TestCase]:
    """
    Parse markdown content to extract test cases
    
    Expected format:
    ### HF-01: Test Name
    **Objective:** ...
    **Steps:**
    1. Step description
    2. Another step
    **Expected Result:**
    ...
    **Pass Criteria:**
    - [ ] Criterion 1
    - [ ] Criterion 2
    """
    test_cases = []
    
    # Split by test case headers (### HF-XX: or ### NEG-XX:)
    test_pattern = r"###\s+(HF-\d+|NEG-\d+):\s+(.+?)(?=###\s+(?:HF-\d+|NEG-\d+):|$)"
    matches = re.finditer(test_pattern, content, re.DOTALL)
    
    for match in matches:
        test_id = match.group(1)
        test_header = match.group(2).strip()
        test_content = match.group(0)
        
        # Extract test name (first line after test ID)
        lines = test_header.split("\n")
        test_name = lines[0].strip() if lines else test_id
        
        # Extract objective
        objective_match = re.search(r"\*\*Objective:\*\*\s*(.+?)(?=\*\*|$)", test_content, re.DOTALL)
        objective = objective_match.group(1).strip() if objective_match else ""
        
        # Extract steps
        steps = extract_steps(test_content)
        
        # Extract expected result
        expected_match = re.search(r"\*\*Expected Result:\*\*\s*(.+?)(?=\*\*|$)", test_content, re.DOTALL)
        expected_result = expected_match.group(1).strip() if expected_match else ""
        
        # Extract pass criteria
        pass_criteria = extract_pass_criteria(test_content)
        
        # Extract prerequisites (from document header)
        prerequisites = extract_prerequisites(content)
        
        # Determine test type
        test_type = "negative" if test_id.startswith("NEG") else "happy_flow"
        
        test_case = TestCase(
            test_id=test_id,
            jira_key=jira_key,
            test_name=test_name,
            description=objective,
            objective=objective,
            test_type=test_type,
            steps=steps,
            pass_criteria=pass_criteria,
            prerequisites=prerequisites,
            expected_result=expected_result,
            estimated_duration=estimate_duration(steps),
        )
        
        test_cases.append(test_case)
        logger.debug(f"Parsed test case: {test_id}")
    
    return test_cases


def extract_steps(content: str) -> List[TestStep]:
    """Extract test steps from content"""
    steps = []
    
    # Look for Steps section
    steps_match = re.search(r"\*\*Steps:\*\*\s*(.+?)(?=\*\*|$)", content, re.DOTALL)
    if not steps_match:
        return steps
    
    steps_content = steps_match.group(1)
    
    # Extract numbered steps (1., 2., etc.)
    step_pattern = r"(\d+)\.\s+(.+?)(?=\d+\.|$)"
    step_matches = re.finditer(step_pattern, steps_content, re.DOTALL)
    
    for match in step_matches:
        step_num = int(match.group(1))
        step_desc = match.group(2).strip()
        
        # Extract command if present (code blocks)
        command = None
        command_match = re.search(r"```\s*(.+?)\s*```", step_desc, re.DOTALL)
        if command_match:
            command = command_match.group(1).strip()
        
        # Check if manual step
        manual_step = "manual" in step_desc.lower() or "spirent" in step_desc.lower()
        
        test_step = TestStep(
            step_number=step_num,
            description=step_desc,
            command=command,
            expected_output=None,
            verification_function=None,
            manual_step=manual_step,
        )
        
        steps.append(test_step)
    
    return steps


def extract_pass_criteria(content: str) -> List[str]:
    """Extract pass criteria (checkbox items)"""
    criteria = []
    
    # Look for Pass Criteria section
    criteria_match = re.search(r"\*\*Pass Criteria:\*\*\s*(.+?)(?=\*\*|$)", content, re.DOTALL)
    if not criteria_match:
        return criteria
    
    criteria_content = criteria_match.group(1)
    
    # Extract checkbox items (- [ ] or - [x])
    checkbox_pattern = r"[-*]\s*\[[ x]\]\s*(.+?)(?=\n|$)"
    checkbox_matches = re.finditer(checkbox_pattern, criteria_content, re.MULTILINE)
    
    for match in checkbox_matches:
        criterion = match.group(1).strip()
        criteria.append(criterion)
    
    return criteria


def extract_prerequisites(content: str) -> List[str]:
    """Extract prerequisites from document"""
    prerequisites = []
    
    # Look for Prerequisites section (usually at top of document)
    prereq_match = re.search(r"##\s+Prerequisites\s*(.+?)(?=##|$)", content, re.DOTALL)
    if prereq_match:
        prereq_content = prereq_match.group(1)
        # Extract list items
        list_items = re.findall(r"[-*]\s+(.+?)(?=\n|$)", prereq_content, re.MULTILINE)
        prerequisites.extend([item.strip() for item in list_items])
    
    return prerequisites


def estimate_duration(steps: List[TestStep]) -> int:
    """Estimate test duration in seconds based on number of steps"""
    base_time = 30  # Base time per test
    step_time = 15  # Time per step
    manual_step_time = 60  # Time for manual steps
    
    duration = base_time
    for step in steps:
        if step.manual_step:
            duration += manual_step_time
        else:
            duration += step_time
    
    return duration


def parse_jira_issue(issue_key: str, require_jira: bool = False) -> List[TestCase]:
    """
    Parse test cases from Jira issue
    
    Args:
        issue_key: Jira issue key (e.g., "SW-234158")
        require_jira: If True, fail if Jira data not available
    
    Returns:
        List of TestCase objects
    """
    # Fetch issue data (Jira is primary source, now handles ADF)
    issue_data = fetch_issue(issue_key)
    if not issue_data:
        logger.error(f"Failed to fetch issue {issue_key}")
        if require_jira:
            logger.error("Jira fetch required but failed. Set JIRA_EMAIL and JIRA_API_TOKEN environment variables.")
        return []
    
    # Warn if using markdown fallback
    if issue_data.get("source") == "markdown":
        logger.warning(f"Using markdown fallback for {issue_key}. For latest test data, fetch from Jira.")
    
    # Get description (now handles ADF format via jira_fetcher)
    description = get_issue_description(issue_data)
    
    if not description:
        logger.warning(f"No description found for {issue_key}, trying markdown fallback")
    
    # If no description or no test cases parsed, try markdown fallback
    test_cases = []
    if description:
        # Parse markdown content (description is now in markdown format after ADF parsing)
        test_cases = extract_test_cases_from_markdown(description, issue_key)
    
    # If no test cases found, try direct markdown file fallback
    if not test_cases:
        logger.info(f"No test cases from Jira description, trying markdown file fallback for {issue_key}")
        
        # Try to find markdown file by issue key
        markdown_path = None
        
        # First, check if it's in JIRA_KEYS mapping
        issue_type = None
        for key, value in JIRA_KEYS.items():
            if value == issue_key:
                issue_type = key
                break
        
        if issue_type:
            markdown_path = MARKDOWN_FILES.get(issue_type)
        else:
            # Try direct file lookup by issue key
            markdown_path = Path(f"/home/dn/SCALER/FLOWSPEC_VPN/{issue_key}_*.md")
            # Find first matching file
            import glob
            matches = glob.glob(str(markdown_path))
            if matches:
                markdown_path = Path(matches[0])
            else:
                markdown_path = None
        
        if markdown_path and markdown_path.exists():
            logger.info(f"Using markdown file as fallback: {markdown_path}")
            markdown_content = parse_markdown_file(markdown_path)
            if markdown_content:
                test_cases = extract_test_cases_from_markdown(markdown_content, issue_key)
                logger.info(f"Parsed {len(test_cases)} test cases from markdown file")
        else:
            logger.warning(f"Markdown fallback file not found for {issue_key}")
    
    logger.info(f"Total parsed {len(test_cases)} test cases from {issue_key}")
    return test_cases


def parse_markdown_file_direct(file_path: Path, jira_key: str) -> List[TestCase]:
    """
    Parse test cases directly from markdown file
    
    Args:
        file_path: Path to markdown file
        jira_key: Jira issue key for these tests
    
    Returns:
        List of TestCase objects
    """
    if not file_path.exists():
        logger.error(f"Markdown file not found: {file_path}")
        return []
    
    content = parse_markdown_file(file_path)
    if not content:
        return []
    
    test_cases = extract_test_cases_from_markdown(content, jira_key)
    logger.info(f"Parsed {len(test_cases)} test cases from {file_path}")
    return test_cases


def get_all_happy_flow_tests() -> List[TestCase]:
    """Get all Happy Flow test cases (HF-01 through HF-15)"""
    issue_key = JIRA_KEYS["happy_flow"]
    
    # Try Jira first
    test_cases = parse_jira_issue(issue_key)
    if test_cases:
        return test_cases
    
    # Fallback to markdown
    markdown_path = MARKDOWN_FILES["happy_flow"]
    return parse_markdown_file_direct(markdown_path, issue_key)


def get_all_negative_tests() -> List[TestCase]:
    """Get all Negative test cases (NEG-01 through NEG-21)"""
    issue_key = JIRA_KEYS["negative"]
    
    # Try Jira first
    test_cases = parse_jira_issue(issue_key)
    if test_cases:
        return test_cases
    
    # Fallback to markdown
    markdown_path = MARKDOWN_FILES["negative"]
    return parse_markdown_file_direct(markdown_path, issue_key)


def get_test_by_id(test_id: str) -> Optional[TestCase]:
    """
    Get a specific test case by ID (e.g., "HF-01", "NEG-05")
    
    Args:
        test_id: Test case ID
    
    Returns:
        TestCase object or None if not found
    """
    if test_id.startswith("HF"):
        all_tests = get_all_happy_flow_tests()
    elif test_id.startswith("NEG"):
        all_tests = get_all_negative_tests()
    else:
        logger.error(f"Unknown test ID format: {test_id}")
        return None
    
    for test in all_tests:
        if test.test_id == test_id:
            return test
    
    return None


def get_all_test_categories_from_jira() -> List[Dict[str, Any]]:
    """
    Get all test categories from Jira (via cache)
    
    Returns:
        List of category dictionaries with key, summary, etc.
    """
    return get_all_test_categories()


def get_category_tests_from_jira(category_key: str) -> List[Dict[str, Any]]:
    """
    Get child tests for a category from Jira (via cache)
    
    Args:
        category_key: Test category issue key (e.g., "SW-231823")
    
    Returns:
        List of test issue dictionaries with key, summary, etc.
    """
    return get_tests_for_category(category_key)


def get_tests_for_category_issue(category_key: str) -> List[TestCase]:
    """
    Get parsed test cases for all tests under a category
    
    Args:
        category_key: Test category issue key (e.g., "SW-231823")
    
    Returns:
        List of TestCase objects from all child tests
    """
    test_issues = get_tests_for_category(category_key)
    all_test_cases = []
    
    for test_issue in test_issues:
        test_key = test_issue.get("key")
        if test_key:
            test_cases = parse_jira_issue(test_key)
            all_test_cases.extend(test_cases)
    
    return all_test_cases


if __name__ == "__main__":
    # Test parser
    logging.basicConfig(level=logging.INFO)
    
    print("Parsing Happy Flow tests...")
    happy_flow_tests = get_all_happy_flow_tests()
    print(f"Found {len(happy_flow_tests)} Happy Flow tests")
    
    for test in happy_flow_tests[:3]:  # Show first 3
        print(f"\n{test.test_id}: {test.test_name}")
        print(f"  Steps: {len(test.steps)}")
        print(f"  Pass Criteria: {len(test.pass_criteria)}")
