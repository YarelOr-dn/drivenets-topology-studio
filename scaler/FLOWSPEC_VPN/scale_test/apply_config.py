#!/usr/bin/env python3
"""Apply DNOS config to PE-4 via SSH. Handles configure + paste + commit."""

import paramiko
import time
import sys
import re

PE4_HOST = "100.64.6.82"
PE4_USER = "dnroot"
PE4_PASS = "dnroot"
PE4_PORT = 22


def apply_config(config_text, commit=True, timeout=300):
    """Apply config to PE-4. Returns (success, output)."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(PE4_HOST, port=PE4_PORT, username=PE4_USER,
                   password=PE4_PASS, timeout=30, look_for_keys=False)

    shell = client.invoke_shell(width=200, height=50)
    shell.settimeout(timeout)
    full_output = ""

    def recv_all(delay=1.0):
        nonlocal full_output
        time.sleep(delay)
        buf = ""
        while shell.recv_ready():
            chunk = shell.recv(65536).decode("utf-8", errors="replace")
            buf += chunk
            full_output += chunk
        return buf

    def send_line(cmd, delay=0.5):
        shell.send(cmd + "\n")
        return recv_all(delay)

    recv_all(2)
    send_line("configure", 1)
    send_line("rollback 0", 0.5)

    lines = config_text.strip().split("\n")
    print(f"  Pasting {len(lines)} lines...", flush=True)
    batch_size = 200
    for i in range(0, len(lines), batch_size):
        batch = lines[i:i + batch_size]
        for line in batch:
            shell.send(line + "\n")
        recv_all(0.1)
        if len(lines) > 1000 and (i + batch_size) % 2000 == 0:
            print(f"    ... pasted {i + batch_size}/{len(lines)} lines", flush=True)

    recv_all(1)

    paste_errors = []
    for line in full_output.split("\n"):
        if "ERROR:" in line:
            paste_errors.append(line.strip())

    if paste_errors:
        print(f"  PASTE ERRORS ({len(paste_errors)}):")
        for e in paste_errors[:5]:
            print(f"    {e}")
        if not commit:
            send_line("rollback 0", 1)
            send_line("exit", 1)
            client.close()
            return False, full_output

    if commit:
        print("  Committing...", flush=True)
        shell.send("commit\n")
        commit_done = False
        ansi_re = re.compile(r'\x1b\[[0-9;]*m')
        accumulated = ""
        for attempt in range(60):
            time.sleep(5)
            buf = ""
            while shell.recv_ready():
                chunk = shell.recv(65536).decode("utf-8", errors="replace")
                buf += chunk
                full_output += chunk
            accumulated += buf
            clean = ansi_re.sub("", accumulated)
            if "Commit complete" in clean or "ommit complete" in clean:
                print("  COMMIT COMPLETE", flush=True)
                commit_done = True
                break
            if "Nothing to commit" in clean:
                print("  NOTHING TO COMMIT", flush=True)
                commit_done = True
                break
            if "COMMIT CHECK FAILED" in clean or "Unable to commit" in clean:
                print("  COMMIT FAILED", flush=True)
                for line in clean.split("\n"):
                    if "Unable" in line or "FAILED" in line or "ERROR" in line:
                        print(f"    {line.strip()}", flush=True)
                send_line("rollback 0", 1)
                send_line("exit", 1)
                client.close()
                return False, full_output
            # After the commit command, if we see the prompt return outside cfg mode, commit is done
            if attempt >= 2 and re.search(r'PE-4\(cfg\)#\s*$', clean):
                print("  COMMIT COMPLETE (detected via prompt)", flush=True)
                commit_done = True
                break
            if attempt > 0 and attempt % 6 == 0:
                print(f"    ... waiting ({attempt * 5}s)...", flush=True)

        if not commit_done:
            print("  COMMIT TIMEOUT (300s)", flush=True)
            send_line("rollback 0", 2)

    send_line("exit", 1)
    client.close()
    return (not paste_errors) and commit_done if commit else (not paste_errors), full_output


def delete_flowspec_local(commit=True):
    """Delete only flowspec-local-policies and flowspec-local forwarding-options."""
    config = "no routing-policy flowspec-local-policies\nno forwarding-options flowspec-local"
    return apply_config(config, commit=commit)


def run_show(command, timeout=30):
    """Run a show command on PE-4. Returns output string."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(PE4_HOST, port=PE4_PORT, username=PE4_USER,
                   password=PE4_PASS, timeout=30, look_for_keys=False)
    shell = client.invoke_shell(width=200, height=50)
    shell.settimeout(timeout)
    time.sleep(1.5)
    while shell.recv_ready():
        shell.recv(65536)
    shell.send(command + " | no-more\n")
    time.sleep(2)
    out = ""
    for _ in range(10):
        time.sleep(0.5)
        while shell.recv_ready():
            out += shell.recv(65536).decode("utf-8", errors="replace")
        if out and not shell.recv_ready():
            break
    client.close()
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: apply_config.py <config_file|--delete> [--no-commit]")
        sys.exit(1)

    cfg_file = sys.argv[1]
    do_commit = "--no-commit" not in sys.argv

    if cfg_file == "--delete":
        ok, out = delete_flowspec_local(commit=do_commit)
    else:
        with open(cfg_file) as f:
            cfg = f.read()
        ok, out = apply_config(cfg, commit=do_commit)

    print(f"Result: {'SUCCESS' if ok else 'FAILED'}")
    sys.exit(0 if ok else 1)
