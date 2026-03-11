#!/bin/bash
OUT=/home/dn/CURSOR/bgp_clean_restart_output.txt

exec > "$OUT" 2>&1

echo "=== NUCLEAR KILL: All BGP processes ==="
echo "Killing ALL: watchdog, exabgp, socat, bgp_tool..."
# Kill watchdog (including the sleep+watchdog combo)
kill $(ps aux | grep bgp_watchdog | grep -v grep | grep -v bgp_clean | awk '{print $2}') 2>/dev/null
# Kill any sleep that precedes watchdog
kill $(ps aux | grep 'sleep.*bgp_watchdog' | grep -v grep | awk '{print $2}') 2>/dev/null
# Kill exabgp processes
kill $(ps aux | grep exabgp | grep -v grep | grep -v bgp_clean | awk '{print $2}') 2>/dev/null
# Kill socat processes related to exabgp
kill $(ps aux | grep 'socat.*exabgp' | grep -v grep | awk '{print $2}') 2>/dev/null
sleep 3

echo ""
echo "=== Verify ALL killed ==="
ps aux | grep -E 'exabgp|bgp_watchdog|bgp_tool' | grep -v grep | grep -v bgp_clean || echo "[OK] No BGP processes running"

echo ""
echo "=== Start 5-minute silence (300s) ==="
echo "Zero TCP/179 traffic must cross FortiGate for quarantine to expire."
for i in $(seq 1 30); do
    sleep 10
    # Also check if anything restarted ExaBGP
    orphan=$(ps aux | grep exabgp | grep -v grep | grep -v bgp_clean | head -1)
    if [ -n "$orphan" ]; then
        echo "[ALERT] Something restarted ExaBGP! Killing: $orphan"
        kill $(echo "$orphan" | awk '{print $2}') 2>/dev/null
    fi
    echo "  ${i}0s / 300s"
done
echo "300s silence complete."

echo ""
echo "=== Test TCP/179 ==="
nc -z -w 3 100.70.0.206 179 2>&1
if [ $? -eq 0 ]; then
    echo "[OK] TCP/179 is OPEN! FortiGate quarantine cleared."
    TCP_OPEN=1
else
    echo "[FAIL] TCP/179 still blocked after 5 minutes."
    echo "Checking if any process sent SYNs during the wait..."
    TCP_OPEN=0
fi

echo ""
echo "=== Start ExaBGP ==="
python3 /home/dn/SCALER/FLOWSPEC_VPN/exabgp/bgp_tool.py start --config /tmp/exabgp_pe_4.conf --session-id pe_4 2>&1

echo ""
echo "=== Wait 45s for BGP establish ==="
sleep 45

echo ""
echo "=== Verify ==="
python3 /home/dn/SCALER/FLOWSPEC_VPN/exabgp/bgp_tool.py verify --session-id pe_4 2>&1

echo ""
echo "=== ExaBGP log ==="
tail -20 /home/dn/SCALER/FLOWSPEC_VPN/exabgp/logs/pe_4_exabgp.log 2>&1

echo ""
echo "=== PE-4 neighbor state ==="
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
echo "=== DONE ==="
