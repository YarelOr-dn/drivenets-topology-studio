#!/bin/bash
# SCALER Config Extraction Script
# Runs every 5 minutes via cron

# Use Israel timezone for all timestamps
export TZ='Asia/Jerusalem'

SCALER_DIR="/home/dn/SCALER"
LOG_FILE="$SCALER_DIR/extraction.log"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
# Human-friendly format: 2025-12-24_09-05
FRIENDLY_DATE=$(date +"%Y-%m-%d_%H-%M")

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# ============================================================================
# DEVICE INTEGRITY ALERTS SYSTEM
# Detects: hostname mismatch, serial change, IP change, stale data, failures
# Alerts are saved to db/alerts.json and shown by wizard on startup
# ============================================================================

ALERTS_FILE="$SCALER_DIR/db/alerts.json"

# Initialize alerts file if missing
if [ ! -f "$ALERTS_FILE" ]; then
    echo '{"alerts":[],"last_check":""}' > "$ALERTS_FILE"
fi

add_alert() {
    local device="$1"
    local severity="$2"   # CRITICAL, WARNING, INFO
    local alert_type="$3" # hostname_mismatch, serial_changed, ip_changed, stale_data, extraction_failed
    local message="$4"
    local timestamp=$(date -Iseconds)
    
    log "⚠ ALERT [$severity] $device: $message"
    
    python3 -c "
import json, sys, os
alerts_file = '$ALERTS_FILE'
try:
    with open(alerts_file) as f:
        data = json.load(f)
except:
    data = {'alerts': [], 'last_check': ''}

# Remove old alerts of the same type for the same device (keep latest only)
data['alerts'] = [a for a in data['alerts'] 
                  if not (a.get('device') == '$device' and a.get('type') == '$alert_type')]

data['alerts'].append({
    'device': '$device',
    'severity': '$severity',
    'type': '$alert_type',
    'message': '''$message''',
    'timestamp': '$timestamp',
    'acknowledged': False
})

# Keep only last 50 alerts
data['alerts'] = data['alerts'][-50:]
data['last_check'] = '$timestamp'

with open(alerts_file, 'w') as f:
    json.dump(data, f, indent=2)
" 2>/dev/null
}

clear_alert() {
    local device="$1"
    local alert_type="$2"
    
    python3 -c "
import json
alerts_file = '$ALERTS_FILE'
try:
    with open(alerts_file) as f:
        data = json.load(f)
    data['alerts'] = [a for a in data['alerts'] 
                      if not (a.get('device') == '$device' and a.get('type') == '$alert_type')]
    with open(alerts_file, 'w') as f:
        json.dump(data, f, indent=2)
except:
    pass
" 2>/dev/null
}

verify_extraction_integrity() {
    local name="$1"
    local output_file="$2"
    local config_dir="$3"
    local expected_ip="$4"
    
    # --- CHECK 1: Hostname verification ---
    # Extract System Name from show system output
    local live_hostname=$(grep -m1 "System Name:" "$output_file" 2>/dev/null | sed 's/.*System Name:[[:space:]]*//' | cut -d',' -f1 | tr -d ' \r')
    
    if [ -n "$live_hostname" ] && [ "$live_hostname" != "N/A" ]; then
        # Use Python for word-boundary hostname matching (same logic as utils.py)
        local hostname_ok=$(python3 -c "
import sys
a = '${live_hostname}'.lower()
e = '${name}'.lower().replace(' ', '')
if a == e:
    print('yes')
    sys.exit()
shorter = e if len(e) <= len(a) else a
longer = a if len(e) <= len(a) else e
pos = longer.find(shorter)
if pos == -1:
    print('no')
    sys.exit()
boundary = {'_', '-', '.'}
left_ok = (pos == 0) or (longer[pos-1] in boundary)
end = pos + len(shorter)
right_ok = (end == len(longer)) or (longer[end] in boundary)
print('yes' if left_ok and right_ok else 'no')
" 2>/dev/null)
        
        if [ "$hostname_ok" = "no" ]; then
            add_alert "$name" "CRITICAL" "hostname_mismatch" \
                "WRONG DEVICE at $expected_ip: device reports '$live_hostname' but DB expects '$name'. Data may belong to wrong device!"
            return 1
        else
            clear_alert "$name" "hostname_mismatch"
        fi
    fi
    
    # --- CHECK 2: Serial number change detection ---
    local live_serial=$(awk -F'|' '/^\|[[:space:]]*(NCP|ncp)[[:space:]]*\|/ {
        oper = $5; gsub(/^[ \t]+|[ \t]+$/, "", oper)
        if (oper !~ /^up/) next
        sn = $9; gsub(/^[ \t]+|[ \t]+$/, "", sn)
        if (sn == "" || sn ~ /^[[:space:]]*$/) { sn = $NF; gsub(/^[ \t]+|[ \t]+$/, "", sn) }
        if (sn != "" && sn !~ /Serial/ && sn !~ /^[[:space:]]*$/ && sn !~ /^[0-9]+:[0-9]+:[0-9]+$/ && sn !~ /days/) print sn
    }' "$output_file" | head -1 | tr -d '\r')
    
    if [ -n "$live_serial" ] && [ "$live_serial" != "N/A" ] && [ -f "$config_dir/operational.json" ]; then
        local stored_serial=$(jq -r '.serial_number // "N/A"' "$config_dir/operational.json" 2>/dev/null)
        if [ "$stored_serial" != "N/A" ] && [ -n "$stored_serial" ] && [ "$live_serial" != "$stored_serial" ]; then
            add_alert "$name" "CRITICAL" "serial_changed" \
                "Serial number CHANGED: was '$stored_serial', now '$live_serial'. Device may have been physically replaced or DB points to wrong device!"
        else
            clear_alert "$name" "serial_changed"
        fi
    fi
    
    # --- CHECK 3: Management IP change detection ---
    local live_mgmt_ip=$(awk -F'|' '/^\|[[:space:]]*mgmt0[[:space:]]*\|/ {
        ip = $5; gsub(/^[ \t]+|[ \t]+$/, "", ip); gsub(/ *\(d\)/, "", ip); print ip
    }' "$output_file" | head -1 | tr -d '\r')
    
    if [ -n "$live_mgmt_ip" ] && [ "$live_mgmt_ip" != "N/A" ]; then
        local live_ip_clean=$(echo "$live_mgmt_ip" | cut -d'/' -f1)
        if [ "$live_ip_clean" != "$expected_ip" ]; then
            add_alert "$name" "WARNING" "ip_changed" \
                "Management IP changed: DB has '$expected_ip', device reports '$live_ip_clean'. Updating DB automatically."
            
            # Auto-update devices.json with correct IP
            python3 -c "
import json
devices_file = '$SCALER_DIR/db/devices.json'
with open(devices_file) as f:
    data = json.load(f)
for dev in data.get('devices', []):
    if dev.get('hostname') == '$name':
        dev['ip'] = '$live_ip_clean'
        break
with open(devices_file, 'w') as f:
    json.dump(data, f, indent=2)
" 2>/dev/null
            log "$name: Auto-updated IP in devices.json: $expected_ip -> $live_ip_clean"
        else
            clear_alert "$name" "ip_changed"
        fi
    fi
    
    return 0
}

track_extraction_result() {
    local name="$1"
    local success="$2"  # "true" or "false"
    local config_dir="$3"
    
    local tracker_file="$config_dir/.extraction_tracker.json"
    
    python3 -c "
import json
from datetime import datetime

tracker_file = '$tracker_file'
try:
    with open(tracker_file) as f:
        tracker = json.load(f)
except:
    tracker = {'consecutive_failures': 0, 'last_success': None, 'last_attempt': None, 'total_failures': 0}

tracker['last_attempt'] = datetime.now().isoformat()

if '$success' == 'true':
    if tracker['consecutive_failures'] > 0:
        print(f'RECOVERED after {tracker[\"consecutive_failures\"]} failures')
    tracker['consecutive_failures'] = 0
    tracker['last_success'] = datetime.now().isoformat()
else:
    tracker['consecutive_failures'] += 1
    tracker['total_failures'] = tracker.get('total_failures', 0) + 1
    print(f'FAILURE #{tracker[\"consecutive_failures\"]}')

with open(tracker_file, 'w') as f:
    json.dump(tracker, f, indent=2)

# Alert thresholds
if tracker['consecutive_failures'] >= 6:  # 30 min (6 x 5min cycles)
    print('ALERT_STALE')
elif tracker['consecutive_failures'] >= 3:  # 15 min
    print('ALERT_FAILING')
" 2>/dev/null
}

extract_config() {
    local host=$1
    local name=$2
    local config_dir="$SCALER_DIR/db/configs/$name"
    local history_dir="$SCALER_DIR/db/history/$name"
    
    mkdir -p "$config_dir" "$history_dir"
    
    log "Extracting $name from $host..."
    
    # Get all info in one session - including show system stack and show system
    expect -c "
set timeout 180
spawn sshpass -p dnroot ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o PubkeyAuthentication=no dnroot@$host
expect \"#\"
send \"show system stack | no-more\r\"
expect \"#\"
send \"show system target-stack load history | no-more\r\"
expect \"#\"
send \"show system install | no-more\r\"
expect \"#\"
send \"show system target-stack load | no-more\r\"
expect \"#\"
send \"show system | no-more\r\"
expect \"#\"
send \"show isis | no-more\r\"
expect \"#\"
send \"show ospf | no-more\r\"
expect \"#\"
send \"show bgp summary | no-more\r\"
expect \"#\"
send \"show ldp summary | no-more\r\"
expect \"#\"
send \"show evpn-vpws-fxc | no-more\r\"
expect \"#\"
send \"show evpn-vpws summary | no-more\r\"
expect \"#\"
send \"show vrf | no-more\r\"
expect \"#\"
send \"show evpn | no-more\r\"
expect \"#\"
send \"show vpws | no-more\r\"
expect \"#\"
send \"show interfaces | no-more\r\"
expect \"#\"
send \"show interfaces management | no-more\r\"
expect \"#\"
send \"show lldp neighbor | no-more\r\"
expect \"#\"
send \"show config | no-more\r\"
expect -re {config-end.*#}
send \"exit\r\"
expect eof
" 2>&1 | grep -v "^spawn\|^Warning\|DRIVENETS" > "$config_dir/full_output.txt"

    local output="$config_dir/full_output.txt"
    
    # Check if we got meaningful output (SSH connected successfully)
    local output_lines=$(wc -l < "$output" 2>/dev/null || echo 0)
    if [ "$output_lines" -lt 10 ]; then
        log "$name: SSH extraction failed - only $output_lines lines of output"
        local track_result=$(track_extraction_result "$name" "false" "$config_dir")
        if echo "$track_result" | grep -q "ALERT_STALE"; then
            add_alert "$name" "CRITICAL" "stale_data" \
                "Device unreachable for 30+ minutes. Operational data is STALE and may not reflect reality. Last IP: $host"
        elif echo "$track_result" | grep -q "ALERT_FAILING"; then
            add_alert "$name" "WARNING" "extraction_failed" \
                "Extraction failing for 15+ minutes. IP $host may be wrong or device is down."
        fi
        return 1
    fi
    
    # ========================================================================
    # EARLY RECOVERY MODE DETECTION - check SSH prompt BEFORE normal parsing
    # In RECOVERY mode, most show commands fail, so detect it from the prompt
    # and update operational.json directly instead of trying normal extraction
    # ========================================================================
    if grep -qiE '\(RECOVERY\)#|\(RECOVERY\)>' "$output" 2>/dev/null; then
        log "$name: 🔴 RECOVERY MODE DETECTED from SSH prompt"
        
        local recovery_detected_at=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
        
        if [ -f "$config_dir/operational.json" ]; then
            # Update existing operational.json with recovery state
            local tmp_op=$(mktemp)
            jq --arg det_at "$recovery_detected_at" '
                .device_state = "RECOVERY" |
                .recovery_mode_detected = true |
                .recovery_type = "DN_RECOVERY" |
                .recovery_mode_detected_at = $det_at |
                .upgrade_in_progress = false |
                .upgrade_status = "RECOVERY" |
                .upgrade_progress = ""
            ' "$config_dir/operational.json" > "$tmp_op" 2>/dev/null && \
                mv "$tmp_op" "$config_dir/operational.json"
        else
            # Create minimal operational.json for RECOVERY state
            cat > "$config_dir/operational.json" <<RECEOF
{
    "device_state": "RECOVERY",
    "recovery_mode_detected": true,
    "recovery_type": "DN_RECOVERY",
    "recovery_mode_detected_at": "$recovery_detected_at",
    "upgrade_in_progress": false,
    "upgrade_status": "RECOVERY",
    "ssh_host": "$host",
    "mgmt_ip": "N/A"
}
RECEOF
        fi
        
        add_alert "$name" "CRITICAL" "recovery_mode" \
            "Device is in RECOVERY mode (dnRouter(RECOVERY)#). DNOS is NOT running. Manual intervention or re-deploy required."
        clear_alert "$name" "extraction_failed"
        clear_alert "$name" "stale_data"
        
        track_extraction_result "$name" "true" "$config_dir"
        log "$name: Recovery state saved to operational.json"
        return 0
    fi
    
    # ========================================================================
    # INTEGRITY CHECKS - verify we connected to the right device
    # Must run BEFORE saving any data to prevent poisoning DB with wrong data
    # ========================================================================
    if ! verify_extraction_integrity "$name" "$output" "$config_dir" "$host"; then
        log "$name: ⛔ INTEGRITY CHECK FAILED - skipping data save to prevent DB corruption"
        track_extraction_result "$name" "false" "$config_dir"
        rm -f "$output"
        return 1
    fi
    
    # Extraction succeeded and integrity verified
    track_extraction_result "$name" "true" "$config_dir"
    clear_alert "$name" "stale_data"
    clear_alert "$name" "extraction_failed"
    clear_alert "$name" "recovery_mode"
    
    # ========================================================================
    # PARSE STACK INFO (show system stack)
    # Format: | Component | HW Model | HW Revision | Revert | Current | Target |
    # Components: DNOS, BASEOS, GI (case-insensitive match)
    # ========================================================================
    local dnos_version=$(awk -F'|' 'toupper($2) ~ /DNOS/ && NF>5 {gsub(/^[ \t]+|[ \t]+$/, "", $6); print $6}' "$output" | head -1)
    local baseos_version=$(awk -F'|' 'toupper($2) ~ /BASEOS/ && NF>5 {gsub(/^[ \t]+|[ \t]+$/, "", $6); print $6}' "$output" | head -1)
    local gi_version=$(awk -F'|' 'toupper($2) ~ /^[[:space:]]*GI[[:space:]]*$/ && NF>5 {gsub(/^[ \t]+|[ \t]+$/, "", $6); print $6}' "$output" | head -1)
    
    # Ensure versions are valid
    dnos_version="${dnos_version:-N/A}"
    baseos_version="${baseos_version:-N/A}"
    gi_version="${gi_version:-N/A}"
    
    # Parse stack download URLs from target-stack load history (most recent for each component)
    # Extract URL that contains 'dnos' in the path
    local dnos_url=$(grep "^url:" "$output" 2>/dev/null | grep -i "drivenets_dnos" | head -1 | sed 's/url:[[:space:]]*//' | tr -d '\r\t')
    dnos_url="${dnos_url:-N/A}"
    
    # Extract URL that contains 'gi' in the path  
    local gi_url=$(grep "^url:" "$output" 2>/dev/null | grep -i "drivenets_gi" | head -1 | sed 's/url:[[:space:]]*//' | tr -d '\r\t')
    gi_url="${gi_url:-N/A}"
    
    # Extract URL that contains 'baseos' in the path
    local baseos_url=$(grep "^url:" "$output" 2>/dev/null | grep -i "drivenets_baseos" | head -1 | sed 's/url:[[:space:]]*//' | tr -d '\r\t')
    baseos_url="${baseos_url:-N/A}"
    
    # Keep legacy stack_url for backwards compatibility (first URL found)
    local stack_url=$(grep -m1 "^url:" "$output" 2>/dev/null | sed 's/url:[[:space:]]*//' | tr -d '\r\t')
    stack_url="${stack_url:-N/A}"
    
    # ========================================================================
    # PARSE INSTALLATION TIME (show system install)
    # ========================================================================
    # Get Task start time and elapsed time to calculate when installation finished
    local install_start=$(grep -m1 "Task start time:" "$output" 2>/dev/null | sed 's/Task start time:[[:space:]]*//' | tr -d '\r\t')
    local install_elapsed=$(grep -m1 "Task elapsed time:" "$output" 2>/dev/null | sed 's/Task elapsed time:[[:space:]]*//' | tr -d '\r\t')
    local install_type=$(grep -m1 "Installation type:" "$output" 2>/dev/null | sed 's/Installation type:[[:space:]]*//' | tr -d '\r\t')
    local install_status=$(grep -m1 "Task status:" "$output" 2>/dev/null | sed 's/Task status:[[:space:]]*//' | tr -d '\r\t' | head -1)
    
    # Calculate finish time by adding elapsed time to start time
    local install_finish=""
    if [ -n "$install_start" ] && [ -n "$install_elapsed" ]; then
        # Parse elapsed time (format: H:MM:SS or HH:MM:SS)
        local elapsed_seconds=0
        if [[ "$install_elapsed" =~ ^([0-9]+):([0-9]+):([0-9]+)$ ]]; then
            # Use 10# prefix to force base-10 (avoids octal issue with 08, 09)
            local h=$((10#${BASH_REMATCH[1]}))
            local m=$((10#${BASH_REMATCH[2]}))
            local s=$((10#${BASH_REMATCH[3]}))
            elapsed_seconds=$((h * 3600 + m * 60 + s))
        fi
        
        # Convert start time to epoch, add elapsed, convert back
        if [ "$elapsed_seconds" -gt 0 ]; then
            local start_epoch=$(date -d "$install_start" +%s 2>/dev/null)
            if [ -n "$start_epoch" ]; then
                local finish_epoch=$((start_epoch + elapsed_seconds))
                install_finish=$(date -d "@$finish_epoch" "+%Y-%m-%d %H:%M:%S" 2>/dev/null)
            fi
        fi
    fi
    install_finish="${install_finish:-N/A}"
    
    # ========================================================================
    # PARSE UPGRADE STATUS (show system target-stack load)
    # Detect if target-stack installation is in progress
    # ========================================================================
    local upgrade_in_progress="false"
    local upgrade_progress=""
    local upgrade_task_status=""
    
    # Check for "Task status: in-progress" in the output
    if grep -q "Task status:.*in-progress" "$output" 2>/dev/null; then
        upgrade_in_progress="true"
        # Get progress percentage
        upgrade_progress=$(grep -m1 "Progress:" "$output" 2>/dev/null | sed 's/Progress:[[:space:]]*//' | tr -d '\r' || echo "")
        upgrade_task_status="in-progress"
    fi
    
    # Also check System status from "show system" 
    local system_status=$(grep -m1 "System status:" "$output" 2>/dev/null | sed 's/.*System status:[[:space:]]*//' | tr -d '\r')
    if echo "$system_status" | grep -qi "upgrade"; then
        upgrade_in_progress="true"
        upgrade_task_status="${system_status}"
    fi
    
    # Check for nodes in upgrade state (baseos-upgrade, firmware-upgrade, nos-upgrade)
    local nodes_upgrading=$(awk -F'|' '/upgrade.*in-progress/ {
        node=$2; state=$5
        gsub(/^[ \t]+|[ \t]+$/, "", node)
        gsub(/^[ \t]+|[ \t]+$/, "", state)
        print node": "state
    }' "$output" 2>/dev/null | tr '\n' ', ' | sed 's/, $//')
    
    if [ -n "$nodes_upgrading" ]; then
        upgrade_in_progress="true"
    fi
    
    # ========================================================================
    # PARSE SYSTEM INFO (show system)
    # ========================================================================
    # IMPORTANT: Read existing operational.json to preserve critical fields when device is in GI mode
    local saved_system_type="N/A"
    local saved_serial_number="N/A"
    local saved_recovery_mode="false"
    local saved_recovery_time="null"
    local saved_recovery_type=""
    local saved_ssh_host=""
    local saved_connection_method=""
    local saved_mgmt_ip="N/A"
    local saved_device_state=""
    local saved_dnos_version="N/A"
    local saved_gi_version="N/A"
    local saved_baseos_version="N/A"
    if [ -f "$config_dir/operational.json" ]; then
        saved_system_type=$(jq -r '.system_type // "N/A"' "$config_dir/operational.json" 2>/dev/null)
        saved_serial_number=$(jq -r '.serial_number // "N/A"' "$config_dir/operational.json" 2>/dev/null)
        saved_recovery_mode=$(jq -r '.recovery_mode_detected // false' "$config_dir/operational.json" 2>/dev/null)
        saved_recovery_time=$(jq -r '.recovery_mode_detected_at // null' "$config_dir/operational.json" 2>/dev/null)
        saved_recovery_type=$(jq -r '.recovery_type // ""' "$config_dir/operational.json" 2>/dev/null)
        # Preserve SSH connection info (set by wizard/monitor)
        saved_ssh_host=$(jq -r '.ssh_host // ""' "$config_dir/operational.json" 2>/dev/null)
        saved_connection_method=$(jq -r '.connection_method // ""' "$config_dir/operational.json" 2>/dev/null)
        saved_mgmt_ip=$(jq -r '.mgmt_ip // "N/A"' "$config_dir/operational.json" 2>/dev/null)
        # Preserve device state and versions (set by monitor/wizard live detection)
        saved_device_state=$(jq -r '.device_state // ""' "$config_dir/operational.json" 2>/dev/null)
        saved_dnos_version=$(jq -r '.dnos_version // "N/A"' "$config_dir/operational.json" 2>/dev/null)
        saved_gi_version=$(jq -r '.gi_version // "N/A"' "$config_dir/operational.json" 2>/dev/null)
        saved_baseos_version=$(jq -r '.baseos_version // "N/A"' "$config_dir/operational.json" 2>/dev/null)
    fi
    
    # System Type: SA-40C, CL-96, etc.
    local system_type=$(grep -m1 "System Type:" "$output" | sed 's/.*System Type: //' | cut -d',' -f1 | tr -d ' ')
    system_type="${system_type:-N/A}"
    
    # Preserve saved system_type if current extraction returned N/A (device might be in GI mode)
    if [ "$system_type" = "N/A" ] && [ "$saved_system_type" != "N/A" ]; then
        system_type="$saved_system_type"
        echo "[INFO] Preserved system_type from previous extraction: $system_type"
    fi
    
    # System Uptime
    local system_uptime=$(grep -m1 "System Uptime:" "$output" | sed 's/.*System Uptime: //' | tr -d '\r')
    system_uptime="${system_uptime:-N/A}"
    
    # Serial Number - from NCP row in system nodes table (for SA system, box S/N is on NCP row)
    # Format: | Type | Id | Admin | Operational | Model | Uptime | Description | Serial Number |
    # Serial Number is in column 9 (field 9 when split by |)
    # For cluster systems, we take the first NCP that is "up" and has a serial number
    local serial_number=$(awk -F'|' '/^\|[[:space:]]*(NCP|ncp)[[:space:]]*\|/ {
        # Check if NCP is in "up" state (column 5 = Operational)
        oper = $5
        gsub(/^[ \t]+|[ \t]+$/, "", oper)
        if (oper !~ /^up/) next
        
        # Serial number is in field 9 (the 8th actual column, after 8 pipes)
        sn = $9
        gsub(/^[ \t]+|[ \t]+$/, "", sn)
        # Also try last field if $9 is empty (different table formats)
        if (sn == "" || sn ~ /^[[:space:]]*$/) {
            sn = $NF
            gsub(/^[ \t]+|[ \t]+$/, "", sn)
        }
        # Print only if valid serial (not empty, not header, not uptime-like)
        if (sn != "" && sn !~ /Serial/ && sn !~ /^[[:space:]]*$/ && sn !~ /^[0-9]+:[0-9]+:[0-9]+$/ && sn !~ /days/) print sn
    }' "$output" | head -1 | tr -d '\r')
    serial_number="${serial_number:-N/A}"
    
    # Preserve saved serial_number if current extraction returned N/A (device might be in GI mode)
    if [ "$serial_number" = "N/A" ] && [ "$saved_serial_number" != "N/A" ]; then
        serial_number="$saved_serial_number"
        echo "[INFO] Preserved serial_number from previous extraction: $serial_number"
    fi
    
    # Management IP (mgmt0) - from show interfaces management
    # Format: | mgmt0 | enabled | up | 100.64.7.202/20 (d) | ... |
    local mgmt_ip=$(awk -F'|' '/^\|[[:space:]]*mgmt0[[:space:]]*\|/ {
        ip = $5
        gsub(/^[ \t]+|[ \t]+$/, "", ip)
        # Remove DHCP indicator (d) and subnet mask for clean IP
        gsub(/ *\(d\)/, "", ip)
        print ip
    }' "$output" | head -1 | tr -d '\r')
    mgmt_ip="${mgmt_ip:-N/A}"
    
    # Preserve saved mgmt_ip if current extraction returned N/A (device might be in GI mode)
    if [ "$mgmt_ip" = "N/A" ] && [ -n "$saved_mgmt_ip" ] && [ "$saved_mgmt_ip" != "N/A" ]; then
        mgmt_ip="$saved_mgmt_ip"
        echo "[INFO] Preserved mgmt_ip from previous extraction: $mgmt_ip"
    fi
    
    # Node counts from the table: | Type | ID | Admin | Operational | ...
    # Count NCCs (up = active-up or standby-up)
    local ncc_total=$(awk -F'|' '/^\|[[:space:]]*NCC[[:space:]]*\|/ {count++} END {print count+0}' "$output")
    local ncc_up=$(awk -F'|' '/^\|[[:space:]]*NCC[[:space:]]*\|/ && ($5 ~ /active-up|standby-up/) {count++} END {print count+0}' "$output")
    
    # Count NCPs (up = "up" in operational column)
    local ncp_total=$(awk -F'|' '/^\|[[:space:]]*NCP[[:space:]]*\|/ {count++} END {print count+0}' "$output")
    local ncp_up=$(awk -F'|' '/^\|[[:space:]]*NCP[[:space:]]*\|/ && $5 ~ /[[:space:]]up[[:space:]]/ {count++} END {print count+0}' "$output")
    
    # Count NCFs
    local ncf_total=$(awk -F'|' '/^\|[[:space:]]*NCF[[:space:]]*\|/ {count++} END {print count+0}' "$output")
    local ncf_up=$(awk -F'|' '/^\|[[:space:]]*NCF[[:space:]]*\|/ && $5 ~ /[[:space:]]up[[:space:]]/ {count++} END {print count+0}' "$output")
    
    # Count NCMs
    local ncm_total=$(awk -F'|' '/^\|[[:space:]]*NCM[[:space:]]*\|/ {count++} END {print count+0}' "$output")
    local ncm_up=$(awk -F'|' '/^\|[[:space:]]*NCM[[:space:]]*\|/ && $5 ~ /[[:space:]]up[[:space:]]/ {count++} END {print count+0}' "$output")
    
    # Ensure counts are valid
    ncc_total="${ncc_total:-0}"
    ncc_up="${ncc_up:-0}"
    ncp_total="${ncp_total:-0}"
    ncp_up="${ncp_up:-0}"
    ncf_total="${ncf_total:-0}"
    ncf_up="${ncf_up:-0}"
    ncm_total="${ncm_total:-0}"
    ncm_up="${ncm_up:-0}"
    
    # ========================================================================
    # PARSE ROUTING INFO
    # ========================================================================
    local router_id=$(grep -m1 "router identifier\|Router id:" "$output" 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | head -1 | tr -d '\n\r')
    router_id="${router_id:-}"
    # Extract AS number after "local AS number" text (not the router-id IP before it)
    local local_as=$(grep -m1 "local AS number" "$output" 2>/dev/null | sed 's/.*local AS number //' | grep -oE '^[0-9]+' | head -1 | tr -d '\n\r')
    local_as="${local_as:-}"
    
    # IGP detection
    local igp="None"
    if grep -q "ISIS routes max" "$output"; then
        igp="IS-IS"
    fi
    if grep -q "OSPF Routing Process" "$output" && ! grep -q "not enabled" "$output"; then
        igp="OSPF"
    fi
    
    # LDP/SR detection  
    local label_proto="None"
    if grep -q "Admin state: enabled" "$output"; then
        label_proto="LDP"
    fi
    
    # BGP neighbor count - parse from "Total number of established neighbors" line
    # Format: "Total number of established neighbors with IPv4 Unicast 1/2" means 1 up out of 2
    # We take the FIRST occurrence (usually IPv4 Unicast) as the canonical count
    local bgp_total_line=$(grep -m1 "Total number of established neighbors" "$output" 2>/dev/null)
    
    if [[ -n "$bgp_total_line" ]]; then
        # Extract "X/Y" pattern - X is up, Y is total
        local bgp_ratio=$(echo "$bgp_total_line" | grep -oE '[0-9]+/[0-9]+' | head -1)
        bgp_up=$(echo "$bgp_ratio" | cut -d'/' -f1)
        bgp_neighbors=$(echo "$bgp_ratio" | cut -d'/' -f2)
    else
        bgp_neighbors=0
        bgp_up=0
    fi
    
    bgp_neighbors=${bgp_neighbors:-0}
    bgp_up=${bgp_up:-0}
    
    # ========================================================================
    # PARSE SERVICE COUNTS
    # ========================================================================
    # FXC service count and UP status (from show evpn-vpws-fxc output)
    local fxc_count=$(grep -c "| FXC-" "$output" 2>/dev/null | head -1 || echo 0)
    local fxc_up=$(grep "| FXC-" "$output" 2>/dev/null | grep -ci "| up " 2>/dev/null | head -1 || echo 0)
    
    # VRF service count and UP status using awk
    local vrf_count=$(awk -F'|' '/^\|/ && $2 ~ /VRF/ && !/VRF Name|Instance/ {count++} END {print count+0}' "$output" 2>/dev/null)
    local vrf_up=$(awk -F'|' '/^\|/ && $2 ~ /VRF/ && /[Uu]p/ {count++} END {print count+0}' "$output" 2>/dev/null)
    
    # EVPN service count and UP status (EVPN-VPLS)
    local evpn_count=$(awk -F'|' '/^\|/ && $2 ~ /EVPN-[0-9]/ && !/Instance/ {count++} END {print count+0}' "$output" 2>/dev/null)
    local evpn_up=$(awk -F'|' '/^\|/ && $2 ~ /EVPN-[0-9]/ && /[Uu]p/ {count++} END {print count+0}' "$output" 2>/dev/null)
    
    # VPWS service count - use show evpn-vpws summary for accurate counts
    # Output format: "Total EVPN-VPWS instances: N" and "Up: N" / "Down: N"
    local vpws_count=$(grep -i "Total EVPN-VPWS" "$output" 2>/dev/null | grep -oE '[0-9]+' | head -1 || echo 0)
    local vpws_up=$(grep -A2 "Total EVPN-VPWS" "$output" 2>/dev/null | grep -i "Up:" | grep -oE '[0-9]+' | head -1 || echo 0)
    
    # Fallback: try show vpws table format (VPWS-* names)
    if [ "${vpws_count:-0}" -eq 0 ]; then
        vpws_count=$(awk -F'|' '/^\|/ && $2 ~ /VPWS-[0-9]/ && !/Instance/ {count++} END {print count+0}' "$output" 2>/dev/null)
        vpws_up=$(awk -F'|' '/^\|/ && $2 ~ /VPWS-[0-9]/ && /[Uu]p/ {count++} END {print count+0}' "$output" 2>/dev/null)
    fi
    
    # Final fallback: count vpws-service-id from config
    if [ "${vpws_count:-0}" -eq 0 ]; then
        local running_cfg="$config_dir/running.txt"
        vpws_count=$(grep -c "vpws-service-id" "$running_cfg" 2>/dev/null || echo 0)
        vpws_up=$vpws_count  # Assume all up if counting from config
    fi
    
    # Ensure counts are valid JSON numbers (no leading zeros, default to 0)
    # Use arithmetic expansion to force proper integer format
    fxc_count=$(($(echo "${fxc_count:-0}" | tr -d '\n' | grep -oE '^[0-9]+' || echo 0) + 0))
    fxc_up=$(($(echo "${fxc_up:-0}" | tr -d '\n' | grep -oE '^[0-9]+' || echo 0) + 0))
    vrf_count=$(($(echo "${vrf_count:-0}" | tr -d '\n' | grep -oE '^[0-9]+' || echo 0) + 0))
    vrf_up=$(($(echo "${vrf_up:-0}" | tr -d '\n' | grep -oE '^[0-9]+' || echo 0) + 0))
    evpn_count=$(($(echo "${evpn_count:-0}" | tr -d '\n' | grep -oE '^[0-9]+' || echo 0) + 0))
    evpn_up=$(($(echo "${evpn_up:-0}" | tr -d '\n' | grep -oE '^[0-9]+' || echo 0) + 0))
    vpws_count=$(($(echo "${vpws_count:-0}" | tr -d '\n' | grep -oE '^[0-9]+' || echo 0) + 0))
    vpws_up=$(($(echo "${vpws_up:-0}" | tr -d '\n' | grep -oE '^[0-9]+' || echo 0) + 0))
    
    # Total services
    local total_svc=$((fxc_count + vrf_count + evpn_count + vpws_count))
    
    # ========================================================================
    # PARSE INTERFACE COUNTS
    # ========================================================================
    local interfaces_total=0
    local interfaces_up=0
    local physical_total=0
    local physical_up=0
    local bundle_total=0
    local bundle_up=0
    local loopback_total=0
    local loopback_up=0
    local irb_total=0
    local irb_up=0
    local pwhe_total=0
    local pwhe_up=0
    
    # Extract interface stats using awk
    eval $(awk -F'|' '
    /^\|.*\|.*\|.*\|/ && !/Interface.*Admin/ {
        iface = $2
        gsub(/^[ \t]+|[ \t]+$/, "", iface)  # trim whitespace
        oper = $4
        gsub(/^[ \t]+|[ \t]+$/, "", oper)   # trim whitespace
        
        if (iface ~ /^(ge|ph)[0-9]/) {
            phys_total++
            if (oper ~ /^up/) phys_up++
        } else if (iface ~ /^bundle/) {
            bundle_total++
            if (oper ~ /^up/) bundle_up++
        } else if (iface ~ /^lo[0-9]/) {
            lo_total++
            if (oper ~ /^up/) lo_up++
        } else if (iface ~ /^irb/) {
            irb_total++
            if (oper ~ /^up/) irb_up++
        } else if (iface ~ /^pwhe/) {
            pwhe_total++
            if (oper ~ /^up/) pwhe_up++
        }
        total++
        if (oper ~ /^up/) up++
    }
    END {
        printf "interfaces_total=%d interfaces_up=%d ", total, up
        printf "physical_total=%d physical_up=%d ", phys_total, phys_up
        printf "bundle_total=%d bundle_up=%d ", bundle_total, bundle_up
        printf "loopback_total=%d loopback_up=%d ", lo_total, lo_up
        printf "irb_total=%d irb_up=%d ", irb_total, irb_up
        printf "pwhe_total=%d pwhe_up=%d", pwhe_total, pwhe_up
    }
    ' "$output")
    
    # ========================================================================
    # DETECT RECOVERY MODE
    # ========================================================================
    # Recovery indicators:
    # 1. All NCCs down (ncc_total > 0 but ncc_up == 0)
    # 2. System uptime = N/A + all interfaces down
    local recovery_mode="false"
    local recovery_time="null"
    local recovery_type=""
    
    # Check if all NCCs are down (critical recovery indicator)
    if [ "$ncc_total" -gt 0 ] && [ "$ncc_up" -eq 0 ]; then
        recovery_mode="true"
        recovery_time="\"$(date -Iseconds)\""
        recovery_type="DN_RECOVERY"
        echo "[WARN] RECOVERY MODE DETECTED: All NCCs down ($ncc_up/$ncc_total UP) - DN_RECOVERY"
    # Check if one NCC down (degraded but operational)
    elif [ "$ncc_total" -eq 2 ] && [ "$ncc_up" -eq 1 ]; then
        recovery_mode="true"
        recovery_time="\"$(date -Iseconds)\""
        recovery_type="STANDALONE"
        echo "[WARN] DEGRADED MODE DETECTED: One NCC down ($ncc_up/$ncc_total UP) - STANDALONE"
    # Check if uptime is N/A and all interfaces are down (secondary indicator)
    elif [ "$system_uptime" = "N/A" ] && [ "${interfaces_up:-0}" -eq 0 ] && [ "${interfaces_total:-0}" -gt 0 ]; then
        recovery_mode="true"
        recovery_time="\"$(date -Iseconds)\""
        recovery_type="DN_RECOVERY"
        echo "[WARN] RECOVERY MODE DETECTED: No uptime + all interfaces down - DN_RECOVERY"
    # If none of the current recovery conditions match, clear any stale recovery flags
    # The device has recovered (NCCs up, interfaces working, uptime exists)
    else
        recovery_mode="false"
        recovery_time="null"
        recovery_type=""
        if [ "$saved_recovery_mode" = "true" ]; then
            echo "[INFO] Recovery flag cleared for $hostname (was: $saved_recovery_type) - device appears healthy"
        fi
    fi
    
    # Extract config portion (raw config only - Python adds enhanced summary)
    # Use temp file to avoid overwriting good config with empty file on extraction failure
    local temp_config="$config_dir/.running.txt.tmp"
    sed -n '/config-start/,/config-end/p' "$output" > "$temp_config"
    
    # Only replace running.txt if we got valid config (>50 lines)
    local temp_lines=$(wc -l < "$temp_config" 2>/dev/null || echo 0)
    if [ "$temp_lines" -gt 50 ]; then
        mv "$temp_config" "$config_dir/running.txt"
    else
        rm -f "$temp_config"
        log "$name: SSH extraction returned only $temp_lines lines - keeping existing config"
        # Check if we have an existing running.txt to use
        if [ ! -f "$config_dir/running.txt" ] || [ ! -s "$config_dir/running.txt" ]; then
            # Try to restore from latest history if available
            local latest_history=$(ls -1t "$history_dir"/*.txt 2>/dev/null | head -1)
            if [ -n "$latest_history" ] && [ -f "$latest_history" ]; then
                log "$name: Restoring from history file: $latest_history"
                cp "$latest_history" "$config_dir/running.txt"
            else
                log "$name: No history to restore from - FAILED"
                rm -f "$config_dir/full_output.txt"
                return 1
            fi
        fi
    fi
    
    # WAN interfaces - find interfaces with 'mpls enabled' in config
    local wan_interfaces=$(awk '
    /^  [a-zA-Z]/ && !/^    / {
        gsub(/^  /, "")
        current_iface = $1
    }
    /mpls enabled/ {
        print current_iface
    }
    ' "$config_dir/running.txt" 2>/dev/null)
    
    local wan_total
    if [ -n "$wan_interfaces" ]; then
        wan_total=$(echo "$wan_interfaces" | grep -c . 2>/dev/null)
    else
        wan_total=0
    fi
    local wan_up=0
    
    # Check UP status by looking up each WAN interface in the show interfaces output
    if [ -n "$wan_interfaces" ] && [ -f "$output" ]; then
        local iface_status_file=$(mktemp)
        grep -E '^\|[[:space:]]+(ge[0-9]|lo[0-9]|bundle|irb|ph[0-9]|ipmi)' "$output" 2>/dev/null | awk -F'|' '{
            iface=$2; oper=$4
            gsub(/^[ \t]+|[ \t]+$/, "", iface)
            gsub(/^[ \t]+|[ \t]+$/, "", oper)
            print iface, oper
        }' > "$iface_status_file"
        
        for iface in $wan_interfaces; do
            status=$(grep "^${iface} " "$iface_status_file" 2>/dev/null | head -1 | awk '{print $2}')
            if [ "$status" = "up" ]; then
                wan_up=$((wan_up + 1))
            fi
        done
        rm -f "$iface_status_file"
    fi
    
    # Ensure WAN counts are valid
    wan_total=$(echo "${wan_total:-0}" | tr -d '\n' | grep -oE '^[0-9]+' || echo 0)
    wan_up=$(echo "${wan_up:-0}" | tr -d '\n' | grep -oE '^[0-9]+' || echo 0)
    
    # ========================================================================
    # PARSE LLDP NEIGHBORS (show lldp neighbor)
    # Format: | Interface | Neighbor System Name | Neighbor interface | Neighbor TTL |
    # Used to suggest LOCAL interfaces connected to other devices for L2-AC
    # ========================================================================
    local lldp_json="[]"
    
    # Parse LLDP table - only between LLDP header and next prompt
    # Key: look for the specific LLDP header format with "Neighbor System Name"
    lldp_json=$(awk -F'|' '
    # Start capturing after we see the LLDP table header
    /Interface.*Neighbor System Name.*Neighbor interface/ { in_lldp=1; next }
    # Stop at any prompt line or empty section
    /^[A-Za-z_-]+#/ || /^$/ { if (in_lldp) in_lldp=0 }
    # Skip separator lines
    /^[|][-+]+[|]/ { next }
    # Process LLDP entries only while in_lldp is set
    in_lldp && NF >= 4 {
        iface = $2
        neighbor = $3
        remote_port = $4
        gsub(/^[ \t]+|[ \t]+$/, "", iface)
        gsub(/^[ \t]+|[ \t]+$/, "", neighbor)
        gsub(/^[ \t]+|[ \t]+$/, "", remote_port)
        
        # Only physical interfaces with valid neighbor names
        if (iface ~ /^(ge|xe|et|hu)[0-9]+-[0-9]+\/[0-9]+\/[0-9]+$/ && neighbor != "" && neighbor !~ /^$|Neighbor/) {
            # Detect if neighbor is a DN device (DNAAS fabric or local DN)
            is_dn = (neighbor ~ /DNAAS|LEAF|SPINE|TOR|NCM|NCC|NCF|NCP|PE-|CE-|YOR_|TLV_|drivenets/i) ? "true" : "false"
            printf "{\"interface\":\"%s\",\"neighbor\":\"%s\",\"remote_port\":\"%s\",\"is_dn_device\":%s}\n", iface, neighbor, remote_port, is_dn
        }
    }' "$output" 2>/dev/null | sort -u | paste -sd, | sed 's/^/[/' | sed 's/$/]/')
    
    # Ensure valid JSON
    if [ -z "$lldp_json" ] || [ "$lldp_json" = "[]" ]; then
        lldp_json="[]"
    elif ! echo "$lldp_json" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
        lldp_json="[]"
    fi
    
    local lldp_count=$(echo "$lldp_json" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo 0)
    
    # ========================================================================
    # SAVE OPERATIONAL DATA AS JSON
    # ========================================================================
    cat > "$config_dir/operational.json" << EOF
{
    "router_id": $([ -n "$router_id" ] && echo "\"$router_id\"" || echo "null"),
    "local_as": $([ -n "$local_as" ] && echo "$local_as" || echo "null"),
    "igp": "$igp",
    "label_protocol": "$label_proto",
    "bgp_neighbors": ${bgp_neighbors:-0},
    "bgp_up": ${bgp_up:-0},
    "dnos_version": "$([ "$dnos_version" = "N/A" ] && [ -n "$saved_dnos_version" ] && [ "$saved_dnos_version" != "N/A" ] && echo "$saved_dnos_version" || echo "$dnos_version")",
    "baseos_version": "$([ "$baseos_version" = "N/A" ] && [ -n "$saved_baseos_version" ] && [ "$saved_baseos_version" != "N/A" ] && echo "$saved_baseos_version" || echo "$baseos_version")",
    "gi_version": "$([ "$gi_version" = "N/A" ] && [ -n "$saved_gi_version" ] && [ "$saved_gi_version" != "N/A" ] && echo "$saved_gi_version" || echo "$gi_version")",
    "stack_url": "$stack_url",
    "dnos_url": "$dnos_url",
    "gi_url": "$gi_url",
    "baseos_url": "$baseos_url",
    "install_type": "$install_type",
    "install_status": "$install_status",
    "install_start": "$install_start",
    "install_elapsed": "$install_elapsed",
    "install_finish": "$install_finish",
    "upgrade_in_progress": $upgrade_in_progress,
    "upgrade_progress": "$upgrade_progress",
    "upgrade_status": "$upgrade_task_status",
    "nodes_upgrading": "$nodes_upgrading",
    "system_type": "$system_type",
    "system_uptime": "$system_uptime",
    "serial_number": "$serial_number",
    "mgmt_ip": "$mgmt_ip",
    "ssh_host": "${saved_ssh_host:-}",
    "connection_method": "${saved_connection_method:-}",
    "ncc_total": $ncc_total,
    "ncc_up": $ncc_up,
    "ncp_total": $ncp_total,
    "ncp_up": $ncp_up,
    "ncf_total": $ncf_total,
    "ncf_up": $ncf_up,
    "ncm_total": $ncm_total,
    "ncm_up": $ncm_up,
    "interfaces_total": ${interfaces_total:-0},
    "interfaces_up": ${interfaces_up:-0},
    "physical_total": ${physical_total:-0},
    "physical_up": ${physical_up:-0},
    "bundle_total": ${bundle_total:-0},
    "bundle_up": ${bundle_up:-0},
    "loopback_total": ${loopback_total:-0},
    "loopback_up": ${loopback_up:-0},
    "irb_total": ${irb_total:-0},
    "irb_up": ${irb_up:-0},
    "pwhe_total": ${pwhe_total:-0},
    "pwhe_up": ${pwhe_up:-0},
    "wan_total": ${wan_total:-0},
    "wan_up": ${wan_up:-0},
    "fxc_total": ${fxc_count:-0},
    "fxc_up": ${fxc_up:-0},
    "vrf_total": ${vrf_count:-0},
    "vrf_up": ${vrf_up:-0},
    "evpn_total": ${evpn_count:-0},
    "evpn_up": ${evpn_up:-0},
    "vpws_total": ${vpws_count:-0},
    "vpws_up": ${vpws_up:-0},
    "lldp_neighbor_count": ${lldp_count:-0},
    "lldp_neighbors": $lldp_json,
    "recovery_mode_detected": $recovery_mode,
    "recovery_type": "$recovery_type",
    "recovery_mode_detected_at": $recovery_time,
    "device_state": "${saved_device_state:-}"
}
EOF
    
    local lines=$(wc -l < "$config_dir/running.txt")
    
    if [ "$lines" -gt 50 ]; then
        # === Smart History: Minimal files - only save when config changes ===
        local new_history_file="${FRIENDLY_DATE}_${name}.txt"
        local current_datetime=$(date +"%Y-%m-%d %H:%M")
        
        # Find the most recent history file (exclude metadata files)
        local last_history=$(ls -t "$history_dir"/*.txt 2>/dev/null | grep -vE '_meta' | head -1)
        
        if [ -n "$last_history" ]; then
            # Compare current config with last saved (skip header lines)
            local current_hash=$(grep -v "^#" "$config_dir/running.txt" | md5sum | cut -d' ' -f1)
            local last_hash=$(grep -v "^#" "$last_history" | md5sum | cut -d' ' -f1)
            local last_filename=$(basename "$last_history" .txt)
            
            # Extract start time from metadata or filename
            mkdir -p "$history_dir/.meta"
            local meta_file="$history_dir/.meta/${last_filename}.txt"
            local start_time=""
            
            if [ -f "$meta_file" ]; then
                start_time=$(grep "^start_time=" "$meta_file" | cut -d= -f2)
            else
                if [[ "$last_filename" =~ ^([0-9]{4})-([0-9]{2})-([0-9]{2})_([0-9]{2})-([0-9]{2})_ ]]; then
                    start_time="${BASH_REMATCH[1]}-${BASH_REMATCH[2]}-${BASH_REMATCH[3]} ${BASH_REMATCH[4]}:${BASH_REMATCH[5]}"
                fi
            fi
            
            if [ "$current_hash" != "$last_hash" ]; then
                # === CONFIG CHANGED ===
                log "$name: Config CHANGED - fetching rollback diff..."
                
                rollback_diff=$(expect -c "
set timeout 60
spawn sshpass -p dnroot ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o PubkeyAuthentication=no dnroot@$host
expect \"#\"
send \"show config compare rollback 1 | no-more\r\"
expect \"#\"
send \"exit\r\"
expect eof
" 2>&1 | grep -v "^spawn\|^Warning\|DRIVENETS" | sed -n '/show config compare/,/exit$/p' | grep -v "^dnroot@\|^exit$" | sed 's/\x1b\[[0-9;]*m//g' | tr -d '\r')
                
                local clean_diff=$(echo "$rollback_diff" | grep -E "^(Added:|Deleted:|  +[+-]|#.*config-)" | head -50 | tr -d '\r')
                
                local prev_end_time=""
                if [ -f "$meta_file" ]; then
                    prev_end_time=$(grep "^end_time=" "$meta_file" | cut -d= -f2)
                fi
                
                # Generate detailed header using Python
                local detailed_header=$(python3 -c "
import sys
sys.path.insert(0, '$SCALER_DIR')
import json
from scaler.config_parser import ConfigParser

parser = ConfigParser()

with open('$config_dir/running.txt') as f:
    raw_config = f.read()
with open('$config_dir/operational.json') as f:
    ops_data = json.load(f)

parsed = parser.parse(raw_config)
header = parser.generate_history_header('$name', parsed, raw_config, ops_data)
print(header)
" 2>/dev/null)
                
                # Create NEW history file
                {
                    echo "#==============================================================================="
                    echo "# $name Configuration History"
                    echo "# Changed: $current_datetime"
                    if [ -n "$prev_end_time" ] && [ "$start_time" != "$prev_end_time" ]; then
                        echo "# Previous config was unchanged from: ${start_time:-Unknown} to $prev_end_time"
                    else
                        echo "# Previous config was unchanged from: ${start_time:-Unknown}"
                    fi
                    echo "#==============================================================================="
                    if [ -n "$detailed_header" ]; then
                        echo "$detailed_header" | sed 's/^/#/'
                    fi
                    echo "#==============================================================================="
                    if [ -n "$clean_diff" ]; then
                        echo "# ROLLBACK DIFF (changes from previous):"
                        # Visual markers: ✚ for added, ✖ for deleted
                        echo "$clean_diff" | while IFS= read -r line; do
                            if [[ "$line" =~ ^[[:space:]]*\+ ]] || [[ "$line" == "Added:"* ]]; then
                                # Green plus marker for added lines
                                echo "# ✚ ${line}"
                            elif [[ "$line" =~ ^[[:space:]]*-[^0-9] ]] || [[ "$line" == "Deleted:"* ]]; then
                                # Red X marker for deleted lines
                                echo "# ✖ ${line}"
                            else
                                echo "# ${line}"
                            fi
                        done
                        echo "#==============================================================================="
                    fi
                    cat "$config_dir/running.txt"
                } > "$history_dir/$new_history_file"
                
                # Finalize the previous file's header
                if [ -f "$meta_file" ]; then
                    local end_time=$(grep "^end_time=" "$meta_file" | cut -d= -f2)
                    local prev_count=$(grep "^count=" "$meta_file" | cut -d= -f2)
                    local temp_file=$(mktemp)
                    {
                        echo "#==============================================================================="
                        echo "# $name Configuration History"
                        echo "# Unchanged: $start_time to ${end_time:-$current_datetime}"
                        echo "# ($prev_count checks, no changes during this period)"
                        echo "#==============================================================================="
                        grep -v "^#" "$last_history"
                    } > "$temp_file"
                    mv "$temp_file" "$last_history"
                    rm -f "$meta_file"
                fi
                
                # Start tracking the NEW file's unchanged period
                local new_meta_file="$history_dir/.meta/${FRIENDLY_DATE}_${name}.txt"
                cat > "$new_meta_file" << METAEOF
start_time=$current_datetime
end_time=$current_datetime
count=1
METAEOF
                
                # Update operational.json
                python3 -c "
import json
with open('$config_dir/operational.json', 'r') as f:
    data = json.load(f)
data['unchanged_since'] = '$current_datetime'
data['unchanged_until'] = '$current_datetime'
data['unchanged_checks'] = 1
data['config_changed'] = True
with open('$config_dir/operational.json', 'w') as f:
    json.dump(data, f, indent=4)
" 2>/dev/null
                
                log "$name: SUCCESS - Config changed, saved $new_history_file"
            else
                # === NO CHANGE ===
                local extraction_count=1
                if [ -f "$meta_file" ]; then
                    extraction_count=$(grep "^count=" "$meta_file" | cut -d= -f2)
                    ((extraction_count++))
                else
                    start_time="${start_time:-$current_datetime}"
                fi
                
                # Update metadata
                cat > "$meta_file" << METAEOF
start_time=$start_time
end_time=$current_datetime
count=$extraction_count
METAEOF
                
                # Regenerate detailed header with CURRENT operational data
                local detailed_header=$(python3 -c "
import sys
sys.path.insert(0, '$SCALER_DIR')
import json
from scaler.config_parser import ConfigParser

parser = ConfigParser()

with open('$config_dir/running.txt') as f:
    raw_config = f.read()
with open('$config_dir/operational.json') as f:
    ops_data = json.load(f)

parsed = parser.parse(raw_config)
header = parser.generate_history_header('$name', parsed, raw_config, ops_data)
print(header)
" 2>/dev/null)
                
                # Rebuild the file with updated header
                local temp_file=$(mktemp)
                {
                    echo "#==============================================================================="
                    echo "# $name Configuration History"
                    echo "# Created: $(echo "$last_filename" | sed 's/_/ /g' | sed 's/-/:/4' | sed 's/-/:/5' | awk '{print $1" "$2}')"
                    echo "#==============================================================================="
                    echo "# Unchanged since: $start_time to $current_datetime ($extraction_count checks)"
                    if [ -n "$detailed_header" ]; then
                        echo "$detailed_header" | sed 's/^/#/'
                    fi
                    echo "#==============================================================================="
                    grep -v "^#" "$last_history"
                } > "$temp_file"
                mv "$temp_file" "$last_history"
                
                log "$name: No change - $start_time to $current_datetime ($extraction_count checks)"
                
                # Update operational.json with unchanged_since info
                python3 -c "
import json
with open('$config_dir/operational.json', 'r') as f:
    data = json.load(f)
data['unchanged_since'] = '$start_time'
data['unchanged_until'] = '$current_datetime'
data['unchanged_checks'] = $extraction_count
with open('$config_dir/operational.json', 'w') as f:
    json.dump(data, f, indent=4)
" 2>/dev/null
            fi
        else
            # First extraction ever
            local detailed_header=$(python3 -c "
import sys
sys.path.insert(0, '$SCALER_DIR')
import json
from scaler.config_parser import ConfigParser

parser = ConfigParser()

with open('$config_dir/running.txt') as f:
    raw_config = f.read()
with open('$config_dir/operational.json') as f:
    ops_data = json.load(f)

parsed = parser.parse(raw_config)
header = parser.generate_history_header('$name', parsed, raw_config, ops_data)
print(header)
" 2>/dev/null)
            
            {
                echo "#==============================================================================="
                echo "# $name Configuration History"
                echo "# Created: $current_datetime"
                echo "#==============================================================================="
                if [ -n "$detailed_header" ]; then
                    echo "$detailed_header" | sed 's/^/#/'
                fi
                echo "#==============================================================================="
                cat "$config_dir/running.txt"
            } > "$history_dir/$new_history_file"
            
            mkdir -p "$history_dir/.meta"
            cat > "$history_dir/.meta/${FRIENDLY_DATE}_${name}.txt" << METAEOF
start_time=$current_datetime
end_time=$current_datetime
count=1
METAEOF
            
            python3 -c "
import json
with open('$config_dir/operational.json', 'r') as f:
    data = json.load(f)
data['unchanged_since'] = '$current_datetime'
data['unchanged_until'] = '$current_datetime'
data['unchanged_checks'] = 1
with open('$config_dir/operational.json', 'w') as f:
    json.dump(data, f, indent=4)
" 2>/dev/null
            
            log "$name: SUCCESS - First extraction saved as $new_history_file"
        fi
    else
        log "$name: FAILED - only $lines lines"
    fi
    
    # Cleanup - remove temporary and unused files
    rm -f "$config_dir/full_output.txt"
    rm -f "$config_dir/operational.txt"      # Legacy file, not used
    rm -f "$config_dir/history_meta.json"    # Merged into operational.json
    rm -f "$config_dir/running.json"         # Can be regenerated if needed
}

log "=== Starting config extraction ==="

# ============================================================================
# DYNAMIC DEVICE EXTRACTION FROM devices.json
# Reads all devices from the database and extracts their configs
# ============================================================================

DEVICES_FILE="$SCALER_DIR/db/devices.json"

if [ -f "$DEVICES_FILE" ]; then
    log "Reading devices from $DEVICES_FILE"
    
    # Parse devices.json and extract for each device
    # Uses jq to parse JSON, fallback to python if jq not available
    if command -v jq &> /dev/null; then
        # Use jq for parsing
        device_count=$(jq '.devices | length' "$DEVICES_FILE" 2>/dev/null || echo 0)
        log "Found $device_count devices in database"
        
        for i in $(seq 0 $((device_count - 1))); do
            hostname=$(jq -r ".devices[$i].hostname" "$DEVICES_FILE")
            ip=$(jq -r ".devices[$i].ip" "$DEVICES_FILE")
            
            # Skip if no valid IP/hostname
            if [ -z "$hostname" ] || [ "$hostname" = "null" ]; then
                log "Skipping device $i - missing hostname"
                continue
            fi
            
            # Skip GI-mode devices -- SSH extraction is pointless (DNOS not running)
            # These devices are reachable via console/virsh but not via SSH to mgmt IP
            local op_file="$SCALER_DIR/db/configs/$hostname/operational.json"
            if [ -f "$op_file" ]; then
                local dev_state=$(jq -r '.device_state // ""' "$op_file" 2>/dev/null)
                local del_init=$(jq -r '.delete_initiated // ""' "$op_file" 2>/dev/null)
                if [ "$dev_state" = "GI" ] || [ "$dev_state" = "RECOVERY" ] || [ "$dev_state" = "DEPLOYING" ] || [ "$dev_state" = "BASEOS_SHELL" ]; then
                    local conn_method=$(jq -r '.connection_method // "unknown"' "$op_file" 2>/dev/null)
                    log "$hostname: Skipping SSH extraction -- device is in $dev_state mode (reachable via $conn_method)"
                    clear_alert "$hostname" "stale_data"
                    clear_alert "$hostname" "extraction_failed"
                    continue
                fi
                # Also skip if system delete was recently initiated (device is rebooting into GI)
                if [ -n "$del_init" ] && [ "$del_init" != "null" ]; then
                    local del_epoch=$(date -d "$del_init" +%s 2>/dev/null || echo 0)
                    local now_epoch=$(date +%s)
                    local age=$(( now_epoch - del_epoch ))
                    if [ "$age" -lt 3600 ]; then
                        log "$hostname: Skipping SSH extraction -- system delete initiated ${age}s ago, device likely rebooting"
                        clear_alert "$hostname" "stale_data"
                        clear_alert "$hostname" "extraction_failed"
                        continue
                    fi
                fi
            fi
            
            # Multi-path IP resolution: try IP, then SN DNS lookup
            resolved_host=""
            
            # 1. Try devices.json IP
            if [ -n "$ip" ] && [ "$ip" != "null" ]; then
                if timeout 2 bash -c "echo >/dev/tcp/$ip/22" 2>/dev/null; then
                    resolved_host="$ip"
                else
                    log "$hostname: IP $ip unreachable, trying SN fallback..."
                fi
            fi
            
            # 2. If IP failed, try serial number DNS resolution
            if [ -z "$resolved_host" ]; then
                local op_file="$SCALER_DIR/db/configs/$hostname/operational.json"
                if [ -f "$op_file" ]; then
                    local sn=$(jq -r '.serial_number // ""' "$op_file" 2>/dev/null)
                    if [ -n "$sn" ] && [ "$sn" != "N/A" ] && [ "$sn" != "null" ]; then
                        local sn_ip=$(getent hosts "$sn" 2>/dev/null | awk '{print $1}' | head -1)
                        if [ -n "$sn_ip" ]; then
                            if timeout 2 bash -c "echo >/dev/tcp/$sn_ip/22" 2>/dev/null; then
                                resolved_host="$sn_ip"
                                log "$hostname: Resolved via SN $sn -> $sn_ip"
                            else
                                # Try connecting directly to SN hostname (SSH handles DNS)
                                if timeout 2 bash -c "echo >/dev/tcp/$sn/22" 2>/dev/null; then
                                    resolved_host="$sn"
                                    log "$hostname: Connecting via SN hostname $sn"
                                fi
                            fi
                        else
                            # DNS didn't resolve, try SN as hostname directly
                            if timeout 2 bash -c "echo >/dev/tcp/$sn/22" 2>/dev/null; then
                                resolved_host="$sn"
                                log "$hostname: Connecting via SN hostname $sn"
                            fi
                        fi
                    fi
                fi
            fi
            
            # 3. If both IP and SN DNS failed, try Network Mapper re-discovery
            if [ -z "$resolved_host" ]; then
                log "$hostname: IP and SN fallback failed, trying Network Mapper re-discovery..."
                local nm_ip=$(cd "$SCALER_DIR" && python3 -m scaler.recover_device_ip "$hostname" 2>/dev/null)
                if [ -n "$nm_ip" ]; then
                    resolved_host="$nm_ip"
                    log "$hostname: ✓ Recovered via Network Mapper -> $nm_ip (devices.json updated)"
                    
                    # Also update the IP variable so alerts use the new IP
                    ip="$nm_ip"
                fi
            fi
            
            if [ -n "$resolved_host" ]; then
                log "Extracting config for $hostname ($resolved_host)"
                extract_config "$resolved_host" "$hostname"
            else
                log "$hostname: All connection methods failed (IP: $ip)"
                # Track failure to trigger alerts
                local config_dir="$SCALER_DIR/db/configs/$hostname"
                mkdir -p "$config_dir"
                local track_result=$(track_extraction_result "$hostname" "false" "$config_dir")
                if echo "$track_result" | grep -q "ALERT_STALE"; then
                    add_alert "$hostname" "CRITICAL" "stale_data" \
                        "Device unreachable for 30+ minutes. Operational data is STALE and may not reflect reality. Last IP: $ip"
                elif echo "$track_result" | grep -q "ALERT_FAILING"; then
                    add_alert "$hostname" "WARNING" "extraction_failed" \
                        "Extraction failing for 15+ minutes. IP $ip may be wrong or device is down."
                fi
            fi
        done
    else
        # Fallback to Python for JSON parsing
        log "jq not found, using Python for JSON parsing"
        python3 -c "
import json
import subprocess
import sys

with open('$DEVICES_FILE') as f:
    data = json.load(f)

devices = data.get('devices', data if isinstance(data, list) else [])
print(f'Found {len(devices)} devices', file=sys.stderr)

for dev in devices:
    hostname = dev.get('hostname', '')
    ip = dev.get('ip', dev.get('management_ip', ''))
    if hostname and ip:
        print(f'{ip}|{hostname}')
" 2>/dev/null | while IFS='|' read -r ip hostname; do
            if [ -n "$hostname" ] && [ -n "$ip" ]; then
                # Skip GI/RECOVERY mode devices (same check as jq path above)
                local op_file="$SCALER_DIR/db/configs/$hostname/operational.json"
                if [ -f "$op_file" ]; then
                    local dev_state=$(jq -r '.device_state // ""' "$op_file" 2>/dev/null)
                    if [ "$dev_state" = "GI" ] || [ "$dev_state" = "RECOVERY" ] || [ "$dev_state" = "DEPLOYING" ] || [ "$dev_state" = "BASEOS_SHELL" ]; then
                        local conn_method=$(jq -r '.connection_method // "unknown"' "$op_file" 2>/dev/null)
                        log "$hostname: Skipping SSH extraction -- device is in $dev_state mode (reachable via $conn_method)"
                        clear_alert "$hostname" "stale_data"
                        clear_alert "$hostname" "extraction_failed"
                        continue
                    fi
                fi
                log "Extracting config for $hostname ($ip)"
                extract_config "$ip" "$hostname"
            fi
        done
    fi
else
    log "ERROR: devices.json not found at $DEVICES_FILE"
    log "Falling back to hardcoded devices..."
    # Fallback to known devices
    extract_config "wk31d7vv00023" "PE-1"
fi

log "=== Extraction complete ==="

# Run Python sync to add enhanced summary headers
log "Running Python sync for enhanced summaries..."
cd "$SCALER_DIR" && python3 -c "
from scaler.scheduler import ConfigSyncScheduler
scheduler = ConfigSyncScheduler()
scheduler.trigger_sync_now()
" >> "$LOG_FILE" 2>&1

log "=== Python sync complete ==="
