#!/bin/bash
OUT=/home/dn/CURSOR/bgp_recovery_output.txt

exec > "$OUT" 2>&1

echo "=== Kill ExaBGP process ==="
pkill -f 'exabgp.application' 2>/dev/null || true
pkill -f '/tmp/exabgp_pe_4' 2>/dev/null || true
sleep 2
ps aux | grep exabgp | grep -v grep | grep -v bgp_recovery || echo "No ExaBGP processes"

echo ""
echo "=== Apply PE-4 neighbor config ==="
python3 << 'PYEOF'
import paramiko, time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('100.64.7.197', username='dnroot', password='dnroot', timeout=10)
chan = client.invoke_shell(width=250, height=50)
time.sleep(2)
chan.recv(65536)

cmds = [
    'configure',
    'rollback 0',
    'protocols bgp 1234567 neighbor 100.64.6.134',
    'remote-as 65200',
    'admin-state enabled',
    'passive enabled',
    'description ExaBGP-server',
    'ebgp-multihop 10',
    'update-source ge100-18/0/6.999',
    'timers hold-time 180',
    'address-family ipv4-flowspec',
    'allow-as-in enabled',
    'send-community community-type both',
    'soft-reconfiguration inbound',
    'exit',
    'address-family ipv4-vpn',
    'allow-as-in enabled',
    'send-community community-type both',
    'soft-reconfiguration inbound',
    'exit',
    'address-family ipv4-unicast',
    'send-community community-type both',
    'soft-reconfiguration inbound',
    'exit',
    'address-family ipv6-flowspec',
    'allow-as-in enabled',
    'send-community community-type both',
    'soft-reconfiguration inbound',
    'exit',
    'address-family ipv6-vpn',
    'allow-as-in enabled',
    'send-community community-type both',
    'soft-reconfiguration inbound',
    'exit',
    'exit',
    'exit',
    'exit',
    'commit',
]

for cmd in cmds:
    chan.send(cmd + '\n')
    time.sleep(1.0)

time.sleep(3)
output = ''
while chan.recv_ready():
    output += chan.recv(65536).decode('utf-8', errors='replace')
    time.sleep(0.3)

print('NEIGHBOR CONFIG OUTPUT:')
print(output)
chan.close()
client.close()
PYEOF

echo ""
echo "=== Verify neighbor config ==="
python3 << 'PYEOF'
import paramiko, time
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('100.64.7.197', username='dnroot', password='dnroot', timeout=10)
chan = client.invoke_shell(width=250, height=50)
time.sleep(2)
chan.recv(65536)
chan.send('show config protocols bgp 1234567 neighbor 100.64.6.134 | no-more\n')
time.sleep(3)
output = ''
while chan.recv_ready():
    output += chan.recv(65536).decode('utf-8', errors='replace')
    time.sleep(0.3)
print(output)
chan.close()
client.close()
PYEOF

echo ""
echo "=== Wait 90s for FortiGate IDS quarantine ==="
for i in $(seq 1 9); do
    sleep 10
    echo "  Waited ${i}0s..."
done
echo "90s done"

echo ""
echo "=== Start ExaBGP ==="
python3 /home/dn/SCALER/FLOWSPEC_VPN/exabgp/bgp_tool.py start --config /tmp/exabgp_pe_4.conf --session-id pe_4 2>&1

echo ""
echo "=== Wait 30s for BGP establish ==="
sleep 30

echo ""
echo "=== Verify ExaBGP ==="
python3 /home/dn/SCALER/FLOWSPEC_VPN/exabgp/bgp_tool.py verify --session-id pe_4 2>&1

echo ""
echo "=== ExaBGP diagnose ==="
python3 /home/dn/SCALER/FLOWSPEC_VPN/exabgp/bgp_tool.py diagnose --session-id pe_4 2>&1

echo ""
echo "=== ExaBGP log tail ==="
tail -25 /home/dn/SCALER/FLOWSPEC_VPN/exabgp/logs/pe_4_exabgp.log 2>&1

echo ""
echo "=== PE-4 neighbor check ==="
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
