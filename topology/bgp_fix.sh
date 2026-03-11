#!/bin/bash
OUT=/home/dn/CURSOR/bgp_fix_result.txt
PE4_IP="100.64.7.197"
PE4_USER="dnroot"
PE4_PASS="dnroot"

ssh_cmd() {
    sshpass -p "$PE4_PASS" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -o UserKnownHostsFile=/dev/null "$PE4_USER@$PE4_IP" "$1" 2>/dev/null
}

{
echo "=== STEP 1: Check PE-4 BGP summary ==="
ssh_cmd "show bgp summary"
echo ""

echo "=== STEP 2: Check ExaBGP neighbor state on PE-4 ==="
ssh_cmd "show bgp neighbor 100.64.6.134"
echo ""

echo "=== STEP 3: Admin-disable ExaBGP neighbor ==="
ssh_cmd "configure
protocols bgp 1234567 neighbor 100.64.6.134 admin-state disabled
commit"
echo ""

echo "=== STEP 4: Verify neighbor disabled ==="
ssh_cmd "show bgp neighbor 100.64.6.134"
echo ""

echo "=== STEP 5: Kill old ExaBGP ==="
pkill -f exabgp 2>/dev/null || true
sleep 2
echo "ExaBGP killed"
echo ""

echo "=== STEP 6: Wait 60s for FortiGate quarantine ==="
sleep 60
echo "Wait done"
echo ""

echo "=== STEP 7: Test TCP/179 via ping ==="
ping -c 2 -W 2 100.70.0.206 2>&1
echo ""

echo "=== STEP 8: Clear ARP on PE-4 ==="
ssh_cmd "clear arp"
echo "ARP cleared"
echo ""

echo "=== STEP 9: Re-enable ExaBGP neighbor ==="
ssh_cmd "configure
protocols bgp 1234567 neighbor 100.64.6.134 admin-state enabled
commit"
echo ""

echo "=== STEP 10: Start ExaBGP ==="
python3 /home/dn/SCALER/FLOWSPEC_VPN/exabgp/bgp_tool.py start --config /tmp/exabgp_pe_4.conf --session-id pe_4 2>&1
echo ""

echo "=== STEP 11: Wait 20s for BGP to establish ==="
sleep 20
echo ""

echo "=== STEP 12: Verify ExaBGP ==="
python3 /home/dn/SCALER/FLOWSPEC_VPN/exabgp/bgp_tool.py verify --session-id pe_4 2>&1
echo ""

echo "=== STEP 13: Check PE-4 BGP summary after fix ==="
ssh_cmd "show bgp summary"
echo ""

echo "=== STEP 14: Check VRF ALPHA BGP ==="
ssh_cmd "show bgp instance vrf ALPHA summary"
echo ""

echo "=== STEP 15: Check VRF ZULU BGP ==="
ssh_cmd "show bgp instance vrf ZULU summary"
echo ""

echo "=== STEP 16: Check PE-4 bundle-100 sub-interfaces ==="
ssh_cmd "show interfaces bundle-100"
echo ""

echo "=== DONE ==="
} > "$OUT" 2>&1

echo "Done. Output saved to $OUT"
