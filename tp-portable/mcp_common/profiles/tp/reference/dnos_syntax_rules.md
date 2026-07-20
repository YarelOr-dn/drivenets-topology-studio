# DNOS Syntax Rules for Test Plan Generation

## `DNOS_SYNTAX_SYSTEM_PROMPT`

## CRITICAL DNOS SYNTAX RULES FOR TEST GENERATION

You are generating tests for DriveNets DNOS (DriveNets Network Operating System).
You MUST use ONLY Drivenets DNOS CLI syntax. 
DO NOT use Cisco IOS, IOS-XR, Juniper, Nokia, or any other vendor syntax.

### MANDATORY RULES:

1. **Indentation**: Use exactly 2 SPACES per level (NOT tabs)
2. **Block Terminators**: Every block ends with "!" at content indent level
3. **Interface Hierarchy**: Interfaces are FLAT (sub-interfaces are siblings, NOT children)
4. **No 'interface' keyword**: Use interface name directly under 'interfaces'
5. **Command Verification**: Only use commands documented in DNOS CLI docs
6. **NLRI Quotes**: Always quote NLRI strings with double quotes ("")
7. **Complex Hierarchy Awareness**: Some features require config in MULTIPLE hierarchies!

### CRITICAL: COMPLEX HIERARCHY PATTERNS

Many DNOS features require configuration ACROSS MULTIPLE HIERARCHIES.
Always check where each command belongs!

#### FlowSpec Local Policies (3 hierarchies):
1. DEFINE: `routing-policy flowspec-local-policies ipv4 match-class/policy`
2. APPLY:  `forwarding-options flowspec-local ipv4 apply-policy-to-flowspec`  ← NOT under routing-policy!
3. ENABLE: `interfaces <IF> flowspec enabled`

#### VRF with Interface (2 hierarchies) - CRITICAL:
1. CONFIGURE INTERFACE: `interfaces <IF> ipv4-address, flowspec enabled`  ← Configure FIRST
2. ATTACH TO VRF: `network-services vrf instance <VRF> interface <IF>`  ← Attach SECOND

**❌ NEVER put `vrf <name>` under interfaces or under flowspec enabled!**
**✅ VRF attachment is ALWAYS under `network-services vrf instance <VRF> interface <IF>`**

#### Routing Policy in BGP (2 hierarchies):
1. DEFINE: `routing-policy policy <NAME>`
2. APPLY:  `protocols bgp neighbor <IP> address-family export-policy <NAME>`

### COMMON DNOS vs OTHER VENDOR DIFFERENCES:

| Feature              | DNOS                                    | Cisco IOS-XR                           |
|---------------------|----------------------------------------|----------------------------------------|
| Enter config mode   | configure                               | configure terminal                     |
| BGP config          | protocols bgp <ASN>                    | router bgp <ASN>                       |
| Neighbor config     | neighbor <IP>                          | neighbor <IP>                          |
| Address family      | address-family ipv4-unicast            | address-family ipv4 unicast            |
| Enable feature      | admin-state enabled                    | no shutdown                            |
| Interface config    | interfaces bundle-1                    | interface Bundle-Ether1                |
| VRF config          | network-services vrf instance <NAME>   | vrf <NAME>                             |
| FlowSpec enable     | flowspec enabled                       | flowspec address-family ipv4           |
| MPLS enable         | mpls enabled                           | mpls ldp                               |
| Static route        | protocols static address-family...     | router static address-family ipv4...   |

### DNOS-SPECIFIC COMMANDS TO USE:

BGP:
- protocols bgp <ASN>
- neighbor <IP> address-family ipv4-flowspec-vpn
- neighbor <IP> address-family ipv4-flowspec
- send-community extended

VRF:
- network-services vrf instance <NAME>
- route-distinguisher <IP>:<N>
- route-target import <ASN>:<N>
- route-target export <ASN>:<N>
- interface <INTERFACE_NAME>  ← Attaches interface to VRF (interface must be configured first!)
- protocols bgp <ASN> address-family ipv4-flowspec import-vpn route-target <ASN>:<N>

**VRF Interface Attachment - CRITICAL SYNTAX:**
- ❌ WRONG: `interfaces bundle-1.100 vrf Source` (vrf is NOT under interfaces!)
- ❌ WRONG: `interfaces bundle-1.100 flowspec enabled vrf Source` (vrf is NOT under flowspec!)
- ✅ CORRECT: `network-services vrf instance Source interface bundle-1.100`

Interface:
- interfaces bundle-1
- interfaces ge100-1/0/1
- interfaces lo0
- flowspec enabled
- mpls enabled
- admin-state enabled/disabled (ONLY for interfaces and BGP neighbors, NOT for BGP address-families!)
- ipv4-address <IP>/mask

**⚠️ BGP Address-Family admin-state Rule:**
- BGP address-family blocks MUST use `admin-state enabled` to activate
- ❌ NEVER generate `admin-state disabled` under a BGP address-family
- To deactivate a BGP address-family, remove it with `no address-family <name>`
- `admin-state disabled` is valid for: interfaces, BGP neighbors, protocols (ISIS/LDP/RSVP)

Show Commands:
- show bgp ipv4 flowspec-vpn summary
- show bgp ipv4 flowspec-vpn neighbors <IP> received-routes
- show bgp instance vrf <VRF> ipv4 flowspec
- show flowspec ncp
- show flowspec-local-policies counters

Clear Commands:
- clear flowspec counters
- clear flowspec counters ipv4

Commit:
- rollback 0 (CRITICAL: Always run before terminal paste)
- commit
- commit check

## `DNOS_CONFIG_RULES`

## DNOS Configuration Hierarchy Rules (MANDATORY)

### Indentation
- Use exactly 2 SPACES per level (NOT tabs!)
- Level 0: No indent
- Level 1: 2 spaces
- Level 2: 4 spaces
- Level 3: 6 spaces

### Block Terminators
- Every block MUST end with "!" at content indentation level
- Closing "!" must match the indentation of the block content

### Interface Hierarchy (CRITICAL)
- DNOS interfaces are FLAT, not hierarchical
- Sub-interfaces are SIBLINGS of parents, NOT children
- Interface names at 2-space indent with NO 'interface' keyword

### Correct Example:
```
interfaces
  bundle-1
    admin-state enabled
    ipv4-address 10.0.0.1/30
  !
  bundle-1.100
    vlan-id 100
    ipv4-address 10.1.0.1/30
  !
!
```

### WRONG Example:
```
interfaces
  bundle-1
    admin-state enabled
    bundle-1.100      <- WRONG: sub-interface nested under parent
      vlan-id 100
    !
  !
!
```

## `DNOS_BGP_SYNTAX`

## DNOS BGP Configuration Syntax

### Global BGP Configuration (Default VRF)
```
protocols
  bgp <ASN>
    router-id <A.B.C.D>
    neighbor <IP>
      remote-as <ASN>
      update-source <interface>
      address-family ipv4-unicast
        admin-state enabled
      !
      address-family ipv4-flowspec
        admin-state enabled
        send-community extended
      !
      address-family ipv4-flowspec-vpn
        admin-state enabled
        send-community extended
      !
    !
    neighbor-group <NAME>
      remote-as <ASN>
      address-family ipv4-flowspec
        admin-state enabled
      !
    !
  !
!
```

### BGP in Non-Default VRF
```
network-services
  vrf instance <VRF_NAME>
    route-distinguisher <IP>:<N>
    route-target import <ASN>:<N>
    route-target export <ASN>:<N>
    protocols bgp <ASN>
      router-id <A.B.C.D>
      address-family ipv4-unicast
        admin-state enabled
      !
      address-family ipv4-flowspec
        import-vpn route-target <ASN>:<N>
      !
    !
  !
!
```

### Supported BGP Address Families
- ipv4-unicast
- ipv6-unicast
- ipv4-multicast
- ipv6-multicast
- ipv4-vpn (L3VPN)
- ipv6-vpn (L3VPN)
- ipv4-labeled-unicast
- ipv6-labeled-unicast
- l2vpn-evpn
- ipv4-flowspec
- ipv6-flowspec
- ipv4-flowspec-vpn (SAFI 134)
- ipv6-flowspec-vpn (SAFI 134)
- ipv4-sr-te (SAFI 73, Segment Routing TE)
- ipv6-sr-te (SAFI 73, Segment Routing TE)
- ipv4-rt-constrains
- ipv6-rt-constrains
- link-state

### ⚠️ CRITICAL: BGP Address-Family admin-state Rules

**`admin-state` under BGP address-family is ONLY used to ACTIVATE the address-family.**

When configuring a BGP address-family under a neighbor, ALWAYS use `admin-state enabled`:
```
address-family ipv4-unicast
  admin-state enabled
!
```

**❌ DO NOT generate `admin-state disabled` under BGP address-family blocks!**
- `admin-state disabled` under a BGP address-family is NOT a standard test action
- To deactivate/remove a BGP address-family from a neighbor, use `no address-family <name>`
- To test "feature OFF" for an address-family, REMOVE the address-family block entirely

**Where `admin-state disabled` IS valid in DNOS:**
- Interfaces: `interfaces bundle-1 admin-state disabled` (bring interface down)
- BGP neighbor: `protocols bgp neighbor <IP> admin-state disabled` (disable entire neighbor)
- BGP neighbor-group: `protocols bgp neighbor-group <NAME> admin-state disabled`
- ISIS: `protocols isis <NAME> admin-state disabled`
- LDP: `protocols ldp admin-state disabled`
- RSVP tunnels: `protocols rsvp tunnel <NAME> admin-state disabled`

**Where `admin-state disabled` is NOT valid / should NOT be generated:**
- BGP address-family blocks (e.g., `address-family ipv4-unicast admin-state disabled`)
- Inside `flowspec enabled` blocks
- Inside VRF `protocols bgp address-family` blocks

## `DNOS_NETCONF_GNMI_SYNTAX`

## DNOS NETCONF / gNMI / OpenConfig / SNMP Test Syntax Rules

### CRITICAL RULES FOR GENERATING NETCONF AND gNMI TEST TASKS

When generating NETCONF or gNMI test tasks for any epic, you MUST follow these rules.
Incorrect syntax causes tests to fail on the device.

### 1. NETCONF Configuration and Session

DNOS NETCONF config hierarchy: `system > netconf`
```
system
  netconf
    vrf mgmt0
      admin-state enabled
    !
    vrf default
      admin-state enabled
    !
  !
!
```

NETCONF show commands:
- `show system netconf` — global config, port 830, VRFs, capabilities
- `show system netconf sessions` — active sessions
- `show config system netconf` — running config

Connection: SSH port 830 with `ssh -p 830 -s dnroot@<mgmt-ip> netconf`

### 2. NETCONF Operations (Safe to Test)

| Operation | Safe? | Usage |
|-----------|-------|-------|
| get-config | YES | Read running/candidate config |
| get | YES | Read config + operational state |
| edit-config (merge) | YES | Default operation, merges config |
| edit-config (replace) | YES | Subtree-scoped replace (SAFE, unlike gNMI) |
| edit-config (create) | YES | Error if exists already |
| edit-config (delete) | YES | Error if doesn't exist |
| edit-config (remove) | YES | Silent if doesn't exist |
| commit | YES | Apply candidate to running |
| confirmed-commit | YES | Auto-revert if not confirmed within timeout |
| validate | YES | Validate candidate config |
| lock/unlock | YES | Lock candidate datastore |

### 3. gNMI / gRPC Configuration

DNOS gRPC config hierarchy: `system > grpc`
```
system
  grpc
    port 50051
    vrf mgmt0
      admin-state enabled
    !
    vrf default
      admin-state enabled
    !
    security
      tls server-certificate <cert-file>
    !
  !
!
```

gNMI show commands:
- `show system grpc` — port, TLS status, VRFs
- `show system grpc sessions` — active gNMI sessions
- `show system grpc subscriptions` — active subscriptions
- `show config system grpc` — running config

### 4. gNMI Operations — SAFETY MATRIX (CRITICAL)

| Operation | Safe? | Notes |
|-----------|-------|-------|
| Get | YES | Read-only, works with or without TLS |
| Subscribe (SAMPLE/ON_CHANGE/ONCE) | YES | Read-only telemetry |
| Capabilities | YES | Read-only |
| Set Update | YES | Merges with existing config. Requires TLS. |
| Set Delete | YES | Removes only targeted path. Requires TLS. |
| **Set Replace** | **DANGEROUS** | **WIPES ENTIRE device config via LOFD! NEVER generate tests using Set Replace!** |

**⚠️ gNMI Set Replace = Full Config Wipe (BY DESIGN in DNOS)**
- gNMI Set Replace runs `load override factory default` (LOFD) before applying values
- This destroys ALL config: BGP, interfaces, system, TLS certs — everything
- This is BY DESIGN per SW-170667, NOT a bug
- For replace semantics: use NETCONF `edit-config` with `xc:operation="replace"` instead (subtree-scoped, safe)
- Tests using gNMI Set Replace should be marked as SKIP with reason: "LOFD full config wipe"

### 5. gNMI Authentication Modes

| Mode | gNMI Get/Subscribe | gNMI Set | Notes |
|------|--------------------|----------|-------|
| No TLS (insecure) | YES (read-only) | NO | `gnmic --insecure` |
| TLS (server cert) | YES | YES | `gnmic --tls-ca cert.crt` or `--skip-verify` |
| mTLS (mutual) | YES | YES | Requires client cert |

**Without TLS, gNMI is read-only. Set tests must gracefully skip on insecure devices.**

### 6. YANG Path Rules (CRITICAL — Wrong Paths = Test Failure)

DN YANG paths start with `/drivenets-top/...`
OpenConfig paths start with `/interfaces/...`, `/network-instances/...`, `/system/...`

**Correct BGP path:**
`/drivenets-top/network-services/vrfs/vrf[vrf-name=default]/protocols/bgp[as-number=X]`

**WRONG paths (do NOT generate):**
- `/drivenets-top/instances/vrfs/vrf` — does NOT exist
- `/drivenets-top/protocols/bgp` — exists but EMPTY for default VRF config

**Three YANG trees — cannot mix in one gNMI SetRequest:**
1. `drivenets-top` (DN native)
2. `nacm` (access control)
3. OpenConfig (`/interfaces`, `/network-instances`, `/system`)

Mixing trees → error: "Combining configurations from multiple models in same operation is not supported"

### 7. DN vs OpenConfig Namespaces

| DN Module | Namespace | OC Module | OC Namespace |
|-----------|-----------|-----------|--------------|
| dn-top | http://drivenets.com/ns/yang/dn-top | — | — |
| dn-bgp | http://drivenets.com/ns/yang/dn-bgp | bgp | http://openconfig.net/yang/bgp |
| dn-interfaces | http://drivenets.com/ns/yang/dn-interfaces | interfaces | http://openconfig.net/yang/interfaces |
| dn-network-services | http://drivenets.com/ns/yang/dn-network-services | network-instances | http://openconfig.net/yang/network-instance |

### 8. gNMI Set Constraints (Must Include in Tests)

- gNMI Set acquires commit lock — blocks CLI, NETCONF, and other Set sessions
- Default gnmic timeout is 10 seconds — always use `--timeout 60s` or higher
- Each SetRequest = one atomic commit (all succeed or all fail)
- Cannot mix DN/OC/NACM trees in the same SetRequest
- No wildcards in Set Update/Replace paths
- gNMI has NO rollback — use CLI `rollback <N>` instead
- gNMI Set does NOT have a candidate datastore — commit is immediate

### 9. NETCONF vs gNMI Key Differences (for Test Design)

| Feature | NETCONF | gNMI |
|---------|---------|------|
| Transport | SSH port 830 | gRPC/TLS port 50051 |
| Auth for writes | SSH credentials | TLS certificate required |
| Replace scope | **Subtree only** (safe) | **Entire config** (LOFD — dangerous) |
| Candidate datastore | Yes (edit → commit) | No (immediate commit) |
| Confirmed commit | Yes (auto-revert) | Not available |
| Rollback | Via proprietary RPC | Not available (use CLI) |
| Commit lock | Explicit lock/unlock | Auto-acquired on Set arrival |

### 10. SNMP Test Rules

- SNMP uses UDP port 161 (polling), port 162 (traps)
- DNOS Enterprise OID: `1.3.6.1.4.1.49739` (DRIVENETS)
- **SNMP Set is NOT production-ready (SW-209493 Backlog) — do NOT generate SNMP Set tests**
- Supported operations: GET, Walk/BulkGet, Traps
- SNMP server is enabled by default
- Not all features have SNMP MIBs (e.g., no FlowSpec MIB exists)

SNMP config:
```
system
  snmp
    community <string> vrf <vrf-name>
    !
    trap-server <ip> vrf <vrf-name>
      community <string>
    !
  !
!
```

SNMP show commands:
- `show system snmp summary`
- `show system snmp communities`
- `show system snmp trap-servers`
- `show system snmp traps`

### 11. Test Task Generation Rules for NETCONF/gNMI

When generating NETCONF or gNMI test tasks:
1. **Always specify the protocol** (NETCONF or gNMI) — they have different syntax and behavior
2. **Include the session setup** — connect, hello exchange, authentication
3. **Include verification** — verify via CLI (`show config`, `show bgp`) AND via get-config
4. **Include cleanup** — remove only config the test added
5. **For gNMI write tests**, always specify TLS is required
6. **For gNMI Set tests**, use ONLY `Set Update` and `Set Delete` — NEVER `Set Replace`
7. **For NETCONF edit-config**, use the candidate datastore and commit workflow
8. **Use correct YANG paths** — `/drivenets-top/network-services/vrfs/vrf[vrf-name=X]/...`
9. **Do NOT generate SNMP Set tests** — SNMP Set is not production-ready

## `DNOS_COMMIT_SYNTAX`

## DNOS Commit and Rollback Commands

### Configuration Mode
```
configure            # Enter configuration mode
exit                # Exit configuration mode
```

### Commit Operations
```
commit               # Commit configuration
commit check         # Validate configuration without committing
commit confirm <N>   # Commit with auto-rollback after N minutes
commit comment "<TEXT>"  # Commit with comment
```

### Rollback Operations
```
rollback 0           # Clear candidate configuration (IMPORTANT: Run before terminal paste!)
rollback 1           # Rollback to previous configuration
rollback <N>         # Rollback to configuration N versions ago
```

### Load Operations
```
load override <FILE>           # Replace configuration from file
load merge <FILE>              # Merge configuration from file
load override factory-default  # Reset to factory defaults
```

### Show Configuration
```
show config
show config compare
show config diff
show config running
show config candidate
```

## `DNOS_COMPLEX_HIERARCHY_ATTACHMENTS`

## DNOS Complex Hierarchy Attachments

CRITICAL: Some DNOS features require configuration ACROSS MULTIPLE HIERARCHIES.
The configuration must be done in the correct order and in the correct place!

### Pattern: Define → Apply → Enable

Many advanced features follow this pattern:
1. **DEFINE**: Create the policy/class/object (hierarchy A)
2. **APPLY**: Activate the policy/class/object (hierarchy B)
3. **ENABLE**: Enable the feature on interfaces (hierarchy C)

---

### Example 1: FlowSpec Local Policies

**❌ WRONG (all in one hierarchy - DOES NOT WORK):**
```
routing-policy
  flowspec-local-policies
    ipv4
      match-class mc-1
        dest-ip 10.0.0.0/8
      !
      policy pol-1
        match-class mc-1
          action rate-limit 0
        !
      !
      apply-policy-to-flowspec pol-1   ← WRONG PLACE! This command doesn't exist here!
    !
  !
!
```

**✅ CORRECT (split across hierarchies):**
```
! STEP 1: DEFINE match-class and policy (routing-policy)
routing-policy
  flowspec-local-policies
    ipv4
      match-class block-ddos
        dest-ip 10.0.0.0/8
        protocol tcp(0x06)
      !
      policy ddos-policy
        match-class block-ddos
          action rate-limit 0
        !
      !
    !
  !
!

! STEP 2: APPLY the policy (forwarding-options)
forwarding-options
  flowspec-local
    ipv4
      apply-policy-to-flowspec ddos-policy
    !
  !
!

! STEP 3: ENABLE flowspec on interfaces (interfaces)
interfaces
  bundle-1
    flowspec enabled
  !
!
```

---

### Example 2: QoS Policy Application

```
! STEP 1: DEFINE QoS class and policy
qos
  class-map CLASS-1
    match dscp 46
  !
  policy-map POLICY-1
    class CLASS-1
      bandwidth percent 30
    !
  !
!

! STEP 2: APPLY on interface
interfaces
  bundle-1
    qos
      input policy-map POLICY-1
      output policy-map POLICY-1
    !
  !
!
```

---

### Example 3: Access Control Lists

```
! STEP 1: DEFINE ACL
access-lists
  ipv4 ACL-DENY-ALL
    rule 10
      action deny
      source-address 0.0.0.0/0
      destination-address 0.0.0.0/0
    !
  !
!

! STEP 2: APPLY on interface
interfaces
  bundle-1
    access-list
      ipv4 input ACL-DENY-ALL
    !
  !
!
```

---

### Example 4: Routing Policy and BGP

```
! STEP 1: DEFINE routing policy
routing-policy
  policy EXPORT-POLICY
    rule 10
      match
        prefix-list MY-PREFIXES
      !
      action accept
        set local-preference 200
      !
    !
  !
!

! STEP 2: APPLY in BGP neighbor
protocols
  bgp 65000
    neighbor 10.0.0.1
      address-family ipv4-unicast
        export-policy EXPORT-POLICY
      !
    !
  !
!
```

---

### Hierarchy Reference Table

| Feature | DEFINE Hierarchy | APPLY Hierarchy | ENABLE Hierarchy |
|---------|-----------------|-----------------|------------------|
| FlowSpec Local | routing-policy flowspec-local-policies | forwarding-options flowspec-local | interfaces <IF> flowspec |
| QoS | qos class-map / policy-map | interfaces <IF> qos | - |
| ACL | access-lists ipv4/ipv6 | interfaces <IF> access-list | - |
| Routing Policy | routing-policy policy | protocols bgp neighbor export-policy | - |
| Prefix List | routing-policy prefix-list | routing-policy policy match prefix-list | - |
| Community List | routing-policy community-list | routing-policy policy match community | - |
| EVPN Instance | l2vpn evpn-vpws | interfaces <IF> l2-service | - |
| **VRF Interface** | **interfaces <IF> (L3 config)** | **network-services vrf instance <VRF> interface <IF>** | - |
| VRF BGP | network-services vrf instance <VRF> protocols bgp | - | - |

---

### Common Mistakes to Avoid

1. **Putting apply command in wrong hierarchy**
   - ❌ `routing-policy flowspec-local-policies ipv4 apply-policy-to-flowspec`
   - ✅ `forwarding-options flowspec-local ipv4 apply-policy-to-flowspec`

2. **Missing the apply step**
   - Defining a policy is NOT enough - you must APPLY it!

3. **Wrong order of configuration**
   - Always DEFINE before APPLY
   - Always configure interfaces BEFORE attaching to VRF

4. **Forgetting the enable step**
   - FlowSpec rules won't work without `flowspec enabled` on interfaces

## `DNOS_CONFIG_FLOW_PATTERNS`

## DNOS Configuration Flow Patterns for Test Generation

When generating tests that configure complex features, follow these patterns:

### Pattern 1: Define-Apply-Enable (FlowSpec Local)
```python
# Test steps should follow this order:
# Step 1: Define match-class and policy
configure_routing_policy_flowspec_local_policies()

# Step 2: Apply the policy  
configure_forwarding_options_flowspec_local()

# Step 3: Enable on interfaces
configure_interfaces_flowspec_enabled()

# Step 4: Commit
commit_configuration()

# Step 5: Verify
verify_flowspec_local_policies_installed()
```

### Pattern 2: Configure-Attach (VRF)
```python
# Step 1: Configure interface (BEFORE VRF attachment)
configure_interface_with_ip()

# Step 2: Create VRF with route-distinguisher and route-target
configure_vrf_instance()

# Step 3: Attach interface to VRF
configure_vrf_interface_attachment()

# Step 4: Commit
commit_configuration()

# Step 5: Verify
verify_vrf_interface_binding()
```

### Pattern 3: Multi-Hierarchy Verification
When verifying complex features, check ALL related hierarchies:

```python
# For FlowSpec Local Policies:
show_commands = [
    "show flowspec-local-policies match-classes",  # Verify DEFINE
    "show flowspec-local-policies policies",       # Verify DEFINE
    "show flowspec-local-policies counters",       # Verify APPLY (counters only if applied)
    "show interfaces bundle-1",                    # Verify ENABLE
]
```

### Pattern 4: Cleanup Order (Reverse of Configuration)
```python
# Cleanup in REVERSE order of configuration:
# Step 1: Remove from forwarding-options (un-apply)
# Step 2: Remove from routing-policy (un-define)
# Step 3: Disable on interfaces
```

## `DNOS_FLOWSPEC_ACTIONS`

## FlowSpec Actions (Extended Communities)

### Supported Actions
| Action                | Extended Community          | Description                           |
|-----------------------|----------------------------|---------------------------------------|
| traffic-rate          | traffic-rate:<AS>:<rate>   | Rate limit in bps (0 = DROP)         |
| redirect-ip           | redirect-ip:<IP>           | Redirect to IP (draft-simpson)        |
| traffic-marking       | traffic-marking:<DSCP>     | Set DSCP marking                      |

### Drop Traffic
traffic-rate:0:0 means DROP all matching traffic

### Rate Limit
traffic-rate:65000:1000000 means limit to 1 Mbps

### Show Extended Communities
```
show bgp ipv4 flowspec nlri "<NLRI>"
# Output includes: Extended Community: flowspec-traffic-rate:1:500
```

## `DNOS_FLOWSPEC_CLEAR_COMMANDS`

## DNOS FlowSpec Clear Commands

```
clear flowspec counters
clear flowspec counters ipv4
clear flowspec counters ipv4 match-class <MC_NAME>
clear flowspec counters ipv6
clear flowspec counters ipv6 match-class <MC_NAME>
clear flowspec-local-policies counters
clear flowspec-local-policies counters address-family ipv4
clear flowspec-local-policies counters address-family ipv6
```

## `DNOS_FLOWSPEC_INTERFACE_SYNTAX`

## DNOS FlowSpec Interface Configuration

### Enable FlowSpec on Interface
FlowSpec MUST be enabled on interfaces to apply filtering rules.

**Supported interface types:**
- Physical (ge10, ge25, ge40, ge50, ge100, ge400)
- Physical VLAN (ge100-X/Y/Z.N)
- Bundle (bundle-N)
- Bundle VLAN (bundle-N.M)
- IRB (irbN)

```
interfaces
  bundle-1
    admin-state enabled
    flowspec enabled
  !
  bundle-1.100
    flowspec enabled
  !
  ge100-1/0/1
    flowspec enabled
  !
  ge100-1/0/1.200
    flowspec disabled
  !
  irb1
    flowspec enabled
  !
!
```

### Default Value
- flowspec: disabled (by default)

### Removing Configuration
```
interfaces
  bundle-1
    no flowspec
  !
!
```

## `DNOS_FLOWSPEC_LOCAL_POLICIES_SYNTAX`

## DNOS FlowSpec Local Policies (Correct Syntax)

### Overview
FlowSpec Local Policies allow you to create locally-originated FlowSpec rules.
These rules are NOT propagated via BGP - they only affect the local router.

### Configuration Split Across THREE Hierarchies:

#### Hierarchy 1: DEFINE (routing-policy)
Define match-classes and policies.

```
routing-policy
  flowspec-local-policies
    ipv4
      match-class <MC_NAME>
        description "<text>"
        dest-ip <A.B.C.D/x>
        source-ip <A.B.C.D/x>
        vrf <VRF_NAME>               ← NEW: VRF match criteria (FlowSpec-VPN feature)
        protocol tcp(0x06) | udp(0x11) | icmp(0x01) | any
        dest-ports <port> | <port-range>
        src-ports <port> | <port-range>
        dscp <0-63>
        packet-length <value>
        fragmented true | false
        tcp-flag syn | ack | fin | rst | psh | urg
      !
      policy <POLICY_NAME>
        description "<text>"
        match-class <MC_NAME>
          action rate-limit <kbps>
          action redirect-to-vrf <VRF_NAME>
        !
      !
    !
    ipv6
      match-class <MC_NAME>
        dest-ip <X:X:X:X::X/x>
        source-ip <X:X:X:X::X/x>
        vrf <VRF_NAME>               ← NEW: VRF match criteria
        ...
      !
      policy <POLICY_NAME>
        ...
      !
    !
  !
!
```

### Match-Class Fields Reference
| Field | Description | Example |
|-------|-------------|---------|
| dest-ip | Destination IP prefix | dest-ip 10.0.0.0/8 |
| source-ip | Source IP prefix | source-ip 192.168.1.0/24 |
| **vrf** | **VRF to match traffic from (FlowSpec-VPN)** | **vrf CUSTOMER-A** |
| protocol | IP protocol | protocol tcp(0x06) |
| dest-ports | Destination port range | dest-ports 80 |
| src-ports | Source port range | src-ports 1024-65535 |
| dscp | DSCP value | dscp 46 |
| packet-length | Packet length | packet-length 1500 |
| fragmented | Match fragmented packets | fragmented |
| tcp-flag | TCP flags to match | tcp-flag syn ack |
| icmp | ICMP message type | icmp echo-request |

#### Hierarchy 2: APPLY (forwarding-options)
Activate the policy (only ONE policy per address family).

```
forwarding-options
  flowspec-local
    ipv4
      apply-policy-to-flowspec <POLICY_NAME>
    !
    ipv6
      apply-policy-to-flowspec <POLICY_NAME>
    !
  !
!
```

#### Hierarchy 3: ENABLE (interfaces)
Enable FlowSpec on interfaces where rules should apply.

```
interfaces
  bundle-1
    flowspec enabled
  !
  ge100-1/0/1
    flowspec enabled
  !
!
```

### Action Types

| Action | Syntax | Description |
|--------|--------|-------------|
| DROP | `action rate-limit 0` | Drop all matching traffic |
| Rate Limit | `action rate-limit <kbps>` | Limit to specified rate in kbps |
| Redirect VRF | `action redirect-to-vrf <VRF>` | Redirect to another VRF |

### Show Commands

```
show flowspec-local-policies match-classes
show flowspec-local-policies match-classes address-family ipv4
show flowspec-local-policies policies
show flowspec-local-policies policies address-family ipv4
show flowspec-local-policies counters
show flowspec-local-policies ncp
```

### Clear Commands

```
clear flowspec-local-policies counters
clear flowspec-local-policies counters address-family ipv4
```

### Complete Working Example

```
! ============================================
! STEP 1: DEFINE match-class and policy
! ============================================
routing-policy
  flowspec-local-policies
    ipv4
      match-class block-tcp-80
        description "Block TCP port 80 traffic"
        dest-ip 10.10.10.0/24
        protocol tcp(0x06)
        dest-ports 80
      !
      match-class rate-limit-udp
        description "Rate limit UDP"
        protocol udp(0x11)
      !
      policy ddos-mitigation
        description "DDoS Mitigation Policy"
        match-class block-tcp-80
          action rate-limit 0
        !
        match-class rate-limit-udp
          action rate-limit 1000000
        !
      !
    !
  !
!

! ============================================
! STEP 2: APPLY the policy
! ============================================
forwarding-options
  flowspec-local
    ipv4
      apply-policy-to-flowspec ddos-mitigation
    !
  !
!

! ============================================
! STEP 3: ENABLE FlowSpec on interfaces
! ============================================
interfaces
  bundle-1
    admin-state enabled
    flowspec enabled
  !
  bundle-2
    admin-state enabled
    flowspec enabled
  !
!

! ============================================
! COMMIT
! ============================================
commit
```

### KEY POINTS:
1. Local policies are NOT propagated via BGP
2. They apply SYSTEM-WIDE to ALL interfaces with `flowspec enabled`
3. Only ONE policy can be active per address family (ipv4 or ipv6)
4. `action rate-limit 0` = DROP
5. Configuration MUST be in 3 hierarchies: routing-policy → forwarding-options → interfaces

### VRF Match-Class (FlowSpec-VPN Feature)

Starting with FlowSpec-VPN support, local policies can now target specific VRFs:

```
routing-policy
  flowspec-local-policies
    ipv4
      match-class block-customer-attack
        vrf CUSTOMER-A                       ← Target this specific VRF
        dest-ip 192.168.100.0/24
        protocol tcp(0x06)
        dest-ports 80
      !
      policy customer-ddos-mitigation
        match-class block-customer-attack
          action rate-limit 0                 ← DROP
        !
      !
    !
  !
!
```

### Rule Precedence: Local vs BGP FlowSpec

When both Local Policy and BGP FlowSpec rules match the same traffic:

| Rule Source | Priority Range | Wins? |
|-------------|---------------|-------|
| **BGP FlowSpec** | 2,000,000 - 4,000,000 | **YES (higher priority)** |
| Local Policy | 0 - 1,999,999 | NO |

**BGP FlowSpec rules from Arbor/controller OVERRIDE local policies!**

### TCAM Resource Limits

Both Local Policies and BGP FlowSpec share the same TCAM space:
- **IPv4 FlowSpec**: 12,000 rules minimum capacity
- **IPv6 FlowSpec**: 4,000 rules minimum capacity

Monitor via: `xraycli /wb_agent/flowspec/bgp/ipv4/info` → `num_tcam_errors`

## `DNOS_FLOWSPEC_NLRI_COMPONENTS`

## FlowSpec NLRI Component Types (RFC 8955)

| Type | Component          | DNOS Syntax in NLRI String  | Example                    |
|------|--------------------|-----------------------------|----------------------------|
| 1    | Destination Prefix | DstPrefix:=<prefix>         | DstPrefix:=100.0.0.0/8     |
| 2    | Source Prefix      | SrcPrefix:=<prefix>         | SrcPrefix:=10.1.2.3/32     |
| 3    | IP Protocol        | Protocol:=<proto>           | Protocol:=6 (TCP)          |
| 4    | Port               | Port:=<value>               | Port:=80                   |
| 5    | Destination Port   | DstPort:=<value>            | DstPort:=443               |
| 6    | Source Port        | SrcPort:=<value>            | SrcPort:=12345             |
| 7    | ICMP Type          | IcmpType:=<value>           | IcmpType:=8                |
| 8    | ICMP Code          | IcmpCode:=<value>           | IcmpCode:=0                |
| 9    | TCP Flags          | TcpFlags:=<value>           | TcpFlags:=SYN              |
| 10   | Packet Length      | PktLen:=<value>             | PktLen:=<1500              |
| 11   | DSCP               | Dscp:=<value>               | Dscp:=46                   |
| 12   | Fragment           | Fragment:=<value>           | Fragment:=DF               |

### Operators in NLRI
- = equals
- < less than
- > greater than
- & AND
- | OR

Example: DstPort:<9&>6|=12 means (DstPort < 9 AND DstPort > 6) OR DstPort = 12

## `DNOS_FLOWSPEC_SHOW_COMMANDS`

## DNOS FlowSpec Show Commands

### BGP FlowSpec in Default VRF
```
show bgp ipv4 flowspec
show bgp ipv4 flowspec summary
show bgp ipv4 flowspec neighbors
show bgp ipv4 flowspec neighbors <IP>
show bgp ipv4 flowspec neighbors <IP> advertised-routes
show bgp ipv4 flowspec neighbors <IP> advertised-routes nlri "<NLRI>"
show bgp ipv4 flowspec neighbors <IP> received-routes
show bgp ipv4 flowspec neighbors <IP> received-routes nlri "<NLRI>"
show bgp ipv4 flowspec nlri "<NLRI>"
show bgp ipv4 flowspec destination <prefix>
show bgp ipv4 flowspec destination <prefix> source <prefix>
show bgp ipv4 flowspec statistics
show bgp ipv4 flowspec community <community>
show bgp ipv4 flowspec community-list <name>
show bgp ipv4 flowspec ext-community regex "<regex>"
show bgp ipv4 flowspec large-community
```

### BGP FlowSpec-VPN (SAFI 134)
```
show bgp ipv4 flowspec-vpn
show bgp ipv4 flowspec-vpn summary
show bgp ipv4 flowspec-vpn neighbors
show bgp ipv4 flowspec-vpn neighbors <IP> advertised-routes
show bgp ipv4 flowspec-vpn neighbors <IP> received-routes
show bgp ipv4 flowspec-vpn rd <RD>
show bgp ipv4 flowspec-vpn rd <RD> nlri "<NLRI>"
show bgp ipv4 flowspec-vpn statistics
show bgp ipv4 flowspec-vpn community <community>
```

### BGP FlowSpec in Non-Default VRF
```
show bgp instance vrf <VRF_NAME> ipv4 flowspec
show bgp instance vrf <VRF_NAME> ipv4 flowspec summary
show bgp instance vrf <VRF_NAME> ipv4 flowspec neighbors
show bgp instance vrf <VRF_NAME> ipv4 flowspec nlri "<NLRI>"
show bgp instance vrf <VRF_NAME> ipv4 flowspec community <community>
```

### FlowSpec Rules and Counters
```
show flowspec ncp
show flowspec ncp <NCP_ID>
show flowspec ncp <NCP_ID> nlri "<NLRI>"
show flowspec-local-policies counters
show flowspec-local-policies counters address-family ipv4
show flowspec-local-policies counters address-family ipv6
show flowspec-local-policies match-classes
show flowspec-local-policies policies
```

### NLRI String Format (CRITICAL)
NLRI strings MUST be quoted with double quotes ("").
Especially important for IPv6-FlowSpec with special symbols.

Example NLRI formats:
```
"DstPrefix:=100.100.100.1/32"
"DstPrefix:=100.100.100.1/32,Protocol:=6"
"DstPrefix:=100.100.100.1/32,Protocol:=6,DstPort:=80"
"DstPrefix:=50.0.0.0/8,SrcPrefix:=50.1.2.3/32,Protocol:=6,DstPort:<9&>6|=12,SrcPort:=50|=30,Dscp:=5"
```

IPv6 Example:
```
"DstPrefix:=aaaa::11:11:11:11/0-96,SrcPrefix:=bbbb::11:22:33:44/128,DstPort:<9&>6|=12,SrcPort:=51|=30,Dscp:=6"
```

## `DNOS_FLOWSPEC_VPN_COMPLETE_EXAMPLE`

## Complete FlowSpec-VPN Configuration Example

### PE Router Configuration
```
! System Configuration
system
  name PE-1
!

! Loopback Interface
interfaces
  lo0
    admin-state enabled
    ipv4-address 10.0.0.1/32
  !
!

! WAN Interface (MPLS Core)
interfaces
  bundle-1
    admin-state enabled
    mpls enabled
    ipv4-address 10.1.1.1/30
  !
!

! CE-Facing Interface (VRF)
interfaces
  bundle-2.100
    vlan-id 100
    ipv4-address 192.168.1.1/24
    flowspec enabled
  !
!

! ISIS for Underlay
protocols
  isis CORE
    admin-state enabled
    net 49.0001.0100.0000.0001.00
    interface bundle-1
      admin-state enabled
      level-capability level-2
      circuit-type point-to-point
    !
    interface lo0
      admin-state enabled
      passive enabled
    !
  !
!

! LDP for MPLS Labels
protocols
  ldp
    admin-state enabled
    router-id 10.0.0.1
    transport-address 10.0.0.1
    interface bundle-1
      admin-state enabled
    !
  !
!

! BGP Configuration
protocols
  bgp 65000
    router-id 10.0.0.1
    ! iBGP to Route Reflector
    neighbor 10.0.0.100
      remote-as 65000
      update-source lo0
      address-family ipv4-flowspec-vpn
        admin-state enabled
        send-community extended
      !
      address-family ipv4-vpn
        admin-state enabled
        send-community extended
      !
    !
    ! eBGP to Arbor (FlowSpec controller)
    neighbor 192.168.100.1
      remote-as 65001
      address-family ipv4-flowspec-vpn
        admin-state enabled
        send-community extended
      !
    !
  !
!

! VRF Configuration
network-services
  vrf instance CUSTOMER-1
    description "Customer 1 VRF"
    route-distinguisher 10.0.0.1:100
    route-target import 65000:100
    route-target export 65000:100
    interface bundle-2.100
    !
    protocols bgp 65000
      router-id 10.0.0.1
      address-family ipv4-unicast
        admin-state enabled
      !
      address-family ipv4-flowspec
        import-vpn route-target 65000:100
      !
    !
  !
!
```

### Verification Commands
```
! Check BGP FlowSpec-VPN session
show bgp ipv4 flowspec-vpn summary
show bgp ipv4 flowspec-vpn neighbors

! Check FlowSpec-VPN routes in GRT
show bgp ipv4 flowspec-vpn

! Check FlowSpec rules in VRF
show bgp instance vrf CUSTOMER-1 ipv4 flowspec

! Check FlowSpec rules installed in NCP
show flowspec ncp

! Check FlowSpec counters
show flowspec-local-policies counters

! Clear counters before testing
clear flowspec counters
```

## `DNOS_FLOWSPEC_VPN_SYNTAX`

## DNOS FlowSpec-VPN Configuration (SAFI 134)

### BGP Neighbor for FlowSpec-VPN (Default VRF)
FlowSpec-VPN is configured in the default VRF with ipv4-flowspec-vpn or ipv6-flowspec-vpn address-family.

```
protocols
  bgp 65000
    neighbor 192.168.1.1
      remote-as 65001
      address-family ipv4-flowspec-vpn
        admin-state enabled
        send-community extended
      !
      address-family ipv6-flowspec-vpn
        admin-state enabled
        send-community extended
      !
    !
    neighbor-group FLOWSPEC_PEERS
      address-family ipv4-flowspec-vpn
        admin-state enabled
        send-community extended
      !
    !
  !
!
```

### VRF Import for FlowSpec Rules
FlowSpec-VPN rules are imported into non-default VRFs via Route Target matching.

```
network-services
  vrf instance VRF1
    route-distinguisher 10.0.0.1:100
    route-target import 65000:100
    route-target export 65000:100
    protocols bgp 65000
      address-family ipv4-flowspec
        import-vpn route-target 65000:100
      !
    !
  !
!
```

### Interface Binding in VRF
Interfaces attached to VRF must have flowspec enabled to apply rules.

```
interfaces
  bundle-2.100
    vlan-id 100
    ipv4-address 10.10.0.1/30
  !
!

network-services
  vrf instance VRF1
    interface bundle-2.100
    !
  !
!
```

### FlowSpec Enable on VRF Interface
```
interfaces
  bundle-2.100
    flowspec enabled
  !
!
```

## `DNOS_ISIS_MPLS_SYNTAX`

## DNOS ISIS and MPLS/LDP Configuration

### ISIS Configuration (Default VRF Only)
```
protocols
  isis <INSTANCE_NAME>
    admin-state enabled
    net <NET_ADDRESS>
    interface <INTERFACE_NAME>
      admin-state enabled
      level-capability level-2
      circuit-type point-to-point
      passive disabled
    !
    interface lo0
      admin-state enabled
      passive enabled
    !
  !
!
```

### LDP Configuration
```
protocols
  ldp
    admin-state enabled
    router-id <LOOPBACK_IP>
    transport-address <LOOPBACK_IP>
    interface <INTERFACE_NAME>
      admin-state enabled
    !
  !
!
```

### MPLS Label Protocols
```
protocols
  mpls
    label-protocol ldp
    !
  !
!
```

### LDP Explicit-Null (for IPv6 over MPLS / 6VPE)
When the penultimate hop pops the label it sends an IPv6 packet; if the core is IPv4-only, that packet is dropped. Enable explicit-null for IPv6 so the PE advertises a non-popped label and the core forwards a labeled packet to the PE.
```
protocols
  ldp
    address-family ipv4-unicast
      label explicit-null enabled
    !
    address-family ipv6-unicast
      label explicit-null enabled
    !
  !
!
```
CLI: protocols → ldp → address-family ipv6-unicast → label explicit-null enabled
Optional (LDP README): label explicit-null for <prefix-list> | filter <prefix-list>

## `DNOS_LOOPBACK_SYNTAX`

## DNOS Loopback Interface Configuration

```
interfaces
  lo0
    admin-state enabled
    ipv4-address <A.B.C.D>/32
    ipv6-address <IPV6>/128
  !
  lo1
    admin-state enabled
    ipv4-address <A.B.C.D>/32
  !
!
```

### Show Commands
```
show interfaces lo0
show interfaces lo0 status
```

## `DNOS_MPLS_INTERFACE_SYNTAX`

## DNOS MPLS Interface Configuration

### Enable MPLS on Interface
```
interfaces
  bundle-1
    admin-state enabled
    mpls enabled
    ipv4-address 10.0.0.1/30
  !
!
```

### Supported interface types for MPLS:
- Physical (ge10, ge25, ge40, ge50, ge100, ge400)
- Physical VLAN (ge100-X/Y/Z.N)
- Bundle (bundle-N)
- Bundle VLAN (bundle-N.M)

### Default Value
- mpls: disabled (by default)

## `DNOS_STATIC_ROUTES_SYNTAX`

## DNOS Static Routes Configuration

### Default VRF Static Routes
```
protocols
  static
    address-family ipv4-unicast
      route <PREFIX>
        next-hop <NEXT_HOP_IP>
          admin-state enabled
        !
      !
    !
    address-family ipv6-unicast
      route <PREFIX>
        next-hop <NEXT_HOP_IP>
          admin-state enabled
        !
      !
    !
  !
!
```

### Non-Default VRF Static Routes
```
network-services
  vrf instance <VRF_NAME>
    protocols static
      address-family ipv4-unicast
        route <PREFIX>
          next-hop <NEXT_HOP_IP>
            admin-state enabled
          !
        !
      !
    !
  !
!
```

### Show Commands
```
show route static
show route vrf <VRF_NAME> static
```

## `DNOS_VRF_SYNTAX`

## DNOS VRF Configuration

### ⚠️ CRITICAL: VRF Interface Attachment Rules

**DNOS uses a TWO-STEP process for VRF interface attachment:**

1. **STEP 1: Configure interface** (under `interfaces` hierarchy)
2. **STEP 2: Attach to VRF** (under `network-services vrf instance` hierarchy)

**❌ WRONG - VRF is NOT configured under interface:**
```
interfaces
  bundle-1.100
    flowspec enabled
        vrf Source    ← WRONG! 'vrf' is NOT a child of 'flowspec'
    !
  !
!
```

**❌ WRONG - VRF is NOT configured under interface (variant 2):**
```
interfaces
  bundle-1.100
    vrf Source        ← WRONG! 'vrf' is NOT under 'interfaces' hierarchy
    flowspec enabled
  !
!
```

**✅ CORRECT - Two separate hierarchies:**
```
! STEP 1: Configure interface (under 'interfaces')
interfaces
  bundle-1.100
    vlan-id 100
    admin-state enabled
    ipv4-address 192.168.100.2/24
    flowspec enabled
  !
!

! STEP 2: Attach interface to VRF (under 'network-services vrf instance')
network-services
  vrf instance Source
    description "VRF for FlowSpec peer"
    route-distinguisher 10.0.0.1:100
    route-target import 65000:100
    route-target export 65000:100
    interface bundle-1.100          ← Attach interface HERE!
    !
    protocols bgp 65000
      router-id 10.0.0.1
      neighbor 192.168.100.1
        remote-as 65000
        address-family ipv4-flowspec
          admin-state enabled
        !
      !
    !
  !
!
```

### VRF Instance Creation
```
network-services
  vrf instance <VRF_NAME>
    description "VRF description"
    route-distinguisher <IP>:<N>
    route-target import <ASN>:<N>
    route-target export <ASN>:<N>
    interface <INTERFACE_NAME>
    !
    protocols bgp <ASN>
      router-id <A.B.C.D>
      address-family ipv4-unicast
        admin-state enabled
        redistribute static
      !
      address-family ipv4-flowspec
        import-vpn route-target <ASN>:<N>
      !
      neighbor <IP>
        remote-as <ASN>
        address-family ipv4-unicast
          admin-state enabled
        !
      !
    !
  !
!
```

### VRF Interface Attachment (Detailed)

**ALWAYS follow this order:**
1. Configure interface with L3 settings (IP address, VLAN, flowspec, etc.)
2. Create VRF instance with RD/RT
3. Attach interface to VRF using `interface <name>` under VRF hierarchy

**Step 1: Configure Interface**
```
interfaces
  bundle-2.100
    vlan-id 100
    ipv4-address 10.10.0.1/30
    flowspec enabled
  !
!
```

**Step 2: Attach to VRF**
```
network-services
  vrf instance VRF1
    interface bundle-2.100
    !
  !
!
```

### VRF Show Commands
```
show vrf
show vrf <VRF_NAME>
show network-services vrf <VRF_NAME>
show route vrf <VRF_NAME>
show route vrf <VRF_NAME> summary
```

### Non-Default VRF Support Matrix
| Protocol | Non-Default VRF Support |
|----------|------------------------|
| BGP      | ✓ Supported            |
| EVPN     | ✓ Supported            |
| Static   | ✓ Supported            |
| VRRP     | ✓ Supported            |
| OSPF     | ✗ NOT Supported        |
| ISIS     | ✗ NOT Supported        |

---

# Networking Guidelines (from networking_guidelines.py)

## `NETWORK_ENGINEER_SYSTEM_PROMPT`

You are an expert Network QA Engineer specializing in:
- BGP protocol family (all AFI/SAFI combinations)
- MPLS and Segment Routing
- EVPN and L2/L3 VPN technologies
- RFC compliance testing
- Multi-vendor interoperability

You work for DriveNets, testing DNOS (DriveNets Network Operating System).
DNOS is a cloud-native, disaggregated networking solution.


## CRITICAL DNOS SYNTAX RULES FOR TEST GENERATION

You are generating tests for DriveNets DNOS (DriveNets Network Operating System).
You MUST use ONLY Drivenets DNOS CLI syntax. 
DO NOT use Cisco IOS, IOS-XR, Juniper, Nokia, or any other vendor syntax.

### MANDATORY RULES:

1. **Indentation**: Use exactly 2 SPACES per level (NOT tabs)
2. **Block Terminators**: Every block ends with "!" at content indent level
3. **Interface Hierarchy**: Interfaces are FLAT (sub-interfaces are siblings, NOT children)
4. **No 'interface' keyword**: Use interface name directly under 'interfaces'
5. **Command Verification**: Only use commands documented in DNOS CLI docs
6. **NLRI Quotes**: Always quote NLRI strings with double quotes ("")
7. **Complex Hierarchy Awareness**: Some features require config in MULTIPLE hierarchies!

### CRITICAL: COMPLEX HIERARCHY PATTERNS

Many DNOS features require configuration ACROSS MULTIPLE HIERARCHIES.
Always check where each command belongs!

#### FlowSpec Local Policies (3 hierarchies):
1. DEFINE: `routing-policy flowspec-local-policies ipv4 match-class/policy`
2. APPLY:  `forwarding-options flowspec-local ipv4 apply-policy-to-flowspec`  ← NOT under routing-policy!
3. ENABLE: `interfaces <IF> flowspec enabled`

#### VRF with Interface (2 hierarchies) - CRITICAL:
1. CONFIGURE INTERFACE: `interfaces <IF> ipv4-address, flowspec enabled`  ← Configure FIRST
2. ATTACH TO VRF: `network-services vrf instance <VRF> interface <IF>`  ← Attach SECOND

**❌ NEVER put `vrf <name>` under interfaces or under flowspec enabled!**
**✅ VRF attachment is ALWAYS under `network-services vrf instance <VRF> interface <IF>`**

#### Routing Policy in BGP (2 hierarchies):
1. DEFINE: `routing-policy policy <NAME>`
2. APPLY:  `protocols bgp neighbor <IP> address-family export-policy <NAME>`

### COMMON DNOS vs OTHER VENDOR DIFFERENCES:

| Feature              | DNOS                                    | Cisco IOS-XR                           |
|---------------------|----------------------------------------|----------------------------------------|
| Enter config mode   | configure                               | configure terminal                     |
| BGP config          | protocols bgp <ASN>                    | router bgp <ASN>                       |
| Neighbor config     | neighbor <IP>                          | neighbor <IP>                          |
| Address family      | address-family ipv4-unicast            | address-family ipv4 unicast            |
| Enable feature      | admin-state enabled                    | no shutdown                            |
| Interface config    | interfaces bundle-1                    | interface Bundle-Ether1                |
| VRF config          | network-services vrf instance <NAME>   | vrf <NAME>                             |
| FlowSpec enable     | flowspec enabled                       | flowspec address-family ipv4           |
| MPLS enable         | mpls enabled                           | mpls ldp                               |
| Static route        | protocols static address-family...     | router static address-family ipv4...   |

### DNOS-SPECIFIC COMMANDS TO USE:

BGP:
- protocols bgp <ASN>
- neighbor <IP> address-family ipv4-flowspec-vpn
- neighbor <IP> address-family ipv4-flowspec
- send-community extended

VRF:
- network-services vrf instance <NAME>
- route-distinguisher <IP>:<N>
- route-target import <ASN>:<N>
- route-target export <ASN>:<N>
- interface <INTERFACE_NAME>  ← Attaches interface to VRF (interface must be configured first!)
- protocols bgp <ASN> address-family ipv4-flowspec import-vpn route-target <ASN>:<N>

**VRF Interface Attachment - CRITICAL SYNTAX:**
- ❌ WRONG: `interfaces bundle-1.100 vrf Source` (vrf is NOT under interfaces!)
- ❌ WRONG: `interfaces bundle-1.100 flowspec enabled vrf Source` (vrf is NOT under flowspec!)
- ✅ CORRECT: `network-services vrf instance Source interface bundle-1.100`

Interface:
- interfaces bundle-1
- interfaces ge100-1/0/1
- interfaces lo0
- flowspec enabled
- mpls enabled
- admin-state enabled/disabled (ONLY for interfaces and BGP neighbors, NOT for BGP address-families!)
- ipv4-address <IP>/mask

**⚠️ BGP Address-Family admin-state Rule:**
- BGP address-family blocks MUST use `admin-state enabled` to activate
- ❌ NEVER generate `admin-state disabled` under a BGP address-family
- To deactivate a BGP address-family, remove it with `no address-family <name>`
- `admin-state disabled` is valid for: interfaces, BGP neighbors, protocols (ISIS/LDP/RSVP)

Show Commands:
- show bgp ipv4 flowspec-vpn summary
- show bgp ipv4 flowspec-vpn neighbors <IP> received-routes
- show bgp instance vrf <VRF> ipv4 flowspec
- show flowspec ncp
- show flowspec-local-policies counters

Clear Commands:
- clear flowspec counters
- clear flowspec counters ipv4

Commit:
- rollback 0 (CRITICAL: Always run before terminal paste)
- commit
- commit check


When generating tests:
1. ALWAYS validate against RFC specifications when mentioned
2. Use ONLY DNOS-specific CLI syntax (2-space indentation, flat interface model)
3. DO NOT use Cisco IOS-XR, Juniper, Nokia, or any other vendor CLI syntax
4. Follow the test template strictly (Name, Description, Steps, Pass Criteria, Variants)
5. Categorize tests appropriately (Basic vs Advanced functionality)
6. Use EXACT DNOS show commands from documentation

CRITICAL DNOS RULES:
- Interface hierarchy is FLAT (sub-interfaces are siblings, NOT children)
- Use 'rollback 0' before terminal paste
- Non-default VRF only for: BGP, EVPN, Static, VRRP
- Container-based architecture affects HA testing
- FlowSpec enable: "flowspec enabled" under interface
- MPLS enable: "mpls enabled" under interface
- NLRI strings MUST be quoted with double quotes ("")

ADMIN-STATE CONTEXT RULES:
- "admin-state enabled/disabled" is valid on: interfaces, BGP neighbors, protocols (ISIS/LDP/RSVP)
- "admin-state disabled" is NOT valid under BGP address-family blocks
- BGP address-families activate with "admin-state enabled"; deactivate with "no address-family <name>"
- DNOS SR-TE address-family names: "ipv4-sr-te" and "ipv6-sr-te" (NOT "sre" or "sr-te")

NETCONF/gNMI TEST GENERATION RULES:
- NETCONF uses SSH port 830, candidate datastore, edit-config + commit workflow
- NETCONF edit-config replace is subtree-scoped (safe)
- gNMI uses gRPC port 50051; Set Update (safe), Set Delete (safe), Set Replace (DANGEROUS — wipes ALL config via LOFD)
- NEVER generate gNMI Set Replace tests — use NETCONF edit-config replace for replace semantics
- gNMI Set requires TLS; without TLS, gNMI is read-only — mark Set tests as SKIP, not FAIL
- gNMI has no candidate datastore (immediate commit) and no rollback (use CLI rollback)
- DN YANG path: /drivenets-top/network-services/vrfs/vrf[vrf-name=X]/protocols/bgp[as-number=Y]
- OpenConfig path: /network-instances/network-instance[name=X]/protocols/protocol[identifier=BGP,name=DEFAULT]/bgp
- Cannot mix DN + OC + NACM YANG trees in one gNMI SetRequest
- SNMP: only test GET, Walk, Traps — SNMP Set is NOT production-ready (SW-209493)
- Not all features have SNMP MIBs (e.g., no FlowSpec MIB exists)

## `DNOS_NETWORKING_KNOWLEDGE`

## DNOS Network Implementation Details


## DNOS Configuration Hierarchy Rules (MANDATORY)

### Indentation
- Use exactly 2 SPACES per level (NOT tabs!)
- Level 0: No indent
- Level 1: 2 spaces
- Level 2: 4 spaces
- Level 3: 6 spaces

### Block Terminators
- Every block MUST end with "!" at content indentation level
- Closing "!" must match the indentation of the block content

### Interface Hierarchy (CRITICAL)
- DNOS interfaces are FLAT, not hierarchical
- Sub-interfaces are SIBLINGS of parents, NOT children
- Interface names at 2-space indent with NO 'interface' keyword

### Correct Example:
```
interfaces
  bundle-1
    admin-state enabled
    ipv4-address 10.0.0.1/30
  !
  bundle-1.100
    vlan-id 100
    ipv4-address 10.1.0.1/30
  !
!
```

### WRONG Example:
```
interfaces
  bundle-1
    admin-state enabled
    bundle-1.100      <- WRONG: sub-interface nested under parent
      vlan-id 100
    !
  !
!
```


### ⚠️ CRITICAL: VRF Interface Attachment Rules

**DNOS uses a TWO-STEP process for attaching interfaces to VRFs:**

1. **STEP 1**: Configure interface (under `interfaces` hierarchy)
2. **STEP 2**: Attach to VRF (under `network-services vrf instance` hierarchy)

**❌ WRONG - VRF is NOT configured under interface:**
```
interfaces
  bundle-1.100
    flowspec enabled
        vrf Source    ← WRONG! 'vrf' is NOT a child of 'flowspec' or 'interfaces'
    !
  !
!
```

**✅ CORRECT - Two separate hierarchies:**
```
! STEP 1: Configure interface (under 'interfaces')
interfaces
  bundle-1.100
    vlan-id 100
    admin-state enabled
    ipv4-address 192.168.100.2/24
    flowspec enabled
  !
!

! STEP 2: Attach interface to VRF (under 'network-services vrf instance')
network-services
  vrf instance Source
    interface bundle-1.100          ← Attach interface HERE!
    !
  !
!
```

**Key Rules:**
- VRF attachment is ALWAYS under `network-services vrf instance <VRF> interface <IF>`
- Interface MUST be configured BEFORE attaching to VRF
- `flowspec enabled` goes under interface hierarchy, NOT under VRF
- NEVER put `vrf <name>` under `interfaces` or under `flowspec enabled`

### VRF Support Matrix
| Protocol | Default VRF | Non-Default VRF |
|----------|:-----------:|:---------------:|
| BGP      | ✓           | ✓               |
| EVPN     | ✓           | ✓               |
| Static   | ✓           | ✓               |
| VRRP     | ✓           | ✓               |
| OSPF     | ✓           | ✗               |
| ISIS     | ✓           | ✗               |

### Commit Model
- Always use 'rollback 0' before terminal paste (CRITICAL!)
- Use 'commit confirm' for safety
- 'load override' replaces config
- 'load merge' preserves existing config
- 'commit check' validates without applying

### Container Architecture
- Each function runs in a Docker container
- Individual process restarts possible
- State stores persist across restarts
- Warm restart preserves forwarding entries

### FlowSpec Interface Configuration
- FlowSpec must be enabled on interfaces: `flowspec enabled`
- Supported on: Physical, Bundle, VLAN sub-interfaces, IRB
- MPLS must be enabled on WAN interfaces: `mpls enabled`

### BGP Address Families for FlowSpec
| Address Family     | SAFI | Use Case                        |
|--------------------|------|----------------------------------|
| ipv4-flowspec      | 133  | FlowSpec in default VRF         |
| ipv6-flowspec      | 133  | IPv6 FlowSpec in default VRF    |
| ipv4-flowspec-vpn  | 134  | FlowSpec VPN (GRT distribution) |
| ipv6-flowspec-vpn  | 134  | IPv6 FlowSpec VPN               |

### FlowSpec VPN Import to VRF
FlowSpec-VPN rules are imported via Route Target matching:
```
network-services
  vrf instance VRF1
    protocols bgp 65000
      address-family ipv4-flowspec
        import-vpn route-target 65000:100
      !
    !
  !
!
```
