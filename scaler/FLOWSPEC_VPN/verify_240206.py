#!/usr/bin/env python3
"""SW-240206: Apply import-vpn RT change to VRF ALPHA, then exit quickly."""
import paramiko, time, re, sys

HOSTS = ["100.64.2.33", "100.64.5.56"]
USER = "dnroot"
PASS = "dnroot"
ANSI_RE = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')

def clean(text):
    return ANSI_RE.sub('', text)

def send_and_wait(shell, cmd, wait=2):
    shell.send(cmd + '\n')
    time.sleep(wait)
    out = ''
    while shell.recv_ready():
        out += shell.recv(65536).decode('utf-8', errors='replace')
        time.sleep(0.3)
    return clean(out)

def apply_config(action="remove"):
    """action: 'remove' = remove 300:300, 'restore' = add it back"""
    for host in HOSTS:
        print(f"Connecting to {host} (action={action})...")
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, username=USER, password=PASS, timeout=15, look_for_keys=False)
            shell = ssh.invoke_shell(width=200, height=50)
            time.sleep(2)
            shell.recv(65536)

            send_and_wait(shell, 'configure', 3)
            send_and_wait(shell, 'network-services', 1)
            send_and_wait(shell, 'vrf', 1)
            send_and_wait(shell, 'instance ALPHA', 1)
            send_and_wait(shell, 'protocols', 1)
            send_and_wait(shell, 'bgp 1234567', 1)
            send_and_wait(shell, 'address-family ipv4-unicast', 1)

            out = send_and_wait(shell, 'no import-vpn route-target', 2)
            print(f"  no import-vpn: {out.strip()[-80:]}")

            if action == "remove":
                new_rt = '100:100,1234567:100'
            else:
                new_rt = '100:100,300:300,1234567:100'

            out = send_and_wait(shell, f'import-vpn route-target {new_rt}', 2)
            print(f"  import-vpn {new_rt}: {out.strip()[-80:]}")

            out = send_and_wait(shell, 'show config compare', 3)
            print(f"  config compare:\n{out}")

            out = send_and_wait(shell, 'commit', 20)
            print(f"  commit: {out.strip()[-200:]}")
            if 'Commit succeeded' in out:
                print("  SUCCESS")
            elif 'no configuration changes' in out:
                print("  NO CHANGES (already in target state)")

            send_and_wait(shell, 'exit', 0.5)
            send_and_wait(shell, 'exit', 0.5)
            send_and_wait(shell, 'exit', 0.5)
            send_and_wait(shell, 'exit', 0.5)
            send_and_wait(shell, 'exit', 0.5)
            send_and_wait(shell, 'exit', 0.5)
            send_and_wait(shell, 'exit', 0.5)
            send_and_wait(shell, 'exit', 0.5)
            ssh.close()
            return True

        except Exception as e:
            print(f"ERROR on {host}: {e}")
            continue
    return False

if __name__ == '__main__':
    action = sys.argv[1] if len(sys.argv) > 1 else "remove"
    success = apply_config(action)
    sys.exit(0 if success else 1)
