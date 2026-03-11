#!/bin/bash
OUT=/home/dn/CURSOR/bgp_fix2_result.txt
PE4_IP="100.64.7.197"

{
echo "=== TEST 1: SSH basic - show version ==="
sshpass -p 'dnroot' ssh -tt -o StrictHostKeyChecking=no -o ConnectTimeout=10 -o UserKnownHostsFile=/dev/null dnroot@$PE4_IP << 'DNOS_EOF'
show version
exit
DNOS_EOF
echo ""

echo "=== TEST 2: SSH show bgp summary ==="
sshpass -p 'dnroot' ssh -tt -o StrictHostKeyChecking=no -o ConnectTimeout=10 -o UserKnownHostsFile=/dev/null dnroot@$PE4_IP << 'DNOS_EOF'
show bgp summary
exit
DNOS_EOF
echo ""

echo "=== TEST 3: ExaBGP diagnose ==="
python3 /home/dn/SCALER/FLOWSPEC_VPN/exabgp/bgp_tool.py diagnose --session-id pe_4 2>&1
echo ""

echo "=== TEST 4: ExaBGP log tail ==="
tail -30 /home/dn/SCALER/FLOWSPEC_VPN/exabgp/logs/pe_4_exabgp.log 2>&1
echo ""

echo "=== TEST 5: Check ExaBGP config ==="
cat /tmp/exabgp_pe_4.conf 2>&1
echo ""

echo "=== DONE ==="
} > "$OUT" 2>&1

echo "Done"
