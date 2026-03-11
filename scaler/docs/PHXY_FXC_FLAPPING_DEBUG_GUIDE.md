# phX.Y / FXC Flapping Debug Guide

**Purpose:** Debug and identify root cause of phX.Y interface and FXC service flapping at scale.

---

## Quick Reference: Trace Locations

| Component | Trace Location | What to Look For |
|-----------|----------------|------------------|
| **wb_agent** (WBox) | `/core/traces/routing_engine/wb_agent` | FRR, interface state, FIB updates |
| **rib-manager** (Zebra) | `/core/traces/routing_engine/rib-manager_traces` | Route updates, nexthop changes, EoR |
| **fib-manager** | `/core/traces/routing_engine/fibmgrd_traces` | FIB distribution to NCPs |
| **bgpd** | `/core/traces/routing_engine/bgpd_traces` | EVPN routes, Type-4 ES routes, DF election |
| **CMC Interface Manager** | `/core/traces/management_engine/cmc*` | Interface state changes |
| **ISIS** | `/core/traces/routing_engine/isisd_traces` | IGP changes |

---

## Step 1: Observe Current State

### DNOS CLI Commands

```bash
# FXC Summary - Overall health
show evpn-vpws-fxc summary

# FXC Services - See up/down state and time in state
show evpn-vpws-fxc

# FXC Detail for specific instance
show evpn-vpws-fxc instance <name> detail

# Ethernet Segment Info - DF/BDF status
show evpn-vpws-fxc instance <name> ethernet-segments-info

# Count services by state
show evpn-vpws-fxc | include up | count
show evpn-vpws-fxc | include down | count

# Count recently changed services (0:00:XX = flapping)
show evpn-vpws-fxc | include "0 days, 0:00" | count

# MH Configuration count
show config network-services multihoming | include "interface ph" | count

# Interface count
show interfaces | include ph | count
```

### Key Metrics to Check

1. **Total Local MH ESIs** - Should be ≤ 2000 (DNOS limit)
2. **Total Local MH ACs** - Should be ≤ 2000
3. **sub-instances/up ratio** - If not 100%, investigate DOWN services
4. **Time in state** - Services with "0 days, 0:00:XX" are actively flapping

---

## Step 2: Access Traces via Shell

```bash
# From DNOS CLI
run start shell
# Password: dnroot

# Navigate to traces
cd /core/traces/routing_engine

# Check latest rib-manager traces
ls -lt rib-manager_traces* | head

# Check latest bgpd traces  
ls -lt bgpd_traces* | head

# Check wb_agent traces
ls -lt wb_agent* | head
```

---

## Step 3: Debug EVPN/FXC State Changes

### Check BGP EVPN Type-4 ES Route Processing

```bash
# From shell - Look for ESI-related BGP events
zgrep -i "esi\|ES-route\|type.*4\|ethernet.segment" bgpd_traces* | tail -50

# Check DF election events
zgrep -i "designated\|DF\|election\|preference" bgpd_traces* | tail -50

# Check for route state changes
zgrep "EVPN.*state\|service.*state" bgpd_traces* | tail -50
```

### Check RIB-Manager Interface State Updates

```bash
# From shell - Interface state changes
zgrep -i "ph1\|phX\|interface.*state\|link.*state" rib-manager_traces* | tail -50

# Check for EVPN service updates
zgrep "evpn\|vpws\|fxc" rib-manager_traces* | tail -50

# NHT (Nexthop Tracking) events
zgrep "NHT\|nexthop" rib-manager_traces* | tail -30
```

### Check WBox/FIB Updates

```bash
# From shell - Interface state from CMC
zgrep "handle_set_iface_oper_state\|FRR\|oper.*state" wb_agent* | tail -30

# Look for FXC-related FIB updates
zgrep -i "fxc\|vpws\|evpn\|ph1" wb_agent* | tail -30
```

---

## Step 4: Debug Interface State Changes

### Check CMC Interface Manager

```bash
# From management_engine container or shell
zgrep "Changing state\|state.*change\|oper_state" /core/traces/management_engine/cmc* | tail -30

# Look for phX.Y specific changes
zgrep "ph1\|phX" /core/traces/management_engine/cmc* | tail -30
```

### Key Patterns to Look For

| Pattern | Meaning |
|---------|---------|
| `set_iface_oper_state` | CMC sending interface state to wb_agent |
| `IF_LINK_STATE_CHANGE_UP` | Interface link state change event |
| `interface-evpn-disabled` | EVPN-specific interface disable |
| `DF election` | Designated Forwarder election event |
| `ESI.*route` | Type-4 ES route processing |

---

## Step 5: Debug DF Election Issues

### From DNOS CLI

```bash
# Check DF status for specific service
show evpn-vpws-fxc instance <name> ethernet-segments-info

# Output shows:
# - Role: DF or BDF
# - Time of Last DF Election
# - Requested vs Actual Algorithm
# - Designated Forwarder IP
# - Backup Designated Forwarder IP
```

### From Traces

```bash
# BGP DF election events
zgrep -i "DF\|designated\|election\|preference.*value" bgpd_traces* | tail -50

# Look for DF changes (instability)
zgrep "Time of Last DF\|DF.*election\|BDF" bgpd_traces* | tail -30
```

---

## Step 6: Check for Scale-Related Issues

### ESI Limit (2000)

```bash
# From DNOS CLI - Verify ESI count
show config network-services multihoming | include esi | count

# If count approaches 2000, you're at the limit!
# DNOS ESI_MAX_SCALE = 2000
```

### Performance Issues at Scale

```bash
# Check for slow processing in routing_manager
zgrep "took\|duration\|timeout\|slow\|delay" bgpd_traces* rib-manager_traces* | tail -30

# Check commit processing time
zgrep "commit\|prepare\|precommit" /core/traces/routing_engine/* | tail -20
```

---

## Step 7: Specific Grep Commands for This Issue

### For MH/ESI Flapping

```bash
# All-in-one grep for phX.Y flapping
zgrep -P "ph1|ESI|DF|designated|state.*change|flap|multihoming|interface-evpn" \
  bgpd_traces* rib-manager_traces* wb_agent* 2>/dev/null | tail -100
```

### For EVPN Service State

```bash
# Track FXC/VPWS service state changes
zgrep -i "evpn.*state\|fxc.*state\|vpws.*state\|service.*up\|service.*down" \
  bgpd_traces* rib-manager_traces* | tail -50
```

### For Interface-EVPN-Disabled

```bash
# This is auto-configured by routing_manager precommit
zgrep "interface-evpn-disabled" rib-manager_traces* | tail -30
```

---

## Step 8: Live Monitoring

### Watch FXC Service State Changes

```bash
# From DNOS CLI - Run multiple times to observe flapping
watch -n 5 'show evpn-vpws-fxc summary'

# Or count services in different states
show evpn-vpws-fxc | include "0 days, 0:00" | count
# Run again after 30 seconds to see if count changes
```

### Tail Traces Live

```bash
# From shell - Watch rib-manager for interface events
tail -F rib-manager_traces | grep -i "ph1\|ESI\|DF"

# Watch bgpd for EVPN events
tail -F bgpd_traces | grep -i "evpn\|ESI\|DF\|election"
```

---

## Root Cause Indicators

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| ESI count = 2000 | At DNOS limit | Reduce to 1800 (90%) |
| Rapid DF elections | BGP instability or Type-4 route issues | Check BGP peer status |
| Services down but AC up | Race condition | Check `interface-evpn-disabled` |
| Duplicate IF_LINK_STATE_CHANGE_UP | Known DNOS bug | Report to Infra team |
| Time in state = 0:00:XX | Active flapping | Identify source of state changes |
| Slow commit times | O(n²) performance issue | Report to Routing team |

---

## Confluence References

| Topic | URL |
|-------|-----|
| Network Reconvergence / FRR Logs | https://drivenets.atlassian.net/wiki/spaces/QA/pages/4087382022 |
| RIB and FIB manager troubleshooting | https://drivenets.atlassian.net/wiki/spaces/CS/pages/2726002770 |
| Debugging Examples | https://drivenets.atlassian.net/wiki/spaces/QA/pages/3172176917 |
| Useful logs grep for debugging | https://drivenets.atlassian.net/wiki/spaces/QA/pages/3965943880 |
| EVPN-VPWS FXC | https://drivenets.atlassian.net/wiki/spaces/QA/pages/4477943825 |
| EVPN + Multihoming | https://drivenets.atlassian.net/wiki/spaces/QA/pages/4090888472 |
| PWHE interface state dependency | https://drivenets.atlassian.net/wiki/spaces/QA/pages/5966594102 |

---

## Team Contacts

| Issue Type | Team | Focus Area |
|------------|------|------------|
| EVPN/BGP Type-4 routes | **Routing Team** | bgpd, zebra |
| Interface state changes | **Infra Team** | CMC, mgmt_interface_manager |
| FIB/Datapath issues | **DP Team** | wb_agent, FIB |
| MH/ESI processing | **Routing Team** | routing_manager |
| Performance at scale | **Both Teams** | precommit handlers, bulk processing |

---

## Bug Report Template

When reporting this issue, include:

1. **DNOS Version:** `show version`
2. **Scale:** Number of ESI interfaces, FXC instances
3. **Configuration:** MH preference values, redundancy mode
4. **Symptoms:**
   - `show evpn-vpws-fxc summary` output
   - Count of services in different states
   - Time in state distribution
5. **Traces:** 
   - Last 100 lines of bgpd_traces with ESI/DF greps
   - Last 100 lines of rib-manager_traces with interface greps
6. **Timing:** When did flapping start? Correlate with any config changes




