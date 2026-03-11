#!/usr/bin/env python3
"""
ensure_dnaas_path.py -- Create DNAAS BD path + DUT config for FlowSpec HA tests.

Creates VLAN 212 path: B-14 (Spirent) <-> B-10 (DUT leaf) <-> PE-4.
Run this before ha_flowspec_test.py if VLAN 212 path does not exist.

Usage:
    python3 ensure_dnaas_path.py --vlan 212 --device YOR_CL_PE-4 [--dry-run]
"""

import argparse
import base64
import json
import sys
from pathlib import Path

CONFIG_PATH = Path.home() / ".spirent_config.json"
SCALER_DB = Path.home() / "SCALER" / "db" / "devices.json"

try:
    from .ha_ssh import run_ssh_shell
except ImportError:
    from ha_ssh import run_ssh_shell


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def load_device(hostname: str) -> dict:
    with open(SCALER_DB) as f:
        data = json.load(f)
    for d in data.get("devices", []):
        if d.get("hostname", "").upper() == hostname.upper():
            pw = d.get("password", "dnroot")
            if pw:
                try:
                    pw = base64.b64decode(pw).decode("utf-8")
                except Exception:
                    pass
            return {"hostname": d["hostname"], "ip": d["ip"], "username": d.get("username", "dnroot"), "password": pw}
    raise ValueError(f"Device {hostname} not found")


def ssh_config(host: str, user: str, password: str, config_blocks: list[str], dry_run: bool = False) -> bool:
    """SSH to device, enter config mode, apply config blocks, commit."""
    if dry_run:
        return True
    commands = ["configure"]
    for block in config_blocks:
        for line in block.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            commands.append(line)
    commands.extend(["commit", "exit"])
    run_ssh_shell(host, user, password, commands, timeout=90)
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vlan", type=int, default=212)
    parser.add_argument("--device", default="YOR_CL_PE-4")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.vlan < 210 or args.vlan > 219:
        print("ERROR: VLAN must be 210-219")
        sys.exit(1)

    config = load_config()
    cred_b64 = config.get("dnaas_credentials_b64", "")
    dnaas_pass = base64.b64decode(cred_b64).decode("utf-8") if cred_b64 else "Drive1234!"
    dnaas_user = config["dnaas_leaves"]["DNAAS-LEAF-B14"]["username"]
    b14_ip = config["dnaas_leaves"]["DNAAS-LEAF-B14"]["ip"]
    b10_ip = config["dnaas_leaves"]["DNAAS-LEAF-B10"]["ip"]
    spirent_port = config["dnaas_leaves"]["DNAAS-LEAF-B14"]["spirent_port"]
    dut_port = config["dnaas_leaves"]["DNAAS-LEAF-B10"]["dut_port_map"].get(args.device, "ge100-0/0/3")

    device = load_device(args.device)
    dut_dnaas_port = "ge100-18/0/0"  # PE-4's port facing DNAAS

    # B-14 config: Spirent-facing AC + BD
    b14_config = f"""
interfaces
  {spirent_port}
    {args.vlan}
      admin-state enabled
      l2-service enabled
      vlan-id {args.vlan}
      vlan-manipulation egress-mapping action pop
      vlan-manipulation ingress-mapping action push outer-tag {args.vlan} outer-tpid 0x8100
    !
  !
!
network-services
  bridge-domain
    instance g_yor_v{args.vlan}_ha_spirent
      interface bundle-60000.{args.vlan}
      !
      interface {spirent_port}.{args.vlan}
      !
    !
  !
!
"""

    # B-10 config: DUT-facing AC + BD
    b10_config = f"""
interfaces
  {dut_port}
    {args.vlan}
      admin-state enabled
      l2-service enabled
      vlan-id {args.vlan}
      vlan-manipulation egress-mapping action pop
      vlan-manipulation ingress-mapping action push outer-tag {args.vlan} outer-tpid 0x8100
    !
  !
!
network-services
  bridge-domain
    instance g_yor_v{args.vlan}_ha_spirent
      interface bundle-60000.{args.vlan}
      !
      interface {dut_port}.{args.vlan}
      !
    !
  !
!
"""

    # PE-4 config: sub-interface + BGP neighbor
    # Use AS 64512 for Spirent peer (STC BgpRouterConfig DutAsNum supports 0-65535 only)
    pe4_config = f"""
interfaces
  {dut_dnaas_port}
    {args.vlan}
      admin-state enabled
      vlan-id {args.vlan}
      ipv4-address 10.99.{args.vlan}.2/24
    !
  !
!
protocols
  bgp
    64512
      neighbor 10.99.{args.vlan}.1
        remote-as 65200
        address-family ipv4-flowspec-vpn
          admin-state enabled
        !
      !
    !
  !
!
"""

    print(f"Creating VLAN {args.vlan} path for {args.device}")
    print("B-14 (Spirent leaf):", b14_ip)
    print("B-10 (DUT leaf):", b10_ip)
    print("PE-4:", device["ip"])

    if args.dry_run:
        print("\n[DRY-RUN] Would apply:")
        print("--- B-14 ---")
        print(b14_config)
        print("--- B-10 ---")
        print(b10_config)
        print("--- PE-4 ---")
        print(pe4_config)
        return

    print("\nApplying B-14 config...")
    ssh_config(b14_ip, dnaas_user, dnaas_pass, [b14_config], dry_run=False)
    print("Applying B-10 config...")
    ssh_config(b10_ip, dnaas_user, dnaas_pass, [b10_config], dry_run=False)
    print("Applying PE-4 config...")
    ssh_config(device["ip"], device["username"], device["password"], [pe4_config], dry_run=False)
    print("Done. Path ready for Spirent BGP peer 10.99.{}.1".format(args.vlan))


if __name__ == "__main__":
    main()
