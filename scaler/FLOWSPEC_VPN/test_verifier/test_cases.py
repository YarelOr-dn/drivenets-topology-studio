#!/usr/bin/env python3
"""
Test Case Definitions - Dataclasses for test structure

This module defines the data structures for test cases and test steps.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Callable, Any
from enum import Enum


class TestStatus(Enum):
    """Test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class StepStatus(Enum):
    """Step execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    MANUAL = "manual"


@dataclass
class TestStep:
    """Represents a single step in a test case"""
    step_number: int
    description: str
    command: Optional[str] = None
    expected_output: Optional[str] = None
    verification_function: Optional[Callable] = None
    manual_step: bool = False  # Requires manual intervention
    
    # Runtime fields (not set during creation)
    status: StepStatus = field(default=StepStatus.PENDING)
    actual_output: Optional[str] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    
    def __post_init__(self):
        """Initialize runtime fields"""
        if self.status == StepStatus.PENDING:
            self.status = StepStatus.MANUAL if self.manual_step else StepStatus.PENDING


@dataclass
class TestCase:
    """Represents a complete test case"""
    test_id: str  # e.g., "HF-01", "HF-02", "NEG-01"
    jira_key: str  # e.g., "SW-234158"
    test_name: str
    description: str
    objective: str
    test_type: str  # happy_flow, negative, edge_case
    steps: List[TestStep]
    pass_criteria: List[str]  # List of checkbox criteria
    prerequisites: List[str]
    expected_result: str
    estimated_duration: int  # seconds
    
    # Runtime fields (not set during creation)
    status: TestStatus = field(default=TestStatus.PENDING)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    execution_time: float = 0.0
    pass_criteria_results: List[bool] = field(default_factory=list)
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """Initialize runtime fields"""
        # Initialize pass criteria results list
        if not self.pass_criteria_results:
            self.pass_criteria_results = [False] * len(self.pass_criteria)
    
    def get_duration(self) -> float:
        """Get test execution duration"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return self.execution_time
    
    def is_passed(self) -> bool:
        """Check if test passed (all pass criteria met)"""
        return (
            self.status == TestStatus.PASSED
            and all(self.pass_criteria_results)
        )
    
    def get_summary(self) -> dict:
        """Get test summary as dictionary"""
        return {
            "test_id": self.test_id,
            "test_name": self.test_name,
            "status": self.status.value,
            "duration": self.get_duration(),
            "steps_total": len(self.steps),
            "steps_passed": sum(1 for s in self.steps if s.status == StepStatus.PASSED),
            "steps_failed": sum(1 for s in self.steps if s.status == StepStatus.FAILED),
            "pass_criteria_met": sum(self.pass_criteria_results),
            "pass_criteria_total": len(self.pass_criteria),
        }


@dataclass
class TestResult:
    """Result of test execution"""
    test_case: TestCase
    status: TestStatus
    message: Optional[str] = None
    step_results: List[dict] = field(default_factory=list)
    command_outputs: dict = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "test_id": self.test_case.test_id,
            "test_name": self.test_case.test_name,
            "status": self.status.value,
            "message": self.message,
            "duration": self.test_case.get_duration(),
            "step_results": self.step_results,
            "command_outputs": self.command_outputs,
            "errors": self.errors,
            "pass_criteria": {
                "total": len(self.test_case.pass_criteria),
                "met": sum(self.test_case.pass_criteria_results),
                "results": self.test_case.pass_criteria_results,
            },
        }


@dataclass
class TestRun:
    """Represents a complete test run with multiple test cases"""
    test_cases: List[TestCase]
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    results: List[TestResult] = field(default_factory=list)
    
    def get_summary(self) -> dict:
        """Get test run summary"""
        total = len(self.test_cases)
        passed = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        skipped = sum(1 for r in self.results if r.status == TestStatus.SKIPPED)
        
        duration = 0.0
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "duration": duration,
            "pass_rate": (passed / total * 100) if total > 0 else 0.0,
        }
