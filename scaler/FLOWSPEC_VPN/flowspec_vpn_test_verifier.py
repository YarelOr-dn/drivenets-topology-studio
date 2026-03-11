#!/usr/bin/env python3
"""
FlowSpec VPN Test Verifier - Main Script

This script automates verification of FlowSpec VPN test cases from the test plan.
Supports both standalone execution and interactive wizard modes.
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import List, Optional

# Add test_verifier to path
sys.path.insert(0, str(Path(__file__).parent))

from test_verifier.test_plan_parser import get_all_happy_flow_tests, get_test_by_id
from test_verifier.device_manager import DeviceManager
from test_verifier.test_runner import TestRunner
from test_verifier.report_generator import ReportGenerator

# Try to import rich for beautiful output
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path("/home/dn/SCALER/FLOWSPEC_VPN/test_results/logs/test_verifier.log")),
        logging.StreamHandler(),
    ]
)

logger = logging.getLogger(__name__)
console = Console() if RICH_AVAILABLE else None


def run_standalone_mode(args):
    """Run tests in standalone mode"""
    logger.info("Starting standalone test execution")
    
    # Initialize components
    device_manager = DeviceManager()
    device_manager.load_devices()
    
    test_runner = TestRunner(device_manager, continue_on_failure=args.continue_on_failure)
    report_generator = ReportGenerator()
    
    # Get test cases
    test_cases = []
    
    if args.test_id:
        # Run specific test(s)
        test_ids = [tid.strip() for tid in args.test_id.split(",")]
        for test_id in test_ids:
            test_case = get_test_by_id(test_id)
            if test_case:
                test_cases.append(test_case)
            else:
                logger.error(f"Test case not found: {test_id}")
    elif args.all_happy_flow:
        # Run all Happy Flow tests
        test_cases = get_all_happy_flow_tests()
    elif args.category:
        # Run tests by category
        if args.category == "happy-flow":
            test_cases = get_all_happy_flow_tests()
        else:
            logger.error(f"Unknown category: {args.category}")
            return
    else:
        logger.error("No test selection specified")
        return
    
    if not test_cases:
        logger.error("No test cases to run")
        return
    
    logger.info(f"Running {len(test_cases)} test case(s)")
    
    # Run tests
    device_hostname = args.device or "DUT"
    test_run = test_runner.run_tests(test_cases, device_hostname)
    
    # Generate reports
    if args.report:
        reports = report_generator.generate_all_reports(test_run)
        if console:
            console.print(f"\n[green]Reports generated:[/green]")
            for fmt, path in reports.items():
                console.print(f"  {fmt.upper()}: {path}")
        else:
            print("\nReports generated:")
            for fmt, path in reports.items():
                print(f"  {fmt.upper()}: {path}")
    
    # Print summary
    summary = test_run.get_summary()
    if console:
        table = Table(title="Test Run Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Total Tests", str(summary["total"]))
        table.add_row("Passed", f"[green]{summary['passed']}[/green]")
        table.add_row("Failed", f"[red]{summary['failed']}[/red]")
        table.add_row("Skipped", f"[yellow]{summary['skipped']}[/yellow]")
        table.add_row("Duration", f"{summary['duration']:.2f}s")
        table.add_row("Pass Rate", f"{summary['pass_rate']:.1f}%")
        
        console.print(table)
    else:
        print("\nTest Run Summary:")
        print(f"  Total: {summary['total']}")
        print(f"  Passed: {summary['passed']}")
        print(f"  Failed: {summary['failed']}")
        print(f"  Skipped: {summary['skipped']}")
        print(f"  Duration: {summary['duration']:.2f}s")
        print(f"  Pass Rate: {summary['pass_rate']:.1f}%")


def run_wizard_mode():
    """Run tests in interactive wizard mode"""
    if not console:
        print("Rich library required for wizard mode. Install with: pip install rich")
        return
    
    console.print(Panel.fit(
        "[bold cyan]FlowSpec VPN Test Verifier - Wizard Mode[/bold cyan]",
        border_style="cyan"
    ))
    
    # Initialize components
    device_manager = DeviceManager()
    device_manager.load_devices()
    
    test_runner = TestRunner(device_manager)
    report_generator = ReportGenerator()
    
    # Show test categories
    console.print("\n[bold]Test Categories:[/bold]")
    console.print("  [1] Basic Functionality (Happy Flow - HF-01 through HF-15)")
    console.print("  [2] Negative Testing (NEG-01 through NEG-21) - Coming soon")
    console.print("  [Q] Quit")
    
    from rich.prompt import Prompt
    choice = Prompt.ask("\nSelect category", default="1")
    
    if choice.lower() == 'q':
        return
    
    # Get test cases
    if choice == "1":
        test_cases = get_all_happy_flow_tests()
    else:
        console.print("[red]Invalid selection[/red]")
        return
    
    if not test_cases:
        console.print("[red]No test cases found[/red]")
        return
    
    # Show test list
    console.print(f"\n[bold]Available Tests ({len(test_cases)}):[/bold]")
    table = Table()
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Type", style="yellow")
    
    for test in test_cases:
        table.add_row(test.test_id, test.test_name, test.test_type)
    
    console.print(table)
    
    # Select tests
    console.print("\n[bold]Test Selection:[/bold]")
    console.print("  Enter test ID(s) separated by comma (e.g., HF-01,HF-02)")
    console.print("  Or 'ALL' to run all tests")
    
    selection = Prompt.ask("Select tests", default="ALL")
    
    if selection.upper() == "ALL":
        selected_tests = test_cases
    else:
        test_ids = [tid.strip() for tid in selection.split(",")]
        selected_tests = [t for t in test_cases if t.test_id in test_ids]
    
    if not selected_tests:
        console.print("[red]No tests selected[/red]")
        return
    
    # Select device
    device_hostname = Prompt.ask("Device hostname", default="DUT")
    
    # Run tests
    console.print(f"\n[bold]Running {len(selected_tests)} test(s)...[/bold]")
    
    with Progress() as progress:
        task = progress.add_task("[cyan]Running tests...", total=len(selected_tests))
        
        test_run = test_runner.run_tests(selected_tests, device_hostname)
        progress.update(task, completed=len(selected_tests))
    
    # Generate reports
    reports = report_generator.generate_all_reports(test_run)
    
    # Show summary
    summary = test_run.get_summary()
    console.print("\n[bold green]Test Run Complete![/bold green]")
    console.print(f"  Total: {summary['total']}")
    console.print(f"  [green]Passed: {summary['passed']}[/green]")
    console.print(f"  [red]Failed: {summary['failed']}[/red]")
    console.print(f"  Duration: {summary['duration']:.2f}s")
    
    console.print("\n[bold]Reports:[/bold]")
    for fmt, path in reports.items():
        console.print(f"  {fmt.upper()}: {path}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="FlowSpec VPN Test Verifier",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="mode", help="Execution mode")
    
    # Run mode
    run_parser = subparsers.add_parser("run", help="Run tests in standalone mode")
    run_parser.add_argument("--test-id", help="Test ID(s) to run (comma-separated)")
    run_parser.add_argument("--all-happy-flow", action="store_true", help="Run all Happy Flow tests")
    run_parser.add_argument("--category", choices=["happy-flow", "negative"], help="Run tests by category")
    run_parser.add_argument("--device", help="Device hostname (default: DUT)")
    run_parser.add_argument("--continue-on-failure", action="store_true", default=True, help="Continue on failure")
    run_parser.add_argument("--report", action="store_true", default=True, help="Generate reports")
    
    # Wizard mode
    wizard_parser = subparsers.add_parser("wizard", help="Run tests in interactive wizard mode")
    
    args = parser.parse_args()
    
    if args.mode == "run":
        run_standalone_mode(args)
    elif args.mode == "wizard":
        run_wizard_mode()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
