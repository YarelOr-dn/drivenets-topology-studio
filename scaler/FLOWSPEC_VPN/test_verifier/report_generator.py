#!/usr/bin/env python3
"""
Report Generator - Generate test reports in various formats

This module generates HTML, JSON, and JUnit XML test reports.
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from .test_cases import TestRun, TestResult, TestStatus

logger = logging.getLogger(__name__)

REPORTS_DIR = Path("/home/dn/SCALER/FLOWSPEC_VPN/test_results/reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


class ReportGenerator:
    """Generate test reports in various formats"""
    
    def __init__(self, output_dir: Path = REPORTS_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_html_report(self, test_run: TestRun, filename: Optional[str] = None) -> Path:
        """
        Generate HTML test report
        
        Args:
            test_run: TestRun object with results
            filename: Optional output filename (default: auto-generated)
        
        Returns:
            Path to generated HTML file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_run_{timestamp}.html"
        
        output_path = self.output_dir / filename
        
        summary = test_run.get_summary()
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>FlowSpec VPN Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .summary {{ background: white; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .test-case {{ background: white; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #3498db; }}
        .test-case.passed {{ border-left-color: #27ae60; }}
        .test-case.failed {{ border-left-color: #e74c3c; }}
        .test-case.error {{ border-left-color: #f39c12; }}
        .step {{ margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 3px; }}
        .step.passed {{ background: #d4edda; }}
        .step.failed {{ background: #f8d7da; }}
        .status-badge {{ display: inline-block; padding: 5px 10px; border-radius: 3px; font-weight: bold; }}
        .status-passed {{ background: #27ae60; color: white; }}
        .status-failed {{ background: #e74c3c; color: white; }}
        .status-error {{ background: #f39c12; color: white; }}
        .status-skipped {{ background: #95a5a6; color: white; }}
        pre {{ background: #f4f4f4; padding: 10px; border-radius: 3px; overflow-x: auto; }}
        .criteria {{ margin: 10px 0; }}
        .criteria-item {{ padding: 5px; margin: 5px 0; }}
        .criteria-item.met {{ background: #d4edda; }}
        .criteria-item.not-met {{ background: #f8d7da; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>FlowSpec VPN Test Report</h1>
        <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    </div>
    
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Total Tests:</strong> {summary['total']}</p>
        <p><strong>Passed:</strong> <span class="status-badge status-passed">{summary['passed']}</span></p>
        <p><strong>Failed:</strong> <span class="status-badge status-failed">{summary['failed']}</span></p>
        <p><strong>Skipped:</strong> <span class="status-badge status-skipped">{summary['skipped']}</span></p>
        <p><strong>Duration:</strong> {summary['duration']:.2f} seconds</p>
        <p><strong>Pass Rate:</strong> {summary['pass_rate']:.1f}%</p>
    </div>
    
    <h2>Test Cases</h2>
"""
        
        for result in test_run.results:
            status_class = result.status.value
            status_badge_class = f"status-{result.status.value}"
            
            html += f"""
    <div class="test-case {status_class}">
        <h3>{result.test_case.test_id}: {result.test_case.test_name}</h3>
        <p><strong>Status:</strong> <span class="status-badge {status_badge_class}">{result.status.value.upper()}</span></p>
        <p><strong>Duration:</strong> {result.test_case.get_duration():.2f} seconds</p>
        <p><strong>Objective:</strong> {result.test_case.objective}</p>
        <p><strong>Message:</strong> {result.message or 'N/A'}</p>
        
        <h4>Steps</h4>
"""
            
            for step_result in result.step_results:
                step_status_class = step_result.get('status', 'pending')
                html += f"""
        <div class="step {step_status_class}">
            <p><strong>Step {step_result['step']}:</strong> {step_result.get('description', 'N/A')}</p>
            <p><strong>Status:</strong> {step_result.get('status', 'N/A')}</p>
"""
                if step_result.get('output'):
                    html += f"""
            <pre>{step_result['output']}</pre>
"""
                if step_result.get('error'):
                    html += f"""
            <p style="color: red;"><strong>Error:</strong> {step_result['error']}</p>
"""
                html += """
        </div>
"""
            
            # Pass criteria
            html += """
        <h4>Pass Criteria</h4>
        <div class="criteria">
"""
            for i, criterion in enumerate(result.test_case.pass_criteria):
                met = result.test_case.pass_criteria_results[i] if i < len(result.test_case.pass_criteria_results) else False
                met_class = "met" if met else "not-met"
                html += f"""
            <div class="criteria-item {met_class}">
                {'✓' if met else '✗'} {criterion}
            </div>
"""
            
            html += """
        </div>
"""
            
            # Errors
            if result.errors:
                html += """
        <h4>Errors</h4>
        <ul>
"""
                for error in result.errors:
                    html += f"""
            <li style="color: red;">{error}</li>
"""
                html += """
        </ul>
"""
            
            html += """
    </div>
"""
        
        html += """
</body>
</html>
"""
        
        with open(output_path, "w") as f:
            f.write(html)
        
        logger.info(f"Generated HTML report: {output_path}")
        return output_path
    
    def generate_json_report(self, test_run: TestRun, filename: Optional[str] = None) -> Path:
        """
        Generate JSON test report
        
        Args:
            test_run: TestRun object with results
            filename: Optional output filename
        
        Returns:
            Path to generated JSON file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_run_{timestamp}.json"
        
        output_path = self.output_dir / filename
        
        summary = test_run.get_summary()
        
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": summary,
            "test_cases": [result.to_dict() for result in test_run.results],
        }
        
        with open(output_path, "w") as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"Generated JSON report: {output_path}")
        return output_path
    
    def generate_junit_xml(self, test_run: TestRun, filename: Optional[str] = None) -> Path:
        """
        Generate JUnit XML report
        
        Args:
            test_run: TestRun object with results
            filename: Optional output filename
        
        Returns:
            Path to generated XML file
        """
        if filename is None:
            filename = "junit.xml"
        
        output_path = self.output_dir / filename
        
        summary = test_run.get_summary()
        
        # Create root element
        testsuites = ET.Element("testsuites")
        testsuites.set("name", "FlowSpec VPN Tests")
        testsuites.set("tests", str(summary["total"]))
        testsuites.set("failures", str(summary["failed"]))
        testsuites.set("time", str(summary["duration"]))
        
        testsuite = ET.SubElement(testsuites, "testsuite")
        testsuite.set("name", "FlowSpec VPN Test Suite")
        testsuite.set("tests", str(summary["total"]))
        testsuite.set("failures", str(summary["failed"]))
        testsuite.set("time", str(summary["duration"]))
        
        for result in test_run.results:
            testcase = ET.SubElement(testsuite, "testcase")
            testcase.set("name", f"{result.test_case.test_id}: {result.test_case.test_name}")
            testcase.set("classname", result.test_case.jira_key)
            testcase.set("time", str(result.test_case.get_duration()))
            
            if result.status == TestStatus.FAILED:
                failure = ET.SubElement(testcase, "failure")
                failure.set("message", result.message or "Test failed")
                failure.text = "\n".join(result.errors) if result.errors else result.message
            elif result.status == TestStatus.ERROR:
                error = ET.SubElement(testcase, "error")
                error.set("message", result.message or "Test error")
                error.text = result.test_case.error_message or result.message
            elif result.status == TestStatus.SKIPPED:
                skipped = ET.SubElement(testcase, "skipped")
                skipped.set("message", result.message or "Test skipped")
        
        # Write XML
        tree = ET.ElementTree(testsuites)
        tree.write(output_path, encoding="utf-8", xml_declaration=True)
        
        logger.info(f"Generated JUnit XML report: {output_path}")
        return output_path
    
    def generate_all_reports(self, test_run: TestRun) -> Dict[str, Path]:
        """
        Generate all report formats
        
        Args:
            test_run: TestRun object with results
        
        Returns:
            Dictionary mapping format names to file paths
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        html_path = self.generate_html_report(test_run, f"test_run_{timestamp}.html")
        json_path = self.generate_json_report(test_run, f"test_run_{timestamp}.json")
        junit_path = self.generate_junit_xml(test_run, "junit.xml")
        
        return {
            "html": html_path,
            "json": json_path,
            "junit": junit_path,
        }
