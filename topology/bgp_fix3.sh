#!/bin/bash
OUT=/home/dn/CURSOR/bgp_fix3_result.txt
PE4_IP="100.64.7.197"

{
echo "=== TEST 1: SSH -T no tty ==="
echo "show version" | sshpass -p 'dnroot' ssh -T -o StrictHostKeyChecking=no -o ConnectTimeout=10 -o UserKnownHostsFile=/dev/null dnroot@$PE4_IP 2>&1
echo "---"

echo "=== TEST 2: SSH with command arg ==="
sshpass -p 'dnroot' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -o UserKnownHostsFile=/dev/null dnroot@$PE4_IP 'show version' 2>&1
echo "---"

echo "=== TEST 3: SSH -T with show bgp ==="
echo "show bgp summary" | sshpass -p 'dnroot' ssh -T -o StrictHostKeyChecking=no -o ConnectTimeout=10 -o UserKnownHostsFile=/dev/null dnroot@$PE4_IP 2>&1
echo "---"

echo "=== TEST 4: ExaBGP diagnose ==="
python3 /home/dn/SCALER/FLOWSPEC_VPN/exabgp/bgp_tool.py diagnose --session-id pe_4 2>&1
echo "---"

echo "=== TEST 5: ExaBGP log last 40 lines ==="
tail -40 /home/dn/SCALER/FLOWSPEC_VPN/exabgp/logs/pe_4_exabgp.log 2>&1
echo "---"

echo "=== TEST 6: ExaBGP config ==="
cat /tmp/exabgp_pe_4.conf 2>&1
echo "---"

echo "=== TEST 7: TCP 179 check via ss ==="
ss -tnp | grep 179 2>&1
echo "---"

echo "=== DONE ==="
} > "$OUT" 2>&1

echo "Done"
