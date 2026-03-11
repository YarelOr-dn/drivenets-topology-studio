#!/usr/bin/env python3
"""Apply swap config to RR-SA-2 to trigger IRB flap bug scenario."""
import paramiko
import time
import re
import sys

HOSTS = ["100.64.4.205", "100.64.5.15"]
USER = "dnroot"
PASS = "dnroot"
SWAP_CONFIG = """network-services
  evpn
    instance evpn_scale_1
      no router-interface irb1
      router-interface irb2
        host-routes enabled
      !
    !
    instance evpn_scale_2
      no router-interface irb2
      router-interface irb1
        host-routes enabled
      !
    !
  !
  vrf
    instance scale_1
      no interface irb1
      interface irb2
    !
    instance scale_2
      no interface irb2
      interface irb1
    !
  !
!"""

ANSI_RE = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')

def clean(text):
    return ANSI_RE.sub("", text)

def recv_all(shell, delay=1.0):
    time.sleep(delay)
    buf = ""
    while shell.recv_ready():
        buf += shell.recv(65536).decode("utf-8", errors="replace")
    return buf

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    host = None
    for h in HOSTS:
        try:
            print(f"Trying {h}...")
            client.connect(h, port=22, username=USER, password=PASS,
                           timeout=15, look_for_keys=False)
            host = h
            print(f"Connected to {h}")
            break
        except Exception as e:
            print(f"Failed {h}: {e}")
    if not host:
        print("ERROR: Cannot connect")
        sys.exit(1)

    shell = client.invoke_shell(width=250, height=50)
    shell.settimeout(300)
    recv_all(shell, 3)

    print("Entering config mode...")
    shell.send("configure\n")
    recv_all(shell, 2)
    shell.send("rollback 0\n")
    recv_all(shell, 1)

    print("Pasting swap config...")
    for line in SWAP_CONFIG.strip().split("\n"):
        shell.send(line + "\n")
    out = recv_all(shell, 2)
    cleaned = clean(out)
    errors = [l for l in cleaned.split("\n") if "ERROR:" in l]
    if errors:
        print(f"PASTE ERRORS: {errors}")
        shell.send("rollback 0\n")
        recv_all(shell, 1)
        shell.send("exit\n")
        client.close()
        sys.exit(1)

    print("Committing swap config...")
    shell.send("commit\n")

    committed = False
    for i in range(60):
        time.sleep(5)
        buf = recv_all(shell, 0.5)
        c = clean(buf)
        if "ommit complete" in c or "Commit complete" in c:
            print(f"COMMIT COMPLETE (detected at {(i+1)*5}s)")
            committed = True
            break
        if "Nothing to commit" in c:
            print("NOTHING TO COMMIT")
            committed = True
            break
        if "COMMIT CHECK FAILED" in c or "Unable to commit" in c:
            print(f"COMMIT FAILED: {c}")
            shell.send("rollback 0\n")
            recv_all(shell, 1)
            shell.send("exit\n")
            client.close()
            sys.exit(1)
        if "#" in c and ("config" not in c.lower()):
            print(f"Prompt returned at {(i+1)*5}s - commit likely done")
            committed = True
            break
        if i > 0 and i % 6 == 0:
            print(f"  waiting ({(i+1)*5}s)...")

    if not committed:
        print("COMMIT TIMEOUT - checking if it actually applied...")

    shell.send("exit\n")
    recv_all(shell, 1)

    print("Verifying swap applied...")
    shell.send("show evpn detail | no-more\n")
    time.sleep(3)
    verify = clean(recv_all(shell, 2))
    print(verify[:2000])

    client.close()
    print("\nSWAP DONE")

if __name__ == "__main__":
    main()
