"""Auto-recover device management IP via Network Mapper.

Called when a device becomes unreachable (e.g., after system delete + upgrade).
Uses the device's stored serial number to re-discover it through Network Mapper,
then updates devices.json and operational.json with the new management IP.

Usage from bash:
    python3 -m scaler.recover_device_ip <hostname>
    # Prints new IP to stdout on success, nothing on failure

Usage from Python:
    from scaler.recover_device_ip import recover_device_ip
    new_ip = recover_device_ip("PE-1")
"""

import json
import re
import sys
import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

SCALER_DIR = Path(os.path.expanduser("~/SCALER"))


def recover_device_ip(hostname: str, scaler_dir: Optional[Path] = None) -> Optional[str]:
    """
    Recover a device's management IP using Network Mapper.

    Steps:
    1. Read serial number from operational.json
    2. discover_device(hostname=<SN>) via Network Mapper MCP
    3. get_device_management_interfaces to find mgmt0 IP
    4. Update devices.json and operational.json with new IP
    5. Clear stale_data/extraction_failed alerts

    Returns:
        New management IP string on success, None on failure.
    """
    scaler_dir = scaler_dir or SCALER_DIR

    sn = _get_serial_number(hostname, scaler_dir)
    if not sn:
        logger.warning(f"{hostname}: No serial number found in operational.json")
        return None

    try:
        from .network_mapper_client import NetworkMapperClient
    except ImportError:
        try:
            from scaler.network_mapper_client import NetworkMapperClient
        except ImportError:
            logger.error("NetworkMapperClient not available")
            return None

    try:
        client = NetworkMapperClient()
    except Exception as e:
        logger.error(f"Failed to create NetworkMapperClient: {e}")
        return None

    # Step 1: Re-discover the device using its serial number
    logger.info(f"{hostname}: Discovering device via SN {sn}...")
    new_ip = None

    try:
        result = client._call_tool("discover_device", {"hostname": sn})
        if result:
            logger.info(f"{hostname}: Discovery result received")
    except Exception as e:
        logger.warning(f"{hostname}: discover_device failed: {e}")

    # Step 2: Query management interfaces (the reliable source for mgmt0 IP)
    try:
        mgmt_result = client._call_tool(
            "get_device_management_interfaces",
            {"device_name": hostname}
        )
        if mgmt_result:
            new_ip = _extract_mgmt0_ip(mgmt_result)
            if new_ip:
                logger.info(f"{hostname}: mgmt0 IP from Network Mapper: {new_ip}")
    except Exception as e:
        logger.warning(f"{hostname}: get_device_management_interfaces failed: {e}")

    # Step 3: Try the client's own multi-strategy IP resolver
    if not new_ip:
        try:
            new_ip = client.get_device_management_ip(hostname)
        except Exception:
            pass

    if not new_ip:
        logger.warning(f"{hostname}: Could not determine new management IP")
        return None

    # Verify the new IP is reachable (TCP port 22)
    if not _is_reachable(new_ip):
        logger.warning(f"{hostname}: New IP {new_ip} discovered but not reachable on port 22")
        return None

    # Step 4: Update devices.json
    _update_devices_json(hostname, new_ip, scaler_dir)

    # Step 5: Update operational.json
    _update_operational_json(hostname, new_ip, scaler_dir)

    # Step 6: Clear stale/failing alerts
    _clear_alerts(hostname, scaler_dir)

    logger.info(f"{hostname}: IP recovered to {new_ip}")
    return new_ip


def _get_serial_number(hostname: str, scaler_dir: Path) -> Optional[str]:
    """Read serial number from the device's operational.json."""
    op_file = scaler_dir / "db" / "configs" / hostname / "operational.json"
    if not op_file.exists():
        return None
    try:
        with open(op_file) as f:
            data = json.load(f)
        sn = data.get("serial_number", "N/A")
        if sn and sn != "N/A" and sn != "null":
            return sn
    except Exception:
        pass
    return None


def _extract_ip_from_text(text: str) -> Optional[str]:
    """Extract a management IP from discovery result text."""
    for line in text.split('\n'):
        lower = line.lower()
        if 'mgmt0' in lower or 'management' in lower:
            match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
            if match:
                ip = match.group(1)
                if not ip.startswith('127.') and not ip.startswith('0.'):
                    return ip

    # Fallback: look for any IP that's not loopback
    ips = re.findall(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', text)
    for ip in ips:
        if not ip.startswith('127.') and not ip.startswith('0.') and not ip.startswith('255.'):
            return ip
    return None


def _extract_mgmt0_ip(mgmt_text: str) -> Optional[str]:
    """Extract mgmt0 IP from get_device_management_interfaces markdown table.

    Expected format:
    | mgmt0 | mgmt | enabled | up | 100.64.7.159/20 (DHCP) | - |  |
    """
    for line in mgmt_text.split('\n'):
        if '|' not in line:
            continue
        cols = [c.strip() for c in line.split('|')]
        # Look for a row where the interface name is exactly mgmt0
        if any(c == 'mgmt0' for c in cols):
            for col in cols:
                match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', col)
                if match:
                    ip = match.group(1)
                    if not ip.startswith('127.') and not ip.startswith('0.'):
                        return ip
    return None


def _is_reachable(ip: str, timeout: int = 3) -> bool:
    """Check if an IP is reachable on SSH port 22."""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, 22))
        sock.close()
        return result == 0
    except Exception:
        return False


def _update_devices_json(hostname: str, new_ip: str, scaler_dir: Path) -> None:
    """Update the device's IP in devices.json."""
    devices_file = scaler_dir / "db" / "devices.json"
    if not devices_file.exists():
        return
    try:
        with open(devices_file) as f:
            data = json.load(f)

        old_ip = None
        for dev in data.get("devices", []):
            if dev.get("hostname") == hostname:
                old_ip = dev.get("ip")
                dev["ip"] = new_ip
                break

        with open(devices_file, 'w') as f:
            json.dump(data, f, indent=2)

        if old_ip:
            logger.info(f"{hostname}: devices.json updated {old_ip} -> {new_ip}")
    except Exception as e:
        logger.error(f"{hostname}: Failed to update devices.json: {e}")


def _update_operational_json(hostname: str, new_ip: str, scaler_dir: Path) -> None:
    """Update mgmt_ip and ssh_host in operational.json."""
    op_file = scaler_dir / "db" / "configs" / hostname / "operational.json"
    if not op_file.exists():
        return
    try:
        with open(op_file) as f:
            data = json.load(f)
        data['mgmt_ip'] = new_ip
        data['ssh_host'] = new_ip
        with open(op_file, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logger.error(f"{hostname}: Failed to update operational.json: {e}")


def _clear_alerts(hostname: str, scaler_dir: Path) -> None:
    """Clear stale_data/extraction_failed/ip_changed alerts for this device."""
    alerts_file = scaler_dir / "db" / "alerts.json"
    if not alerts_file.exists():
        return
    try:
        with open(alerts_file) as f:
            data = json.load(f)
        original_count = len(data.get('alerts', []))
        data['alerts'] = [
            a for a in data.get('alerts', [])
            if a.get('device') != hostname or a.get('type') not in
               ('stale_data', 'extraction_failed', 'ip_changed')
        ]
        cleared = original_count - len(data['alerts'])
        with open(alerts_file, 'w') as f:
            json.dump(data, f, indent=2)
        if cleared:
            logger.info(f"{hostname}: Cleared {cleared} alert(s)")
    except Exception as e:
        logger.error(f"{hostname}: Failed to clear alerts: {e}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(message)s',
        stream=sys.stderr
    )

    if len(sys.argv) < 2:
        print("Usage: python3 -m scaler.recover_device_ip <hostname>", file=sys.stderr)
        sys.exit(1)

    hostname = sys.argv[1]
    new_ip = recover_device_ip(hostname)
    if new_ip:
        print(new_ip)
        sys.exit(0)
    else:
        sys.exit(1)
