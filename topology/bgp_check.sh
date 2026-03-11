#!/bin/bash
OUT=/home/dn/CURSOR/bgp_state.txt

{
  echo "=== EXABGP VERIFY ==="
  python3 /home/dn/SCALER/FLOWSPEC_VPN/exabgp/bgp_tool.py verify --session-id pe_4 2>&1
  echo ""
  echo "=== EXABGP PROCESSES ==="
  ps aux | grep -E 'exabgp|bgp_watchdog' | grep -v grep 2>&1
  echo ""
  echo "=== PING INBAND ==="
  ping -c 2 -W 2 100.70.0.206 2>&1
  echo ""
  echo "=== PE-4 BGP SUMMARY ==="
  sshpass -p 'dnroot' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 dnroot@100.64.7.197 "show bgp summary | no-more" 2>&1
  echo ""
  echo "=== PE-4 VRF ALPHA BGP ==="
  sshpass -p 'dnroot' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 dnroot@100.64.7.197 "show bgp instance vrf ALPHA summary | no-more" 2>&1
  echo ""
  echo "=== PE-4 VRF ZULU BGP ==="
  sshpass -p 'dnroot' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 dnroot@100.64.7.197 "show bgp instance vrf ZULU summary | no-more" 2>&1
  echo ""
  echo "=== SPIRENT BGP STATUS ==="
  python3 /home/dn/SCALER/SPIRENT/spirent_tool.py bgp-status --json 2>&1
  echo ""
  echo "=== PE-4 BUNDLE-100 SUBIFS ==="
  sshpass -p 'dnroot' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 dnroot@100.64.7.197 "show config interfaces bundle-100 | no-more" 2>&1
} > "$OUT" 2>&1

echo "Done. Output in $OUT"
