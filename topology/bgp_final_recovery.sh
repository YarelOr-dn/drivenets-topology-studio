#!/bin/bash
OUT=/home/dn/CURSOR/bgp_final_recovery_output.txt

exec > "$OUT" 2>&1

echo "=== Step 1: Kill ExaBGP process ==="
pkill -f 'exabgp.application' 2>/dev/null || true
pkill -f '/tmp/exabgp_pe' 2>/dev/null || true
sleep 2
ps aux | grep -E 'exabgp' | grep -v grep | grep -v bgp_final || echo "No ExaBGP processes"

echo ""
echo "=== Step 2: Enable bgp_guard iptables (drop RSTs while ExaBGP is down) ==="
python3 /home/dn/SCALER/FLOWSPEC_VPN/exabgp/bgp_tool.py guard --enable 2>&1 || echo "Guard not available, continuing"

echo ""
echo "=== Step 3: Wait 5 FULL minutes with ZERO TCP/179 traffic ==="
echo "FortiGate IDS quarantine needs 2-5 min of silence to expire."
echo "PE-4 has passive=enabled (no SYNs from device)."
echo "ExaBGP killed (no SYNs from server)."
echo "Starting 300s countdown..."
for i in $(seq 1 30); do
    sleep 10
    echo "  Waited ${i}0s... ($(( 300 - i*10 ))s remaining)"
done
echo "300s silence complete."

echo ""
echo "=== Step 4: Test TCP/179 reachability ==="
echo "Single nc -z test (one SYN packet)..."
nc -z -w 3 100.70.0.206 179 2>&1
if [ $? -eq 0 ]; then
    echo "[OK] TCP/179 OPEN - FortiGate quarantine has cleared!"
else
    echo "[WARN] TCP/179 still blocked. Will try starting ExaBGP anyway (PE-4 has passive)."
fi

echo ""
echo "=== Step 5: Start ExaBGP ==="
python3 /home/dn/SCALER/FLOWSPEC_VPN/exabgp/bgp_tool.py start --config /tmp/exabgp_pe_4.conf --session-id pe_4 2>&1

echo ""
echo "=== Step 6: Wait 45s for BGP establish ==="
sleep 45

echo ""
echo "=== Step 7: Verify ExaBGP ==="
python3 /home/dn/SCALER/FLOWSPEC_VPN/exabgp/bgp_tool.py verify --session-id pe_4 2>&1

echo ""
echo "=== Step 8: ExaBGP log ==="
tail -25 /home/dn/SCALER/FLOWSPEC_VPN/exabgp/logs/pe_4_exabgp.log 2>&1

echo ""
echo "=== Step 9: PE-4 neighbor state ==="
python3 << 'PYEOF'
import paramiko, time
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('100.64.7.197', username='dnroot', password='dnroot', timeout=10)
chan = client.invoke_shell(width=250, height=50)
time.sleep(2)
chan.recv(65536)
chan.send('show bgp neighbor 100.64.6.134 | no-more\n')
time.sleep(4)
output = ''
while chan.recv_ready():
    output += chan.recv(65536).decode('utf-8', errors='replace')
    time.sleep(0.3)
print(output)
chan.close()
client.close()
PYEOF

echo ""
echo "=== Step 10: Spirent BGP status ==="
python3 /home/dn/SCALER/SPIRENT/spirent_tool.py bgp-status --json 2>&1

echo ""
echo "=== DONE ==="
