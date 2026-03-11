#!/usr/bin/env python3
"""
Test Runner - Test execution engine

This module executes test cases, verifies steps, and collects results.
"""

import time
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime
import logging

from .test_cases import TestCase, TestStep, TestResult, TestRun, TestStatus, StepStatus
from .device_manager import DeviceManager, SSHConnection
from .verifiers import (
    verify_bgp_session,
    verify_flowspec_routes,
    verify_ncp_installation,
    verify_traffic_enforcement,
    verify_vrf_import,
    verify_admin_state,
    verify_config_deletion,
    verify_rollback,
)

logger = logging.getLogger(__name__)

# Map verification function names to actual functions
VERIFIER_MAP = {
    "verify_bgp_session": verify_bgp_session,
    "verify_flowspec_routes": verify_flowspec_routes,
    "verify_ncp_installation": verify_ncp_installation,
    "verify_traffic_enforcement": verify_traffic_enforcement,
    "verify_vrf_import": verify_vrf_import,
    "verify_admin_state": verify_admin_state,
    "verify_config_deletion": verify_config_deletion,
    "verify_rollback": verify_rollback,
}


class TestRunner:
    """Test execution engine"""
    
    def __init__(self, device_manager: DeviceManager, continue_on_failure: bool = True):
        self.device_manager = device_manager
        self.continue_on_failure = continue_on_failure
        self.results: List[TestResult] = []
    
    def run_test(self, test_case: TestCase, device_hostname: str = "DUT") -> TestResult:
        """
        Execute a single test case
        
        Args:
            test_case: TestCase to execute
            device_hostname: Hostname of device to test (default: "DUT")
        
        Returns:
            TestResult object
        """
        logger.info(f"Starting test: {test_case.test_id} - {test_case.test_name}")
        
        test_case.status = TestStatus.RUNNING
        test_case.start_time = time.time()
        
        # Get device connection
        conn = self.device_manager.get_connection(device_hostname)
        if not conn:
            test_case.status = TestStatus.ERROR
            test_case.error_message = f"Failed to connect to device: {device_hostname}"
            test_case.end_time = time.time()
            return TestResult(
                test_case=test_case,
                status=TestStatus.ERROR,
                message=f"Device connection failed: {device_hostname}",
            )
        
        result = TestResult(test_case=test_case, status=TestStatus.RUNNING)
        
        # Execute each step
        for step in test_case.steps:
            step.status = StepStatus.RUNNING
            step_start = time.time()
            
            try:
                # Handle manual steps
                if step.manual_step:
                    logger.info(f"  Step {step.step_number}: MANUAL - {step.description}")
                    step.status = StepStatus.MANUAL
                    step.execution_time = time.time() - step_start
                    result.step_results.append({
                        "step": step.step_number,
                        "status": "manual",
                        "description": step.description,
                    })
                    continue
                
                # Execute command if present
                if step.command:
                    logger.info(f"  Step {step.step_number}: Running command: {step.command}")
                    success, output = conn.run_cli_command(step.command)
                    
                    step.actual_output = output
                    result.command_outputs[f"step_{step.step_number}"] = output
                    
                    if not success:
                        step.status = StepStatus.FAILED
                        step.error_message = f"Command failed: {output}"
                        result.errors.append(f"Step {step.step_number}: Command failed")
                        step.execution_time = time.time() - step_start
                        result.step_results.append({
                            "step": step.step_number,
                            "status": "failed",
                            "error": step.error_message,
                        })
                        continue
                
                # Run verification function if present
                if step.verification_function:
                    verifier_name = step.verification_function.__name__ if hasattr(step.verification_function, '__name__') else str(step.verification_function)
                    logger.info(f"  Step {step.step_number}: Verifying with {verifier_name}")
                    
                    # Call verification function
                    # For now, we'll use a simple approach - verifiers take (conn, ...) args
                    try:
                        verify_success, verify_message = step.verification_function(conn)
                        
                        if verify_success:
                            step.status = StepStatus.PASSED
                            step.actual_output = verify_message
                        else:
                            step.status = StepStatus.FAILED
                            step.error_message = verify_message
                            result.errors.append(f"Step {step.step_number}: {verify_message}")
                    except Exception as e:
                        step.status = StepStatus.FAILED
                        step.error_message = f"Verification error: {e}"
                        result.errors.append(f"Step {step.step_number}: Verification error: {e}")
                else:
                    # No verification function - mark as passed if command succeeded
                    step.status = StepStatus.PASSED
                
                step.execution_time = time.time() - step_start
                result.step_results.append({
                    "step": step.step_number,
                    "status": step.status.value,
                    "description": step.description,
                    "output": step.actual_output[:500] if step.actual_output else None,
                })
                
            except Exception as e:
                logger.error(f"Error executing step {step.step_number}: {e}")
                step.status = StepStatus.FAILED
                step.error_message = str(e)
                step.execution_time = time.time() - step_start
                result.errors.append(f"Step {step.step_number}: {e}")
                result.step_results.append({
                    "step": step.step_number,
                    "status": "error",
                    "error": str(e),
                })
            
            # Check if we should continue on failure
            if step.status == StepStatus.FAILED and not self.continue_on_failure:
                logger.warning(f"Step {step.step_number} failed, stopping test")
                break
        
        # Evaluate pass criteria
        self._evaluate_pass_criteria(test_case, result)
        
        # Determine final test status
        failed_steps = [s for s in test_case.steps if s.status == StepStatus.FAILED]
        if failed_steps:
            test_case.status = TestStatus.FAILED
            result.status = TestStatus.FAILED
            result.message = f"Test failed: {len(failed_steps)} step(s) failed"
        elif not all(test_case.pass_criteria_results):
            test_case.status = TestStatus.FAILED
            result.status = TestStatus.FAILED
            result.message = "Test failed: Not all pass criteria met"
        else:
            test_case.status = TestStatus.PASSED
            result.status = TestStatus.PASSED
            result.message = "Test passed: All steps and criteria met"
        
        test_case.end_time = time.time()
        test_case.execution_time = test_case.get_duration()
        
        logger.info(f"Test {test_case.test_id} completed: {result.status.value}")
        return result
    
    def _evaluate_pass_criteria(self, test_case: TestCase, result: TestResult):
        """Evaluate pass criteria based on test results"""
        # This is a simplified evaluation - in practice, you'd check each criterion
        # For now, we'll mark criteria as met if all steps passed
        all_steps_passed = all(
            s.status == StepStatus.PASSED or s.status == StepStatus.MANUAL
            for s in test_case.steps
        )
        
        # Mark all criteria as met if all steps passed
        # In a real implementation, you'd check each criterion individually
        test_case.pass_criteria_results = [all_steps_passed] * len(test_case.pass_criteria)
    
    def run_tests(self, test_cases: List[TestCase], device_hostname: str = "DUT") -> TestRun:
        """
        Execute multiple test cases
        
        Args:
            test_cases: List of TestCase objects
            device_hostname: Hostname of device to test
        
        Returns:
            TestRun object with results
        """
        test_run = TestRun(test_cases=test_cases)
        test_run.start_time = time.time()
        
        logger.info(f"Starting test run with {len(test_cases)} test cases")
        
        for test_case in test_cases:
            try:
                result = self.run_test(test_case, device_hostname)
                test_run.results.append(result)
                
                # Stop on failure if continue_on_failure is False
                if result.status == TestStatus.FAILED and not self.continue_on_failure:
                    logger.warning("Test failed and continue_on_failure=False, stopping test run")
                    break
                    
            except Exception as e:
                logger.error(f"Error running test {test_case.test_id}: {e}")
                result = TestResult(
                    test_case=test_case,
                    status=TestStatus.ERROR,
                    message=f"Test execution error: {e}",
                )
                test_run.results.append(result)
        
        test_run.end_time = time.time()
        
        logger.info(f"Test run completed: {test_run.get_summary()}")
        return test_run
    
    def run_test_by_id(self, test_id: str, device_hostname: str = "DUT") -> Optional[TestResult]:
        """
        Run a single test by ID
        
        Args:
            test_id: Test case ID (e.g., "HF-01")
            device_hostname: Hostname of device to test
        
        Returns:
            TestResult or None if test not found
        """
        from .test_plan_parser import get_test_by_id
        
        test_case = get_test_by_id(test_id)
        if not test_case:
            logger.error(f"Test case not found: {test_id}")
            return None
        
        return self.run_test(test_case, device_hostname)
