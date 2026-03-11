"""PE-2 console fallback: connect via console server when SSH/IP fails.

When normal config extraction over SSH fails for PE-2, we can try the console
path (SSH to console server, port access, PE-2 serial port) to detect recovery
mode or confirm reachability. Used by the wizard Refresh flow and by monitor.py.
"""

import time
import socket
from typing import Tuple, Optional

CONSOLE_HOST = "console-b15"
CONSOLE_USER = "dn"
CONSOLE_PASSWORD = "drive1234"
CONSOLE_PE2_PORT = 13
# Credentials for port 13 access (prompted after selecting port)
PORT_ACCESS_USER = "dnroot"
PORT_ACCESS_PASSWORD = "dnroot"
CONSOLE_CHECK_TIMEOUT_SEC = 25


def check_pe2_recovery_via_console() -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Connect to console server (ssh to CONSOLE_HOST), port access option 3,
    port 13 (PE-2), read console output and detect PE-2 state.
    
    Changes nothing on the device; detection only.
    
    Returns:
        (in_recovery: bool, recovery_type: str, error_message: Optional[str])
        
    recovery_type values:
        - "GI" - Device in GI mode (ready for DNOS deployment)
        - "BASEOS_SHELL" - Device in BaseOS shell (need to run dncli)
        - "DN_RECOVERY" - Device in DNOS recovery mode
        - "ONIE" - Device in ONIE rescue mode
        - "DNOS" - Device running DNOS normally
        - "" - Unknown state or detection failed
    """
    try:
        import paramiko
    except ImportError:
        return False, "", "paramiko not installed"
    ssh = None
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            CONSOLE_HOST,
            username=CONSOLE_USER,
            password=CONSOLE_PASSWORD,
            timeout=8,
            banner_timeout=10,
        )
        channel = ssh.invoke_shell(width=200, height=50)
        channel.settimeout(CONSOLE_CHECK_TIMEOUT_SEC)
        time.sleep(1.5)
        _ = channel.recv(8192).decode("utf-8", errors="replace")
        channel.send("3\r\n")
        time.sleep(5)
        _ = channel.recv(8192).decode("utf-8", errors="replace")
        channel.send("13\r\n")
        time.sleep(1.0)
        channel.send("\r\n")  # Enter key to trigger prompts
        time.sleep(2.0)
        after_13 = channel.recv(8192).decode("utf-8", errors="replace")
        
        # Detect state from initial output
        lower = after_13.lower()
        output_combined = after_13
        
        # Try to login if prompted (works for DNOS/GI/Recovery with dnroot/dnroot)
        if "login" in lower or "username" in lower or "password" in lower:
            # Try DNOS/GI credentials first
            channel.send(PORT_ACCESS_USER + "\r\n")
            time.sleep(0.8)
            channel.send(PORT_ACCESS_PASSWORD + "\r\n")
            time.sleep(6)
            channel.settimeout(10)
            out = channel.recv(16384).decode("utf-8", errors="replace")
            output_combined += out
            channel.settimeout(CONSOLE_CHECK_TIMEOUT_SEC)
        else:
            # Already at device shell
            out = after_13
            channel.settimeout(3)
            try:
                extra = channel.recv(8192).decode("utf-8", errors="replace")
                if extra:
                    out += extra
                    output_combined += extra
            except socket.timeout:
                pass
            channel.settimeout(CONSOLE_CHECK_TIMEOUT_SEC)
        
        # Send newline to trigger prompt display
        channel.send("\r\n")
        time.sleep(2.0)
        try:
            prompt_out = channel.recv(8192).decode("utf-8", errors="replace")
            output_combined += prompt_out
        except socket.timeout:
            pass
        
        # Clean up connection
        try:
            channel.send("exit\r\n")
            time.sleep(1.0)
            exit_out = channel.recv(8192).decode("utf-8", errors="replace")
            output_combined += exit_out
        except:
            pass
        
        ssh.close()
        ssh = None
        
        # Detect state from combined output
        lower_combined = output_combined.lower()
        
        # Priority order: ONIE → BaseOS Shell → GI → Recovery → DNOS
        if "onie:/" in lower_combined or "onie-" in lower_combined:
            return True, "ONIE", None
        elif "@" in output_combined and ":~$" in output_combined and ("dn@" in output_combined or "WKY" in output_combined):
            # BaseOS shell prompt: dn@WKY1BC7400002B2:~$
            return True, "BASEOS_SHELL", None
        elif "gi#" in lower_combined or "gi(" in lower_combined or "gicli" in lower_combined:
            # GI mode
            return False, "GI", None
        elif "recovery" in lower_combined:
            # DNOS Recovery mode
            return True, "DN_RECOVERY", None
        elif "#" in output_combined and ("router" in lower_combined or "pe-" in lower_combined):
            # Normal DNOS
            return False, "DNOS", None
        else:
            # Unknown state
            return False, "", "Could not determine device state"
            
    except socket.timeout:
        return False, "", "console connection timeout"
    except Exception as e:
        return False, "", str(e)
    finally:
        if ssh:
            try:
                ssh.close()
            except Exception:
                pass
