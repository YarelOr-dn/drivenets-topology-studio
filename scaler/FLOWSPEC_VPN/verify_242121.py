#!/usr/bin/env python3
"""SW-242121 verification: delete neighbor + rollback, check per-AF knobs survive."""
import paramiko, time, re, sys

HOSTS = ["100.64.2.33", "100.64.5.56"]
USER = "dnroot"
PASS = "dnroot"
ANSI_RE = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')

def clean(text):
    return ANSI_RE.sub('', text)

def send_and_wait(shell, cmd, wait=2, prompt='#'):
    shell.send(cmd + '\n')
    time.sleep(wait)
    out = ''
    while shell.recv_ready():
        out += shell.recv(65536).decode('utf-8', errors='replace')
        time.sleep(0.3)
    return clean(out)

def run():
    for host in HOSTS:
        print(f"\n{'='*60}")
        print(f"Connecting to {host}...")
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, username=USER, password=PASS, timeout=15, look_for_keys=False)
            shell = ssh.invoke_shell(width=200, height=50)
            time.sleep(2)
            shell.recv(65536)

            print("Step 1: Enter config mode and navigate to BGP...")
            out = send_and_wait(shell, 'configure', 3)
            print(f"  configure: {out.strip()[-80:]}")
            out = send_and_wait(shell, 'protocols', 2)
            out = send_and_wait(shell, 'bgp 1234567', 2)
            print(f"  bgp context: {out.strip()[-80:]}")

            print("Step 2: Delete neighbor 2.2.2.2...")
            out = send_and_wait(shell, 'no neighbor 2.2.2.2', 3)
            print(f"  no neighbor: {out.strip()[-150:]}")
            if 'ERROR' in out or 'Unknown' in out:
                print("  ERROR deleting neighbor - aborting")
                send_and_wait(shell, 'exit', 1)
                send_and_wait(shell, 'exit', 1)
                send_and_wait(shell, 'exit', 1)
                ssh.close()
                return False

            print("Step 3: Commit (removes neighbor from running config)...")
            out = send_and_wait(shell, 'commit', 20)
            print(f"  commit: {out.strip()[-200:]}")

            print("Step 4: Wait 10s for BGP session to drop...")
            time.sleep(10)

            print("Step 5: Rollback to previous config (restores neighbor)...")
            out = send_and_wait(shell, 'rollback 1', 5)
            print(f"  rollback: {out.strip()[-200:]}")

            print("Step 6: Commit (restores neighbor to running config)...")
            out = send_and_wait(shell, 'commit', 20)
            print(f"  commit: {out.strip()[-200:]}")

            print("Step 7: Exit config mode...")
            send_and_wait(shell, 'exit', 1)
            send_and_wait(shell, 'exit', 1)
            send_and_wait(shell, 'exit', 1)

            print("Step 8: Wait 45s for BGP to re-establish...")
            for i in range(9):
                time.sleep(5)
                print(f"  waiting... {(i+1)*5}s")

            print("Step 9: Check BGP session state...")
            out = send_and_wait(shell, 'show bgp ipv4 flowspec-vpn summary | include 2.2.2.2', 5)
            print(f"  FlowSpec-VPN state: {out.strip()}")
            out = send_and_wait(shell, 'show bgp ipv4 vpn summary | include 2.2.2.2', 3)
            print(f"  VPN state: {out.strip()}")

            print("\nDONE - ready for AFTER state capture via MCP")
            ssh.close()
            return True

        except Exception as e:
            print(f"ERROR on {host}: {e}")
            continue

    print("FAILED to connect to any host")
    return False

if __name__ == '__main__':
    success = run()
    sys.exit(0 if success else 1)
