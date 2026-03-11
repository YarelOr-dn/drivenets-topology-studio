# EVPN-VPWS-FXC NLRI Path Analysis: PE-2 to PE-1

## Problem Statement

**Issue**: NLRI from PE-2 to PE-1 is received but marked as `(inaccessible)` on PE-1, preventing service installation. PE-2 successfully installs the service from PE-1.

**Key Observation**: 
- PE-1 shows: `2.2.2.2 (inaccessible)` in BGP EVPN table
- PE-2 shows: `1.1.1.1 [vrf default]` and successfully installs the route

---

## NLRI Path Flow: PE-2 → PE-1

### Step-by-Step Path

1. **PE-2 Originates Route**
   - Route: `type:=1,esi:=00:00:00:00:00:00:00:00:00:00,eth-tag:=14288`
   - RD: `2.2.2.2:100`
   - Next-Hop: `Self` (2.2.2.2)
   - Label: `564`
   - RT: `123456:100`

2. **PE-2 Advertises to RR (PE-4)**
   - PE-2 → PE-4: BGP session on `4.4.4.4`
   - Next-hop remains `2.2.2.2` (no `nexthop self` configured for l2vpn-evpn on PE-2)

3. **RR (PE-4) Reflects Route**
   - PE-4 receives route with next-hop `2.2.2.2`
   - **CRITICAL**: PE-4 does NOT have `nexthop self` configured for `l2vpn-evpn` address family
   - PE-4 reflects route to PE-1 with **original next-hop `2.2.2.2`**

4. **PE-1 Receives Route**
   - Route received from PE-4 (RR) with next-hop `2.2.2.2`
   - PE-1 must resolve next-hop `2.2.2.2` in default VRF
   - **PROBLEM**: Next-hop resolution fails → Route marked as `(inaccessible)`

---

## Root Cause Analysis

### Why Next-Hop is Inaccessible on PE-1

The issue is in the **next-hop resolution logic** for EVPN routes. Let's trace through the code:

#### 1. Next-Hop Reachability Check

When PE-1 receives the EVPN route, it calls:

```8847:8887:services/control/quagga/bgpd/bgp_route.c
void bgp_nexthop_reachability_check(struct peer *peer,
                                     afi_t orig_afi,
                                     safi_t orig_safi,
                                     struct bgp_info *ri,
                                     struct attr *intern_attr,
                                     struct bgp *bgp_of_ri,
                                     bgp_rmap_set_flags *flags,
                                     const char *nh_vrf_name)
{
    // ... validation checks ...
    
    struct bgp *bgp_of_bnc = bgp_get_bgp_of_nh_instance(bgp_of_ri, ri->attr);
    if (bgp_find_or_add_nexthop(bgp_of_bnc, orig_afi, orig_safi, ri, NULL, BGP_NHT_TYPE_ROUTE, NULL, nh_vrf_name))
    {
        bgp_info_set_flag(ri, BGP_INFO_VALID);
    }
    else
    {
        bgp_info_unset_flag(ri, BGP_INFO_VALID);  // ← Route marked as invalid
    }
}
```

#### 2. MPLS Reachability Requirement for EVPN

For EVPN routes, the system checks if MPLS reachability is needed:

```822:850:services/control/quagga/bgpd/bgp_mpls.c
bool bgp_info_is_mpls_reachability_needed_evpn(const struct bgp_info *info)
{
    // ... checks for VXLAN/SRv6 ...
    
    if (bgp_info_has_remote_label(info))
    {
        return true;  // ← EVPN with MPLS label requires MPLS reachability
    }
    
    // For EVPN routes, there are some types (ES route) that doesn't have mpls label 
    // but need to enforce MPLS reachability
    return true;  // ← Default: MPLS reachability required
}
```

#### 3. Next-Hop Validation Logic

The next-hop is validated in `bgp_nht.c`:

```1015:1020:services/control/quagga/bgpd/bgp_nht.c
if (BGP_AF_OPS(bgp_of_ri, afi_dst_safi).bgp_info_is_mpls_reachability_needed(ri))
{
    /* MPLS route is valid if its nexthop is either MPLS reachable, or connected*/
    mpls_valid = (CHECK_FLAG(bnc->flags, BGP_NEXTHOP_MPLS_REACHABLE)
                | CHECK_FLAG(bnc->flags, BGP_NEXTHOP_CONNECTED));
}
```

**Critical Requirement**: For EVPN routes, the next-hop must be:
- **MPLS reachable** (has MPLS label via LDP/SR), OR
- **Connected** (directly connected interface)

#### 4. Why PE-1 Fails

PE-1's routing table shows:
```
route 2.2.2.2/32
  Known via "static", priority high, distance 1, metric 0
  * 12.12.12.2, via ge100-0/0/5.12
```

**Problem**: 
- Static routes **do NOT provide MPLS labels**
- The route is **not directly connected** (goes via 12.12.12.2)
- Therefore: `BGP_NEXTHOP_MPLS_REACHABLE` = **FALSE**
- Therefore: `BGP_NEXTHOP_CONNECTED` = **FALSE**
- Result: `mpls_valid = FALSE` → Route marked as **invalid/inaccessible**

#### 5. Why PE-2 Succeeds

PE-2's routing table shows:
```
route 1.1.1.1/32
  Known via "static", priority high, distance 1, metric 0
  4.4.4.4 (recursive)
  * 24.24.24.4, via bundle-100.24 label 3
```

**Wait**: PE-2 also has a static route, but it shows `label 3` in the output. However, this might be misleading. Let me check if PE-2 actually has an IGP route or if there's another reason.

Actually, looking more carefully: PE-2 receives the route from PE-1 via RR with next-hop `1.1.1.1`. The route shows `[vrf default]` which suggests it can resolve the next-hop. But PE-2 also has a static route to 1.1.1.1.

**Key Difference**: The route on PE-2 shows it's installed in the service instance, which means the next-hop was successfully resolved. This could be because:
1. PE-2 has an IGP route to 1.1.1.1 with MPLS labels (not shown in output)
2. Or there's a different next-hop resolution path

---

## Code Flow: Next-Hop Resolution for EVPN

### Complete Flow Diagram

```
PE-2 Originates Route
    ↓
PE-2 → PE-4 (RR): Advertise with next-hop 2.2.2.2
    ↓
PE-4 (RR): Reflects route (NO nexthop-self for l2vpn-evpn)
    ↓
PE-1 Receives Route
    ↓
bgp_nexthop_reachability_check() called
    ↓
bgp_find_or_add_nexthop() called
    ↓
bgp_info_is_mpls_reachability_needed_evpn() → returns TRUE
    ↓
Check: Is next-hop MPLS reachable?
    ↓
Lookup route to 2.2.2.2 in default VRF
    ↓
Found: Static route via 12.12.12.2
    ↓
Static route does NOT provide MPLS label
    ↓
BGP_NEXTHOP_MPLS_REACHABLE = FALSE
BGP_NEXTHOP_CONNECTED = FALSE
    ↓
mpls_valid = FALSE
    ↓
bgp_info_unset_flag(ri, BGP_INFO_VALID)
    ↓
Route marked as (inaccessible)
    ↓
Service does NOT install
```

---

## Why Service Doesn't Install on PE-1

The service installation check happens in the EVPN service handler. The route must be valid (BGP_INFO_VALID flag set) for it to be installed:

```16514:16528:services/control/quagga/bgpd/bgp_route.c
static bool bgp_show_path_inactive_flags(struct vty *vty, struct bgp_info *binfo)
{
    if (!BGP_IS_COPY(binfo) && !CHECK_FLAG (binfo->path.flags, BGP_INFO_VALID))
    {
        if (CHECK_FLAG (binfo->path.flags, BGP_INFO_LOOPED))
        {
            vty_out (vty, " (inaccessible, looped)");
        }
        else
        {
            vty_out (vty, " (inaccessible)");  // ← This is what PE-1 shows
        }
        return true;
    }
    return false;
}
```

When `BGP_INFO_VALID` is not set, the route is not considered for:
- Service installation
- FIB programming
- Forwarding

---

## Solutions

### Solution 1: Configure `nexthop self` on RR (PE-4) for l2vpn-evpn

**Recommended Solution**

Configure on PE-4:
```
protocols bgp 1234567 neighbor 1.1.1.1 address-family l2vpn-evpn nexthop self
protocols bgp 1234567 neighbor 2.2.2.2 address-family l2vpn-evpn nexthop self
```

**Why this works**:
- RR changes next-hop to itself (4.4.4.4)
- PE-1 can resolve 4.4.4.4 via IS-IS with MPLS labels
- Next-hop becomes MPLS reachable → Route becomes valid

### Solution 2: Ensure IGP Route with MPLS Labels

Ensure PE-1 has an IGP route (OSPF/IS-IS) to 2.2.2.2 with MPLS labels (LDP/SR).

**Why this works**:
- IGP routes provide MPLS labels
- Next-hop becomes MPLS reachable → Route becomes valid

### Solution 3: Direct BGP Session (Not Recommended)

Establish direct BGP session between PE-1 and PE-2 (bypassing RR).

**Why this works**:
- Direct eBGP sessions can use `nexthop-self` or connected check
- But this defeats the purpose of using RR

---

## Configuration Comparison

### PE-4 (RR) Configuration Analysis

**Current Configuration**:
- `nexthop self` configured for: `ipv4-vpn`, `ipv6-labeled-unicast`, `ipv4-unicast` (for 2.2.2.2)
- `nexthop self` **NOT configured** for: `l2vpn-evpn` ← **MISSING**

**Required Configuration**:
```
protocols bgp 1234567 neighbor 1.1.1.1 address-family l2vpn-evpn nexthop self
protocols bgp 1234567 neighbor 2.2.2.2 address-family l2vpn-evpn nexthop self
```

---

## Verification Commands

### On PE-1 (After Fix)

```bash
# Check BGP EVPN route
show bgp l2vpn evpn rd 2.2.2.2:100 nlri type:=1,esi:=00:00:00:00:00:00:00:00:00:00,eth-tag:=14288

# Expected: Should show next-hop as 4.4.4.4 (not 2.2.2.2)
# Expected: Should NOT show (inaccessible)

# Check service installation
show bgp instance evpn-vpws-fxc FXC-1

# Expected: Route should be installed with > best path indicator
```

### On PE-4 (RR)

```bash
# Verify nexthop-self configuration
show config protocols bgp 1234567 neighbor 1.1.1.1 address-family l2vpn-evpn
show config protocols bgp 1234567 neighbor 2.2.2.2 address-family l2vpn-evpn

# Expected: Should show "nexthop self"
```

---

## Summary

**Root Cause**: 
- PE-1 receives EVPN route with next-hop `2.2.2.2` from RR
- PE-1 only has static route to `2.2.2.2` (no MPLS labels)
- EVPN requires next-hop to be MPLS reachable or connected
- Static route doesn't satisfy MPLS reachability requirement
- Route marked as invalid → Service doesn't install

**Solution**: 
- Configure `nexthop self` on PE-4 (RR) for `l2vpn-evpn` address family
- This changes next-hop to `4.4.4.4` which PE-1 can resolve via IS-IS with MPLS labels

**Code References**:
- Next-hop reachability check: `bgp_route.c:8847-8887`
- MPLS reachability requirement: `bgp_mpls.c:822-850`
- Next-hop validation: `bgp_nht.c:1015-1020`
- Invalid route display: `bgp_route.c:16514-16528`

---

*Analysis based on DriveNets cheetah_25_4 codebase*
*Date: December 10, 2025*






