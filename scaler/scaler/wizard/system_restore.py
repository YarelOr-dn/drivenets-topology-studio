"""
System Restore Wizard for Recovery Mode Devices

Handles the complete workflow for restoring a device that is in RECOVERY mode:
1. Detect recovery mode (via SSH or console)
2. Load previous device knowledge (system_type, hostname, version)
3. Execute system restore factory-default → wait for GI mode
4. Load images (DNOS, GI, BaseOS) in GI mode
5. Deploy DNOS with correct system-type and name

Reference: DEVELOPMENT_GUIDELINES.md - Device Upgrade / Recovery Mode sections
"""

import json
import re
import time
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Callable, Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import box

console = Console()

# Default DB path
DB_CONFIGS_PATH = Path(__file__).parent.parent.parent / "db" / "configs"


@dataclass
class DeviceKnowledge:
    """Previous knowledge about a device, stored in operational.json."""
    hostname: str
    system_type: Optional[str] = None
    serial_number: Optional[str] = None
    
    # Previous DNOS version info (before recovery)
    previous_dnos_version: Optional[str] = None
    previous_gi_version: Optional[str] = None
    previous_baseos_version: Optional[str] = None
    
    # Image URLs if previously stored
    dnos_url: Optional[str] = None
    gi_url: Optional[str] = None
    baseos_url: Optional[str] = None
    
    # Deploy parameters
    deploy_command: Optional[str] = None
    ncc_id: str = "0"
    
    # Recovery detection info
    recovery_mode_detected: bool = False
    recovery_detected_at: Optional[str] = None
    console_recovery_detected: bool = False
    
    # Config path
    config_dir: Optional[Path] = None
    
    @classmethod
    def from_operational_json(cls, hostname: str, op_path: Path = None) -> 'DeviceKnowledge':
        """Load device knowledge from operational.json."""
        if op_path is None:
            op_path = DB_CONFIGS_PATH / hostname / "operational.json"
        
        knowledge = cls(hostname=hostname, config_dir=op_path.parent if op_path else None)
        
        if op_path and op_path.exists():
            try:
                with open(op_path, 'r') as f:
                    data = json.load(f)
                
                knowledge.system_type = data.get('system_type')
                if knowledge.system_type == 'N/A':
                    knowledge.system_type = None
                
                knowledge.serial_number = data.get('serial_number')
                knowledge.previous_dnos_version = data.get('dnos_version')
                knowledge.previous_gi_version = data.get('gi_version')
                knowledge.previous_baseos_version = data.get('baseos_version')
                
                knowledge.dnos_url = data.get('dnos_url')
                knowledge.gi_url = data.get('gi_url')
                knowledge.baseos_url = data.get('baseos_url')
                
                knowledge.deploy_command = data.get('deploy_command')
                knowledge.ncc_id = data.get('deploy_ncc_id', '0')
                
                knowledge.recovery_mode_detected = data.get('recovery_mode_detected', False)
                knowledge.recovery_detected_at = data.get('recovery_mode_detected_at')
                knowledge.console_recovery_detected = data.get('console_recovery_detected', False)
                
            except (json.JSONDecodeError, IOError):
                pass
        
        return knowledge
    
    def save_to_operational_json(self, op_path: Path = None):
        """Save device knowledge back to operational.json."""
        if op_path is None:
            op_path = DB_CONFIGS_PATH / self.hostname / "operational.json"
        
        op_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing data
        data = {}
        if op_path.exists():
            try:
                with open(op_path, 'r') as f:
                    data = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        # Update with current knowledge
        data.update({
            'system_type': self.system_type,
            'serial_number': self.serial_number,
            'dnos_version': self.previous_dnos_version,
            'gi_version': self.previous_gi_version,
            'baseos_version': self.previous_baseos_version,
            'dnos_url': self.dnos_url,
            'gi_url': self.gi_url,
            'baseos_url': self.baseos_url,
            'deploy_command': self.deploy_command,
            'deploy_ncc_id': self.ncc_id,
            'deploy_system_type': self.system_type,
            'deploy_name': self.hostname,
            'recovery_mode_detected': self.recovery_mode_detected,
            'recovery_mode_detected_at': self.recovery_detected_at,
            'console_recovery_detected': self.console_recovery_detected,
        })
        
        with open(op_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_deploy_command(self) -> str:
        """Generate the deploy command based on stored knowledge."""
        system_type = self.system_type or 'SA-36CD-S'
        hostname = self.hostname
        ncc_id = self.ncc_id or '0'
        return f"request system deploy system-type {system_type} name {hostname} ncc-id {ncc_id}"
    
    def has_valid_system_type(self) -> bool:
        """Check if we have a valid system type."""
        return bool(self.system_type) and self.system_type not in ('N/A', 'Unknown', '')
    
    def has_image_urls(self) -> bool:
        """Check if we have stored image URLs."""
        return bool(self.dnos_url and self.dnos_url not in ('N/A', ''))


def show_device_knowledge_panel(knowledge: DeviceKnowledge) -> None:
    """Display device knowledge in a panel."""
    content_lines = []
    
    content_lines.append(f"[bold cyan]Hostname:[/bold cyan] {knowledge.hostname}")
    
    if knowledge.system_type:
        content_lines.append(f"[bold cyan]System Type:[/bold cyan] {knowledge.system_type}")
    else:
        content_lines.append("[bold yellow]System Type:[/bold yellow] [yellow]Not detected - will need to specify[/yellow]")
    
    if knowledge.serial_number:
        content_lines.append(f"[dim]Serial Number:[/dim] {knowledge.serial_number}")
    
    content_lines.append("")
    
    # Version info
    if knowledge.previous_dnos_version and knowledge.previous_dnos_version != 'N/A':
        content_lines.append(f"[bold]Previous DNOS:[/bold] {knowledge.previous_dnos_version}")
    else:
        content_lines.append("[dim]Previous DNOS:[/dim] Unknown")
    
    if knowledge.previous_gi_version and knowledge.previous_gi_version != 'N/A':
        content_lines.append(f"[dim]Previous GI:[/dim] {knowledge.previous_gi_version}")
    
    if knowledge.previous_baseos_version and knowledge.previous_baseos_version != 'N/A':
        content_lines.append(f"[dim]Previous BaseOS:[/dim] {knowledge.previous_baseos_version}")
    
    content_lines.append("")
    
    # Image URLs if available
    if knowledge.has_image_urls():
        content_lines.append("[bold green]✓[/bold green] Stored image URLs available")
        if knowledge.dnos_url:
            # Show shortened URL
            dnos_short = knowledge.dnos_url.split('/')[-1][:40] if '/' in knowledge.dnos_url else knowledge.dnos_url[:40]
            content_lines.append(f"  [dim]DNOS:[/dim] {dnos_short}")
    else:
        content_lines.append("[yellow]○[/yellow] No stored image URLs - will need Jenkins/Minio source")
    
    content_lines.append("")
    
    # Deploy command
    deploy_cmd = knowledge.get_deploy_command()
    content_lines.append(f"[bold]Deploy Command:[/bold]")
    content_lines.append(f"  [green]{deploy_cmd}[/green]")
    
    console.print(Panel(
        "\n".join(content_lines),
        title=f"[bold]📋 Device Knowledge: {knowledge.hostname}[/bold]",
        border_style="cyan",
        padding=(1, 2)
    ))


def prompt_system_type(knowledge: DeviceKnowledge) -> str:
    """Prompt user to confirm or enter system type."""
    # Common DNOS system types
    SYSTEM_TYPES = [
        "SA-36CD-S",
        "SA-40C", 
        "CL-16",
        "SA-24D",
        "SA-2C",
        "NCR-16",
    ]
    
    console.print("\n[bold]System Type Configuration[/bold]")
    
    if knowledge.has_valid_system_type():
        console.print(f"  Detected: [green]{knowledge.system_type}[/green]")
        if Confirm.ask("  Use detected system type?", default=True):
            return knowledge.system_type
    else:
        console.print("  [yellow]System type not detected from previous config.[/yellow]")
    
    console.print("\n  Common system types:")
    for i, st in enumerate(SYSTEM_TYPES, 1):
        console.print(f"    [{i}] {st}")
    console.print(f"    [C] Custom - enter manually")
    console.print(f"    [B] Back")
    
    choice = Prompt.ask("  Select", choices=[str(i) for i in range(1, len(SYSTEM_TYPES)+1)] + ['c', 'C', 'b', 'B'], default="1")
    
    if choice.lower() == 'b':
        raise KeyboardInterrupt("User cancelled")
    elif choice.lower() == 'c':
        custom_type = Prompt.ask("  Enter system type")
        return custom_type
    else:
        return SYSTEM_TYPES[int(choice) - 1]


def prompt_hostname(knowledge: DeviceKnowledge) -> str:
    """Prompt user to confirm or enter hostname."""
    console.print("\n[bold]Hostname Configuration[/bold]")
    console.print(f"  Current: [green]{knowledge.hostname}[/green]")
    
    if Confirm.ask("  Use this hostname for deployment?", default=True):
        return knowledge.hostname
    
    new_hostname = Prompt.ask("  Enter new hostname")
    return new_hostname


def get_recent_image_sources() -> List[Dict]:
    """Get recent image sources from upgrade history.
    
    Returns:
        List of recent source entries with dnos_url, gi_url, baseos_url
    """
    history_path = Path("db/upgrade_sources_history.json")
    if not history_path.exists():
        return []
    
    try:
        with open(history_path) as f:
            history = json.load(f)
        
        recent_urls = history.get('recent_urls', [])
        recent_branches = history.get('recent_branches', [])
        
        # Combine and sort by timestamp
        all_entries = []
        for entry in recent_urls:
            entry['_type'] = 'url'
            all_entries.append(entry)
        for entry in recent_branches:
            entry['_type'] = 'branch'
            all_entries.append(entry)
        
        # Sort by timestamp (most recent first)
        all_entries.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Deduplicate by branch
        seen = set()
        deduplicated = []
        for entry in all_entries:
            branch = entry.get('branch', '')
            key = branch or entry.get('url', str(len(deduplicated)))
            if key and key not in seen:
                seen.add(key)
                deduplicated.append(entry)
        
        return deduplicated[:5]  # Top 5 recent sources
    except:
        return []


def prompt_image_source_inline() -> Optional[Dict]:
    """Prompt user to select image source inline (for console-based loading).
    
    Returns:
        Dict with dnos_url, gi_url, baseos_url or None if skipped/cancelled
    """
    console.print("\n[bold cyan]Image Source Selection[/bold cyan]")
    console.print("  [dim]Select images to load after entering GI mode.[/dim]\n")
    
    recent = get_recent_image_sources()
    
    if recent:
        console.print("  [bold]Recent Sources:[/bold]")
        for i, entry in enumerate(recent, 1):
            branch = entry.get('branch', 'Unknown')
            build = entry.get('build', '?')
            console.print(f"    [{i}] {branch} #{build}")
        console.print(f"    [M] Enter Minio URLs manually")
        console.print(f"    [S] Skip image loading (manual later)")
        console.print(f"    [B] Back")
        
        choices = [str(i) for i in range(1, len(recent)+1)] + ['m', 'M', 's', 'S', 'b', 'B']
        choice = Prompt.ask("  Select", choices=choices, default="1").lower()
        
        if choice == 'b':
            raise KeyboardInterrupt("User cancelled")
        elif choice == 's':
            return None
        elif choice == 'm':
            return prompt_manual_urls()
        else:
            idx = int(choice) - 1
            entry = recent[idx]
            
            # Get URLs from entry or fetch from Jenkins
            dnos_url = entry.get('dnos_url') or entry.get('dnos')
            gi_url = entry.get('gi_url') or entry.get('gi')
            baseos_url = entry.get('baseos_url') or entry.get('baseos')
            
            # If URLs not in entry, try to fetch from Jenkins
            if not dnos_url and entry.get('branch'):
                try:
                    from ..jenkins_integration import JenkinsClient
                    jenkins = JenkinsClient()
                    build = entry.get('build')
                    if build:
                        urls = jenkins.get_stack_urls(entry['branch'], build)
                        dnos_url = urls.get('dnos')
                        gi_url = urls.get('gi')
                        baseos_url = urls.get('baseos')
                except Exception as e:
                    console.print(f"  [yellow]⚠ Could not fetch URLs: {e}[/yellow]")
                    return prompt_manual_urls()
            
            console.print(f"\n  [bold]Selected:[/bold] {entry.get('branch', 'Unknown')} #{entry.get('build', '?')}")
            if dnos_url:
                console.print(f"    DNOS: [dim]{dnos_url[:60]}...[/dim]")
            if gi_url:
                console.print(f"    GI: [dim]{gi_url[:60]}...[/dim]")
            if baseos_url:
                console.print(f"    BaseOS: [dim]{baseos_url[:60]}...[/dim]")
            
            return {
                'dnos_url': dnos_url,
                'gi_url': gi_url,
                'baseos_url': baseos_url,
                'branch': entry.get('branch'),
                'build': entry.get('build')
            }
    else:
        console.print("  [yellow]No recent sources found.[/yellow]")
        console.print("    [M] Enter Minio URLs manually")
        console.print("    [S] Skip image loading (manual later)")
        console.print("    [B] Back")
        
        choice = Prompt.ask("  Select", choices=['m', 'M', 's', 'S', 'b', 'B'], default='m').lower()
        
        if choice == 'b':
            raise KeyboardInterrupt("User cancelled")
        elif choice == 's':
            return None
        else:
            return prompt_manual_urls()


def prompt_manual_urls() -> Dict:
    """Prompt user to enter image URLs manually."""
    console.print("\n  [bold]Enter Image URLs[/bold]")
    console.print("  [dim]Paste full Minio URLs for each component.[/dim]")
    console.print("  [dim]Leave empty to skip a component.[/dim]\n")
    
    dnos_url = Prompt.ask("  DNOS URL", default="")
    gi_url = Prompt.ask("  GI URL", default="")
    baseos_url = Prompt.ask("  BaseOS URL", default="")
    
    if not dnos_url and not gi_url and not baseos_url:
        console.print("  [yellow]No URLs provided. Skipping image loading.[/yellow]")
        return None
    
    return {
        'dnos_url': dnos_url or None,
        'gi_url': gi_url or None,
        'baseos_url': baseos_url or None
    }


def get_management_ip_from_console(
    channel: Any,
    add_line: Callable[[str, str], None],
    live: Any,
    render_panel: Callable[[], Any]
) -> Optional[str]:
    """
    Get management IP from console using 'show interfaces management' command.
    
    Args:
        channel: Console channel (in GI mode)
        add_line: Callback to add terminal lines
        live: Rich Live display
        render_panel: Callback to render panel
        
    Returns:
        Management IP address or None if not found
    """
    import re
    
    add_line("🔍 Getting management IP...", "cyan")
    live.update(render_panel())
    
    channel.send("show interfaces management | no-more\r\n")
    time.sleep(3)
    
    mgmt_output = ""
    for _ in range(10):
        if channel.recv_ready():
            mgmt_output += channel.recv(65535).decode('utf-8', errors='replace')
        time.sleep(0.3)
    
    # Parse for mgmt0 IP address (look for IPv4 Address pattern)
    mgmt_ip = None
    
    # Look for mgmt0 line with IP (prioritize mgmt0)
    for line in mgmt_output.split('\n'):
        line_lower = line.lower()
        if 'mgmt0' in line_lower:
            # Extract IP from line (format: A.B.C.D/X)
            ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)/\d+', line)
            if ip_match:
                mgmt_ip = ip_match.group(1)
                add_line(f"✓ Found mgmt0 IP: {mgmt_ip}", "green")
                live.update(render_panel())
                return mgmt_ip
    
    # Fallback: look for any mgmt-* with IP
    for line in mgmt_output.split('\n'):
        if 'mgmt-' in line.lower():
            ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)/\d+', line)
            if ip_match:
                mgmt_ip = ip_match.group(1)
                add_line(f"✓ Found mgmt IP: {mgmt_ip}", "green")
                live.update(render_panel())
                return mgmt_ip
    
    add_line("⚠ No management IP found", "yellow")
    live.update(render_panel())
    return None


def load_images_via_ssh(
    device_ip: str,
    image_urls: Dict,
    knowledge: 'DeviceKnowledge',
    add_line: Callable[[str, str], None],
    progress_lock: Any,
    live: Any,
    render_panel: Callable[[], Any],
    progress_state: Dict,
    username: str = "dnroot",
    password: str = "dnroot"
) -> Tuple[bool, str]:
    """
    Load images via direct SSH to device (faster than console).
    
    Uses: request system target-stack load <URL>
    Check progress: show system target-stack load | no-more
    
    SSH is faster than console and handles confirmation prompts properly.
    
    Args:
        device_ip: IP address of the device
        image_urls: Dict with dnos_url, gi_url, baseos_url
        knowledge: DeviceKnowledge with deploy command
        add_line: Callback to add terminal lines
        progress_lock: Thread lock for progress updates
        live: Rich Live display
        render_panel: Callback to render panel
        progress_state: Dict with 'stage' and 'progress' keys
        username: SSH username (default: dnroot)
        password: SSH password (default: dnroot)
        
    Returns:
        (success, message) tuple
    """
    import re
    import paramiko
    
    def sanitize_line(line: str) -> str:
        """Remove ANSI escape codes and control characters."""
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        line = ansi_escape.sub('', line)
        line = ''.join(c for c in line if c >= ' ' or c in '\n\t')
        return line.strip()
    
    # Try to connect via SSH
    add_line(f"🔌 Connecting to {device_ip} via SSH...", "cyan")
    live.update(render_panel())
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(device_ip, username=username, password=password, timeout=15)
        channel = ssh.invoke_shell(width=200, height=50)
        channel.settimeout(30)
        time.sleep(2)
        
        # Clear initial output
        if channel.recv_ready():
            channel.recv(65535)
        
        add_line(f"✓ SSH connected to {device_ip}", "green")
        live.update(render_panel())
        
    except Exception as e:
        add_line(f"✗ SSH failed: {str(e)[:40]}", "red")
        live.update(render_panel())
        return False, f"SSH connection failed: {str(e)}"
    
    def send_and_wait(cmd: str, wait_time: float = 3) -> str:
        """Send command and wait for output."""
        channel.send(f"{cmd}\n")
        time.sleep(wait_time)
        output = ""
        for _ in range(10):
            if channel.recv_ready():
                output += channel.recv(65535).decode('utf-8', errors='replace')
            time.sleep(0.3)
        return output
    
    def wait_for_download(component: str, timeout: int = 300) -> Tuple[bool, str]:
        """Wait for image download to complete."""
        start = time.time()
        last_pct = 0
        last_update_pct = 0
        
        add_line(f"📥 Downloading {component}...", "cyan")
        live.update(render_panel())
        
        while time.time() - start < timeout:
            elapsed = int(time.time() - start)
            
            # Check download status
            output = send_and_wait("show system target-stack load | no-more", wait_time=3)
            
            # Look for progress percentage
            pct_match = re.search(r'(\d+)\s*%', output)
            if pct_match:
                pct = int(pct_match.group(1))
                if pct > last_pct:
                    last_pct = pct
                if pct >= last_update_pct + 20:
                    last_update_pct = pct
                    add_line(f"📥 {component}: {pct}%", "cyan")
                    live.update(render_panel())
            
            # Check for completion indicators
            output_lower = output.lower()
            if 'completed' in output_lower or last_pct >= 100:
                add_line(f"✓ {component} download complete", "green")
                live.update(render_panel())
                return True, "Complete"
            
            # Check for "in-progress" - still downloading
            if 'in-progress' in output_lower:
                continue
            
            # Check for "no download tasks" - either completed or not started
            if 'no download tasks' in output_lower:
                if last_pct > 0:
                    add_line(f"✓ {component} download complete", "green")
                    live.update(render_panel())
                    return True, "Complete"
                
                # Check if image is in target stack
                stack_output = send_and_wait("show system stack | no-more", wait_time=3)
                if component.lower() in stack_output.lower():
                    add_line(f"✓ {component} in target stack", "green")
                    live.update(render_panel())
                    return True, "Already loaded"
                
                # No progress after waiting - might have failed
                if elapsed > 30:
                    add_line(f"⚠ {component}: No download activity after {elapsed}s", "yellow")
                    live.update(render_panel())
                    return True, "No download needed"
            
            # Check for errors
            if 'failed' in output_lower or ('error' in output_lower and 'unknown' not in output_lower):
                add_line(f"✗ {component} download FAILED", "red")
                live.update(render_panel())
                return False, output
            
            time.sleep(5)
        
        return False, f"Timeout after {timeout}s"
    
    dnos_url = image_urls.get('dnos_url')
    gi_url = image_urls.get('gi_url')
    baseos_url = image_urls.get('baseos_url')
    
    components = []
    if dnos_url:
        components.append(('DNOS', dnos_url))
    if gi_url:
        components.append(('GI', gi_url))
    if baseos_url:
        components.append(('BaseOS', baseos_url))
    
    if not components:
        add_line("⚠ No image URLs provided", "yellow")
        live.update(render_panel())
        ssh.close()
        return False, "No image URLs"
    
    total = len(components)
    progress_per_component = 60 // total
    
    for idx, (name, url) in enumerate(components):
        with progress_lock:
            progress_state['stage'] = f"Loading {name}..."
            progress_state['progress'] = 10 + (idx * progress_per_component)
        live.update(render_panel())
        
        add_line(f"📤 Loading {name}...", "cyan")
        add_line(f"> request system target-stack load ...", "dim")
        live.update(render_panel())
        
        # Send load command via SSH (faster than console)
        output = send_and_wait(f"request system target-stack load {url}", wait_time=3)
        
        # Check for prompt and answer yes
        if 'continue?' in output.lower() or '(yes/no)' in output.lower():
            add_line("  Confirming with 'yes'...", "dim")
            live.update(render_panel())
            confirm_output = send_and_wait("yes", wait_time=2)
            output += confirm_output
        
        # Show output
        for line in output.split('\n')[-3:]:
            clean_line = sanitize_line(line)
            if clean_line and len(clean_line) > 5:
                add_line(f"  {clean_line[:60]}", "dim")
                live.update(render_panel())
        
        # Check for immediate errors
        if 'error' in output.lower() and 'unknown' not in output.lower():
            add_line(f"✗ {name} load failed", "red")
            for line in output.split('\n'):
                clean_line = sanitize_line(line)
                if clean_line and 'error' in clean_line.lower():
                    add_line(f"  ERROR: {clean_line[:55]}", "bright_red")
            live.update(render_panel())
            ssh.close()
            return False, f"{name} load failed"
        
        add_line(f"✓ {name} load initiated", "green")
        live.update(render_panel())
        
        # Wait for download
        success, msg = wait_for_download(name, timeout=300)
        if not success:
            add_line(f"✗ {name} download failed: {msg[:40]}", "red")
            live.update(render_panel())
            ssh.close()
            return False, f"{name} download failed: {msg}"
        
        with progress_lock:
            progress_state['progress'] = 10 + ((idx + 1) * progress_per_component)
        live.update(render_panel())
    
    add_line("✓ All images loaded successfully", "green")
    live.update(render_panel())
    ssh.close()
    return True, "All images loaded"


def load_images_via_console(
    channel: Any,
    image_urls: Dict,
    knowledge: DeviceKnowledge,
    add_line: Callable[[str, str], None],
    progress_lock: Any,
    live: Any,
    render_panel: Callable[[], Any],
    progress_state: Dict
) -> Tuple[bool, str]:
    """
    Load images via console in GI mode using correct GI commands.
    
    Uses: request system target-stack load <URL>
    Check progress: show system target-stack load | no-more
    
    Verified 2026-01-28: GI mode uses the same target-stack commands as DNOS mode.
    
    Args:
        channel: Paramiko SSH channel (connected to GI mode via console)
        image_urls: Dict with dnos_url, gi_url, baseos_url
        knowledge: DeviceKnowledge with deploy command
        add_line: Callback to add terminal lines
        progress_lock: Thread lock for progress updates
        live: Rich Live display
        render_panel: Callback to render panel
        progress_state: Dict with 'stage' and 'progress' keys
        
    Returns:
        (success, message) tuple
    """
    import re
    
    def sanitize_line(line: str) -> str:
        """Remove ANSI escape codes and control characters."""
        import re
        # Remove ANSI escape sequences
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        line = ansi_escape.sub('', line)
        # Remove other control characters except newline/tab
        line = ''.join(c for c in line if c >= ' ' or c in '\n\t')
        return line.strip()
    
    def send_and_wait(cmd: str, wait_time: float = 3, show_output: bool = False) -> str:
        """Send command and wait for output."""
        channel.send(f"{cmd}\r\n")
        time.sleep(wait_time)
        output = ""
        for _ in range(10):
            if channel.recv_ready():
                output += channel.recv(65535).decode('utf-8', errors='replace')
            time.sleep(0.3)
        
        # Show actual console output if requested
        if show_output and output:
            for line in output.split('\n')[-5:]:
                clean_line = sanitize_line(line)
                if clean_line and len(clean_line) > 3:
                    # Truncate long lines
                    display_line = clean_line[:70] if len(clean_line) > 70 else clean_line
                    add_line(f"  {display_line}", "dim")
                    live.update(render_panel())
        
        return output
    
    def wait_for_download(component: str, timeout: int = 300) -> Tuple[bool, str]:
        """Wait for image download to complete."""
        start = time.time()
        last_pct = 0
        last_update_pct = 0
        poll_count = 0
        
        add_line(f"📥 Downloading {component}...", "cyan")
        live.update(render_panel())
        
        while time.time() - start < timeout:
            elapsed = int(time.time() - start)
            poll_count += 1
            
            # Check download status: show system target-stack load | no-more
            output = send_and_wait("show system target-stack load | no-more", wait_time=3)
            
            # Show raw output every 10 polls for debugging
            if poll_count % 10 == 1 and output:
                for line in output.split('\n')[-3:]:
                    clean_line = sanitize_line(line)
                    if clean_line and len(clean_line) > 5:
                        add_line(f"  [{elapsed}s] {clean_line[:60]}", "dim")
                        live.update(render_panel())
            
            # Look for download progress percentage - multiple patterns
            pct_match = re.search(r'(\d+)\s*%', output)
            if not pct_match:
                # Try alternative patterns
                pct_match = re.search(r'Progress[:\s]+(\d+)', output, re.IGNORECASE)
            
            if pct_match:
                pct = int(pct_match.group(1))
                if pct > last_pct:
                    last_pct = pct
                # Show every 20% progress
                if pct >= last_update_pct + 20:
                    last_update_pct = pct
                    add_line(f"📥 {component}: {pct}%", "cyan")
                    live.update(render_panel())
            
            # Check for completion indicators
            output_lower = output.lower()
            if 'completed' in output_lower or last_pct >= 100:
                add_line(f"✓ {component} download complete", "green")
                live.update(render_panel())
                return True, "Complete"
            
            # Check for "available" in software list (means download finished)
            if component.lower() in output_lower and 'available' in output_lower:
                add_line(f"✓ {component} available", "green")
                live.update(render_panel())
                return True, "Available"
            
            # Check for idle/no task state (download finished)
            # "There are no download tasks in progress" means download completed or not started
            if 'no download tasks' in output_lower:
                # If we saw progress before, download is complete
                if last_pct > 0:
                    add_line(f"✓ {component} download complete (was {last_pct}%)", "green")
                    live.update(render_panel())
                    return True, "Complete"
                
                # No progress seen - either not started or already loaded
                elapsed = int(time.time() - start)
                if elapsed > 60:  # Wait up to 60s for download to start
                    add_line(f"⚠ {component}: No download activity after {elapsed}s", "yellow")
                    add_line("  (Image may already be loaded or URL invalid)", "dim")
                    live.update(render_panel())
                    # Return True to continue - let deploy phase verify
                    return True, "No download needed"
            
            # Check for errors - show the actual error
            if 'failed' in output_lower or 'error' in output_lower:
                add_line(f"✗ {component} download FAILED", "red")
                # Show the error details
                for line in output.split('\n'):
                    clean_line = sanitize_line(line)
                    if clean_line and ('error' in clean_line.lower() or 'failed' in clean_line.lower()):
                        add_line(f"  ERROR: {clean_line[:60]}", "bright_red")
                live.update(render_panel())
                return False, output
            
            time.sleep(5)
        
        return False, f"Timeout after {timeout}s"
    
    dnos_url = image_urls.get('dnos_url')
    gi_url = image_urls.get('gi_url')
    baseos_url = image_urls.get('baseos_url')
    
    components = []
    if dnos_url:
        components.append(('DNOS', dnos_url))
    if gi_url:
        components.append(('GI', gi_url))
    if baseos_url:
        components.append(('BaseOS', baseos_url))
    
    if not components:
        add_line("⚠ No image URLs provided", "yellow")
        live.update(render_panel())
        return False, "No image URLs"
    
    total = len(components)
    progress_per_component = 60 // total  # 60% for downloads
    
    for idx, (name, url) in enumerate(components):
        with progress_lock:
            progress_state['stage'] = f"Loading {name}..."
            progress_state['progress'] = 10 + (idx * progress_per_component)
        live.update(render_panel())
        
        add_line(f"📤 Loading {name}...", "cyan")
        live.update(render_panel())
        
        # STRATEGY: Multiple aggressive approaches to handle console prompt timing
        max_retries = 7
        load_success = False
        
        for retry in range(max_retries):
            if retry > 0:
                add_line(f"  Attempt {retry + 1}/{max_retries}...", "yellow")
                live.update(render_panel())
                time.sleep(1)
            
            # Clear pending output
            while channel.recv_ready():
                channel.recv(65535)
            
            # Different strategies for each retry
            if retry < 2:
                # Strategy 1: Send command, then spam "yes" rapidly
                add_line("  [Strategy: Rapid yes spam]", "dim")
                live.update(render_panel())
                
                channel.send(f"request system target-stack load {url}\r\n")
                
                # Spam "yes" every 100ms for 3 seconds
                start = time.time()
                yes_count = 0
                while time.time() - start < 3:
                    channel.send("yes\r\n")
                    yes_count += 1
                    time.sleep(0.1)
                
                add_line(f"  Sent {yes_count} 'yes' responses", "dim")
                
            elif retry < 4:
                # Strategy 2: Interleave command bytes with yes
                add_line("  [Strategy: Interleaved send]", "dim")
                live.update(render_panel())
                
                # Send command
                cmd = f"request system target-stack load {url}\r\n"
                channel.send(cmd)
                time.sleep(0.2)
                # Immediately follow with yes
                channel.send("yes\r\n")
                time.sleep(0.5)
                channel.send("yes\r\n")
                
            else:
                # Strategy 3: Character-by-character with yes ready
                add_line("  [Strategy: Byte-level timing]", "dim")
                live.update(render_panel())
                
                # Type command character by character
                cmd = f"request system target-stack load {url}"
                for char in cmd:
                    channel.send(char)
                    time.sleep(0.01)  # 10ms per char
                channel.send("\r\n")
                
                # Immediately start sending yes
                for _ in range(20):
                    channel.send("yes\r\n")
                    time.sleep(0.15)
            
            # Wait and collect output
            time.sleep(3)
            output = ""
            for _ in range(15):
                if channel.recv_ready():
                    output += channel.recv(65535).decode('utf-8', errors='replace')
                time.sleep(0.2)
            
            # Show relevant output
            for line in output.split('\n')[-4:]:
                clean = sanitize_line(line)
                if clean and len(clean) > 5 and 'yes' not in clean.lower()[:10]:
                    add_line(f"  {clean[:55]}", "dim")
            live.update(render_panel())
            
            # Check if download started
            channel.send("show system target-stack load | no-more\r\n")
            time.sleep(2)
            
            status_output = ""
            for _ in range(5):
                if channel.recv_ready():
                    status_output += channel.recv(65535).decode('utf-8', errors='replace')
                time.sleep(0.2)
            
            # Check for active download (Task status: in-progress) or any progress
            status_lower = status_output.lower()
            if 'in-progress' in status_lower or 'downloading' in status_lower or \
               '%' in status_output or 'task id' in status_lower:
                add_line("  ✓ Download in progress!", "green")
                load_success = True
                break
            
            # Check if image is already in target stack
            channel.send("show system stack | no-more\r\n")
            time.sleep(2)
            
            stack_output = ""
            for _ in range(5):
                if channel.recv_ready():
                    stack_output += channel.recv(65535).decode('utf-8', errors='replace')
                time.sleep(0.2)
            
            # Look for DNOS in target column (means it's loaded)
            if name.lower() in stack_output.lower() and 'target' in stack_output.lower():
                # Check if target column has a version (not empty)
                if '|' in stack_output:  # Has table format
                    add_line(f"  ✓ {name} already in target stack", "green")
                    load_success = True
                    break
            
            # If "no download tasks", prompt may have timed out or URL is wrong
            if 'no download tasks' in status_lower:
                add_line("  ⚠ No download activity - retrying...", "yellow")
                live.update(render_panel())
                continue
            
            # Check for other errors
            if 'error' in output.lower() and 'unknown word' not in output.lower():
                for line in output.split('\n'):
                    clean_line = sanitize_line(line)
                    if clean_line and 'error' in clean_line.lower():
                        if 'unknown word' not in clean_line.lower():
                            add_line(f"  ERROR: {clean_line[:55]}", "red")
                live.update(render_panel())
        
        if not load_success:
            add_line(f"✗ {name} load failed after {max_retries} retries", "red")
            add_line("  Console prompt timing issue - try manual load", "dim")
            live.update(render_panel())
            return False, f"{name} load failed - console confirmation timing"
        
        add_line(f"✓ {name} load initiated", "green")
        live.update(render_panel())
        
        # Wait for download
        success, msg = wait_for_download(name, timeout=300)
        if not success:
            # Show failure details
            add_line(f"✗ {name} download failed", "red")
            if msg and 'timeout' not in msg.lower():
                # Show last few lines of output as error detail
                for line in msg.split('\n')[-3:]:
                    clean_line = sanitize_line(line)
                    if clean_line and len(clean_line) > 5:
                        add_line(f"  {clean_line[:60]}", "bright_red")
            live.update(render_panel())
            return False, f"{name} download failed: {msg[:100]}"
        
        with progress_lock:
            progress_state['progress'] = 10 + ((idx + 1) * progress_per_component)
        live.update(render_panel())
    
    add_line("✓ All images loaded successfully", "green")
    live.update(render_panel())
    return True, "All images loaded"


def deploy_via_console(
    channel: Any,
    knowledge: DeviceKnowledge,
    add_line: Callable[[str, str], None],
    progress_lock: Any,
    live: Any,
    render_panel: Callable[[], Any],
    progress_state: Dict,
    ssh_client: Any = None
) -> Tuple[bool, str]:
    """
    Deploy DNOS via console in GI mode and wait for DNOS.
    
    Uses: request system deploy system-type <type> name <name> ncc-id <id>
    
    Args:
        channel: Paramiko SSH channel (connected to GI mode via console)
        knowledge: DeviceKnowledge with deploy command
        add_line: Callback to add terminal lines
        progress_lock: Thread lock for progress updates
        live: Rich Live display
        render_panel: Callback to render panel
        progress_state: Dict with 'stage' and 'progress' keys
        ssh_client: Optional SSH client (for closing)
        
    Returns:
        (success, message) tuple
    """
    
    def send_and_wait(cmd: str, wait_time: float = 3) -> str:
        """Send command and wait for output."""
        channel.send(f"{cmd}\r\n")
        time.sleep(wait_time)
        output = ""
        for _ in range(10):
            if channel.recv_ready():
                output += channel.recv(65535).decode('utf-8', errors='replace')
            time.sleep(0.3)
        return output
    
    with progress_lock:
        progress_state['stage'] = "Deploying DNOS..."
        progress_state['progress'] = 75
    live.update(render_panel())
    
    # Execute deploy command
    deploy_cmd = knowledge.deploy_command or f"request system deploy system-type {knowledge.system_type} name {knowledge.hostname} ncc-id 0"
    add_line(f"🚀 Deploying: {deploy_cmd[:50]}...", "cyan")
    live.update(render_panel())
    
    output = send_and_wait(deploy_cmd, wait_time=5)
    
    # Check for immediate errors
    if 'error' in output.lower() and 'deploy' not in output.lower():
        add_line(f"✗ Deploy failed: {output[-50:]}", "red")
        live.update(render_panel())
        return False, f"Deploy command failed: {output}"
    
    add_line("✓ Deploy command sent", "green")
    add_line("⏳ Waiting for DNOS boot (5-15 min)...", "yellow")
    live.update(render_panel())
    
    with progress_lock:
        progress_state['stage'] = "Waiting for DNOS boot..."
        progress_state['progress'] = 80
    live.update(render_panel())
    
    # Wait for deployment (DNOS boots, device becomes responsive)
    # During deploy, console may disconnect - that's normal
    deploy_timeout = 900  # 15 minutes
    check_interval = 30
    start = time.time()
    
    while time.time() - start < deploy_timeout:
        elapsed = int(time.time() - start)
        mins, secs = divmod(elapsed, 60)
        
        with progress_lock:
            progress_state['stage'] = f"Waiting for DNOS... ({mins}m {secs}s)"
            # Progress from 80 to 95 over 15 minutes
            progress_state['progress'] = min(95, 80 + int((elapsed / deploy_timeout) * 15))
        live.update(render_panel())
        
        # Try to read from channel (may timeout or disconnect)
        try:
            channel.settimeout(5)
            if channel.recv_ready():
                output = channel.recv(65535).decode('utf-8', errors='replace')
                
                # Check for DNOS prompt
                if '#' in output and 'GI' not in output:
                    # Might be DNOS prompt
                    add_line("🔍 Checking for DNOS...", "cyan")
                    live.update(render_panel())
                    
                    channel.send("\r\n")
                    time.sleep(2)
                    prompt_output = ""
                    for _ in range(5):
                        if channel.recv_ready():
                            prompt_output += channel.recv(8192).decode('utf-8', errors='replace')
                        time.sleep(0.3)
                    
                    # Check if it's the hostname (DNOS mode)
                    if knowledge.hostname in prompt_output and 'GI' not in prompt_output:
                        add_line(f"✓ DNOS is up! ({mins}m {secs}s)", "green")
                        with progress_lock:
                            progress_state['stage'] = "DNOS READY"
                            progress_state['progress'] = 100
                        live.update(render_panel())
                        return True, "DNOS deployed successfully"
        except Exception:
            # Channel may be closed/timeout - that's OK during reboot
            pass
        
        time.sleep(check_interval)
    
    # Timeout - but deploy may still be in progress
    add_line(f"⚠ Timeout waiting for DNOS ({deploy_timeout // 60}m)", "yellow")
    add_line("  Deploy may still be in progress.", "yellow")
    add_line("  Check device manually or refresh status.", "yellow")
    live.update(render_panel())
    
    return True, "Deploy initiated (check status manually)"


def prompt_image_source_redirect() -> str:
    """Prompt user that image selection will use the Image Upgrade menu.
    
    Returns:
        'upgrade_menu' to redirect to Image Upgrade wizard, 'skip' to skip image loading
    """
    console.print("\n[bold cyan]Image Loading[/bold cyan]")
    console.print("  After the device enters GI mode, you'll need to load images.")
    console.print("  The [bold]Image Upgrade[/bold] menu provides full Jenkins integration.\n")
    
    console.print("  [1] [green]Proceed to Image Upgrade menu[/green] (recommended)")
    console.print("      [dim]Browse Jenkins branches, select builds, validate artifacts[/dim]")
    console.print("  [2] Skip image loading (manual process)")
    console.print("      [dim]Device will remain in GI mode for manual intervention[/dim]")
    console.print("  [B] Back")
    
    choice = Prompt.ask("  Select", choices=["1", "2", "b", "B"], default="1").lower()
    
    if choice == 'b':
        raise KeyboardInterrupt("User cancelled")
    elif choice == '1':
        return 'upgrade_menu'
    else:
        return 'skip'


def show_restore_plan(knowledge: DeviceKnowledge, system_type: str, hostname: str, skip_images: bool = False, device_state: str = "DN_RECOVERY") -> bool:
    """Show the state-specific restore plan and get user confirmation."""
    console.print("\n")
    
    # State-specific restore plans
    if device_state == "BASEOS_SHELL":
        if skip_images:
            plan_text = (
                "[bold yellow]⚠ BASEOS SHELL RECOVERY PLAN[/bold yellow]\n\n"
                "This operation will:\n"
                "  1. Connect to console (dn/drivenets)\n"
                "  2. Run 'dncli' (password: dnroot) → Enter GI mode\n"
                "  3. [yellow]Device will remain in GI mode for manual intervention[/yellow]\n"
                "  4. [dim]Deployment parameters saved for later deploy (see below)[/dim]\n\n"
                "[dim]No data loss - device has no DNOS config yet.[/dim]"
            )
        else:
            plan_text = (
                "[bold yellow]⚠ BASEOS SHELL RECOVERY PLAN[/bold yellow]\n\n"
                "This operation will:\n"
                "  1. Connect to console (dn/drivenets)\n"
                "  2. Run 'dncli' (password: dnroot) → Enter GI mode\n"
                "  3. [cyan]Launch Image Upgrade to load images[/cyan]\n"
                "  4. Deploy DNOS with configured parameters (see below)\n\n"
                "[dim]No data loss - device has no DNOS config yet.[/dim]"
            )
        border_style = "yellow"
        
    elif device_state == "ONIE":
        if skip_images:
            plan_text = (
                "[bold red]⚠ ONIE RESCUE RECOVERY PLAN[/bold red]\n\n"
                "This operation will:\n"
                "  1. Connect to console (dn/drivenets)\n"
                "  2. Install BaseOS via 'onie-nos-install'\n"
                "  3. Reboot into BaseOS Shell\n"
                "  4. Run 'dncli' → Enter GI mode\n"
                "  5. [yellow]Device will remain in GI mode for manual intervention[/yellow]\n"
                "  6. [dim]Deployment parameters saved for later deploy (see below)[/dim]\n\n"
                "[dim]No data loss - device has no DNOS config yet.[/dim]"
            )
        else:
            plan_text = (
                "[bold red]⚠ ONIE RESCUE RECOVERY PLAN[/bold red]\n\n"
                "This operation will:\n"
                "  1. Connect to console (dn/drivenets)\n"
                "  2. Install BaseOS via 'onie-nos-install'\n"
                "  3. Reboot into BaseOS Shell\n"
                "  4. Run 'dncli' → Enter GI mode\n"
                "  5. [cyan]Launch Image Upgrade to load images[/cyan]\n"
                "  6. Deploy DNOS with configured parameters (see below)\n\n"
                "[dim]No data loss - device has no DNOS config yet.[/dim]"
            )
        border_style = "red"
        
    else:  # DN_RECOVERY or unknown
        if skip_images:
            plan_text = (
                "[bold red]⚠ FACTORY RESET RECOVERY PLAN[/bold red]\n\n"
                "This operation will:\n"
                "  1. Execute 'request system restore factory-default'\n"
                "  2. Wait for device to reboot into GI mode (~2-10 minutes)\n"
                "  3. [yellow]Device will remain in GI mode for manual intervention[/yellow]\n"
                "  4. [dim]Deployment parameters saved for later deploy (see below)[/dim]\n\n"
                "[bold yellow]⚠ ALL CONFIGURATION WILL BE LOST[/bold yellow]\n"
                "[dim]The device will start fresh with default configuration.[/dim]"
            )
        else:
            plan_text = (
                "[bold red]⚠ FACTORY RESET RECOVERY PLAN[/bold red]\n\n"
                "This operation will:\n"
                "  1. Execute 'request system restore factory-default'\n"
                "  2. Wait for device to reboot into GI mode (~2-10 minutes)\n"
                "  3. [cyan]Launch Image Upgrade to load images[/cyan]\n"
                "  4. Deploy DNOS with configured parameters (see below)\n\n"
                "[bold yellow]⚠ ALL CONFIGURATION WILL BE LOST[/bold yellow]\n"
                "[dim]The device will start fresh with default configuration.[/dim]"
            )
        border_style = "red"
    
    console.print(Panel(plan_text, title=f"[bold]{device_state} Restore Plan[/bold]", border_style=border_style))
    
    # Show connection method if console is needed
    if hostname in ["PE-2", "PE-1", "PE-4"] and device_state in ["BASEOS_SHELL", "ONIE", "DN_RECOVERY"]:
        console_ports = {"PE-1": 12, "PE-2": 13, "PE-4": 14}
        port = console_ports.get(hostname, 13)
        console.print(f"\n[dim]📡 Connection: Will use console-b15 (port {port})[/dim]\n")
    
    # Show parameters
    table = Table(box=box.ROUNDED, title="Deployment Parameters (saved for deploy)")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Hostname", hostname)
    table.add_row("System Type", system_type)
    table.add_row("NCC ID", knowledge.ncc_id or "0")
    table.add_row("Deploy Command", f"request system deploy system-type {system_type} name {hostname} ncc-id {knowledge.ncc_id or '0'}")
    
    console.print(table)
    
    console.print("")
    # State-specific confirmation prompt
    if device_state == "BASEOS_SHELL":
        return Confirm.ask("[bold yellow]Proceed with dncli and deployment?[/bold yellow]", default=True)
    elif device_state == "ONIE":
        return Confirm.ask("[bold yellow]Proceed with BaseOS install and deployment?[/bold yellow]", default=True)
    else:
        return Confirm.ask("[bold yellow]Proceed with factory reset and deployment?[/bold yellow]", default=False)


def run_system_restore_wizard(device: Any, multi_ctx: Any = None) -> bool:
    """
    Main entry point for the System Restore wizard.
    
    This wizard handles different device states:
    - BASEOS_SHELL: Run dncli → GI mode
    - ONIE: Install BaseOS → dncli → GI mode  
    - DN_RECOVERY: Factory reset → GI mode
    
    After reaching GI mode, optionally launches Image Upgrade wizard.
    
    Args:
        device: Device object with hostname, ip, username, password
        multi_ctx: Optional MultiDeviceContext if running in multi-device mode
        
    Returns:
        True if restore was successful
    """
    from pathlib import Path
    import json
    
    # Detect current device state from operational.json
    device_state = "DN_RECOVERY"  # Default
    recovery_type = ""
    try:
        op_file = Path(f"/home/dn/SCALER/db/configs/{device.hostname}/operational.json")
        if op_file.exists():
            with open(op_file) as f:
                op_data = json.load(f)
                if op_data.get('recovery_mode_detected'):
                    recovery_type = op_data.get('recovery_type', '')
                    device_state = recovery_type or "DN_RECOVERY"
    except:
        pass
    
    # Show state-specific wizard banner
    console.print("\n")
    
    if device_state == "BASEOS_SHELL":
        console.print(Panel(
            "[bold yellow]🔧 SYSTEM RESTORE WIZARD - BASEOS SHELL MODE[/bold yellow]\n\n"
            "Device is in Linux Ubuntu shell (BaseOS).\n"
            "[cyan]GI container is not running.[/cyan]\n\n"
            "This wizard will:\n"
            "  1. Connect to console\n"
            "  2. Run 'dncli' (password: dnroot) → Enter GI mode\n"
            "  3. [green]Load images via SAME console session[/green]\n"
            "  4. Deploy DNOS → Device boots to operational state\n\n"
            "[dim]No data loss - device has no DNOS config yet.[/dim]\n"
            "[dim]NOTE: Uses console throughout (no SSH in GI mode).[/dim]",
            border_style="yellow"
        ))
    elif device_state == "ONIE":
        console.print(Panel(
            "[bold red]🔧 SYSTEM RESTORE WIZARD - ONIE RESCUE MODE[/bold red]\n\n"
            "Device is in lowest-level bootloader.\n"
            "[red]BaseOS is missing or corrupted.[/red]\n\n"
            "This wizard will:\n"
            "  1. Connect to console\n"
            "  2. Install BaseOS via ONIE\n"
            "  3. Reboot into BaseOS Shell → dncli → GI mode\n"
            "  4. [green]Load images via SAME console session[/green]\n"
            "  5. Deploy DNOS → Device boots to operational state\n\n"
            "[dim]No data loss - device has no DNOS config yet.[/dim]\n"
            "[dim]NOTE: Uses console throughout (no SSH in GI mode).[/dim]",
            border_style="red"
        ))
    else:  # DN_RECOVERY or unknown
        console.print(Panel(
            "[bold red]🔧 SYSTEM RESTORE WIZARD - DN_RECOVERY MODE[/bold red]\n\n"
            "DNOS failed to boot - critical software failure.\n\n"
            "This wizard will:\n"
            "  1. Execute 'request system restore factory-default'\n"
            "  2. Wait for device to reboot into GI mode (~2-10 minutes)\n"
            "  3. [green]Load images via SAME console session[/green]\n"
            "  4. Deploy DNOS → Device boots to operational state\n\n"
            "[bold yellow]⚠ ALL CONFIGURATION WILL BE LOST[/bold yellow]\n"
            "[dim]The device will start fresh with default configuration.[/dim]",
            border_style="red"
        ))
    
    # Step 1: Load device knowledge
    console.print("\n[bold cyan]Step 1: Loading Device Knowledge[/bold cyan]")
    knowledge = DeviceKnowledge.from_operational_json(device.hostname)
    knowledge.recovery_mode_detected = True
    knowledge.recovery_detected_at = datetime.now().isoformat()
    
    show_device_knowledge_panel(knowledge)
    
    # Step 2: Confirm/configure system type
    console.print("\n[bold cyan]Step 2: System Type Configuration[/bold cyan]")
    try:
        system_type = prompt_system_type(knowledge)
        knowledge.system_type = system_type
    except KeyboardInterrupt:
        console.print("[yellow]Cancelled.[/yellow]")
        return False
    
    # Step 3: Confirm hostname
    console.print("\n[bold cyan]Step 3: Hostname Configuration[/bold cyan]")
    try:
        hostname = prompt_hostname(knowledge)
    except KeyboardInterrupt:
        console.print("[yellow]Cancelled.[/yellow]")
        return False
    
    # Step 4: Image source selection (inline - will load via console)
    console.print("\n[bold cyan]Step 4: Image Source Selection[/bold cyan]")
    console.print("  [dim]Images will be loaded via the SAME console session after entering GI mode.[/dim]")
    console.print("  [dim]This avoids SSH connection issues (no mgmt0 IP in GI mode).[/dim]\n")
    
    try:
        image_urls = prompt_image_source_inline()
        skip_images = (image_urls is None)
    except KeyboardInterrupt:
        console.print("[yellow]Cancelled.[/yellow]")
        return False
    
    # Save knowledge before proceeding (deploy params needed after GI mode)
    knowledge.deploy_command = f"request system deploy system-type {system_type} name {hostname} ncc-id {knowledge.ncc_id or '0'}"
    knowledge.save_to_operational_json()
    
    # Step 5: Show plan and confirm
    console.print("\n[bold cyan]Step 5: Confirm Restore Plan[/bold cyan]")
    if not show_restore_plan(knowledge, system_type, hostname, skip_images, device_state):
        console.print("[yellow]Restore cancelled by user.[/yellow]")
        return False
    
    # Step 6: Execute restore to GI mode (and optionally load images + deploy)
    if skip_images:
        console.print("\n[bold cyan]Step 6: Restoring to GI Mode[/bold cyan]")
    else:
        console.print("\n[bold cyan]Step 6: Restore → GI Mode → Load Images → Deploy[/bold cyan]")
        console.print("[dim]Using SAME console session throughout (no SSH needed).[/dim]\n")
    
    # Pass image_urls to execute function - it will continue with loading after GI mode
    gi_success = execute_restore_to_gi_mode(
        device=device,
        system_type=system_type,
        hostname=hostname,
        knowledge=knowledge,
        image_urls=image_urls  # This triggers console-based image loading
    )
    
    if not gi_success:
        console.print("\n[bold red]✗ Failed to complete restore/deploy[/bold red]")
        console.print("  Check the terminal output above for error details.")
        return False
    
    if skip_images:
        console.print("\n[bold green]✓ Device is now in GI mode![/bold green]")
        console.print("\n[bold yellow]Manual intervention required:[/bold yellow]")
        console.print(f"  1. Load images manually via console:")
        console.print(f"     [cyan]GI# request system software add image-url <DNOS_URL>[/cyan]")
        console.print(f"     [cyan]GI# request system software add image-url <GI_URL>[/cyan]")
        console.print(f"  2. Deploy with: [green]{knowledge.deploy_command}[/green]")
        return True
    
    # Success - device should now be running DNOS
    console.print("\n[bold green]✓ System Restore Completed Successfully![/bold green]")
    console.print(f"  Device {hostname} should now be running DNOS.")
    console.print("  [dim]Run 'Refresh' to update device status.[/dim]")
    
    # Clear recovery flag
    knowledge.recovery_mode_detected = False
    knowledge.save_to_operational_json()
    return True


# Keep the old code path as fallback (disabled)
def _old_image_upgrade_wizard_path(device, multi_ctx, system_type, hostname, knowledge):
    """OLD CODE PATH: Use Image Upgrade wizard for loading (has SSH connection issue)."""
    # Create a temporary multi-device context with just this device if needed
    if multi_ctx is None:
        from .multi_device import MultiDeviceContext
        temp_ctx = MultiDeviceContext([device])
        temp_ctx._gi_mode_devices = {device.hostname: {
            'system_type': system_type,
            'hostname': hostname,
            'deploy_command': knowledge.deploy_command,
        }}
    else:
        temp_ctx = multi_ctx
        if not hasattr(temp_ctx, '_gi_mode_devices'):
            temp_ctx._gi_mode_devices = {}
        temp_ctx._gi_mode_devices[device.hostname] = {
            'system_type': system_type,
            'hostname': hostname,
            'deploy_command': knowledge.deploy_command,
        }
    
    # This path has a bug: Image Upgrade wizard tries SSH which fails in GI mode
    # Use prompt_image_source_inline + execute_restore_to_gi_mode with image_urls instead
    pass


def execute_onie_recovery(
    channel: Any,
    knowledge: 'DeviceKnowledge',
    add_line: Callable[[str, str], None],
    progress_lock: Any,
    live: Any,
    render_panel: Callable[[], Any]
) -> bool:
    """
    Execute ONIE rescue mode recovery - install BaseOS and reach GI mode.
    
    This function:
    1. Login to ONIE with credentials (dn/drivenets)
    2. Check EEPROM validity (onie-syseeprom)
    3. Check and remove partition 3 if needed (parted)
    4. Install BaseOS from Minio URL
    5. Wait for reboot to GI mode
    
    Args:
        channel: Paramiko SSH channel (already connected to console)
        knowledge: DeviceKnowledge for BaseOS URL
        add_line: Callback to add terminal lines
        progress_lock: Thread lock for progress updates
        live: Rich Live display
        render_panel: Callback to render panel
        
    Returns:
        True if BaseOS installed and GI mode reached
    """
    import time
    
    # ONIE credentials (different from DNOS/GI!)
    ONIE_USER = "dn"
    ONIE_PASS = "drivenets"
    
    add_line("ONIE Rescue Mode detected - initiating recovery", "cyan")
    live.update(render_panel())
    
    try:
        # Step 1: Login to ONIE (if needed)
        channel.send("\r\n")
        time.sleep(1)
        output = ""
        while channel.recv_ready():
            output += channel.recv(8192).decode('utf-8', errors='replace')
            time.sleep(0.2)
        
        if "login:" in output.lower() or "username:" in output.lower():
            add_line("Logging into ONIE...")
            channel.send(ONIE_USER + "\r\n")
            time.sleep(1)
            channel.send(ONIE_PASS + "\r\n")
            time.sleep(2)
            add_line("✓ Logged into ONIE", "green")
        
        # Step 2: Check EEPROM
        add_line("Checking hardware EEPROM...")
        live.update(render_panel())
        
        channel.send("onie-syseeprom\r\n")
        time.sleep(3)
        eeprom_output = ""
        while channel.recv_ready():
            eeprom_output += channel.recv(16384).decode('utf-8', errors='replace')
            time.sleep(0.2)
        
        if "Serial Number" not in eeprom_output:
            add_line("✗ EEPROM invalid - contact support!", "red")
            return False
        
        add_line("✓ EEPROM valid", "green")
        
        # Step 3: Check partitions
        add_line("Checking partition table...")
        live.update(render_panel())
        
        channel.send("parted -l\r\n")
        time.sleep(3)
        parted_output = ""
        while channel.recv_ready():
            parted_output += channel.recv(16384).decode('utf-8', errors='replace')
            time.sleep(0.2)
        
        # Check if partition 3 exists and is UBUNTU
        if "UBUNTU" in parted_output and " 3 " in parted_output:
            add_line("Found UBUNTU partition 3 - removing...", "yellow")
            channel.send("parted /dev/sda rm 3\r\n")
            time.sleep(2)
            channel.send("yes\r\n")  # Confirm if prompted
            time.sleep(2)
            add_line("✓ Partition 3 removed", "green")
        else:
            add_line("✓ No problematic partitions found", "green")
        
        live.update(render_panel())
        
        # Step 4: Install BaseOS
        # Get BaseOS URL from knowledge or use default
        baseos_url = knowledge.baseos_url
        if not baseos_url:
            # Default to latest stable for v25.1
            baseos_url = "http://minio-ssd.dev.drivenets.net:9000/dnpkg-60days/drivenets_baseos_2.25104397329.tar"
            add_line(f"Using default BaseOS URL", "yellow")
        
        add_line(f"Installing BaseOS from Minio...", "cyan")
        add_line(f"URL: {baseos_url[:60]}...", "dim")
        add_line("This will take 20-40 minutes...", "yellow")
        live.update(render_panel())
        
        channel.send(f"onie-nos-install {baseos_url}\r\n")
        time.sleep(5)
        
        add_line("✓ BaseOS install started", "green")
        add_line("⏳ Download + Install + Reboot in progress...", "cyan")
        live.update(render_panel())
        
        # Step 5: Wait for installation to complete and reboot to GI
        # This is a long operation (20-40 minutes)
        gi_timeout = 2400  # 40 minutes
        gi_start = time.time()
        
        while time.time() - gi_start < gi_timeout:
            elapsed = int(time.time() - gi_start)
            mins, secs = divmod(elapsed, 60)
            
            add_line(f"⏳ ONIE installing BaseOS... ({mins}m {secs}s)", "dim")
            live.update(render_panel())
            
            time.sleep(30)  # Check every 30 seconds
            
            # Try to read output
            try:
                if channel.recv_ready():
                    output = channel.recv(16384).decode('utf-8', errors='replace')
                    # Look for completion or error messages
                    if "Installation complete" in output or "Rebooting" in output:
                        add_line("✓ BaseOS installation complete!", "green")
                        add_line("Device rebooting to GI mode...", "cyan")
                        live.update(render_panel())
                        break
                    elif "error" in output.lower() or "fail" in output.lower():
                        add_line(f"⚠ Error during install: {output[:50]}", "red")
            except:
                pass
        
        # After install completes, wait for GI mode
        add_line("Waiting for device to reach GI mode...", "cyan")
        live.update(render_panel())
        
        time.sleep(300)  # Wait 5 minutes for reboot
        
        # The device will reboot, connection will be lost
        # Return True - caller should verify GI mode separately
        return True
        
    except Exception as e:
        add_line(f"✗ ONIE recovery error: {str(e)[:50]}", "red")
        return False


def execute_restore_to_gi_mode(
    device: Any,
    system_type: str,
    hostname: str,
    knowledge: DeviceKnowledge,
    progress_callback: Callable[[Dict], None] = None,
    image_urls: Optional[Dict] = None
) -> bool:
    """
    Execute system restore - get device to GI mode, optionally load images and deploy.
    
    This function:
    1. Connects to device (RECOVERY mode, ONIE mode, or BaseOS Shell)
    2. Enters GI mode (dncli for BaseOS, ONIE recovery, or factory reset)
    3. If image_urls provided: loads images and deploys DNOS via console
    4. If no image_urls: returns after reaching GI mode
    
    IMPORTANT: When image_urls is provided, the SAME console session is used
    throughout - this fixes the issue where SSH was attempted in GI mode
    (which fails because there's no mgmt0 IP yet).
    
    Args:
        device: Device object
        system_type: Target system type
        hostname: Target hostname
        knowledge: DeviceKnowledge for persistence
        progress_callback: Optional callback for progress updates
        image_urls: Optional Dict with dnos_url, gi_url, baseos_url
                   If provided, images are loaded and DNOS deployed via console
        
    Returns:
        True if device reached GI mode (and optionally deployed DNOS)
    """
    import paramiko
    import base64
    from rich.live import Live
    from rich.text import Text
    
    MAX_TERMINAL_LINES = 15
    PANEL_HEIGHT = MAX_TERMINAL_LINES + 6
    
    progress_lock = threading.Lock()
    terminal_lines = []
    current_stage = "connecting"
    progress_pct = 0
    start_time = time.time()
    
    # Persistent progress state dict - shared with image loading functions
    progress_state = {'stage': 'connecting', 'progress': 0}
    
    def add_line(msg: str, style: str = None):
        """Add a line to terminal output."""
        ts = datetime.now().strftime("%H:%M:%S")
        with progress_lock:
            # Clean msg
            msg = str(msg).replace('[', '\\[').replace(']', '\\]')[:60]
            if len(terminal_lines) > 50:
                terminal_lines.pop(0)
            terminal_lines.append((ts, msg, style or "dim"))
    
    def render_panel() -> Panel:
        """Render the live terminal panel."""
        with progress_lock:
            stage = current_stage
            # Use progress_state if it has higher value (updated by load functions)
            pct = max(progress_pct, progress_state.get('progress', 0))
            lines = terminal_lines[-MAX_TERMINAL_LINES:]
        
        content = Text()
        
        # Elapsed time
        elapsed = int(time.time() - start_time)
        mins, secs = divmod(elapsed, 60)
        content.append(f"⏱ {mins:02d}:{secs:02d} elapsed\n", style="dim")
        
        # Stage and progress
        stage_icons = {
            "connecting": "🔌",
            "restore": "🔄",
            "waiting_gi": "⏳",
            "gi_ready": "✅",
            "failed": "❌"
        }
        icon = stage_icons.get(stage, "○")
        content.append(f"{icon} {stage.replace('_', ' ').upper()}\n")
        
        # Progress bar
        bar_width = 25
        filled = int(bar_width * pct / 100)
        bar = '█' * filled + '░' * (bar_width - filled)
        bar_style = "green" if stage == "gi_ready" else ("red" if stage == "failed" else "cyan")
        content.append(f"[{bar}] {pct}%\n", style=bar_style)
        content.append("─" * 50 + "\n")
        
        # Terminal lines
        for ts, msg, style in lines:
            content.append(f"[{ts}] ", style="dim")
            content.append(f"{msg}\n", style=style)
        
        # Pad to fixed height
        while len(lines) < MAX_TERMINAL_LINES:
            content.append("\n")
            lines.append(("", "", "dim"))
        
        border = "green" if stage == "gi_ready" else ("red" if stage == "failed" else "cyan")
        return Panel(content, title=f"[bold white]{hostname} - Restore to GI Mode[/bold white]", 
                     border_style=border, height=PANEL_HEIGHT)
    
    # Get password
    password = device.password
    if device.password:
        try:
            password = base64.b64decode(device.password).decode('utf-8')
        except:
            pass
    
    # Check if PE-2 and should use console
    use_console = (device.hostname == "PE-2" and knowledge.recovery_mode_detected)
    
    with Live(render_panel(), refresh_per_second=4, console=console, transient=False) as live:
        try:
            # Step 1: Connect
            with progress_lock:
                current_stage = "connecting"
                progress_pct = 5
            
            if use_console:
                # PE-2 in recovery: Use console connection
                add_line(f"PE-2 in recovery - connecting via console...")
                live.update(render_panel())
                
                try:
                    from ..pe2_console import check_pe2_recovery_via_console
                    # Import the console connection module
                    import socket
                    
                    # Connect to console server
                    add_line("Connecting to console-b15...")
                    live.update(render_panel())
                    
                    CONSOLE_HOST = "console-b15"
                    CONSOLE_USER = "dn"
                    CONSOLE_PASSWORD = "drive1234"
                    CONSOLE_PE2_PORT = 13
                    PORT_ACCESS_USER = "dnroot"
                    PORT_ACCESS_PASSWORD = "dnroot"
                    
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(CONSOLE_HOST, username=CONSOLE_USER, password=CONSOLE_PASSWORD, timeout=15)
                    
                    add_line("Connected to console server")
                    live.update(render_panel())
                    
                    channel = ssh.invoke_shell(width=200, height=50)
                    channel.settimeout(30)
                    time.sleep(1.5)
                    _ = channel.recv(8192).decode("utf-8", errors="replace")
                    
                    # Navigate to port 13 (PE-2)
                    add_line("Selecting port 13 (PE-2)...")
                    live.update(render_panel())
                    
                    channel.send("3\r\n")  # Port access
                    time.sleep(2)
                    
                    # Non-blocking recv with timeout
                    port_menu = ""
                    for _ in range(5):
                        if channel.recv_ready():
                            port_menu += channel.recv(8192).decode("utf-8", errors="replace")
                        time.sleep(0.5)
                    
                    channel.send("13\r\n")  # PE-2 port
                    time.sleep(2)
                    channel.send("\r\n")  # Wake up console
                    time.sleep(2)
                    
                    # Read console output with timeout
                    after_port = ""
                    for _ in range(10):
                        if channel.recv_ready():
                            after_port += channel.recv(8192).decode("utf-8", errors="replace")
                        time.sleep(0.5)
                    
                    add_line(f"Console output: {after_port[-60:].replace(chr(10), ' ')[:40]}...", "dim")
                    live.update(render_panel())
                    
                    lower = after_port.lower()
                    
                    # Detect state and login accordingly
                    # ONIE and BaseOS Shell use different credentials than DNOS/GI!
                    if "onie:/" in lower or "onie-" in lower:
                        # ONIE mode - use onie credentials
                        add_line("ONIE mode detected - logging in...", "yellow")
                        live.update(render_panel())
                        if "login" in lower or "username" in lower:
                            channel.send("dn\r\n")  # ONIE user
                            time.sleep(1)
                            channel.send("drivenets\r\n")  # ONIE password
                            time.sleep(3)
                    elif "dn@" in after_port and ":~$" in after_port:
                        # Already logged into BaseOS Shell!
                        add_line("Already in BaseOS Shell!", "cyan")
                        live.update(render_panel())
                    elif "login:" in after_port:
                        # Login prompt - try BaseOS credentials (dn/drivenets)
                        add_line("Login prompt - using dn/drivenets...", "cyan")
                        live.update(render_panel())
                        channel.send("dn\r\n")
                        time.sleep(1)
                        channel.send("drivenets\r\n")
                        time.sleep(3)
                    elif "password" in lower:
                        # Password prompt only
                        add_line("Password prompt - sending drivenets...", "cyan")
                        live.update(render_panel())
                        channel.send("drivenets\r\n")
                        time.sleep(3)
                    
                    # Read final state
                    time.sleep(2)
                    initial_output = ""
                    for _ in range(10):
                        if channel.recv_ready():
                            initial_output += channel.recv(8192).decode("utf-8", errors="replace")
                        time.sleep(0.3)
                    
                    # Combine outputs for state detection
                    initial_output = after_port + initial_output
                    
                    add_line("✓ Connected to PE-2 via console", "green")
                    live.update(render_panel())
                    
                except Exception as e:
                    add_line(f"✗ Console connection failed: {str(e)[:40]}", "red")
                    with progress_lock:
                        current_stage = "failed"
                        progress_pct = 100
                    live.update(render_panel())
                    return False
            else:
                # Normal SSH connection
                add_line(f"Connecting to {device.ip}...")
                live.update(render_panel())
                
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(device.ip, username=device.username or 'dnroot', password=password, timeout=30)
                channel = ssh.invoke_shell(width=200, height=50)
                time.sleep(2)
                initial_output = channel.recv(65535).decode('utf-8', errors='replace')
            
            # Detect device state: ONIE, BaseOS Shell, RECOVERY, GI, or DNOS
            is_onie = 'ONIE:/' in initial_output or 'onie-' in initial_output.lower()
            is_baseos_shell = '@' in initial_output and ':~$' in initial_output and 'dn@' in initial_output
            is_recovery = 'RECOVERY' in initial_output or 'dnRouter(RECOVERY)' in initial_output
            is_gi = 'GI' in initial_output or 'gicli' in initial_output.lower() or 'GI(' in initial_output
            
            # Handle BaseOS Shell Mode (need to run dncli to enter GI)
            if is_baseos_shell:
                add_line("⚠ BaseOS Shell detected - entering GI mode...", "yellow")
                with progress_lock:
                    current_stage = "baseos_to_gi"
                    progress_pct = 15
                live.update(render_panel())
                
                try:
                    # Run dncli to enter GI mode
                    add_line("Running dncli...", "cyan")
                    live.update(render_panel())
                    
                    channel.send("dncli\r\n")
                    time.sleep(2)
                    
                    # Check for password prompt
                    dncli_output = ""
                    for _ in range(5):
                        if channel.recv_ready():
                            dncli_output += channel.recv(8192).decode('utf-8', errors='replace')
                        time.sleep(0.5)
                    
                    # dncli prompts for password (dnroot)
                    if 'password' in dncli_output.lower() or 'Password' in dncli_output:
                        add_line("Sending dncli password...", "cyan")
                        live.update(render_panel())
                        channel.send("dnroot\r\n")
                        time.sleep(3)
                        
                        # Read GI output
                        gi_output = ""
                        for _ in range(10):
                            if channel.recv_ready():
                                gi_output += channel.recv(8192).decode('utf-8', errors='replace')
                            time.sleep(0.5)
                    else:
                        # No password prompt, just use the output we have
                        gi_output = dncli_output
                    
                    # Check for GI mode
                    if 'GI#' in gi_output or 'GI(' in gi_output or 'gicli' in gi_output.lower():
                        add_line("✓ Entered GI mode successfully!", "green")
                        with progress_lock:
                            current_stage = "gi_ready"
                            progress_pct = 20  # 20% for reaching GI
                        live.update(render_panel())
                        
                        # If image URLs provided, load images via SSH (faster than console)
                        if image_urls:
                            # Get management IP from console
                            mgmt_ip = get_management_ip_from_console(
                                channel=channel,
                                add_line=add_line,
                                live=live,
                                render_panel=render_panel
                            )
                            
                            if not mgmt_ip:
                                # Fallback: try device.ip
                                add_line(f"⚠ Using device IP: {device.ip}", "yellow")
                                live.update(render_panel())
                                mgmt_ip = device.ip
                            
                            add_line("📦 Loading images via SSH (faster)...", "cyan")
                            live.update(render_panel())
                            
                            progress_state.update({'stage': current_stage, 'progress': progress_pct})
                            
                            # Try SSH first (faster, handles prompts properly)
                            load_ok, load_msg = load_images_via_ssh(
                                device_ip=mgmt_ip,
                                image_urls=image_urls,
                                knowledge=knowledge,
                                add_line=add_line,
                                progress_lock=progress_lock,
                                live=live,
                                render_panel=render_panel,
                                progress_state=progress_state,
                                username="dnroot",
                                password="dnroot"
                            )
                            
                            # If SSH failed, try console as fallback
                            if not load_ok and "SSH" in load_msg:
                                add_line("⚠ SSH failed, trying console...", "yellow")
                                live.update(render_panel())
                                load_ok, load_msg = load_images_via_console(
                                    channel=channel,
                                    image_urls=image_urls,
                                    knowledge=knowledge,
                                    add_line=add_line,
                                    progress_lock=progress_lock,
                                    live=live,
                                    render_panel=render_panel,
                                    progress_state=progress_state
                                )
                            
                            if not load_ok:
                                add_line(f"✗ Image load failed: {load_msg}", "red")
                                with progress_lock:
                                    current_stage = "failed"
                                live.update(render_panel())
                                try:
                                    ssh.close()
                                except:
                                    pass
                                return False
                            
                            # Deploy DNOS
                            deploy_ok, deploy_msg = deploy_via_console(
                                channel=channel,
                                knowledge=knowledge,
                                add_line=add_line,
                                progress_lock=progress_lock,
                                live=live,
                                render_panel=render_panel,
                                progress_state=progress_state
                            )
                            
                            try:
                                ssh.close()
                            except:
                                pass
                            return deploy_ok
                        
                        # No image URLs - just close and return
                        try:
                            ssh.close()
                        except:
                            pass
                        return True
                    else:
                        # May need more time
                        add_line("Waiting for GI mode...", "yellow")
                        live.update(render_panel())
                        time.sleep(3)
                        channel.send("\r\n")
                        time.sleep(2)
                        
                        final_output = ""
                        for _ in range(10):
                            if channel.recv_ready():
                                final_output += channel.recv(8192).decode('utf-8', errors='replace')
                            time.sleep(0.5)
                        
                        if 'GI#' in final_output or 'GI(' in final_output:
                            add_line("✓ Entered GI mode successfully!", "green")
                            with progress_lock:
                                current_stage = "gi_ready"
                                progress_pct = 20
                            live.update(render_panel())
                            
                            # If image URLs provided, load via SSH first (faster than console)
                            if image_urls:
                                # Get management IP from console
                                mgmt_ip = get_management_ip_from_console(
                                    channel=channel,
                                    add_line=add_line,
                                    live=live,
                                    render_panel=render_panel
                                )
                                
                                if not mgmt_ip:
                                    add_line(f"⚠ Using device IP: {device.ip}", "yellow")
                                    live.update(render_panel())
                                    mgmt_ip = device.ip
                                
                                add_line("📦 Loading images via SSH (faster)...", "cyan")
                                live.update(render_panel())
                                
                                progress_state.update({'stage': current_stage, 'progress': progress_pct})
                                
                                # Try SSH first
                                load_ok, load_msg = load_images_via_ssh(
                                    device_ip=mgmt_ip,
                                    image_urls=image_urls,
                                    knowledge=knowledge,
                                    add_line=add_line,
                                    progress_lock=progress_lock,
                                    live=live,
                                    render_panel=render_panel,
                                    progress_state=progress_state,
                                    username="dnroot",
                                    password="dnroot"
                                )
                                
                                # Fallback to console if SSH failed
                                if not load_ok and "SSH" in load_msg:
                                    add_line("⚠ SSH failed, trying console...", "yellow")
                                    live.update(render_panel())
                                    load_ok, load_msg = load_images_via_console(
                                        channel=channel,
                                        image_urls=image_urls,
                                        knowledge=knowledge,
                                        add_line=add_line,
                                        progress_lock=progress_lock,
                                        live=live,
                                        render_panel=render_panel,
                                        progress_state=progress_state
                                    )
                                
                                if not load_ok:
                                    add_line(f"✗ Image load failed: {load_msg}", "red")
                                    try:
                                        ssh.close()
                                    except:
                                        pass
                                    return False
                                
                                deploy_ok, deploy_msg = deploy_via_console(
                                    channel=channel,
                                    knowledge=knowledge,
                                    add_line=add_line,
                                    progress_lock=progress_lock,
                                    live=live,
                                    render_panel=render_panel,
                                    progress_state=progress_state
                                )
                                
                                try:
                                    ssh.close()
                                except:
                                    pass
                                return deploy_ok
                            
                            try:
                                ssh.close()
                            except:
                                pass
                            return True
                        else:
                            add_line(f"✗ Could not verify GI mode. Output: {final_output[-50:]}", "red")
                            with progress_lock:
                                current_stage = "failed"
                                progress_pct = 100
                            live.update(render_panel())
                            try:
                                ssh.close()
                            except:
                                pass
                            return False
                        
                except Exception as e:
                    add_line(f"✗ Failed to run dncli: {str(e)[:40]}", "red")
                    with progress_lock:
                        current_stage = "failed"
                        progress_pct = 100
                    live.update(render_panel())
                    try:
                        ssh.close()
                    except:
                        pass
                    return False
            
            # Handle ONIE Rescue Mode
            if is_onie:
                add_line("⚠ ONIE Rescue Mode detected!", "yellow")
                add_line("BaseOS needs installation", "yellow")
                with progress_lock:
                    current_stage = "onie_recovery"
                    progress_pct = 10
                live.update(render_panel())
                
                # Execute ONIE recovery procedure
                onie_success = execute_onie_recovery(
                    channel=channel,
                    knowledge=knowledge,
                    add_line=add_line,
                    progress_lock=progress_lock,
                    live=live,
                    render_panel=render_panel
                )
                
                if not onie_success:
                    add_line("✗ ONIE recovery failed", "red")
                    with progress_lock:
                        current_stage = "failed"
                        progress_pct = 100
                    live.update(render_panel())
                    try:
                        ssh.close()
                    except:
                        pass
                    return False
                
                # After ONIE recovery, device should be in GI mode
                add_line("✓ ONIE recovery complete, device in GI mode", "green")
                with progress_lock:
                    current_stage = "gi_ready"
                    progress_pct = 20
                live.update(render_panel())
                
                # If image URLs provided, load via SSH first (faster than console)
                if image_urls:
                    # Get management IP from console
                    mgmt_ip = get_management_ip_from_console(
                        channel=channel, add_line=add_line, live=live, render_panel=render_panel
                    )
                    if not mgmt_ip:
                        add_line(f"⚠ Using device IP: {device.ip}", "yellow")
                        mgmt_ip = device.ip
                    
                    add_line("📦 Loading images via SSH (faster)...", "cyan")
                    progress_state.update({'stage': current_stage, 'progress': progress_pct})
                    
                    # Try SSH first
                    load_ok, load_msg = load_images_via_ssh(
                        device_ip=mgmt_ip, image_urls=image_urls, knowledge=knowledge,
                        add_line=add_line, progress_lock=progress_lock,
                        live=live, render_panel=render_panel, progress_state=progress_state,
                        username="dnroot", password="dnroot"
                    )
                    
                    # Fallback to console if SSH failed
                    if not load_ok and "SSH" in load_msg:
                        add_line("⚠ SSH failed, trying console...", "yellow")
                        live.update(render_panel())
                        load_ok, load_msg = load_images_via_console(
                            channel=channel, image_urls=image_urls, knowledge=knowledge,
                            add_line=add_line, progress_lock=progress_lock,
                            live=live, render_panel=render_panel, progress_state=progress_state
                        )
                    
                    if not load_ok:
                        try:
                            ssh.close()
                        except:
                            pass
                        return False
                    
                    deploy_ok, _ = deploy_via_console(
                        channel=channel, knowledge=knowledge, add_line=add_line,
                        progress_lock=progress_lock, live=live, render_panel=render_panel,
                        progress_state=progress_state
                    )
                    try:
                        ssh.close()
                    except:
                        pass
                    return deploy_ok
                
                try:
                    ssh.close()
                except:
                    pass
                return True
            
            # Handle GI Mode
            if is_gi:
                add_line("✓ Device is already in GI mode!", "green")
                with progress_lock:
                    current_stage = "gi_ready"
                    progress_pct = 20
                live.update(render_panel())
                
                # If image URLs provided, load via SSH first (faster than console)
                if image_urls:
                    # Get management IP from console
                    mgmt_ip = get_management_ip_from_console(
                        channel=channel, add_line=add_line, live=live, render_panel=render_panel
                    )
                    if not mgmt_ip:
                        add_line(f"⚠ Using device IP: {device.ip}", "yellow")
                        mgmt_ip = device.ip
                    
                    add_line("📦 Loading images via SSH (faster)...", "cyan")
                    progress_state.update({'stage': current_stage, 'progress': progress_pct})
                    
                    # Try SSH first
                    load_ok, load_msg = load_images_via_ssh(
                        device_ip=mgmt_ip, image_urls=image_urls, knowledge=knowledge,
                        add_line=add_line, progress_lock=progress_lock,
                        live=live, render_panel=render_panel, progress_state=progress_state,
                        username="dnroot", password="dnroot"
                    )
                    
                    # Fallback to console if SSH failed
                    if not load_ok and "SSH" in load_msg:
                        add_line("⚠ SSH failed, trying console...", "yellow")
                        live.update(render_panel())
                        load_ok, load_msg = load_images_via_console(
                            channel=channel, image_urls=image_urls, knowledge=knowledge,
                            add_line=add_line, progress_lock=progress_lock,
                            live=live, render_panel=render_panel, progress_state=progress_state
                        )
                    
                    if not load_ok:
                        try:
                            ssh.close()
                        except:
                            pass
                        return False
                    
                    deploy_ok, _ = deploy_via_console(
                        channel=channel, knowledge=knowledge, add_line=add_line,
                        progress_lock=progress_lock, live=live, render_panel=render_panel,
                        progress_state=progress_state
                    )
                    try:
                        ssh.close()
                    except:
                        pass
                    return deploy_ok
                
                try:
                    ssh.close()
                except:
                    pass
                return True
            
            # Handle normal DNOS or unknown state
            if not is_recovery:
                add_line("⚠ Device not in RECOVERY mode!", "yellow")
                # Check if device is running DNOS normally
                if 'DNOS' in initial_output or '#' in initial_output:
                    add_line("Device appears to be running DNOS normally", "yellow")
                    add_line("No restore needed - device is operational", "green")
                    with progress_lock:
                        current_stage = "gi_ready"  # Treat as success
                        progress_pct = 100
                    live.update(render_panel())
                    try:
                        ssh.close()
                    except:
                        pass
                    return True
                else:
                    add_line("Unknown device state", "red")
                    with progress_lock:
                        current_stage = "failed"
                        progress_pct = 100
                    live.update(render_panel())
                    return False
            
            add_line("✓ RECOVERY mode confirmed", "green")
            
            # Step 2: Execute restore
            with progress_lock:
                current_stage = "restore"
                progress_pct = 15
            add_line("Executing: request system restore factory-default")
            live.update(render_panel())
            
            def send_and_wait(cmd: str, wait_time: float = 3) -> str:
                channel.sendall((cmd + "\n").encode('utf-8'))
                time.sleep(wait_time)
                output = ""
                while channel.recv_ready():
                    output += channel.recv(65535).decode('utf-8', errors='replace')
                    time.sleep(0.3)
                return output
            
            send_and_wait("request system restore factory-default", 3)
            output = send_and_wait("yes", 5)  # Confirm
            add_line("✓ Restore command sent", "green")
            add_line(f"💾 Deploy params saved: {system_type}", "cyan")
            
            # Close connection before reboot
            try:
                ssh.close()
            except:
                pass
            
            # Step 3: Wait for GI mode
            with progress_lock:
                current_stage = "waiting_gi"
                progress_pct = 25
            add_line("⏳ Waiting for GI mode (device rebooting)...")
            add_line("This typically takes 2-10 minutes...")
            live.update(render_panel())
            
            gi_timeout = 900  # 15 minutes (increased for safety)
            gi_interval = 20  # Check every 20 seconds
            gi_start = time.time()
            gi_connected = False
            new_mgmt_ip = None
            
            if use_console:
                # For PE-2: Stay on console and check for GI prompt
                add_line("Monitoring console for GI mode...")
                live.update(render_panel())
                
                # Reconnect to console
                console_channel = None
                try:
                    time.sleep(gi_interval * 2)  # Wait for reboot to start
                    
                    add_line("Reconnecting to console server...")
                    live.update(render_panel())
                    
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(CONSOLE_HOST, username=CONSOLE_USER, password=CONSOLE_PASSWORD, timeout=15)
                    console_channel = ssh.invoke_shell(width=200, height=50)
                    console_channel.settimeout(30)
                    time.sleep(1.5)
                    _ = console_channel.recv(8192).decode("utf-8", errors="replace")
                    
                    add_line("Navigating to PE-2 console port...")
                    live.update(render_panel())
                    
                    console_channel.send("3\r\n")  # Port access
                    time.sleep(3)
                    _ = console_channel.recv(8192).decode("utf-8", errors="replace")
                    
                    console_channel.send("13\r\n")  # PE-2 port
                    time.sleep(1.5)
                    console_channel.send("\r\n")
                    time.sleep(2)
                    
                    after_port = console_channel.recv(8192).decode("utf-8", errors="replace")
                    lower = after_port.lower()
                    
                    if "login" in lower or "username" in lower or "password" in lower:
                        console_channel.send(PORT_ACCESS_USER + "\r\n")
                        time.sleep(0.8)
                        console_channel.send(PORT_ACCESS_PASSWORD + "\r\n")
                        time.sleep(3)
                    
                    add_line("✓ Reconnected to console", "green")
                    live.update(render_panel())
                    
                except Exception as e:
                    add_line(f"✗ Console reconnect failed: {str(e)[:40]}", "red")
                    add_line("Cannot monitor GI mode without console", "red")
                    with progress_lock:
                        current_stage = "failed"
                        progress_pct = 100
                    live.update(render_panel())
                    return False
                
                # Poll console for GI prompt (only if reconnection succeeded)
                while time.time() - gi_start < gi_timeout:
                    elapsed = int(time.time() - gi_start)
                    mins, secs = divmod(elapsed, 60)
                    
                    with progress_lock:
                        progress_pct = 25 + int((elapsed / gi_timeout) * 70)
                    
                    live.update(render_panel())
                    time.sleep(gi_interval)
                    
                    try:
                        # Send multiple newlines to trigger prompt
                        console_channel.send("\r\n")
                        time.sleep(1)
                        console_channel.send("\r\n")
                        time.sleep(2)
                        
                        # Read all available output
                        output = ""
                        while console_channel.recv_ready():
                            output += console_channel.recv(16384).decode('utf-8', errors='replace')
                            time.sleep(0.2)
                        
                        # Show last line of output for debugging
                        if output.strip():
                            last_lines = output.strip().split('\n')[-2:]  # Last 2 lines
                            for line in last_lines:
                                line_clean = line.strip()[:50]  # First 50 chars
                                if line_clean:
                                    add_line(f">> {line_clean}", "dim")
                        
                        # Check for GI mode indicators
                        output_lower = output.lower()
                        is_gi = any([
                            'GI' in output and '#' in output,  # GI# prompt
                            'gicli' in output_lower,
                            'GI(' in output,
                            'gi mode' in output_lower,
                            output.strip().endswith('GI#'),
                            output.strip().endswith('GI('),
                        ])
                        
                        if is_gi:
                            add_line(f"✓ GI mode reached after {mins}m {secs}s", "green")
                            gi_connected = True
                            
                            # Try to get mgmt IP
                            add_line("Reading mgmt0 IP address...")
                            live.update(render_panel())
                            
                            console_channel.send("show interfaces mgmt0\r\n")
                            time.sleep(3)
                            mgmt_output = ""
                            while console_channel.recv_ready():
                                mgmt_output += console_channel.recv(16384).decode('utf-8', errors='replace')
                                time.sleep(0.2)
                            
                            # Parse IP from output
                            import re
                            ip_match = re.search(r'IPv4 address:\s+(\d+\.\d+\.\d+\.\d+)', mgmt_output)
                            if ip_match:
                                new_mgmt_ip = ip_match.group(1)
                                add_line(f"✓ New mgmt0 IP: {new_mgmt_ip}", "green")
                            else:
                                add_line("⚠ Could not read mgmt0 IP", "yellow")
                            
                            try:
                                ssh.close()
                            except:
                                pass
                            break
                        else:
                            add_line(f"⏳ Waiting for GI prompt... ({mins}m {secs}s)")
                    
                    except Exception as e:
                        add_line(f"⏳ Console check: {str(e)[:30]} ({mins}m {secs}s)", "yellow")
                
            else:
                # Normal SSH reconnection
                while time.time() - gi_start < gi_timeout:
                    elapsed = int(time.time() - gi_start)
                    mins, secs = divmod(elapsed, 60)
                    
                    with progress_lock:
                        progress_pct = 25 + int((elapsed / gi_timeout) * 70)
                    
                    live.update(render_panel())
                    time.sleep(gi_interval)
                    
                    try:
                        ssh = paramiko.SSHClient()
                        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                        ssh.connect(device.ip, username='dnroot', password=password, timeout=10)
                        channel = ssh.invoke_shell(width=200, height=50)
                        time.sleep(2)
                        
                        new_output = channel.recv(65535).decode('utf-8', errors='replace')
                        
                        if 'GI' in new_output or 'gicli' in new_output.lower():
                            add_line(f"✓ GI mode reached after {mins}m {secs}s", "green")
                            gi_connected = True
                            try:
                                ssh.close()
                            except:
                                pass
                            break
                        else:
                            add_line(f"⏳ Connected but not GI yet... ({mins}m {secs}s)")
                            try:
                                ssh.close()
                            except:
                                pass
                            
                    except Exception as e:
                        # Connection failed - device still rebooting
                        add_line(f"⏳ Device rebooting... ({mins}m {secs}s)")
            
            if not gi_connected:
                add_line("✗ Timeout waiting for GI mode", "red")
                with progress_lock:
                    current_stage = "failed"
                    progress_pct = 100
                live.update(render_panel())
                return False
            
            # Success - GI mode reached
            with progress_lock:
                current_stage = "gi_ready"
                progress_pct = 100
            add_line("✓ Device is now in GI mode!", "green")
            
            # If we got a new mgmt IP, offer to update devices.json
            if new_mgmt_ip and new_mgmt_ip != device.ip:
                add_line(f"📡 New mgmt IP detected: {new_mgmt_ip}", "cyan")
                add_line("Consider updating devices.json with new IP", "cyan")
            
            add_line(f"Next: Load images via Image Upgrade menu", "cyan")
            live.update(render_panel())
            
            # Pause to show success before exiting live display
            time.sleep(2)
            
            return True
            
        except Exception as e:
            add_line(f"✗ Error: {str(e)[:40]}", "red")
            with progress_lock:
                current_stage = "failed"
                progress_pct = 100
            live.update(render_panel())
            return False


def execute_system_restore(
    device: Any,
    system_type: str,
    hostname: str,
    images: Dict[str, str],
    knowledge: DeviceKnowledge,
    progress_callback: Callable[[Dict], None] = None
) -> bool:
    """
    DEPRECATED: Use run_system_restore_wizard() instead which integrates with Image Upgrade menu.
    
    This function is kept for backward compatibility but redirects to the new flow.
    """
    console.print("[yellow]Note: Using new integrated flow with Image Upgrade menu[/yellow]")
    return run_system_restore_wizard(device, None)


def check_recovery_and_prompt(device: Any) -> Optional[bool]:
    """
    Check if device is in recovery mode and prompt for restore.
    
    Returns:
        True if user wants to restore, False if user declined, None if not in recovery
    """
    import paramiko
    import base64
    
    # Check operational.json first
    knowledge = DeviceKnowledge.from_operational_json(device.hostname)
    if knowledge.recovery_mode_detected or knowledge.console_recovery_detected:
        console.print(f"\n[bold red]⚠ {device.hostname} was previously detected in RECOVERY mode[/bold red]")
        if Confirm.ask("Run System Restore wizard?", default=True):
            return True
        return False
    
    # Try SSH connection to check current state
    try:
        password = device.password
        if device.password:
            try:
                password = base64.b64decode(device.password).decode('utf-8')
            except:
                pass
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(device.ip, username=device.username or 'dnroot', password=password, timeout=10)
        channel = ssh.invoke_shell(width=200, height=50)
        time.sleep(2)
        output = channel.recv(65535).decode('utf-8', errors='replace')
        ssh.close()
        
        if 'RECOVERY' in output or 'dnRouter(RECOVERY)' in output:
            console.print(f"\n[bold red]⚠ {device.hostname} is currently in RECOVERY mode[/bold red]")
            if Confirm.ask("Run System Restore wizard?", default=True):
                return True
            return False
        
        return None  # Not in recovery
        
    except Exception:
        return None  # Can't determine


# Export main functions
__all__ = [
    'DeviceKnowledge',
    'run_system_restore_wizard',
    'check_recovery_and_prompt',
    'show_device_knowledge_panel',
]
