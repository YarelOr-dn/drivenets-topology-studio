# Cluster Post-Upgrade Recovery: NCP/NCF Stuck Disconnected After System Delete + Redeploy

## Incident: YOR_CL_PE-4 (CL-86) -- 2026-03-22

### Problem Statement

After `request system delete` followed by fresh DNOS deployment on a CL-86 cluster, only the
active NCC (NCC-1) received DNOS. All NCPs, NCFs, standby NCC, and standby NCM remained in
`disconnected` state with zero serial numbers and zero uptime. BGP sessions flapped continuously
(ACTIVE -> CONNECT) because no data plane interfaces were available.

### Environment

- Device: YOR_CL_PE-4 (CL-86, Family: NCR)
- Version: DNOS 26.2.0 build 22_priv
- NCC-1 (active): kvm108-cl408d-ncc1 (VM on KVM host)
- NCP-6, NCP-18: Physical UfiSpace S9700-53DX hardware (NCP-40C model)
- NCF 0-5: Physical NCF-48CD hardware
- NCM-A0: Physical NCM-48X-6C (serial AAF1944AAAJ)

---

## Investigation Methodology

### Step 1: Verify cluster component status

```
show system | no-more
```

Key indicators of the problem:
- NCPs/NCFs: `disconnected`, uptime `0:00:00`, serial number EMPTY
- Only NCC-1 shows `active-up` with serial number and uptime
- BGP neighbors cycling ACTIVE -> CONNECT every ~10 seconds

### Step 2: Check physical layer (NCM control ports)

```
show system backplane
show interfaces control
```

What we found:
- `ctrl-ncm-A0/30` (NCP-6 path): **UP** -- physical link active
- `ctrl-ncm-A0/42` (NCP-18 path): **UP** -- physical link active
- `ctrl-ncm-A0/16` (NCF-0 path): **UP** -- physical link active
- All others: `down` or `not-present` (expected -- only these slots are populated)

**Conclusion**: Physical hardware IS powered on and connected. Links are alive.
The backplane shows `unavailable-node` (v26.1+) = expected by topology but not yet deployed.

### Step 3: Check GI deployment history

```
show system install
```

What we found:
- Task 1774167921767: deploy, COMPLETED in 0:15:40
- Only 2 finished tasks: GI + DNOS on NCC-1
- Zero tasks for any NCP, NCF, NCC-0, NCM-B0
- Zero running tasks

**Conclusion**: The GI Manager deployed DNOS only to NCC-1 and never started the
add-node process for any other NCE.

### Step 4: Check control-network reachability from NCC-1

SSH into NCC-1 shell:
```
run start shell ncc 1
# password: dnroot
```

Then check ARP table on ctrl-bond:
```
ip netns exec host_ns ip addr show ctrl-bond
ip netns exec host_ns ip neigh show
```

What we found:
- ctrl-bond: UP with IP 192.168.240.2/20
- ARP table shows 3 hosts reachable: 192.168.240.10, .11, .12
- IPMI addresses: 192.168.255.0, 192.168.255.1 also in ARP table

**Conclusion**: NCPs/NCFs have control-network IP addresses and are reachable at L2/L3.

### Step 5: Check if NCP services are running

```
ip netns exec host_ns ssh -o ConnectTimeout=3 root@192.168.240.10 hostname
ip netns exec host_ns ssh -o ConnectTimeout=3 root@192.168.240.11 hostname
```

What we found:
- All 3 nodes: `Connection refused` on port 22
- No SSH daemon running on any NCP/NCF

**Conclusion**: The NCPs have network connectivity but are in a minimal state where
SSH/GI agent has NOT started. They are likely stuck in early BaseOS boot, ONIE shell,
or a state where the GI agent container failed to start.

### Step 6: Check CMC (Cluster Manager) logs

```
# Inside NCC-1 shell:
docker exec <cluster-engine-container> tail -80 /var/log/dn/cluster_manager_supervisor.log
```

What we found:
- CMC is actively processing `CMC_SYS_EVENT_ACTIVE_DOWNSTREAM_EVENT`
- Events are continuously sent to `ring disconnected_nces`
- The `inactive_entities_manager` thread is handling these events in a loop
- No new node registrations are logged
- The `discovery_broadcast` process (pid 780) is running
- The `gi_discovery_outband` process (pid 827) is running

**Conclusion**: The CMC is broadcasting discovery beacons and actively trying to reach
the disconnected NCEs, but no GI agent on any NCP/NCF is responding/registering.

### Step 7: Check discovery broadcast content

```
# Inside NCC-1 shell:
docker exec <ncc-conductor-container> cat /var/log/dn/discovery_broadcast_supervisor.log | tail -20
```

What we found:
- Beacon broadcast from IP 192.168.240.4 every 5 seconds
- Payload includes cluster UUID, cluster_identifier, and timestamp
- Beacons were sent during GI mode (pre-DNOS deployment)
- After DNOS deployment, the DNOS-mode beacon process took over

---

## Root Cause Analysis

The NCPs and NCFs are physically powered on and have control-network connectivity (NCM
links UP, IP addresses assigned), but their GI agents are NOT running. SSH on port 22
is refused, indicating that the BaseOS services (including GI agent and SSH daemon)
have not started or are failing to start.

After `request system delete`:
1. All nodes are moved to GI mode
2. DNOS configDB, keys, certificates are deleted on all nodes
3. When NCC-1 gets DNOS redeployed, it starts broadcasting CMC discovery beacons
4. NCP/NCF nodes should hear these beacons and register their GI agents with the CMC
5. The CMC then runs the add-node state machine: FW -> BaseOS -> DNOS deploy

The failure is at step 4: the NCP/NCF GI agents are not registering. Possible causes:

1. **GI agent crashed or failed to start on NCP** -- The most likely cause. After
   system delete, the NCP BaseOS may have started but the GI agent container failed.
2. **Cluster identifier mismatch** -- If the NCPs remember an old cluster UUID, they
   may reject the new CMC's beacons. However, system delete should clear this.
3. **BaseOS boot failure** -- The NCP BaseOS may have partially booted (enough for
   networking) but failed before starting Docker/GI agent.
4. **Console server interference** -- Known issue (CS-2570): console servers sending
   garbage characters during boot can interrupt GRUB, leaving NCPs stuck.

---

## Remediation Steps (ordered by likelihood of success)

### FIX 1: Nuclear Reset from NCP Console (highest success rate)

**Source:** [GI Logic | Basic Concepts](https://drivenets.atlassian.net/wiki/spaces/QA/pages/5271060596)

If you can get console access to the NCP, run from a privileged shell on the host:

```bash
docker swarm leave --force
reboot
```

This resets the node's deployment status and returns it to the embedded GI image.
After reboot, the GI agent will start fresh and discover the CMC via beacons.

To get console access, try IN THIS ORDER:

1. **Via IPMI from DNOS CLI** (fastest):
   ```
   run ipmi shell ncp 6
   # password: dnroot
   ```
   NOTE: This will FAIL if the NCM IPMI path to the NCP is broken (as in PE-4 case
   where backplane showed empty IPMI connection state).

2. **Via physical console server** (if connected):
   ```
   ssh <console_server_ip> -p <ncp_port>
   ```
   Check `scaler/db/configs/console_mappings.json` for port assignments.
   WARNING: Console servers can cause the problem (CS-2570) -- see Prevention section.

3. **Via IPMI BMC directly** (if you know the BMC IP):
   ```
   # From NCC-1 shell (run start shell ncc 1):
   ip netns exec host_ns ipmitool -H <NCP_BMC_IP> -U admin -P admin -I lanplus sol activate
   ```
   NCP BMC IPs are typically in the 192.168.255.x range on the ctrl-bond network.

4. **Via NCM switch shell** (access_host.sh path):
   ```
   run start shell ncm A0
   # password: dnroot
   # NCM uses StrataX CLI, not Linux. Use: oscmd <linux_command>
   ```

### FIX 2: Re-enable ctrl-bond from NCP Host (if NCP has SSH)

**Source:** [How to add NCP/F to cluster by disconnect/connect ctrl-bond](https://drivenets.atlassian.net/wiki/spaces/QA/pages/4114219229)

If the NCP has SSH accessible (port 22 open), access the NCP host and re-enable
the ctrl-bond interface:

```bash
# From DNOS CLI:
run start shell ncp 6
# password: dnroot

# Inside NCP container, access host:
access_host.sh

# Check ctrl-bond interface status:
ip link show ctrl-bond
ip link show enp2s0f0    # ctrl port 0
ip link show enp2s0f1    # ctrl port 1

# Re-enable if down:
ip link set enp2s0f0 up
```

After ctrl-bond comes up, the NCP will:
1. Receive CMC discovery beacons
2. GI agent connects to CMC
3. CMC starts versioning process (FW -> BaseOS -> DNOS)
4. NCP transitions: disconnected -> versioning -> dnos-deployment -> up

Expected timeline: ~10-15 minutes from ctrl-bond up to fully operational.

### FIX 3: Manual GI Agent Reset

**Source:** [G.I. Explained](https://drivenets.atlassian.net/wiki/spaces/QA/pages/3407642717)

If the NCP has SSH and the GI agent is stuck (not registering with CMC):

```bash
# Check node_flavor (should be "GI" after system delete):
cat /etc/node_flavor

# If it says DNOS but should be GI:
echo GI > /etc/node_flavor
systemctl restart gi-bootloader.service

# If it says GI but GI agent isn't running:
docker ps | grep gi
# If no gi_agent container:
systemctl restart gi-bootloader.service

# Nuclear option (resets everything):
docker swarm leave --force
reboot
```

### FIX 4: IPMI Power Cycle

If the NCP is completely unresponsive (no SSH, no console), and you have a working
IPMI path:

```bash
# From NCC-1 shell:
ip netns exec host_ns ipmitool -H <NCP_BMC_IP> -U admin -P admin -I lanplus power cycle
```

Or from DNOS CLI (requires NCM IPMI path working):
```
request system restart ncp 6
# Confirm: yes
```

NOTE: `request system restart ncp 6` uses the NCM's IPMI path. If the NCM backplane
shows empty IPMI connection state, this will fail with "NCP restart failed".

### FIX 5: Cluster ID Mismatch Resolution

**Source:** [G.I. Explained](https://drivenets.atlassian.net/wiki/spaces/QA/pages/3407642717)

After system delete, if the NCP still has an old Cluster ID, it will REJECT beacons
from the new CMC. The GI discovery listener compares:
  `broadcasted Cluster ID == Local Cluster ID`

If they don't match, the beacon is ignored.

To fix from NCP console:
```bash
# Check stored cluster ID:
cat /docker/volume/<hostname>_gi-persistent-data/_data/cm/cluster_id

# Remove it to accept any CMC:
rm /docker/volume/<hostname>_gi-persistent-data/_data/cm/cluster_id
docker swarm leave --force
reboot
```

### FIX 6: BaseOS Reinstall (ONIE mode)

If the NCP is in ONIE mode (no BaseOS at all), it needs a complete reinstall:

1. Ensure BaseOS image is loaded on the NCC:
   ```
   request system target-stack load http://<repo>/baseos-<version>.tar
   ```

2. Once the NCP registers (after getting BaseOS from ONIE), use:
   ```
   request system install retry ncp 6
   ```
   NOTE: `install retry` only works if the cluster is in a "failed" state for that node.

---

## Key Diagnostic Commands Summary

| What to Check | Command | Where to Run |
|---|---|---|
| Cluster component status | `show system` | DNOS CLI |
| Physical link status | `show interfaces control` | DNOS CLI |
| Control network topology | `show system backplane control` | DNOS CLI |
| Fabric connectivity | `show system backplane fabric` | DNOS CLI |
| GI deployment history | `show system install` | DNOS CLI |
| NCC shell access | `run start shell ncc 1` | DNOS CLI |
| NCP IPMI access | `run ipmi shell ncp <id>` | DNOS CLI |
| ctrl-bond status | `ip netns exec host_ns ip addr show ctrl-bond` | NCC Linux shell |
| ARP neighbors on ctrl-bond | `ip netns exec host_ns ip neigh show` | NCC Linux shell |
| CMC cluster manager log | `docker exec <cluster-engine> tail /var/log/dn/cluster_manager_supervisor.log` | NCC Linux shell |
| Discovery beacon log | `docker exec <ncc-conductor> cat /var/log/dn/discovery_broadcast_supervisor.log` | NCC Linux shell |
| Connectivity watchdog | `docker exec <ncc-conductor> cat /var/log/dn/connectivity_watchdog_supervisor.log` | NCC Linux shell |

---

## Key Indicators by NCP State

| NCP State | SSH Port 22 | ctrl-bond ARP | NCM Link | CMC Registration | Action |
|---|---|---|---|---|---|
| Powered off | N/A | No entry | down | No | IPMI power on |
| ONIE mode | Refused | May have entry | up | No | BaseOS install |
| BaseOS boot (early) | Refused | Has entry | up | No | Wait or check console |
| GI mode (agent running) | Open | Has entry | up | Yes | Wait for FW/BaseOS/DNOS deploy |
| GI mode (agent failed) | Refused | Has entry | up | No | Console access, restart agent |
| DNOS running | Open | Has entry | up | N/A (already joined) | Normal operation |

Current PE-4 NCP state matches: **GI mode with agent failed** (SSH refused, ARP entry
present, NCM link up, no CMC registration).

---

## Related Confluence Documentation

- [cluster-overview](https://drivenets.atlassian.net/wiki/spaces/~557058be7c2e9d0db24004a36470aee16954e8/pages/6309250009/cluster-overview) -- NCP join sequence, fabric health
- [deployment-and-lifecycle](https://drivenets.atlassian.net/wiki/spaces/~557058be7c2e9d0db24004a36470aee16954e8/pages/6309838993/deployment-and-lifecycle) -- System delete flow, node addition state machine
- [NCP upgrade issues](https://drivenets.atlassian.net/wiki/spaces/CS/pages/3476848651/NCP+upgrade+issues) -- Historical cases of NCPs stuck disconnected
- [CS-5880 NCF disconnected after deploy](https://drivenets.atlassian.net/wiki/spaces/~5570588b031dd398049199750a8fdd50b4c47/pages/3696918529) -- Similar root cause analysis
- [How to add NCP/F by ctrl-bond](https://drivenets.atlassian.net/wiki/spaces/QA/pages/4114219229) -- Manual NCP reconnection procedure

---

## Understanding the GI Discovery Flow (why it breaks)

**Source:** [G.I. Explained](https://drivenets.atlassian.net/wiki/spaces/QA/pages/3407642717)
and [GI Logic | Basic Concepts](https://drivenets.atlassian.net/wiki/spaces/QA/pages/5271060596)

After `request system delete`, ALL nodes move to GI mode. When DNOS is redeployed on
the active NCC, the following sequence MUST complete for each NCP/NCF:

1. NCC starts `ncc_discovery_broadcaster` (in cluster-engine container)
2. Broadcaster sends IPv6 Link-Local beacons on ctrl-bond every 5 seconds
3. NCP's `ncc_discovery_listener` (in gi-agent container) receives beacon
4. Listener checks: `beacon.cluster_id == local_cluster_id` (or local is "None"/default)
5. If match, EM connects to CMC using the IPv6 LL address from beacon
6. CMC collects stack terms, starts versioning (FW -> BaseOS -> DNOS deploy)

**Failure points:**
- Step 3 fails if GI agent on NCP didn't start (BaseOS boot issue, Docker failure)
- Step 4 fails if NCP has old Cluster ID that doesn't match new CMC's ID
- Step 3 also fails if ctrl-bond is DOWN on the NCP side

**How to verify the broadcaster is working** (from NCC-1 shell):
```bash
# Check broadcaster process:
docker exec <cluster-engine-container> ps aux | grep discover
# Should show: ncc_discovery_broadcaster and gi_discovery_outband

# Check beacon log (in ncc-conductor container):
docker exec <ncc-conductor-container> cat /var/log/dn/discovery_broadcast_supervisor.log | tail -5
# Should show: "Sending service announcement" every 5 seconds

# Check cluster manager for node events:
docker exec <cluster-engine-container> tail -20 /var/log/dn/cluster_manager_supervisor.log
# If all NCPs are disconnected, you'll see:
# CMC_SYS_EVENT_ACTIVE_DOWNSTREAM_EVENT sent to ring disconnected_nces (looping)
```

## Prevention

1. **Before running `request system delete`**: Ensure you have WORKING console access
   to NCPs. After delete, the GI agent on NCPs must register with the new CMC -- if
   it fails, you need console access to diagnose. Test `run ipmi shell ncp <id>` first.

2. **Disconnect console servers from NCPs during upgrade** (per CS-2570): Console
   servers sending garbage characters during boot interrupt GRUB, leaving NCPs stuck.
   This is the #1 cause of NCPs stuck disconnected in production (AT&T clusters).

3. **After deployment completes on NCC**: Check `show system` within 5-10 minutes.
   NCPs should start appearing in `initializing` or `versioning` state. If still
   `disconnected` after 15 minutes, the GI agents are stuck.

4. **Monitor `show system install`**: Active running tasks should appear for NCPs
   shortly after NCC deployment completes. If no tasks appear, the add-node process
   hasn't started -- the NCPs never registered with the CMC.

5. **Verify IPMI paths before upgrade**: Run `show system backplane` and confirm
   the IPMI ports (ipmi-ncp-X/0) show actual neighbor interface and "ok" connection
   state. If IPMI is empty/broken, you won't be able to restart NCPs remotely.

## Confluence Sources

| Page | Space | Why it's relevant |
|------|-------|-------------------|
| [GI Logic - Basic Concepts](https://drivenets.atlassian.net/wiki/spaces/QA/pages/5271060596) | QA | `docker swarm leave --force; reboot` nuclear reset, node_flavor file, discovery broadcaster/listener |
| [G.I. Explained](https://drivenets.atlassian.net/wiki/spaces/QA/pages/3407642717) | QA | Full GI architecture, Cluster ID matching, EM FSM, versioning flow |
| [How to add NCP/F by ctrl-bond](https://drivenets.atlassian.net/wiki/spaces/QA/pages/4114219229) | QA | Step-by-step ctrl-bond reconnection procedure with show system output examples |
| [NCP Upgrade Issues](https://drivenets.atlassian.net/wiki/spaces/CS/pages/3476848651) | CS | Historical table of all NCP stuck-disconnected cases and fixes |
| [Cluster Deployment](https://drivenets.atlassian.net/wiki/spaces/DV/pages/607879218) | DV | Local conductor add/remove node flows |
| [Deployment and Lifecycle](https://drivenets.atlassian.net/wiki/spaces/~557058be7c2e9d0db24004a36470aee16954e8/pages/6309838993) | Personal | System delete behavior, node addition state machine |
| [NCCM LCM & HA](https://drivenets.atlassian.net/wiki/spaces/DV/pages/4923261892) | DV | NCCM-based cluster NCP/NCF discovery and deployment |
| [CMC High Priority Bugs](https://drivenets.atlassian.net/wiki/spaces/~5c6e9e9f4b5199464e922f71/pages/5076582470) | Personal | Known CMC bugs that can cause stuck states |

## Historical Cases (from NCP Upgrade Issues page)

| Ticket | Symptom | Root Cause | Fix |
|--------|---------|------------|-----|
| CS-3549 | NCP disconnected after redeployment, console blank | BaseOS boot failure | IPMI power cycle |
| CS-2570 | NCPs 17,18,20,21 disconnected after BaseOS upgrade | Console server sending garbage to GRUB | Remove console, reboot |
| CS-2568 | NCPs stuck in "baseos-upgrade (failed)" | Console server GRUB interruption | Remove console, reboot |
| CS-2924 | NCP-20 down, no IPMI response, orange LED | Hardware failure (dead box) | Physical reboot by vendor |
| CS-1929 | Constant reboot of NCP-19/20 after deployment | ONIE can't recognize HDD | Hardware issue |
| CS-1740 | NCP didn't join after deployment | Salt process down on NCP | Investigate salt-minion logs |
