#!/usr/bin/env python3
"""Remove IRB flap test config from RR-SA-2."""
import paramiko, time, re, sys

HOSTS = ["100.64.4.205", "100.64.5.15"]
ANSI_RE = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')

CLEANUP = """no network-services evpn instance evpn_scale_1
no network-services evpn instance evpn_scale_2
no network-services vrf instance scale_1
no network-services vrf instance scale_2
no interfaces irb1
no interfaces irb2
no interfaces bundle-100.500
no interfaces bundle-100.501"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    for h in HOSTS:
        try:
            client.connect(h, port=22, username="dnroot", password="dnroot",
                           timeout=15, look_for_keys=False)
            print(f"Connected to {h}")
            break
        except:
            continue
    shell = client.invoke_shell(width=250, height=50)
    shell.settimeout(300)
    time.sleep(3); shell.recv(65536)

    shell.send("configure\n"); time.sleep(2); shell.recv(65536)
    shell.send("rollback 0\n"); time.sleep(1); shell.recv(65536)

    for line in CLEANUP.strip().split("\n"):
        shell.send(line + "\n")
    time.sleep(2); shell.recv(65536)

    print("Committing cleanup...")
    shell.send("commit\n")
    for i in range(60):
        time.sleep(5)
        buf = ""
        while shell.recv_ready():
            buf += shell.recv(65536).decode("utf-8", errors="replace")
        c = ANSI_RE.sub("", buf)
        if "ommit complete" in c or "Commit complete" in c or "Nothing to commit" in c:
            print(f"Cleanup committed at {(i+1)*5}s")
            break
        if "#" in c and "config" not in c.lower():
            print(f"Prompt returned at {(i+1)*5}s")
            break
    shell.send("exit\n"); time.sleep(1)
    client.close()
    print("Cleanup DONE")

if __name__ == "__main__":
    main()
