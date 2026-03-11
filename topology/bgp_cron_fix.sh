#!/bin/bash
OUT=/home/dn/CURSOR/bgp_cron_fix_output.txt

exec > "$OUT" 2>&1

echo "=== Step 1: Show current crontab ==="
crontab -l 2>&1

echo ""
echo "=== Step 2: Remove watchdog cron entries ==="
cd /home/dn/SCALER/FLOWSPEC_VPN/exabgp && python3 bgp_watchdog.py --remove-cron 2>&1
echo ""
echo "Crontab after removal:"
crontab -l 2>&1

echo ""
echo "=== Step 3: Kill ALL BGP processes ==="
# Kill watchdog sleep processes
for pid in $(ps aux | grep 'bgp_watchdog' | grep -v grep | grep -v bgp_cron_fix | awk '{print $2}'); do
    echo "Killing PID $pid"
    kill $pid 2>/dev/null
done
# Kill any exabgp
for pid in $(ps aux | grep 'exabgp' | grep -v grep | grep -v bgp_cron_fix | awk '{print $2}'); do
    echo "Killing ExaBGP PID $pid"
    kill $pid 2>/dev/null
done
# Kill socat for exabgp
for pid in $(ps aux | grep 'socat.*exabgp' | grep -v grep | awk '{print $2}'); do
    echo "Killing socat PID $pid"
    kill $pid 2>/dev/null
done
sleep 3

echo ""
echo "=== Step 4: Verify NOTHING BGP-related running ==="
ps aux | grep -E 'exabgp|bgp_watchdog|bgp_tool' | grep -v grep | grep -v bgp_cron_fix || echo "[OK] Zero BGP processes"

echo ""
echo "=== Step 5: Wait 5 MINUTES (300s) - NO CRON WILL RESPAWN ==="
echo "FortiGate IDS quarantine requires 2-5 min of complete TCP/179 silence."
echo "Cron is disabled. PE-4 has passive=enabled. Server has no ExaBGP."
echo "This time, silence will actually be maintained."
for i in $(seq 1 30); do
    sleep 10
    # Safety: check if anything somehow respawned
    orphan=$(ps aux | grep -E 'exabgp|bgp_watchdog' | grep -v grep | grep -v bgp_cron_fix | head -1)
    if [ -n "$orphan" ]; then
        echo "[ALERT ${i}0s] Orphan found: $orphan"
        kill $(echo "$orphan" | awk '{print $2}') 2>/dev/null
    else
        echo "  ${i}0s / 300s -- clean"
    fi
done
echo "300s silence complete."

echo ""
echo "=== Step 6: Test TCP/179 ==="
nc -z -w 3 100.70.0.206 179 2>&1
TCP_RESULT=$?
if [ $TCP_RESULT -eq 0 ]; then
    echo "[OK] TCP/179 OPEN! FortiGate quarantine cleared!"
else
    echo "[INFO] TCP/179 test failed (exit $TCP_RESULT). May still work with passive neighbor."
    echo "PE-4 has passive=enabled, so it won't send SYN-ACK until ExaBGP sends SYN."
    echo "Starting ExaBGP anyway - the SYN will go through if FortiGate cleared."
fi

echo ""
echo "=== Step 7: Start ExaBGP ==="
python3 /home/dn/SCALER/FLOWSPEC_VPN/exabgp/bgp_tool.py start --config /tmp/exabgp_pe_4.conf --session-id pe_4 2>&1

echo ""
echo "=== Step 8: Wait 45s for BGP to establish ==="
sleep 45

echo ""
echo "=== Step 9: Verify ExaBGP ==="
python3 /home/dn/SCALER/FLOWSPEC_VPN/exabgp/bgp_tool.py verify --session-id pe_4 2>&1

echo ""
echo "=== Step 10: ExaBGP log ==="
tail -25 /home/dn/SCALER/FLOWSPEC_VPN/exabgp/logs/pe_4_exabgp.log 2>&1

echo ""
echo "=== Step 11: PE-4 neighbor state ==="
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
echo "=== Step 12: ss TCP/179 check ==="
ss -tnp | grep 179 2>&1 || echo "No TCP/179 connections"

echo ""
echo "=== DONE ==="
