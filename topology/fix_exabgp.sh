#!/bin/bash
set -x
OUT=/home/dn/CURSOR/fix_exabgp_output.txt

exec > "$OUT" 2>&1

echo "=== Kill ExaBGP ==="
pkill -f exabgp 2>/dev/null || true
sleep 2
echo "ExaBGP killed"

echo ""
echo "=== Apply PE-4 neighbor config via Python ==="
python3 -c "
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

print('CLI OUTPUT:')
print(output)
chan.close()
client.close()
"

echo ""
echo "=== Verify neighbor config ==="
python3 -c "
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
"

echo ""
echo "=== Wait 90s for FortiGate ==="
sleep 90
echo "Wait done"

echo ""
echo "=== Start ExaBGP ==="
python3 /home/dn/SCALER/FLOWSPEC_VPN/exabgp/bgp_tool.py start --config /tmp/exabgp_pe_4.conf --session-id pe_4 2>&1

echo ""
echo "=== Wait 30s ==="
sleep 30

echo ""
echo "=== Verify ExaBGP ==="
python3 /home/dn/SCALER/FLOWSPEC_VPN/exabgp/bgp_tool.py verify --session-id pe_4 2>&1

echo ""
echo "=== ExaBGP diagnose ==="
python3 /home/dn/SCALER/FLOWSPEC_VPN/exabgp/bgp_tool.py diagnose --session-id pe_4 2>&1

echo ""
echo "=== ExaBGP log ==="
tail -20 /home/dn/SCALER/FLOWSPEC_VPN/exabgp/logs/pe_4_exabgp.log 2>&1

echo ""
echo "=== Check PE-4 neighbor ==="
python3 -c "
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
"

echo ""
echo "=== DONE ==="
