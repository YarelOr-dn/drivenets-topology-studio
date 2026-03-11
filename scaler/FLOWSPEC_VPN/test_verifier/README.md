# FlowSpec VPN Test Verifier

Automated test verification script for FlowSpec VPN Basic Functionality tests from the test plan.

## Overview

This tool automates verification of FlowSpec VPN test cases by:
- Fetching test structure from Jira tickets (SW-234158, SW-234159, SW-234160)
- Executing test steps and verifying results
- Generating comprehensive test reports (HTML, JSON, JUnit XML)

## Features

- **Jira Integration**: Fetches test cases directly from Jira tickets (with markdown fallback)
- **Test Execution**: Runs test cases sequentially with step-by-step verification
- **Device Management**: Connects to network devices via SSH
- **Verification Functions**: Automated verification of BGP sessions, routes, NCP installation, etc.
- **Report Generation**: HTML, JSON, and JUnit XML reports
- **Wizard Integration**: Integrated into `fsvpn_wizard.py` with [T] TP RUN option

## Installation

No special installation required. Dependencies:
- Python 3.6+
- `pexpect` (for SSH connections)
- `rich` (for beautiful terminal output, optional)

Install dependencies:
```bash
pip install pexpect rich
```

## Usage

### Standalone Mode

Run specific test:
```bash
python3 flowspec_vpn_test_verifier.py run --test-id HF-01
```

Run multiple tests:
```bash
python3 flowspec_vpn_test_verifier.py run --test-id HF-01,HF-02,HF-03
```

Run all Happy Flow tests:
```bash
python3 flowspec_vpn_test_verifier.py run --all-happy-flow
```

Run by category:
```bash
python3 flowspec_vpn_test_verifier.py run --category happy-flow
```

### Interactive Wizard Mode

```bash
python3 flowspec_vpn_test_verifier.py wizard
```

### FSVPN Wizard Integration

Run the main wizard and select `[T] TP RUN`:
```bash
python3 fsvpn_wizard.py
```

Then:
1. Select device
2. Choose `[T] TP RUN` from main menu
3. Select test category (Basic Functionality)
4. Select test(s) or `[ALL]`
5. View results and reports

## Test Cases

### Happy Flow Tests (HF-01 through HF-15)

- **HF-01**: IPv4 FlowSpec-VPN Session Establishment
- **HF-02**: IPv4 FlowSpec-VPN Drop Action
- **HF-03**: IPv4 FlowSpec-VPN Rate-Limit Action
- **HF-04**: IPv6 FlowSpec-VPN Drop Action
- **HF-05**: Non-Default VRF FlowSpec Import
- **HF-06**: Neighbor-Group FlowSpec-VPN
- **HF-07**: Maximum-Prefix Limit
- **HF-08**: Policy In Filtering
- **HF-09**: Allow-as-in
- **HF-10**: Nexthop Self
- **HF-11**: RT-C Integration
- **HF-12**: Route Reflector Path
- **HF-13**: Redirect-to-RT Action
- **HF-14**: Enable/Disable FlowSpec
- **HF-15**: Configure/Delete FlowSpec

### Negative Tests (NEG-01 through NEG-21)

Coming soon - will be added in future updates.

## Configuration

Edit `test_config.yaml` to configure:
- Device information (DUT, PE2, RR, Traffic Gen)
- Topology settings (VRF, BGP ASN, RT)
- Test settings (timeouts, retry count, etc.)

## Reports

Reports are generated in `test_results/reports/`:
- **HTML**: Visual test report with step-by-step results
- **JSON**: Machine-readable test results
- **JUnit XML**: For CI/CD integration

## Troubleshooting

### Device Connection Issues

- Verify device IP and credentials in `db/devices.json`
- Check SSH connectivity: `ssh dnroot@<device-ip>`
- Ensure `pexpect` is installed

### Test Parsing Issues

- Check Jira cache in `test_results/jira_cache/`
- Verify markdown files exist: `SW-234158_HAPPY_FLOW.md`, etc.
- Check logs in `test_results/logs/test_verifier.log`

### Import Errors

- Ensure `test_verifier/__init__.py` exists
- Check Python path includes `SCALER/FLOWSPEC_VPN/`
- Verify all dependencies installed

## Architecture

```
test_verifier/
├── __init__.py
├── jira_fetcher.py          # Fetch from Jira or markdown
├── test_plan_parser.py      # Parse test cases
├── test_cases.py            # TestCase/TestStep dataclasses
├── verifiers.py             # Verification functions
├── device_manager.py        # SSH device connections
├── test_runner.py           # Test execution engine
└── report_generator.py      # Report generation
```

## References

- Jira Test Category: SW-231823 (Basic functionality + Topology)
- Jira Happy Flow: SW-234158
- Jira Negative Tests: SW-234159
- Jira Topology: SW-234160

## License

Internal tool for FlowSpec VPN testing.
