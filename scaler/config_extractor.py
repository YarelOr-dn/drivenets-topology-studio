"""SSH-based configuration extractor using Paramiko."""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import paramiko

from .models import Device, DeviceConfig
from .utils import (
    get_device_config_dir,
    get_device_history_dir,
    timestamp_filename,
)


class ConfigExtractor:
    """Extract running configuration from DNOS devices via SSH."""

    def __init__(self, timeout: int = 30, buffer_size: int = 65535):
        """
        Initialize the config extractor.
        
        Args:
            timeout: SSH connection timeout in seconds
            buffer_size: SSH channel buffer size
        """
        self.timeout = timeout
        self.buffer_size = buffer_size

    def connect(self, device: Device) -> paramiko.SSHClient:
        """
        Establish SSH connection to a device.
        
        Args:
            device: Device object with connection details
        
        Returns:
            Connected SSHClient
        
        Raises:
            paramiko.SSHException: On connection failure
        """
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Use helper function to get best SSH hostname
        from .utils import get_ssh_hostname
        hostname = get_ssh_hostname(device)
        
        client.connect(
            hostname=hostname,
            username=device.username,
            password=device.get_password(),
            timeout=self.timeout,
            look_for_keys=False,
            allow_agent=False
        )
        
        return client

    def execute_command(
        self,
        client: paramiko.SSHClient,
        command: str,
        timeout: int = 60
    ) -> Tuple[str, str, int]:
        """
        Execute a command on the device.
        
        Args:
            client: Connected SSHClient
            command: Command to execute
            timeout: Command timeout in seconds
        
        Returns:
            Tuple of (stdout, stderr, exit_code)
        """
        stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
        
        exit_code = stdout.channel.recv_exit_status()
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')
        
        return output, error, exit_code

    def extract_running_config(
        self,
        device: Device,
        save_to_db: bool = True
    ) -> Optional[DeviceConfig]:
        """
        Extract the running configuration from a device.
        
        Uses InteractiveExtractor for DNOS devices which require
        an interactive shell (invoke_shell) rather than exec_command.
        
        Args:
            device: Device to extract config from
            save_to_db: Whether to save the config to local DB
        
        Returns:
            DeviceConfig object or None on failure
        """
        try:
            # Use InteractiveExtractor for DNOS devices
            # exec_command doesn't work - DNOS needs interactive shell
            # Use 180s timeout for large configs
            with InteractiveExtractor(device, timeout=180) as extractor:
                output = extractor.get_running_config()
            
            if not output or len(output) < 100:
                raise Exception(f"Failed to get config: received only {len(output) if output else 0} bytes")
            
            # Create DeviceConfig
            config = DeviceConfig(
                device_id=device.id,
                hostname=device.hostname,
                extracted_at=datetime.now(),
                raw_config=output,
                parsed_config={},
                wan_interfaces=[],
                has_protocols=False,
                has_system=False,
                has_routing_policy=False
            )
            
            # Quick detection of major sections
            config.has_protocols = "protocols {" in output or "protocols\n" in output
            config.has_system = "system {" in output or "system\n" in output
            config.has_routing_policy = "routing-policy {" in output or "routing-policy\n" in output
            
            # Generate enhanced summary for header
            try:
                from .config_parser import ConfigParser
                parser = ConfigParser()
                parsed = parser.parse_config(output)
                config.parsed_config = parsed
                
                # Try to get operational data for richer summary
                operational_data = {}
                try:
                    config_dir = get_device_config_dir(device.hostname)
                    ops_file = config_dir / "operational.json"
                    if ops_file.exists():
                        with open(ops_file) as f:
                            operational_data = json.load(f)
                except Exception:
                    pass
                
                # Generate summary header
                config.enhanced_summary = parser.generate_history_header(
                    device.hostname,
                    parsed,
                    output,
                    operational_data
                )
            except Exception:
                # If summary generation fails, continue without it
                pass
            
            if save_to_db:
                self._save_config(device.hostname, config)
            
            return config
            
        except Exception as e:
            raise Exception(f"Failed to extract config from {device.hostname}: {str(e)}")

    def extract_specific_hierarchy(
        self,
        device: Device,
        hierarchy: str
    ) -> Optional[str]:
        """
        Extract a specific configuration hierarchy.
        
        Args:
            device: Device to extract from
            hierarchy: Hierarchy path (e.g., "interfaces", "protocols bgp")
        
        Returns:
            Configuration text for the hierarchy or None
        """
        client = None
        try:
            client = self.connect(device)
            
            output, error, exit_code = self.execute_command(
                client,
                f"show configuration {hierarchy}",
                timeout=60
            )
            
            if exit_code != 0 and not output:
                return None
            
            return output
            
        except Exception:
            return None
        finally:
            if client:
                client.close()

    def test_connection(self, device: Device) -> Tuple[bool, str]:
        """
        Test SSH connection to a device.
        
        Args:
            device: Device to test
        
        Returns:
            Tuple of (success, message)
        """
        client = None
        try:
            client = self.connect(device)
            
            # Try a simple command
            output, error, exit_code = self.execute_command(
                client,
                "show system name",
                timeout=10
            )
            
            return True, f"Connected successfully to {device.hostname}"
            
        except paramiko.AuthenticationException:
            return False, "Authentication failed - check username/password"
        except paramiko.SSHException as e:
            return False, f"SSH error: {str(e)}"
        except Exception as e:
            return False, f"Connection error: {str(e)}"
        finally:
            if client:
                client.close()

    def extract_operational_summary(self, device: Device) -> Dict[str, Any]:
        """
        Execute show commands to get operational state for enhanced summary.
        
        Args:
            device: Device to extract operational state from
        
        Returns:
            Dict with raw output from each show command
        """
        client = None
        results = {
            "isis_interfaces": None,
            "ospf_interfaces": None,
            "ospf_interfaces_detail": None,
            "bgp_summary": None,
            "interfaces_brief": None,
        }
        
        # Show commands to execute for operational state (| no-more disables paging)
        commands = {
            "isis_interfaces": "show isis interfaces | no-more",
            "ospf_interfaces": "show ospf interfaces | no-more",
            "ospf_interfaces_detail": "show ospf interfaces detail | no-more",
            "bgp_summary": "show bgp summary | no-more",
            "interfaces_brief": "show interfaces | no-more",
        }
        
        try:
            client = self.connect(device)
            
            for key, command in commands.items():
                try:
                    output, error, exit_code = self.execute_command(
                        client,
                        command,
                        timeout=30
                    )
                    # Store output even if exit code is non-zero (some commands may return 1 if no data)
                    if output and output.strip():
                        results[key] = output
                except Exception:
                    # Continue with other commands if one fails
                    pass
            
            return results
            
        except Exception as e:
            # Return partial results if connection fails midway
            return results
        finally:
            if client:
                client.close()

    def _save_config(self, hostname: str, config: DeviceConfig):
        """
        Save configuration to local database.
        Note: History saving is handled by the bash script with smart diff detection.
        
        Args:
            hostname: Device hostname
            config: DeviceConfig to save
        """
        config_dir = get_device_config_dir(hostname)
        history_dir = get_device_history_dir(hostname)
        
        # Build config with enhanced summary header
        raw_config = config.raw_config
        
        # Strip any existing header (lines starting with # at the beginning)
        lines = raw_config.split('\n')
        config_start = 0
        found_config = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                config_start = i
                found_config = True
                break
        
        # If no actual config found (all lines are comments/headers), set clean_config to empty
        # This prevents header accumulation for devices with no config (like GI mode devices)
        if found_config:
            clean_config = '\n'.join(lines[config_start:])
        else:
            clean_config = ''
        
        # Read unchanged_since info from operational.json (set by bash script)
        unchanged_since = None
        unchanged_until = None
        unchanged_checks = None
        try:
            ops_file = config_dir / "operational.json"
            if ops_file.exists():
                with open(ops_file) as f:
                    ops_data = json.load(f)
                    unchanged_since = ops_data.get("unchanged_since")
                    unchanged_until = ops_data.get("unchanged_until")
                    unchanged_checks = ops_data.get("unchanged_checks")
        except Exception:
            pass
        
        # Build new header with enhanced summary
        header_lines = [
            "#" + "=" * 79,
            f"# DEVICE SUMMARY - {hostname}",
        ]
        
        # Add unchanged period info
        if unchanged_since and unchanged_until:
            if unchanged_since == unchanged_until:
                header_lines.append(f"# Config unchanged since: {unchanged_since}")
            else:
                header_lines.append(f"# Config unchanged: {unchanged_since} to {unchanged_until} ({unchanged_checks or 1} checks)")
        else:
            header_lines.append(f"# Extracted: {config.extracted_at.strftime('%Y-%m-%d %H:%M:%S') if config.extracted_at else 'N/A'}")
        
        header_lines.append("#" + "=" * 79)
        
        # Add enhanced summary if available
        if config.enhanced_summary:
            header_lines.append("#")
            for line in config.enhanced_summary.split('\n'):
                header_lines.append(f"# {line}")
        
        header_lines.extend([
            "#" + "=" * 79,
            "",  # Empty line before config
        ])
        
        # Combine header with clean config
        final_config = '\n'.join(header_lines) + clean_config
        
        # Save current config (raw text with header)
        raw_file = config_dir / "running.txt"
        with open(raw_file, 'w') as f:
            f.write(final_config)
        
        # Update operational.json with parsed config data (comprehensive)
        try:
            ops_file = config_dir / "operational.json"
            ops_data = {}
            
            # Load existing ops data (preserve system info from network-mapper)
            if ops_file.exists():
                with open(ops_file) as f:
                    ops_data = json.load(f)
            
            # === BGP ===
            bgp_match = re.search(r'(?:protocols\s+)?bgp\s+(\d+)\s*\n', clean_config)
            if bgp_match:
                ops_data['local_as'] = int(bgp_match.group(1))
            peer_count = len(re.findall(r'\n\s{4,8}neighbor\s+\d+\.\d+\.\d+\.\d+\s*\n', clean_config))
            if peer_count > 0:
                ops_data['bgp_neighbors'] = peer_count
            
            # === Loopback & Router ID ===
            lo_match = re.search(r'^\s+lo0\s*\n\s+ipv4-address\s+(\d+\.\d+\.\d+\.\d+)', clean_config, re.MULTILINE)
            if lo_match:
                ops_data['lo0_ip'] = lo_match.group(1)
            rid_match = re.search(r'router-id\s+(\d+\.\d+\.\d+\.\d+)', clean_config)
            if rid_match:
                ops_data['router_id'] = rid_match.group(1)
            
            # === IGP (ISIS/OSPF) ===
            protocols_match = re.search(r'^protocols\s*\n(.*?)(?=^[^\s]|\Z)', clean_config, re.MULTILINE | re.DOTALL)
            if protocols_match:
                protocols_block = protocols_match.group(1)
                if re.search(r'^\s+isis\s*$', protocols_block, re.MULTILINE):
                    ops_data['igp'] = 'ISIS'
                    instance_match = re.search(r'isis\s*\n\s+instance\s+(\S+)', protocols_block)
                    if instance_match:
                        ops_data['igp_instance'] = instance_match.group(1)
                elif re.search(r'^\s+ospf\s*$', protocols_block, re.MULTILINE):
                    ops_data['igp'] = 'OSPF'
                    instance_match = re.search(r'ospf\s*\n\s+instance\s+(\S+)', protocols_block)
                    if instance_match:
                        ops_data['igp_instance'] = instance_match.group(1)
                
                # Label protocol
                if re.search(r'^\s+ldp\s*$', protocols_block, re.MULTILINE):
                    ops_data['label_protocol'] = 'LDP'
                elif re.search(r'segment-routing', protocols_block, re.IGNORECASE):
                    ops_data['label_protocol'] = 'SR'
                
                # Other protocols
                if re.search(r'^\s+lacp\s*$', protocols_block, re.MULTILINE):
                    lacp_ifaces = len(re.findall(r'interface\s+bundle-\d+', protocols_block))
                    ops_data['lacp_interfaces'] = lacp_ifaces
                if re.search(r'^\s+lldp\s*$', protocols_block, re.MULTILINE):
                    lldp_section = protocols_block.split('lldp')[1].split('!')[0] if 'lldp' in protocols_block else ''
                    lldp_ifaces = len(re.findall(r'interface\s+\S+', lldp_section))
                    ops_data['lldp_interfaces'] = lldp_ifaces
                if re.search(r'^\s+bfd\s*$', protocols_block, re.MULTILINE):
                    bfd_section = protocols_block.split('  bfd')[1].split('!')[0] if '  bfd' in protocols_block else ''
                    bfd_ifaces = len(re.findall(r'interface\s+\S+', bfd_section))
                    ops_data['bfd_interfaces'] = bfd_ifaces
            
            # === Services ===
            # VRF count - find network-services > vrf > instance <name>
            vrf_instances = set()
            ns_match = re.search(r'^network-services\s*\n(.*?)(?=^[^\s]|\Z)', clean_config, re.MULTILINE | re.DOTALL)
            if ns_match:
                ns_block = ns_match.group(1)
                vrf_match = re.search(r'^\s+vrf\s*\n(.*?)(?=^\s{2}[^\s]|\Z)', ns_block, re.MULTILINE | re.DOTALL)
                if vrf_match:
                    vrf_instances = set(re.findall(r'instance\s+(\S+)', vrf_match.group(1)))
            # Also check l3vpn vrf syntax
            l3vpn_vrfs = set(re.findall(r'l3vpn\s+vrf\s+(\S+)', clean_config))
            all_vrfs = vrf_instances | l3vpn_vrfs
            if all_vrfs:
                ops_data['vrf_total'] = len(all_vrfs)
                ops_data['vrf_names'] = list(all_vrfs)
            
            # FXC count - count all "instance FXC..." lines anywhere in config
            # Pattern matches: FXC_1, FXC-1, FXC1, fxc_1, FXC_100, etc.
            # Using direct search on full config for reliability
            fxc_instances = set(re.findall(r'\binstance\s+(FXC[-_]?\d+)', clean_config, re.IGNORECASE))
            if fxc_instances:
                ops_data['fxc_total'] = len(fxc_instances)
                ops_data['fxc_up'] = 0  # Will be updated by live check
            
            # Also check if evpn-vpws-fxc section exists (for header display)
            if '  evpn-vpws-fxc' in clean_config or 'evpn-vpws-fxc\n' in clean_config:
                ops_data['has_evpn_vpws_fxc'] = True
            
            # EVPN-VPWS count (not FXC) - matches EVPN_1, VPWS_1, etc.
            # Pattern: instance followed by EVPN, VPWS, or similar naming
            vpws_instances = set(re.findall(r'\binstance\s+(EVPN[-_]?\d+|VPWS[-_]?\d+)', clean_config, re.IGNORECASE))
            if vpws_instances:
                ops_data['vpws_total'] = len(vpws_instances)
                ops_data['vpws_up'] = 0
            
            # Check if evpn-vpws section exists (not FXC)
            if re.search(r'^\s{2}evpn-vpws\s*$', clean_config, re.MULTILINE):
                ops_data['has_evpn_vpws'] = True
            
            # EVPN-VPLS count
            vpls_instances = set(re.findall(r'\binstance\s+(VPLS[-_]?\d+)', clean_config, re.IGNORECASE))
            if vpls_instances:
                ops_data['vpls_total'] = len(vpls_instances)
                ops_data['vpls_up'] = 0
            
            # Check if evpn-vpls section exists
            if re.search(r'^\s{2}evpn-vpls\s*$', clean_config, re.MULTILINE):
                ops_data['has_evpn_vpls'] = True
            
            # L2VPN / Bridge Domain count
            bd_instances = set(re.findall(r'\bbridge-domain\s+(\S+)', clean_config, re.IGNORECASE))
            if bd_instances:
                ops_data['bridge_domain_total'] = len(bd_instances)
            
            # Generic instance count (all instances under network-services)
            all_instances = set(re.findall(r'\binstance\s+(\S+)', clean_config))
            # Exclude ISIS/OSPF instances
            service_instances = [i for i in all_instances if not re.match(r'^(isis|ospf|ldp|rsvp|bfd)', i.lower())]
            ops_data['total_service_instances'] = len(service_instances)
            
            # Route Targets
            rt_list = set(re.findall(r'route-target\s+(\d+:\d+)', clean_config))
            if rt_list:
                ops_data['route_targets'] = list(rt_list)
            
            # === Interfaces ===
            # Count interfaces by type from config (detailed breakdown)
            iface_pattern = re.compile(r'^  (\S+)\s*$', re.MULTILINE)
            interfaces_block = re.search(r'^interfaces\s*\n(.*?)(?=^[^\s]|\Z)', clean_config, re.MULTILINE | re.DOTALL)
            if interfaces_block:
                iface_names = iface_pattern.findall(interfaces_block.group(1))
                ops_data['interface_count'] = len(iface_names)
                
                # PWHE detailed breakdown
                pwhe_all = [i for i in iface_names if i.startswith('ph')]
                pwhe_parents = [i for i in pwhe_all if '.' not in i]
                pwhe_subifs = [i for i in pwhe_all if '.' in i]
                ops_data['pwhe_count'] = len(pwhe_all)
                ops_data['pwhe_parents'] = len(pwhe_parents)
                ops_data['pwhe_subifs'] = len(pwhe_subifs)
                
                # Bundle interfaces
                bundle_all = [i for i in iface_names if i.startswith('bundle')]
                bundle_parents = [i for i in bundle_all if '.' not in i]
                bundle_subifs = [i for i in bundle_all if '.' in i]
                ops_data['bundle_count'] = len(bundle_all)
                ops_data['bundle_parents'] = len(bundle_parents)
                ops_data['bundle_subifs'] = len(bundle_subifs)
                
                # Physical interfaces (ge, xe, et, hun)
                phys_all = [i for i in iface_names if re.match(r'^(ge|xe|et|hun)', i)]
                phys_parents = [i for i in phys_all if '.' not in i]
                phys_subifs = [i for i in phys_all if '.' in i]
                ops_data['physical_count'] = len(phys_all)
                ops_data['physical_parents'] = len(phys_parents)
                ops_data['physical_subifs'] = len(phys_subifs)
                
                # Loopback and IRB
                ops_data['loopback_count'] = len([i for i in iface_names if i.startswith('lo')])
                ops_data['irb_count'] = len([i for i in iface_names if i.startswith('irb')])
            
            # === System info from config ===
            sys_name_match = re.search(r'^\s+name\s+(\S+)', clean_config, re.MULTILINE)
            if sys_name_match:
                ops_data['system_name'] = sys_name_match.group(1)
            sys_type_match = re.search(r'^\s+profile\s+(\S+)', clean_config, re.MULTILINE)
            if sys_type_match:
                ops_data['system_profile'] = sys_type_match.group(1)
            
            # === Multihoming ===
            mh_esi_count = clean_config.count('\n      esi ')
            if mh_esi_count:
                ops_data['mh_interfaces'] = mh_esi_count
            
            # Save updated ops data
            with open(ops_file, 'w') as f:
                json.dump(ops_data, f, indent=2)
        except Exception:
            pass  # Don't fail the save if ops update fails
        
        # Note: running.json disabled to keep only 2 files (running.txt + operational.json)
        # The config data is stored in running.txt with header, and parsed on-demand if needed
        # json_file = config_dir / "running.json"
        # with open(json_file, 'w') as f:
        #     json.dump(config.model_dump(), f, indent=2, default=str)

    def get_saved_config(self, hostname: str) -> Optional[DeviceConfig]:
        """
        Load saved configuration from local database.
        
        Args:
            hostname: Device hostname
        
        Returns:
            DeviceConfig or None if not found
        """
        config_dir = get_device_config_dir(hostname)
        txt_file = config_dir / "running.txt"
        
        if not txt_file.exists():
            return None
        
        # Read running.txt and strip header lines (starting with #)
        with open(txt_file, 'r') as f:
            content = f.read()
        
        # Strip header (lines starting with #)
        lines = content.split('\n')
        config_start = 0
        for i, line in enumerate(lines):
            if line.strip() and not line.strip().startswith('#'):
                config_start = i
                break
        raw_config = '\n'.join(lines[config_start:])
        
        # Get file modification time as extracted_at (in local timezone for consistency)
        from datetime import datetime
        try:
            import pytz
            local_tz = pytz.timezone('Asia/Jerusalem')
            extracted_at = datetime.fromtimestamp(txt_file.stat().st_mtime, tz=local_tz)
        except:
            extracted_at = datetime.fromtimestamp(txt_file.stat().st_mtime)
        
        return DeviceConfig(
            device_id=hostname.lower().replace('-', ''),
            hostname=hostname,
            raw_config=raw_config,
            extracted_at=extracted_at
        )

    def get_config_history(self, hostname: str) -> list:
        """
        Get list of historical configs for a device.
        
        Args:
            hostname: Device hostname
        
        Returns:
            List of history file info dicts
        """
        history_dir = get_device_history_dir(hostname)
        
        history = []
        for f in sorted(history_dir.glob("*.json"), reverse=True):
            history.append({
                "filename": f.name,
                "timestamp": f.stem,
                "size": f.stat().st_size,
                "path": str(f)
            })
        
        return history

    def load_history_config(self, hostname: str, filename: str) -> Optional[DeviceConfig]:
        """
        Load a specific historical config.
        
        Args:
            hostname: Device hostname
            filename: History filename (e.g., "20251223_100000.json")
        
        Returns:
            DeviceConfig or None if not found
        """
        history_dir = get_device_history_dir(hostname)
        history_file = history_dir / filename
        
        if not history_file.exists():
            return None
        
        with open(history_file, 'r') as f:
            data = json.load(f)
        
        return DeviceConfig(**data)


class InteractiveExtractor:
    """Interactive SSH session for DNOS devices."""

    def __init__(self, device: Device, timeout: int = 30):
        """
        Initialize interactive extractor.
        
        Args:
            device: Device to connect to
            timeout: Connection timeout
        """
        self.device = device
        self.timeout = timeout
        self.client = None
        self.channel = None

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def connect(self):
        """Establish interactive SSH session."""
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Use helper function to get best SSH hostname
        # Prefers mgmt IP from operational.json over devices.json IP
        from .utils import get_ssh_hostname, update_device_connection_info
        hostname = get_ssh_hostname(self.device)
        
        self.client.connect(
            hostname=hostname,
            username=self.device.username,
            password=self.device.get_password(),
            timeout=self.timeout,
            look_for_keys=False,
            allow_agent=False
        )
        
        self.channel = self.client.invoke_shell()
        self.channel.settimeout(self.timeout)
        
        # Wait for initial prompt
        time.sleep(1)
        self._read_until_prompt()
        
        # Update devices.json with working connection info
        update_device_connection_info(self.device.hostname, hostname, "SSH→MGMT")

    def close(self):
        """Close SSH connection."""
        if self.channel:
            self.channel.close()
        if self.client:
            self.client.close()

    def send_command(self, command: str, wait_for_prompt: bool = True) -> str:
        """
        Send a command and optionally wait for prompt.
        
        Args:
            command: Command to send
            wait_for_prompt: Whether to wait for the prompt
        
        Returns:
            Command output
        """
        self.channel.send(command + "\n")
        
        if wait_for_prompt:
            return self._read_until_prompt()
        else:
            time.sleep(0.5)
            return self._read_available()

    def _read_until_prompt(self, timeout: int = 180) -> str:
        """Read output until we see a prompt."""
        output = ""
        start_time = time.time()
        last_recv_time = start_time
        
        while True:
            elapsed = time.time() - start_time
            idle_time = time.time() - last_recv_time
            
            # Hard timeout
            if elapsed > timeout:
                break
            
            # If we have output and no new data for 5 seconds, check for prompt
            if idle_time > 5 and output:
                lines = output.rstrip().split('\n')
                last_line = lines[-1].strip() if lines else ""
                # DNOS prompt patterns: hostname#, hostname>, hostname:cfg#
                if last_line.endswith('#') or last_line.endswith('>'):
                    break
            
            if self.channel.recv_ready():
                chunk = self.channel.recv(65535).decode('utf-8', errors='ignore')
                output += chunk
                last_recv_time = time.time()
                
                # Quick check for prompt after each chunk
                lines = output.rstrip().split('\n')
                last_line = lines[-1].strip() if lines else ""
                if last_line.endswith('#') or last_line.endswith('>'):
                    # Wait a bit more to ensure no more data
                    time.sleep(0.3)
                    if not self.channel.recv_ready():
                        break
            else:
                time.sleep(0.1)
        
        return output

    def _read_available(self) -> str:
        """Read all available output without waiting."""
        output = ""
        while self.channel.recv_ready():
            output += self.channel.recv(65535).decode('utf-8', errors='ignore')
        return output

    def enter_config_mode(self) -> str:
        """Enter configuration mode."""
        return self.send_command("configure")

    def exit_config_mode(self) -> str:
        """Exit configuration mode."""
        return self.send_command("exit")

    def get_running_config(self, fetch_lldp: bool = True) -> str:
        """
        Get the full running configuration.
        
        Args:
            fetch_lldp: If True, also fetch LLDP neighbors and update operational.json
        """
        # Use 'show config | no-more' to disable paging in DNOS
        output = self.send_command("show config | no-more", wait_for_prompt=True)
        
        # Extract config between markers
        lines = output.split('\n')
        config_lines = []
        in_config = False
        
        for line in lines:
            if 'config-start' in line:
                in_config = True
                config_lines.append(line)
            elif 'config-end' in line:
                config_lines.append(line)
                break
            elif in_config:
                config_lines.append(line)
        
        config_text = ""
        if config_lines:
            config_text = '\n'.join(config_lines)
        else:
            # Fallback: return everything except command echo and prompt
            if lines and 'show config' in lines[0]:
                lines = lines[1:]
            if lines and lines[-1].strip().endswith(('#', '>')):
                lines = lines[:-1]
            config_text = '\n'.join(lines)
        
        # Optionally fetch LLDP neighbors and update operational.json
        if fetch_lldp:
            try:
                lldp_data = fetch_lldp_neighbors(self.channel, self.device.hostname, timeout=15.0)
                if lldp_data and lldp_data.get('lldp_neighbors'):
                    update_lldp_in_operational_json(self.device.hostname, lldp_data)
            except Exception:
                # Don't fail config extraction if LLDP fetch fails
                pass
        
        return config_text


def update_recovery_mode_header(hostname: str):
    """
    Update the running.txt header for a device in recovery mode.
    
    Creates a clean, single header replacing any existing content.
    
    Args:
        hostname: Device hostname
    """
    from datetime import datetime
    
    config_dir = get_device_config_dir(hostname)
    running_file = config_dir / "running.txt"
    ops_file = config_dir / "operational.json"
    
    # Load operational data
    ops_data = {}
    if ops_file.exists():
        try:
            with open(ops_file) as f:
                ops_data = json.load(f)
        except:
            pass
    
    # Get device state - check both device_state and recovery_type
    device_state = ops_data.get('device_state')
    if not device_state or device_state == 'UNKNOWN':
        device_state = ops_data.get('recovery_type', 'UNKNOWN')
    
    connection_method = ops_data.get('connection_method', 'N/A')
    target_dnos = ops_data.get('target_dnos_version', '')
    target_gi = ops_data.get('target_gi_version', '')
    target_baseos = ops_data.get('target_baseos_version', '')
    serial_number = ops_data.get('serial_number', 'N/A')
    system_type = ops_data.get('system_type', 'N/A')
    mgmt_ip = ops_data.get('mgmt_ip', 'N/A')
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # Check if target stacks are available
    has_targets = any([
        target_dnos and target_dnos not in ('N/A', '-', ''),
        target_gi and target_gi not in ('N/A', '-', ''),
        target_baseos and target_baseos not in ('N/A', '-', '')
    ])
    
    # Build clean single header
    lines = [
        "#" + "=" * 79,
        f"# DEVICE SUMMARY - {hostname}",
        f"# State: {device_state} | Last checked: {now}",
        "#" + "=" * 79,
        "#",
        "# ╔" + "═" * 76 + "╗",
        f"# ║ STACK [{device_state} MODE]" + " " * (64 - len(device_state)) + "║",
        "# ╚" + "═" * 76 + "╝",
        f"#   • Connection: {connection_method}",
        f"#   • Current DNOS: N/A (not deployed)",
    ]
    
    # Add target stacks if available
    if has_targets:
        lines.append("#   ─────────────────────────────────────")
        lines.append("#   Target Stacks (Ready to Deploy):")
        if target_dnos and target_dnos not in ('N/A', '-', ''):
            lines.append(f"#   • DNOS:   {target_dnos}")
        if target_gi and target_gi not in ('N/A', '-', ''):
            lines.append(f"#   • GI:     {target_gi}")
        if target_baseos and target_baseos not in ('N/A', '-', ''):
            lines.append(f"#   • BaseOS: {target_baseos}")
    else:
        lines.append("#   • Target: None loaded")
    
    # SYSTEM section
    lines.extend([
        "# ╔" + "═" * 76 + "╗",
        "# ║ SYSTEM" + " " * 69 + "║",
        "# ╚" + "═" * 76 + "╝",
        f"#   • Type: {system_type}",
        f"#   • Serial: {serial_number}",
        f"#   • Mgmt IP: {mgmt_ip}",
    ])
    
    # Action guidance
    lines.extend([
        "# ╔" + "═" * 76 + "╗",
        "# ║ NEXT STEPS" + " " * 65 + "║",
        "# ╚" + "═" * 76 + "╝",
    ])
    
    if device_state == 'GI':
        if has_targets:
            lines.append("#   → Run: scaler-wizard → Select device → Deploy Now")
            lines.append("#   → Or:  Image Upgrade → System Deploy")
        else:
            lines.append("#   → Run: scaler-wizard → Image Upgrade → Load images")
    elif device_state == 'BASEOS_SHELL':
        lines.append("#   → Run: dncli (password: dnroot) → Enter GI mode")
        lines.append("#   → Then: Load images and deploy")
    elif device_state == 'ONIE':
        lines.append("#   → Install BaseOS via ONIE first")
        lines.append("#   → Then: dncli → GI → Load images → Deploy")
    else:
        lines.append("#   → Check device manually")
    
    lines.extend([
        "#",
        "#" + "=" * 79,
    ])
    
    # Write clean header (replaces entire file)
    try:
        with open(running_file, 'w') as f:
            f.write('\n'.join(lines) + '\n')
    except Exception as e:
        pass  # Don't fail on write error


# ═══════════════════════════════════════════════════════════════════════════════
# LLDP NEIGHBOR PARSING AND FETCHING
# ═══════════════════════════════════════════════════════════════════════════════

def parse_lldp_output(output: str) -> list:
    """
    Parse 'show lldp neighbors' table output.
    
    Expected format:
    | Interface     | Neighbor System Name | Neighbor interface | Capability |
    |---------------|----------------------|--------------------|------------|
    | ge400-0/0/1   | SPINE-1              | Ethernet1/1        | Router     |
    
    Returns:
        List of dicts with: local_interface, neighbor_device, neighbor_port, capability
    """
    import re
    
    neighbors = []
    in_table = False
    
    for line in output.split('\n'):
        # Detect table header to start parsing
        if 'Interface' in line and 'Neighbor' in line and '|' in line:
            in_table = True
            continue
        
        # Skip separator lines
        if '---' in line or '|-' in line or '-|' in line:
            continue
        
        # Stop at prompt
        if re.match(r'^[A-Za-z_-]+#', line.strip()) or re.match(r'^[A-Za-z_-]+\(', line.strip()):
            in_table = False
            continue
        
        # Parse table rows
        if in_table and '|' in line:
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 3:
                local_iface = parts[0]
                neighbor_dev = parts[1]
                neighbor_port = parts[2]
                capability = parts[3] if len(parts) > 3 else ''
                
                # Only physical interfaces with valid neighbor names
                if re.match(r'^(ge|xe|et|hu|ce|qsfp|bundle)[0-9]', local_iface, re.IGNORECASE):
                    if neighbor_dev and neighbor_dev not in ('Neighbor', '-', ''):
                        # Detect if neighbor is a DN device
                        is_dn = bool(re.search(
                            r'DNAAS|LEAF|SPINE|TOR|NCM|NCC|NCF|NCP|PE-|CE-|YOR_|TLV_|drivenets',
                            neighbor_dev, re.IGNORECASE
                        ))
                        
                        neighbors.append({
                            'local_interface': local_iface,
                            'neighbor_device': neighbor_dev,
                            'neighbor_port': neighbor_port,
                            'capability': capability,
                            'is_dn_device': is_dn
                        })
    
    return neighbors


def fetch_lldp_neighbors(channel, hostname: str = '', timeout: float = 10.0) -> dict:
    """
    Fetch LLDP neighbors via an existing SSH channel.
    
    Args:
        channel: Open paramiko channel
        hostname: Device hostname (for logging)
        timeout: Command timeout
    
    Returns:
        Dict with lldp_neighbors list, lldp_neighbor_count, lldp_last_updated
    """
    try:
        # Clear any pending output
        while channel.recv_ready():
            channel.recv(65535)
        
        # Send command
        channel.send("show lldp neighbors | no-more\r\n")
        time.sleep(2)
        
        # Collect output
        output = ""
        start = time.time()
        while time.time() - start < timeout:
            if channel.recv_ready():
                chunk = channel.recv(65535).decode('utf-8', errors='replace')
                output += chunk
                if '#' in chunk or '>' in chunk:
                    break
            time.sleep(0.3)
        
        # Parse output
        neighbors = parse_lldp_output(output)
        
        # Use local timezone (Asia/Jerusalem) for timestamps
        from .utils import get_local_now
        timestamp = get_local_now().isoformat()
        
        return {
            'lldp_neighbors': neighbors,
            'lldp_neighbor_count': len(neighbors),
            'lldp_last_updated': timestamp,
            'lldp_enabled': len(neighbors) > 0 or 'lldp' in output.lower()
        }
    
    except Exception as e:
        return {
            'lldp_neighbors': [],
            'lldp_neighbor_count': 0,
            'lldp_error': str(e),
            'lldp_stale': True
        }


def check_lldp_configured(channel, timeout: float = 5.0) -> bool:
    """
    Check if LLDP is configured on the device.
    
    Uses show running-config protocols lldp. We must not match the command
    echo (which contains "protocols lldp") - only actual config block.
    
    Returns True only if we see LLDP config hierarchy (e.g. " lldp" on its own
    line) and admin-state enabled. Returns False for "No matching" or empty.
    """
    import re
    try:
        while channel.recv_ready():
            channel.recv(65535)
        
        channel.send("show running-config protocols lldp | no-more\r\n")
        time.sleep(2)
        
        output = ""
        start = time.time()
        while time.time() - start < timeout:
            if channel.recv_ready():
                output += channel.recv(65535).decode('utf-8', errors='replace')
                if '#' in output or '>' in output:
                    break
            time.sleep(0.2)
        
        out_lower = output.lower()
        # No config: device says no matching / nothing to show
        if 'no matching' in out_lower or 'nothing to show' in out_lower or 'invalid' in out_lower:
            return False
        
        # Must have admin-state enabled in the output (actual LLDP config)
        if 'admin-state enabled' not in out_lower:
            return False
        
        # Must see "lldp" as a config line (newline + spaces + lldp), not just in command echo
        # Command echo is "show running-config protocols lldp | no-more" - no newline before "lldp"
        # Config block has "protocols" then newline then " lldp" or "  lldp"
        if not re.search(r'\n\s+lldp\b', output, re.IGNORECASE):
            return False
        
        return True
    
    except Exception:
        return False


def enable_lldp_on_device(channel, physical_interfaces: list = None, timeout: float = 30.0, progress_callback=None) -> bool:
    """
    Enable LLDP on device if not configured.
    
    Args:
        channel: Open paramiko channel
        physical_interfaces: List of interfaces to enable LLDP on (auto-detect if None)
        timeout: Command timeout
        progress_callback: Optional callable(str) for progress messages (e.g. lambda msg: console.print(msg))
    
    Returns:
        True if LLDP was enabled successfully
    """
    def _progress(msg):
        if progress_callback:
            try:
                progress_callback(msg)
            except Exception:
                pass
    
    try:
        # Auto-detect physical interfaces if not provided
        if not physical_interfaces:
            _progress("Fetching interface list from device...")
            while channel.recv_ready():
                channel.recv(65535)
            
            channel.send("show interfaces | no-more\r\n")
            time.sleep(3)
            
            output = ""
            start = time.time()
            while time.time() - start < 10:
                if channel.recv_ready():
                    output += channel.recv(65535).decode('utf-8', errors='replace')
                    if '#' in output:
                        break
                time.sleep(0.3)
            
            import re
            # Extract physical interface names - match anywhere in line (table format: | ge400-0/0/1 |)
            # DNOS "show interfaces" can be table or list; support ge, hu, ce, qsfp, xe, et
            physical_interfaces = list(set(re.findall(
                r'\b(?:ge|hu|ce|qsfp|xe|et)\d+-\d+/\d+/\d+\b',
                output,
                re.IGNORECASE
            )))
            # Sort for consistent ordering; exclude sub-interfaces (e.g. ge400-0/0/1.0)
            physical_interfaces = sorted([i for i in physical_interfaces if '.' not in i])
        
        if not physical_interfaces:
            return False
        
        n = min(len(physical_interfaces), 50)
        _progress(f"Found {len(physical_interfaces)} physical interface(s), enabling LLDP on {n}...")
        
        # Enter configure mode
        _progress("Entering configure mode...")
        channel.send("configure\r\n")
        time.sleep(0.5)
        
        # Enable LLDP: protocols lldp, admin-state enabled, then interface entries
        _progress("Configuring protocols lldp admin-state enabled...")
        channel.send("protocols lldp\r\n")
        time.sleep(0.3)
        channel.send("admin-state enabled\r\n")
        time.sleep(0.3)
        
        # Add interfaces under protocols lldp (DNOS: "interface ge400-0/0/0" under lldp)
        for i, iface in enumerate(physical_interfaces[:50], 1):
            if i <= 5 or i == n or i % 10 == 0:
                _progress(f"  Adding interface {i}/{n}: {iface}")
            channel.send(f"interface {iface}\r\n")
            time.sleep(0.1)
            channel.send("!\r\n")
            time.sleep(0.1)
        
        _progress("Closing protocols lldp...")
        channel.send("!\r\n")  # Close protocols lldp
        time.sleep(0.3)
        channel.send("!\r\n")  # Close protocols
        time.sleep(0.3)
        
        # Commit
        _progress("Committing configuration...")
        channel.send("commit\r\n")
        time.sleep(5)  # Wait for commit
        
        # Drain output and check for errors
        commit_output = ""
        while channel.recv_ready():
            commit_output += channel.recv(65535).decode('utf-8', errors='replace')
        
        if commit_output and ('error' in commit_output.lower() or 'invalid' in commit_output.lower()):
            _progress("Commit reported an error.")
            return False
        
        _progress("Commit completed.")
        return True
    
    except Exception:
        return False


def update_lldp_in_operational_json(hostname: str, lldp_data: dict) -> bool:
    """
    Update LLDP data in operational.json for a device.
    
    Args:
        hostname: Device hostname
        lldp_data: Dict with lldp_neighbors, lldp_neighbor_count, etc.
    
    Returns:
        True if update was successful
    """
    op_file = Path(f"/home/dn/SCALER/db/configs/{hostname}/operational.json")
    
    try:
        # Read existing data
        op_data = {}
        if op_file.exists():
            with open(op_file, 'r') as f:
                op_data = json.load(f)
        
        # Merge LLDP data
        op_data.update(lldp_data)
        
        # Write back
        op_file.parent.mkdir(parents=True, exist_ok=True)
        with open(op_file, 'w') as f:
            json.dump(op_data, f, indent=2)
        
        return True
    
    except Exception:
        return False
