# Test Plan Examples (from RAG)

This document aggregates example test cases from the TP Generator RAG corpus (openai_v2 `test_plan_examples/SW-91352`) plus a sample generated enhanced test plan from openai_v3. It is intended as a flat reference for agents (replacing FAISS vector retrieval).

**Source epic (RAG JSON):** SW-91352 OSPFv2 network-type broadcast

## Table of contents

- [Feature context](#feature-context-sw-91352)
- [CLI tests](#cli-tests)
- [HA tests](#ha-tests)
- [Functionality tests](#functionality-tests)
- [System resources tests](#system-resources-tests)
- [Logs and traces tests](#logs-and-traces-tests)
- [System events tests](#system-events-tests)
- [SNMP tests](#snmp-tests)
- [NETCONF tests](#netconf-tests)
- [gNMI tests](#gnmi-tests)
- [Upgrade tests](#upgrade-tests)
- [Special tests](#special-tests)
- [Generated enhanced test plan sample (openai v3)](#generated-enhanced-test-plan-sample-openai-v3)

---

## Feature context (SW-91352)

- **Epic ID:** SW-91352
- **Epic name:** OSPFv2 network-type broadcast
- **Epic type:** Epic

**Epic description:**

+*Background*+
STNet’s core consists of a backbone (Area 0), which is a single broadcast domain. The backbone area connects to multiple non-zero area networks, which can be either broadcast or P2P. DNOS is planned to be deployed as a Core router and later as an ABR.

+*Functional explanation*+
The OSPF broadcast network type is used on networks where multiple OSPF routers are connected to a single shared broadcast medium, such as an Ethernet LAN, and all routers must communicate.

In a multiaccess segment, as more routers are added to the link, more adjacencies must be formed. This full-mesh requirement places extra load on the routers with little extra benefit, since all advertise the same link information. The solution is to have different roles for routers in the broadcast domain.

+Roles:+

* DR (Designated Router) - Represents the broadcast link to the rest of the network and forms adjacencies with all routers in the broadcast network.
* BDR (Backup Designated Router) - Elected to take over if the DR fails. Forms adjacencies with all OSPF routers on the segment, but does not advertise learned link-state information unless it becomes DR.
* DR Other - Any router in the broadcast network that is not DR or BDR. Must form adjacencies with the DR and BDR.

!image-20240909-064650.png|width=50%,alt="image-20240909-064650.png"!

+DR and BDR Election:+

OSPF elects the DR based on two criteria: *Priority* and *Router ID (RID)*. OSPF DR priorities range from 0 to 255. A higher priority increases the chance of becoming DR; a priority of 0 means the router is ineligible. If priorities tie, the router with the higher RID wins.

The DR election is nondeterministic. To avoid instability, the current DR remains until it leaves the network. The first DR election on a segment occurs within 40 seconds of the first Hello packet. This wait time is honored for every election.

After the DR is elected, a BDR is elected using the same rules. The BDR monitors the DR and takes over if the DR leaves. A new BDR is then elected. BDR election is also nondeterministic.

Each non-DR router sends LSA type 1 to DR/BDR at 224.0.0.6. The DR then sends LSA type 2 to 224.0.0.5.

!image-20240909-070623.png|width=91.67%,alt="image-20240909-070623.png"!

In the example above, the next-hop of the broadcast network is the DR address (10.1.255.2), and the OSPF LSDB appears as follows:

{noformat}Router Link States (Area 0) <----- LSA Type 1
Link ID         ADV Router      
0.0.0.1         0.0.0.1         
0.0.0.2         0.0.0.2         
0.0.0.3         0.0.0.3
0.0.0.4         0.0.0.4         
0.0.0.5         0.0.0.5         

Net Link States (Area 0) <----- LSA Type 2
Link ID         ADV Router      
10.1.255.2      0.0.0.2 <----- DR address/RID{noformat}

OSPF Database example:

{noformat}OSPF Router with ID (0.0.0.1) (Process ID 101)

Net Link States (Area 0)
  LS age: 1196
  Options: (No TOS-capability, DC)
  LS Type: Network Links
  Link State ID: 10.1.255.2 <----- DR address
  Advertising Router: 0.0.0.2 <----- DR
  LS Seq Number: 80000002
  Checksum: 0xC356
  Length: 40
  Network Mask: /24 <--------------- Network/routers in the broadcast domain
        Attached Router: 0.0.0.1
        Attached Router: 0.0.0.2
        Attached Router: 0.0.0.3
        Attached Router: 0.0.0.4
        Attached Router: 0.0.0.5{noformat}

Network example with both P2P and Broadcast in the same area:

!image-20240909-162130.png|width=66.67%,alt="image-20240909-162130.png"!

+*Requirements:*+

* Support broadcast network interfaces for OSPFv2/v3.
* Both broadcast and P2P networks must work in the same OSPF area.
* Support DR and BDR roles.
* Support priority configuration range 0-255 (default: 100).
* Support LSA Type 2 (flood scope: broadcast domain).
* Add DR/BDR/DR Other information in show commands (see below).
* Support HA mechanisms:
  * NSR
  * GR
* Add a system event reflecting DR/BDR election.
* Assumptions:
  * Expected traffic is native IP only, no MPLS.
  * Single OSPFv2/v3 instance.
  * Multiple OSPFv2 areas (single OSPFv3 area is OK).
  * A broadcast network will have at least 2 routers.
  * Future: OSPF on non-default VRF may be required; consider if relevant.
* Waivers:
  * MPLS is not required. If MPLS config can break DNOS, block it from broadcast.
  * Stub/NSSA not required (should work, but not required).
  * BFD is not required on broadcast links.
  * LFA is out of scope.

+*CLI examples*+

+Example configuration:+

{noformat}protocols
  ospf
    instance <NAME>
      area <AREA#>
        interface <INTERFACE>
          priority <0-255>
          network-type broadcast

protocols
  ospfv3
    area <AREA#>
      interface <INTERFACE>
        priority <0-255>
        network-type broadcast{noformat}

+Show command:+

{noformat}<DNOS>
CL_1# show ospf neighbors

Neighbor ID     Pri State           Dead Time Address         Interface                           Uptime RXmtL RqstL DBsmL
10.0.0.2        128 Full              36.498s 10.10.3.2       ge100-4/0/0:10.10.3.1             11h47m4s     0     0     0
10.0.0.3        128 Full              31.786s 10.10.1.2       ge100-0/0/68:10.10.1.1            11h47m4s     0     0     0

<IOS-XR>
RP/0/0/CPU0:IOSXR-1#show ospf neighbor
 
Neighbor ID     Pri   State           Dead Time   Address         Interface
2.2.2.2         1     FULL/BDR        00:00:35    192.168.0.2     GigabitEthernet0/0/0/0{noformat}

{noformat}<DNOS>
CL_1(cfg)# show ospf interfaces
OSPF instance OSPF-SR
Interface                                         State     Type                Area
ge100-0/0/68                                      Up        POINT-TO-POINT      0.0.0.0
lo0                                               Up        LOOPBACK            0.0.0.0

<IOS-XR>
RP/0/0/CPU0:IOSXR-1#show ospf interface brief
Interfaces for OSPF 1
 
Interface          PID   Area            IP Address/Mask    Cost  State Nbrs F/C
Lo0                1     0               1.1.1.1/32         1     LOOP  0/0
Gi0/0/0/0          1     0               192.168.0.1/24     1     DR    1/1{noformat}

+*Testing Guidance:*+

* 4 non-zero OSPFv2 areas (+1 backbone area)
* 5K OSPF routes
* Customer topology: ~130 routers
  * ~30 routers in the Backbone area
  * ~10 routers in each non-zero area
* Interop considerations: Cisco/Juniper

+*RFC:*+

|*Required – Added by Product*|*Actual/Implemented – Added by SysArch*|*Comments*|
|[https://datatracker.ietf.org/doc/html/rfc2328|https://datatracker.ietf.org/doc/html/rfc2328|smart-link]|||

Req review [OSPFv2_v3 Broadcast network Req review - Placeholder-20240909_160556-Meeting Recording.mp4|https://drivenets-my.sharepoint.com/:v:/r/personal/ielbaz_drivenets_com/Documents/Recordings/OSPFv2_v3%20Broadcast%20network%20Req%20review%20-%20Placeholder-20240909_160556-Meeting%20Recording.mp4?csf=1&web=1&e=ChTEnm]

---

## CLI tests

Subsections mirror `01_CLI_Configuration_Tests/` (main CLI, show commands, negative).

### Main CLI

**JSON label:** CLI Tests  
**Mandatory:** True  

**Purpose:** Test the basic functionality of the feature in terms of cli, make sure to check the config and the 'no' form of the command from all hierarchies

#### 1. Verify command "protocols ospf instance <value> area <value> interface network-type broadcast" availability and description
**Steps:**

1. Verify the command availability.
2. Verify the description for this command.
3. Verify the help menu using <TAB> and <?> for multiple commands per line.
4. Verify the help menu using <TAB> and <?> for single command per line.
5. Verify auto-completition for the given command.
6. Verify that the keyboard shortcuts are working when entering priority and tag value configuration commands ( e.g Ctrl+C , Ctrl+V , Ctrl+W, Ctrl+A etc. ).

**Pass criteria:**

1. The command should be available as specified in functional spec document.
2. The command description should be intuitive and with no typos.
3. Help menu should display relevant/correct information about the command when using <TAB> and <?> when configuring multiple command per line.
4. Help menu should display relevant/correct information about the command when using <TAB> and <?> when configuring a single command per line.
5. Auto-completition should work for the given command.
6. The keyboard shortcuts should work when entering priority and tag value configuration command ( e.g Ctrl+C , Ctrl+V , Ctrl+W etc. ).

---

#### 2. Verify command "protocols ospf instance <value> area <value> interface network-type broadcast" - only the valid values are accepted and applied
**Steps:**

1. Positive testing: for "protocols ospfv3 area interface network-type broadcast" command involving valid values from the command.
2. Negative testing: for "protocols ospfv3 area interface network-type broadcast" command involving invalid values from the command, words, special characters and empty value.

**Pass criteria:**

1. All valid values should be accepted and successfully applied.
2. All invalid values should be rejected and relevant error messages should be returned.

---

#### 3. Verify command "protocols ospf instance <value> area <value> interface network-type broadcast" - command is successfully applied/removed to/from the running config
**Steps:**

1. Configure a valid value for the "protocols ospfv3 area interface network-type broadcast" command.
2. Verify that the candidate configuration is displayed properly.
3. Commit the transaction.
4. Verify the running configuration.
5. Remove the previous configuration or reset it to its default value.
6. Verify that the candidate configuration is displayed properly.
7. Commit the transaction.
8. Verify the running configuration.

**Pass criteria:**

1. The valid configuration should be accepted, and the candidate configuration should reflect the actual config change.
2. Validate that the hierarchy is displayed correctly, all entries are correct.
3. The transaction gets successfully committed.
4. The running configuration reflects the configuration changes.
5. The valid configuration should be accepted, and the candidate configuration should reflect the actual config change.
6. Validate that the hierarchy is displayed correctly, all entries are correct.
7. The transaction gets successfully committed.
8. The running configuration reflects the configuration changes.

---

#### 4. Verify command "protocols ospf instance <value> area <value> interface priority <0-255>" availability and description
**Steps:**

1. Verify the “protocols ospfv3 area interface priority <0-255>” command availability.
2. Verify the description for this command.
3. Verify the help menu using <TAB> and <?> for multiple commands per line.
4. Verify the help menu using <TAB> and <?> for single command per line.
5. Verify auto-completition for the given command.
6. Verify that the keyboard shortcuts are working when entering priority and tag value configuration commands ( e.g Ctrl+C , Ctrl+V , Ctrl+W, Ctrl+A etc. ).

**Pass criteria:**

1. The command should be available as specified in functional spec document.
2. The command description should be intuitive and with no typos.
3. Help menu should display relevant/correct information about the command when using <TAB> and <?> when configuring multiple command per line.
4. Help menu should display relevant/correct information about the command when using <TAB> and <?> when configuring a single command per line.
5. Auto-completition should work for the given command.
6. The keyboard shortcuts should work when entering priority and tag value configuration command ( e.g Ctrl+C , Ctrl+V , Ctrl+W etc. ).

---

#### 5. Verify command "protocols ospf instance <value> area <value> interface priority <0-255>" - only the valid values are accepted and applied
**Steps:**

1. Positive testing: for "protocols ospfv3 area interface priority <0-255>" command involving valid values from the command.
2. Negative testing: for "protocols ospfv3 area interface priority <0-255>" command involving invalid values from the command, words, special characters and empty value.

**Pass criteria:**

1. All valid values should be accepted and successfully applied.
2. All invalid values should be rejected and relevant error messages should be returned.

---

#### 6. Verify command "protocols ospf instance <value> area <value> interface priority <0-255>" - command is successfully applied/removed to/from the running config
**Steps:**

1. Configure a valid value for the new command.
2. Verify that the candidate configuration is displayed properly.
3. Commit the transaction.
4. Verify the running configuration.
5. Remove the previous configuration or reset it to its default value.
6. Verify that the candidate configuration is displayed properly.
7. Commit the transaction.
8. Verify the running configuration.

**Pass criteria:**

1. The valid configuration should be accepted, and the candidate configuration should reflect the actual config change.
2. Validate that the hierarchy is displayed correctly, all entries are correct.
3. The transaction gets successfully committed.
4. The running configuration reflects the configuration changes.
5. The valid configuration should be accepted, and the candidate configuration should reflect the actual config change.
6. Validate that the hierarchy is displayed correctly, all entries are correct.
7. The transaction gets successfully committed.
8. The running configuration reflects the configuration changes.

---

#### 7. Verify that config with ospf network-type broadcast can be copied to/from SCP server
**Steps:**

1. Configure ospfv3 network-type broadcast and commit the transaction.
2. Save the configuration to a SCP server.
3. Delete the setup made at step one.
4.Download the config from SCP server backed-up at step 2, apply the config and commit the changes.

**Pass criteria:**

1. The valid configuration should be accepted and successfully committed.
2. The configuration file should be successfully copied to the SCP server.
3. Configuration is applied successfully.
4. The configuration backed-up at step 2 should be successfully applied.

---

#### 8. Verify that config with ospf network-type broadcast can be copied to/from FTP client
**Steps:**

1. Configure ospfv3 network-type broadcast and commit the transaction.
2. Download the DUT configuration file locally using a FTP client (Windows/Linux machine).
3. Delete the setup made at step one.
4. Change the value of a parameter related to ospfv3 network-type broadcast on the configuration file saved on FTP client (Windows/Linux machine).
5. Upload the modified configuration made at step 4 to DUT using a FTP client machine.
6. Check on DUT that the  ospfv3 network-type broadcast is present with the new value.

**Pass criteria:**

1. The valid configuration should be accepted and successfully committed.
2. The configuration file should be successfully copied to the FTP client.
3. Configuration is applied successfully.
4. Configuration is applied successfully.
5. The configuration backed-up at step 2 and modified at step 4 should be successfully applied.
6. The new value for the parameter inside ospfv3 network-type broadcast configuration should be present in the configuration of the DUT.

---

#### 9. Verify that config with ospf network-type broadcast can be backed up to/from DNOR
**Steps:**

1. Configure ospf network-type broadcast and commit the transaction.
2. Verify that the configuration made at step 1 is properly installed in the running-config.
3. Do a backup of the config on the DNOR.
4. Remove ospf network-type broadcast configuration from running-config.
5. Load the config saved at step 3 on DUT using DNOR.
6. Verify that the ospf network-type broadcast is properly re-installed in the running-config.

**Pass criteria:**

1. The valid configuration should be accepted and successfully committed.
2. Configuration is applied successfully.
3. The configuration file should be successfully copied to DNOR.
4. Configuration is applied successfully.
5. Configuration is applied successfully.
6. Configuration is applied successfully.

---

#### 10. Verify "load override factory-default" + "rollback 1" behaviour in ospf network-type broadcast context
**Steps:**

1. On DUT, configure ospfv3 network-type broadcast and commit the transaction.
2. Delete configuration on DUT using “load override factory-default” command.
3. Verify if “show config compare” is correctly displayed.
4.Rollback the configuration on DUT.

**Pass criteria:**

1. Configuration accepted.
2. Configuration deleted on DUT.
3. "show config compare" is correctly displayed.
4.Rollback is correctly applied on DUT.

---

#### 11. Verify that config with ospf network-type broadcast appears in tech-support file
**Steps:**

1. Configure ospfv3 network-type broadcast and commit the transaction.
2. Verify the running configuration.
3. Dump the entire tech-support and check for ospfv3 network-type broadcast information.

**Pass criteria:**

1. The valid configuration should be accepted and successfully committed.
2. The running configuration reflects the changes that were made.
3.The information about ospfv3 network-type broadcast config should be present in tech-support file.

---

#### 12. Test various types of commit
**Steps:**

1. All the OSPF metrics should be configured accordingly.
2. Add all broadcast related knobs(network type, priority etc), then commit check
3. Add all broadcast related knobs(network type, priority etc), then commit confirm
4. Rollback 1 then repeat step 3 with commit and-exit
5. Rollback 1 then repeat step 3 with commit no-warning
6. Check commit log

**Pass criteria:**

1. Topology is UP and Running, adjacencies are up and running.
2. Commit check should pass correctly
3. Commit should work correctly, after a few mins commit should be rolled back
4. Commit should work correctly
5. Commit should work correctly
6. Commit log should work correctly

---

### Show commands

**JSON label:** Show Commands Tests  
**Mandatory:** True  

**Purpose:** Test the show commands of the feature

#### 1. Verify show config defaults
**Steps:**

1. Validate config defaults without any broadcast related knobs configured
2. Configure all available knobs related to broadcast
3. Change knob values for broadcast
4. Delete knobs

**Pass criteria:**

1. Default knobs only should be present with their default values
2. Knobs with no default value should appear in the config, knobs with default value should display current and default value if current value is different
3. Config defaults should reflect this change
4. Config defaults should reflect this change

---

#### 2. verify show config knobs
**Steps:**

1. Configure all related ospfv3 broadcast knobs
2. check show config | count
3. check show config | exclude
4. check show config | find
5. check show config | include
6. check show config | flatten
7. check show config | monitor
8. check show config | no-more
9. check show config | tail

**Pass criteria:**

1. command should work correctly
2. command should work correctly
3. command should work correctly
4. command should work correctly
5. command should work correctly
6. command should work correctly
7. command should work correctly
8. command should work correctly
9. command should work correctly

---

#### 3. Verify the output of "show ospf interfaces"
**Show commands legend:**

```
# show ospf interfaces
# show ospf interfaces detail
```

---

#### 4. Verify the output of "show ospf neighbors"
**Show commands legend:**

```
# show ospf neighbors interface ge100-0/0/15
 # show ospf neighbors interface bundle-1997.231
 # show ospf neighbors interface bundle-1996
 # show ospf neighbors detail
 # show ospf neighbors address
 # show ospf neighbors interface ge100-0/0/3.1231
```

---

#### 5. Verify the output of "show ospf"
**Show commands legend:**

```
# show ospf | no-more
```

---

#### 6. Verify the output of "show ospf database"
**Show commands legend:**

```
# show ospf instance test database network self-originate
 # show ospf instance test database network link-state-id 10.1.1.7
 # show ospf instance test database network link-state-id 10.1.1.1
 # show ospf instance test database network adv-router 10.10.10.10
 # show ospf instance test database network self-originate
 # show ospf instance test database router self-originate
 # show ospf instance test database
```

---

### Negative (CLI validation)

**JSON label:** Negative Tests  
**Mandatory:** True  

**Purpose:** Test the negative tests of the feature

#### 1. Negative - Verify that an interface associated win an OSPF insance and configured as broadcast may not have mpls on that interface
**Steps:**

1. Have one broadcast interface in an area and try to enable mpls on that interface
2.Have one interface with mpls enabled and  try to configure an interface in the OSPF as broadcast

**Pass criteria:**

1. We are not able to commit; there is a commit validation with a relevant message
2. We are not able to commit; there is a commit validation with a relevant message

---

#### 2. Negative - If Segment Routing is enabled on an OSPF instance then any interfaces that are associated with that OSPF instance may not be configured as broadcast
**Steps:**

1. Have one broadcast interface in an area and try to enable segment routing on the instance level
2. Have one broadcast interface in an area and try to enable segment routing on the area level
3. Have the ospf instance configured with segment-routing admin-state enabled, and try to add/edit an OSPF interface to network-type broadcast
4. Have the ospf area configured with segment-routing admin-state enabled, and try to add/edit an OSPF interface to network-type  broadcast

**Pass criteria:**

1. We are not able to commit; there is a commit validation with a relevant message
2. We are not able to commit; there is a commit validation with a relevant message
3. We are not able to commit; there is a commit validation with a relevant message
4. We are not able to commit; there is a commit validation with a relevant message

---

#### 3. Negative - An interface that has LDP enabled on that interface may not also be associated with an OSPF instance and configured as broadcast
**Steps:**

1. Have one broadcast interface in an area and try to enable LDP on that interface
2.Have one interface with LDP enabled and  try to configure an interface in the OSPF as broadcast

**Pass criteria:**

1. We are not able to commit, there is a commit validation with a relevant message
2.We are not able to commit, there is a commit validation with a relevant message

---

#### 4. Negative - For an interface associated with an OSPF instance and configured as broadcast, BFD may not be applied on that interface
**Steps:**

1. Have one broadcast interface in an area and try to enable BFD on that interface
2. Have one interface with BFD enabled and  try to configure an interface in the OSPF as broadcast

**Pass criteria:**

1. We are not able to commit; there is a commit validation with a relevant message
 2. We are not able to commit; there is a commit validation with a relevant message

**Variants:** * area level
 * interface level

---

#### 5. Negative - For an interface associated with an OSPF instance and configured as broadcast, LFA shall not be applied on such an interface.
**Steps:**

1. Have one broadcast interface in an area and try to enable LFA on that instance.
2.Have the instance with LFA enabled and  try to configure an interface in the OSPF as broadcast

**Pass criteria:**

1. We are not able to commit; there is a commit validation with a relevant message
2.We are not able to commit; there is a commit validation with a relevant message

---

#### 6. Negative - If an OSPF area has been configured as a Stub/NSSA area then any interfaces associated with that OSPF area must not be configured as broadcast - configuration validation shall be applied.
**Steps:**

1. Have one broadcast interface an area and try to change that area to Stub.
2. Have one broadcast interface an area and try to change that area to NSSA
3. Have one area as Stub and try to configure an interface in the area as broadcast
4.Have one area as NSSA and try to configure an interface in the area as broadcast

**Pass criteria:**

1. We are not able to commit, there is an commit validation with a relevant message
2. We are not able to commit, there is an commit validation with a relevant message
3. We are not able to commit, there is an commit validation with a relevant message
4. We are not able to commit, there is an commit validation with a relevant message

---

## HA tests

### Primary (NCC switchover/failover, device restart, process restart)

**JSON label:** HA  
**Mandatory:** True  

#### 1. NCC Switchover
**Steps:**

1. Have the devices connected as in the attached topology
2. Configure OSPF network-type broadcast
3. Advertise some OSPF routes 
4. Trigger a NCC switchover
5. Check that all good after the NCC switchover

**Pass criteria:**

1. The devices are connected as in the topology
2. OSPF network-type broadcast was successfully configured and the , the DR and BDR was elected
3. The ospf routes are present and correct on all devices
4. The ncc switchover was successfully triggered
5. Everything is good after the NCC SO

---

#### 2. NCC Failover
**Steps:**

1. Have the devices connected as in the attached topology
2. Configure OSPF network-type broadcast
3. Advertise some OSPF routes
4. Trigger a NCC failover
5.Check that all good after the NCC failover

**Pass criteria:**

1. The devices are connected as in the topology
2. OSPF network-type broadcast was successfully configured and the , the DR and BDR was elected
3. The ospf routes are present and correct on all devices
4. The ncc failover was successfully triggered
5. Everything is good after the NCC failover

---

#### 3. Device Cold/Warm Restart
**Steps:**

1. Have the devices connected as in the attached topology
2. Configure OSPF network-type broadcast
3. Advertise some OSPF routes
4. Trigger device restart
5. Check that all good after the device restart

**Pass criteria:**

1. The devices are connected as in the topology
2. OSPF network-type broadcast was successfully configured and the , the DR and BDR was elected
3. The ospf routes are present and correct on all devices
4. The device restart was successfully triggered
5. Everything is good after the device restart

**Variants:** cold restart
warm restart
power off + on

---

#### 4. Process Restart
**Steps:**

1. have bellow topology, DN1, DN4 and DN7 are DUTs.
2. configure ospfv2 as depicted in topology.
3. have GR disabled on DN4 and configure all other router as GR helpers
4. push traffic between: IXIA ↔︎ IXIA3 and IXIA2 ↔︎ IXIA3
5. restart ospfv2 process on DN4.

**Pass criteria:**

1. topology configured.
2. ospfv2 adjacencies are up as expected in the topology.
3. GR is disabled on DN4. all other routers act as GR helpers.
4. traffic is running between mentioned IXIA end-points.
5. DN4 reinitialize ospf adjacencies, it does not generate type 9 opaque LSAs(GR LSA) to announce its neighbors about the restart. Traffic loss is seen due to adjacencies restart.

**Show commands legend:**

```
# show ospf database opaque-link | no-more
# show ospf database | no-more
```

---

### Secondary (OSPF/RIB/routing-engine restart, GR variants)

**JSON label:** Secondary_HA  
**Mandatory:** True  

#### 1. OSPF process restart (NSR disabled)
**Steps:**

1. Have the devices connected as in the attached topology
2. Configure OSPF network-type broadcast
3. Advertise some OSPF routes
4. Trigger OSPF process restart
5. Check that all good after the  OSPF process restart

**Pass criteria:**

1. The devices are connected as in the topology
2. OSPF network-type broadcast was successfully configured and the , the DR and BDR was elected
3. The ospf routes are present and correct on all devices
4. The OSPF process restart was successfully triggered
5.Everything is good after the OSPF process restart

---

#### 2. RIB-Manager restart
**Steps:**

1. Have the devices connected as in the attached topology
2. Configure OSPF network-type broadcast
3. Advertise some OSPF routes
4. Trigger RIB Manager process restart
5. Check that all good after the RIB Manager

**Pass criteria:**

1. The devices are connected as in the topology
2. OSPF network-type broadcast was successfully configured and the , the DR and BDR was elected
3. The ospf routes are present and correct on all devices
4. The RIB Manager process restart was successfully triggered
5. Everything is good after the RIB Manager restart

---

#### 3. Routing-engine container restart
**Steps:**

1. Have the devices connected as in the attached topology
2. Configure OSPF network-type broadcast
3. Advertise some OSPF routes
4. Trigger Routing-engine container restart
5. Check that all good after the Routing-engine container

**Pass criteria:**

1. The devices are connected as in the topology
2. OSPF network-type broadcast was successfully configured and the , the DR and BDR was elected
3. The ospf routes are present and correct on all devices
4. The Routing-engine container restart was successfully triggered
5. Everything is good after the Routing-engine container restart

---

#### 4. Restart/switchover with GR disabled
**Steps:**

1. On R1 and R2, configure OSPF broadcast and verify the session is in FULL state.  
2. On R1 and R1, disable Graceful Restart (e.g., protocols ospf graceful-restart restarting-mode admin-state disabled), and disable the NSR
3. From an external injector (e.g., IXIA1), advertise a test prefix (192.0.2.0/24) into R1.  
4. Start also a traffic flow from IXIA1(connected to R1) to IXIA2(connected to R2).
5. On R2, verify receipt and installation of the test prefix in the OSPF route table.  
6. On R1, restart the OSPF process
7. On R2, monitor the OSPF session state and prefix reachability during R1’s restart.  
8. Wait for R1’s OSPF session to re-establish with R2.  
9. On R2, verify that the test prefix is re-advertised and re-installed in the OSPF route table.
10. Check the statistics of the traffic flow

**Pass criteria:**

1. R1–R2 OSPF session is in FULL state before any changes.  
2. R1’s running configuration shows Graceful Restart is disabled and NSR disabled
3. R2’s OSPF route table contains the test prefix (192.0.2.0/24) before R1’s restart.
4. The traffic is up, no packet loss  
5. Upon R1’s OSPF process restart, R2 immediately withdraws the test prefix (no helper state).  
6. R2’s OSPF session to R1 transitions to Down and then back to FULL.  
7. There is no temporary retention of the test prefix in R2’s forwarding table during R1’s restart.  
8. R2 re-establishes the OSPF session with R1.
9. After session recovery, R2 receives and installs the test prefix again exactly as before.
10. There is some traffic loss, which is fine

---

#### 5. Graceful restart with no helpers
**Steps:**

1. have bellow topology, DN1, DN4 and DN7 are DUTs.
 2. configure ospfv2 as depicted in topology.
3. enable DN4 as GR restarter and disable on all other routers in topology GR helper mode.
4. push traffic between: IXIA ↔︎ IXIA3 and IXIA2 ↔︎ IXIA3
5. restart ospfv2 process on DN4 from CLI.

**Pass criteria:**

1. topology configured.
 2. ospfv2 adjacencies are up as expected in the topology.
3. GR restarter is enabled on DN4 as per output of “show ospf” command. GR helper mode is confirmed on neighbors per output in “show ospf” commands or similar commands for other vendors.
4. traffic is running between mentioned IXIA end-points.
5. When ospf process is gracefully restarted, DN4 will originate a grace LSA and forward it to all neighbors. Even if DN4 announces its neighbors that it will restart, neighbor routers will have helper mode disabled, will not keep the adjacency with DN4 up, they will get the adjacency down and then form it again when DN4 will initiate the process. Traffic loss is expected.

**Variants:** DN4 as:
DR
BDR
DROther

---

#### 6. GR with helpers
**Steps:**

1. have bellow topology, DN4 is DUT.
2. configure ospfv2 as depicted in topology.
3. enable DN4 as GR restarter and enable on all other routers in topology GR helper mode.
4. push traffic between: IXIA ↔︎ IXIA3 and IXIA2 ↔︎ IXIA3
5. restart ospfv2 process on DN4:
a. CLI
b. kill process

**Pass criteria:**

1. topology configured.
2. ospfv2 adjacencies are up as expected in the topology.
3. GR restarter is enabled on DN4 as per output of “show ospf” command. GR helper mode is confirmed on neighbors per output in “show ospf” commands or similar commands for other vendors.
4. traffic is running between mentioned IXIA end-points.
5.process restarted successfully and bellow are verified:
6. grace LSA is seen in output of “show ospf database” during restart on DN4. grace LSA is received by neighbors(it is seen in “show ospf database” output).
7. ospfv2 routes are marked as stale(S) during restart on DN4
8. ospfv2 routes are not removed from helpers RIB(uptime is not reset)
9. there is no traffic loss.
10. “show ospf” outputs shows ongoing restart on GR restarter.
11. “show ospf” output on helpers shows entering helper mode(DN).
12GR ends successfully on restarter, system-event shows successful GR event.

**Show commands legend:**

```
show ospf
```

---

#### 7. Graceful LSA flooding
**Steps:**

1. On R1, enable OSPF graceful-restart (graceful-restart) in instance 1; on R2 enable only helper support (graceful-restart helper-only).
2. Clear or start OSPF instance 1 on both R1 and R2 and verify FULL adjacency via show ospf instance 1 neighbors.
3. On R1, inject Loopback0 (10.1.1.1/32) into OSPF instance 1; verify R2’s LSDB contains the corresponding Router-LSA (Type 1) via show ospf instance 1 database.
4. On R1, issue a graceful restart (clear ospf instance 1 graceful).
5. Immediately on R2, run show ospf instance 1 database and confirm R1’s Loopback0 LSA remains present (no withdrawal).
6. After R1 comes back up (adjacency returns to FULL), inject Loopback1 (10.1.1.2/32) on R1 and verify R2’s LSDB now contains both Loopback0 and Loopback1 LSAs.
7. On R1, withdraw Loopback0 and clear OSPF instance 1 gracefully again.
8. On R2, verify that after the second graceful restart it floods only the withdrawal for Loopback0 (Router-LSA age is advertised as MaxAge) and retains Loopback1’s LSA intact.

**Pass criteria:**

1. show ospf instance 1 neighbors on R1/R2 shows FULL adjacency with GR capability negotiated.
2. R2’s show ospf instance 1 database lists R1’s Loopback0 LSA after step 3.
3. Immediately after R1’s graceful restart, R2’s LSDB still contains the LSA for Loopback0 (no removal).
4. After R1 recovery and Loopback1 injection, R2’s LSDB contains LSAs for both Loopback0 and Loopback1.
5. Upon withdrawing Loopback0 and second graceful restart, R2’s LSDB shows Loopback0 LSA with Age=MaxAge (withdrawal flood).
6. R2’s LSDB continues to contain Loopback1 LSA with normal Age (<MaxAge).
7. No unintended LSAs (e.g., spurious floods or drops) occur during either graceful restart.
8. Throughout, show ospf instance 1 database on R2 reflects exactly the expected LSA additions/withdrawals in each phase.

---

#### 8. GR restarter was DR before restart it elects itself as DR again
**Steps:**

1. have bellow topology, DN1, DN4 and DN7 are DUTs.
2. configure ospfv2 as depicted in topology.
3. make DN4 as DR for two network segments.
4. enable DN4 as GR restarter and enable on all other routers in topology GR helper mode.
5. push traffic between: IXIA ↔︎ IXIA3 and IXIA2 ↔︎ IXIA3
6. restart ospfv2 process on DN4 and DN7(one at a time) from CLI.

**Pass criteria:**

1. topology configured.
2. ospfv2 adjacencies are up as expected in the topology.
3. DN4 is confirmed as DR from operational commands on DN4 and on neighbors.
4. GR restarter is enabled on DN4 as per output of “show ospf” command. GR helper mode is confirmed on neighbors per output in “show ospf” commands or similar commands for other vendors.
5. traffic is running between mentioned IXIA end-points.
6. verify that during GR process DN4 re-elects itself as DR on the two network segments.

---

## Functionality tests

**JSON label:** Functionality  
**Mandatory:** True  

#### 1. Verify Network type mismatch
**Steps:**

1. Set up the network as shown in Figure 1. Shutdown all links
2. On R1, configure OSPF network type point-to-point for the link connected to IXIA. Configure OSPF area 0 between R1 and IXIA1
3. On IXIA1 interface towards R1, configure network type point-to-point
4. On IXIA1 interface towards R1, configure network type broadcast
5. On R1, clear OSPF process
6. On R1, disable/enable OSPF interface towards IXIA1
7. On R1, disable/enable interface towards IXIA1
8. On R1, restart OSPFD process
9. On IXIA1 interface towards R1, configure network type point-to-point
10. On R1, configure OSPF network type broadcast for the link connected to IXIA
11. On IXIA1 interface towards R1, configure network type broadcast
12. On IXIA1 interface towards R1, configure network type point-to-point
13. On R1, clear OSPF process
14. On R1, disable/enable OSPF interface towards IXIA1
15. On R1, disable/enable interface towards IXIA1
16. On R1, restart OSPFD process
17. On IXIA1 interface towards R1, configure network type broadcast

**Pass criteria:**

1. Configuration is successfully applied and can be seen in the show output
2. R1 successfully configured as network type p2p
3. R1 establishes adjacencies in different areas with the network type set to point-to-point
4. R1 does not establish adjacencies in different areas with network type set to point-to-point (network-type mismatch)
5. OSPF successfully cleared
6. R1 does not establish adjacencies in different areas with network type set to point-to-point (network-type mismatch)
7. R1 does not establish adjacencies in different areas with network type set to point-to-point (network-type mismatch)
8. OSPF process successfully restarted
9. R1 establishes adjacencies in different areas with the network type set to point-to-point
10. R1 does not establish adjacencies in different areas with network type set to point-to-point (network-type mismatch)
11. R1 establishes adjacencies in different areas with the network type set to broadcast
12. R1 does not establish adjacencies in different areas with network type set to point-to-point (network-type mismatch)
13. OSPF successfully cleared
14. R1 does not establish adjacencies in different areas with network type set to broadcast (network-type mismatch)
15. R1 does not establish adjacencies in different areas with network type set to broadcast (network-type mismatch)
16. OSPF process successfully restarted
17. R1 establishes adjacencies in different areas with the network type set to broadcast

---

#### 2. Verify DR/BDR election process
**Steps:**

1. Set up the network as shown in Figure 1. Shutdown all the links connecting R1, R2, R3, and R4. Connect R1, R2, R3 and R4 to the same broadcast domain using the L2 device.
2. On all routers, configure OSPF network type broadcast for all the links connected to the L2 device. On all routers configure IP addresses from the same subnet (e.g. 172.120.0.0/24)
3. Configure the router-id for the routers in the following way: R1 = 111.111.111.111; R2 = 22.22.22.22; R3 = 33.33.33.33; R4 = 44.44.44.44. Assign all the interfaces to OSPF Area 0. Check the default priority.
4. Disable OSPF on every router. Configure the OSPF priority for the interfaces in the following way: R1’s interface priority = 51; R2’s interface priority = 101; R3’s interface priority = 50; R4’s interface priority = 99.
5. Enable OSPF on every router
6. Disable OSPF on R2 and enable it back after more than 40 sec
7. Disable OSPF on R1 and enable it back after more than 40 sec
8. Change the interface priority to “0” on R4
9. Disable OSPF on R2 and enable it back after more than 40 sec.
10. Toggle the interface between routers and verify that the ospf adjacency gets established

**Pass criteria:**

1. Configuration is successfully applied
2. Configuration is successfully applied
3. Based on router-id: R1 should be DR, R4 should be BDR and R2 <-> R3 adjacency should be in the 2WAY state. The default priority must be set to 1.
4. Based on priority: R2 should be DR, R4 should be BDR and R1 <-> R3 adjacency should be in the 2WAY state
5. OSPF enabled on all routers
6. Based on Priority: R4 should be DR, R1 should be BDR and R2 <-> R3 adjacency should be in the 2WAY state
7. Based on Priority: R4 should be DR, R2 should be BDR and R1 <-> R3 adjacency should be in the 2WAY state
8. Based on Priority: R2 should be DR, R1 should be BDR and R4 <-> R3 adjacency should be in the 2WAY state. When the interface priority is set to 0, the interface does not participate in the DR/BDR election.
10. Based on Priority: R1 should be DR, R3 should be BDR and R4 <-> R2 adjacency should be in the 2WAY state
11. The ospf adjacencies are established and the DR/BDR elections

---

#### 3. OSPF database creation
**Steps:**

1. Configure R1 and R2 on a common Ethernet segment in OSPFv2 area 0, assign unique router-IDs and default interface priorities.
2. Enable OSPF on each interface connecting R1↔R2 and start the OSPF process on both routers.
3. Verify that each router’s OSPF interfaces transition to “DR”/“BDR”/“DROTHER” as appropriate and reach FULL neighbor state.
4. On R1, issue show ip ospf database and record the count and types of LSAs (Router-LSA, Network-LSA).
5. On R2, issue show ip ospf database and record the count and types of LSAs.
6. Compare R1’s and R2’s LSDB entries to ensure they match exactly.
7. Inject a Loopback0 on R1 (e.g., 10.1.1.1/32) into OSPF and clear the OSPF process on R1.
8. Verify that R1 re-originates a new Router-LSA for the loopback and floods it to R2.
9. On R2, issue show ip ospf database router 10.1.1.1 to confirm the new LSA appears in its LSDB.

**Pass criteria:**

1. OSPF processes on R1 and R2 start without errors and interfaces come up in area 0.
2. R1 and R2 reach FULL adjacency on their OSPF interfaces.
3. Initial LSDB on each router contains one Router-LSA (itself) and one Network-LSA for the segment.
4. R1’s and R2’s LSDBs are identical in LSA count and type.
5. After injecting Loopback0 on R1 and clearing OSPF, R1’s LSDB shows a new Router-LSA with advertising router R1.
6. R2’s LSDB receives and installs the new Router-LSA for 10.1.1.1/32.
7. No LSAs are missing or duplicated; both LSDBs remain synchronized throughout.

---

#### 4. Manipulations with interfaces
**Steps:**

1. Set up the network as shown in Figure 1 
2. Change the OSPF interface type to broadcast and start OSPF globally. Verify that all the OSPF adjacencies between routers are reaching the FULL state
3. Enable OSPF on loopback interfaces and verify the LSDB, routing tables on every router. Initiate pings with the source set as loopback
4. Shut down the interface R3-R1
5. Shut down the interface R3-R2
7. Shut down the interface R1-R2 
8. Open all the interfaces
9. Shut down, one by one, the Ix interfaces

**Pass criteria:**

1. Configurations applied
2. The OSPF adjacencies over point-to-point interfaces should be established (DR/BDR are elected)
3. The loopback subnets are learned in LSDB, routing tables, ping is successful
5. The LSDB and routing table is changed accordingly
6. The LSDB and routing table is changed accordingly
7. The LSDB and routing table is changed accordingly
8. The LSDB and routing table is changed accordingly
9. The LSDB and routing table is changed accordingly

---

#### 5. Throttle SPF
**Steps:**

1. Set up the network as shown in Figure 1  as follows: links between R1 and R2 in area 0 (backbone), links R1-R3  in area 1,
2. Check the default values for SPF delay / hold / max-wait
3. Configure the throttle spf timers on R1
4. Cause within 20000 ms (min-holdtime) a link flapping or something causing a lot of LSAs being sent and requiring SPF to run (this can affect the performance of CPU)
5. Cause another link flapping within the new hold-time of 4000 ms
6. SPF max-holdtime makes sure there is a roof so that the timer is not set to high

**Pass criteria:**

1. Configurations applied
2. The default values for SPF delay is 50 msecs, for SPF hold is 200 msecs, for max-wait is 5000 msecs
3. When the first LSA arrives, the timer will run SPF after 2000 ms (the delay timer)
4. The timer from 2. will be doubled. Therefore, SPF will run after 4000 ms
6. The timer from 3. will be doubled. Therefore, SPF will run after 8000 ms
7. If there are no events for 2 times the max-holdtime the timer will revert back to delay (2000)

---

#### 6. Throttle LSA
**Steps:**

1. Set up the network as shown in Figure 1 (100/400GB connections) as follow: links between R1 and R2 in area 0 (backbone), links R1-R3 area 1
2. Check the default values for LSA throttle delay / hold for LSA throttle / max-wait for LSA throttle
3. Configure the throttle lsa timers on R1 (timers throttle lsa all 5000)

**Pass criteria:**

1. Configurations applied
2. The default values for LSA throttle delay is 50 msecs, for LSA throttle min hold is 200 msecs, for LSA throttle max-wait is 5000 msecs (2)
3. This timer defines how long to wait before sending LSAs. By default, the first LSA is sent immediately and the timer is set to 5000 (3)

---

#### 7. Verify LSA-arrival
**Steps:**

1. Set up the network as shown in Figure 1 as follow: links between R1 and R2 in area 0 (backbone), links R1-R3 and R2-R3 in area 3, links R1-R4 and R2-R4 in area 4. At this point, the link between R3-R4 remains unconfigured. Ix1 is in area0, Ix2 in area0, Ix3 in area3 and Ix4 in area4
2. Configure the lsa-arrival timer on R1

**Pass criteria:**

1. Configurations applied
2. This timer defines how long to wait before accepting the same LSA. If it is received faster than 1000 ms the LSA will be dropped. (This timer should be set to less than or equal to the hold-time interval of the timers throttle lsa all command)

---

#### 8. Verify OSPF Refresh timer
**Steps:**

1.Set up the network as shown in Figure 1 (100/400GB connections) as follow: links between R1 and R2 in area 0 (backbone), links R1-R3 and R2-R3 in area 3, links R1-R4 and R2-R4 in area 4. At this point the link between R3-R4 remains unconfigured.  Ix1 is in area0, Ix2 in area0, Ix3 in area3 and Ix4 in area4
2. Configure the OSPF refresh timer (the default is 30 minutes)
3. Configure different values for the refresh timer (even the most aggressive limit of 10 seconds)

**Pass criteria:**

Configurations applied
2. Every 15 minutes all the routers are exchanging all the LSAs
3. Every 10 seconds the complete LSDB is exchanged

---

#### 9. Manually set router-id for OSPF process
**Steps:**

1. Set up the network as shown in Figure 1. Enable only the links connected to the L2 SW
2. Configure the areas as in the fingure 1. Set the router-id manually on all routers
3. Change the router-id on R1 to be the same as R2’s router ID and clear OSPF process
4. Remove the router-id manual configuration, clear ospf process, and verify the ospf adjacencies
5. Verify that the OSPF database is being updated with the new router ID

**Pass criteria:**

1. Devices connected as in the attached topology
2. R1 establishes OSPF adjacencies with all connected OSPF routers
3. R1 will not establish and adjacency with R2 due to Router ID conflict, but it will establish adjacencies with R3 and R4
4. The OSPF session established between R1 and R2
5. OSPF Database successfully updated

---

#### 10. Automatically elected router-id
**Steps:**

1. Set up the network as shown in Figure 1. 
2. Do not set manually the router-id on any router
3. Change the router-id on R1 to be the same as R2’s dynamically elected router ID and clear OSPF process
4. On R1, configure manually a unique router-id and clear the ospf process
5. On R1 configure a loopback address and clear the ospf process and remove the static router-id configuration
6. On R1, delete all loopback interfaces and clear the OSPF process

**Pass criteria:**

1. Devices are configured and connected as in the attached topology
2. OSPF is configured, router ID is automatically set. 
3. R1 will not establish an adjacency with R2 due to Router ID conflict, but it will establish adjacencies with R3 and R4 
4. R1 will establish an adjacency with R2
5. The loopback IP address will be elected as router-id and the OSPF adjacencies will be established. If there are more loopback addresses, the highest IP address of any of the router’s loopback interfaces is selected as router-id.
6. The elected router-id will be the highest IP address on active interfaces

---

#### 11. Flap DR/BDR links
**Steps:**

1. Configure R1, R2 and R3 on the same OSPFv2 broadcast segment in area 0; verify they form FULL adjacencies and R1 is DR, R2 is BDR, R3 is DROTHER.
2. On R1 (the DR), shut down its OSPF‐enabled interface to the segment.
3. Wait for at least one Hello/Dead interval.
4. Bring R1’s interface back up.
5. Wait for another Hello/Dead interval.
6. On R2 (now acting as DR), shut down its OSPF‐enabled interface to the segment.
7. Wait one Hello/Dead interval, then bring R2’s interface back up.
8. Wait a final Hello/Dead interval.

**Pass criteria:**

1. R1, R2 and R3 form FULL adjacency; R1 is DR, R2 is BDR, R3 is DROTHER.
2. R1’s interface shutdown causes R2 to be elected DR and R3 to be elected BDR.
3. Within one Hello/Dead interval, R2→DR and R3→BDR roles are visible in each router’s neighbor table.
4. After R1’s interface comes back up, R1 is not re-elected DR (no preemption) and R2(DR) and R3 keeps(BDR) the new roles.
5. R1 is not re-elected DR (no preemption) and R2(DR) and R3 keeps(BDR) the new roles. The DR and BDR is not re-triggered by the fact that R1 is up/
6. Shutting R2’s interface causes R3 to be elected DR and R1 to become BDR (R1 still up).
7. Within one Hello/Dead interval, R3→DR and R1→BDR roles are visible.
8. After R2’s interface recovery, there is no preemption, no change in the DR and BDR

---

#### 12. Verify passive mode on the interface
**Steps:**

1. On R1 and R2, configure OSPFv2 on GigabitEthernet0/0 in area 0 with default priorities and ensure the interface is up.
2. Verify that R1 and R2 form a FULL adjacency on GigabitEthernet0/0.
3. On R2, under the OSPF process, configure passive-interface GigabitEthernet0/0.
4. Clear the OSPF process on R2 (clear ip ospf process).
5. On R2, monitor the interface and verify that no OSPF Hello packets are transmitted on GigabitEthernet0/0.
6. On R1, monitor the neighbor state for R2 on GigabitEthernet0/0 and confirm the adjacency moves to Down.
7. On R2, remove the passive-interface GigabitEthernet0/0 configuration.
8. Clear the OSPF process on R2 again and verify that R1 and R2 re-form a FULL adjacency on GigabitEthernet0/0.

**Pass criteria:**

1. OSPFv2 is configured on GigabitEthernet0/0 for R1 and R2 in area 0 without errors.
2. R1 and R2 reach FULL neighbor state on GigabitEthernet0/0.
3. The passive-interface GigabitEthernet0/0 command is accepted under the OSPF process on R2.
4. Clearing OSPF on R2 completes without errors.
5. R2 sends no OSPF Hello packets on GigabitEthernet0/0 after passive mode is enabled.
6. R1’s neighbor table shows the R2 adjacency on GigabitEthernet0/0 as Down.
7. Removing passive-interface GigabitEthernet0/0 on R2 is accepted without errors.
8. After clearing OSPF on R2, R1 and R2 re-establish FULL adjacency on GigabitEthernet0/0.

---

#### 13. Cost
**Steps:**

1. Configure OSPFv2 on R1, R2 and R3 in area 0 over a common broadcast segment; leave all interface costs at the default (10).
2. Verify that R1–R2 and R2–R3 adjacencies reach FULL state and that each router’s interface cost shows as 10.
3. On R1, inspect its Router-LSA in the LSDB and confirm the Link-State ID for the segment carries cost=10.
4. Change the OSPF cost on R1’s interface to the segment to 20.
5. Clear the OSPF process on R1 to force LSA refresh.
6. On R2 and R3, verify in the LSDB that R1’s Router-LSA for that link now shows cost=20.
7. On R2, change its interface cost to 1 and clear OSPF there.
8. On R1 and R3, verify R2’s Router-LSA now shows cost=1 for the shared link.
9. From R3, trace the route to a network only reachable via R1 and R2 (e.g., a loopback on R1); verify the chosen path reflects lowest total cost.
10. Reset R1 and R2 interface costs to default and clear OSPF on both to restore original state.

**Pass criteria:**

1. R1–R2 and R2–R3 adjacencies form to FULL with default cost=10 on each link.
2. show ip ospf interface on each router reports cost=10 for the broadcast segment.
3. show ip ospf database router on R1 shows its LSA cost=10 for the segment.
4. After setting R1’s cost=20, show ip ospf interface on R1 reflects cost=20.
5. R2 and R3’s LSDBs show R1’s LSA with cost=20 after R1 clears OSPF.
6. After setting R2’s cost=1, show ip ospf interface on R2 reflects cost=1.
7. R1 and R3’s LSDBs show R2’s LSA with cost=1 after R2 clears OSPF.
8. A traceroute from R3 to R1’s loopback chooses the path via R2 (lower total cost).
9. No adjacency flaps occur during cost changes and LSDB updates.
10. Restoring defaults returns all costs to 10 and adjacencies remain stable.

---

#### 14. auto-cost reference bandwidth
**Steps:**

1. Set up the network as shown in Figure 1 (100/400GB connections) as follow: links between R1 and R2 in area 0 (backbone), links R1-R3 and R2-R3 in area 3, links R1-R4 and R2-R4 in area 4. At this point the link between R3-R4 remains unconfigured. Ix1 is in area0, Ix2 in area0, Ix3 in area3 and Ix4 in area4
2. Change the OSPF interface type to broadcast and start OSPF globally. Verify that all the OSPF adjacencies between routers are reaching the correct state
3. Enable OSPF on loopback interfaces and verify the LSDB, routing tables on every router. Initiate pings with the source set as loopback
4. Verify the cost on every interface and in the OSPF routing table
5. Modify the default auto-cost reference-bandwidth to 4000000
6. Verify on the R4 (with default cost configured) the cost for Ix1 subnet learned as external OSPF route (area0 – area4) in the LSDB table
7. Configure a lower cost on the Ix1-R1-R2-R4 path that the Ix1-R1-R4 one
8. Change the cost for the loopback interfaces
9. Re-configure the setup with some bundles where min 2 links exist
10. Change the cost for a bundle and read all the LSDB/routing tables on every router
11. Check the traffic impact when the cost changes.

**Pass criteria:**

1. Configurations applied (1,2)
2. The OSPF adjacencies over point-to-point interfaces should be established without waiting for the Wait timer to expire (no DR/BDR are elected) (1,2)
3. The loopback subnets are learned in LSDB, routing tables, ping is successful (3,4)
4. The OSPF cost is calculated by default as 10^8 / bandwidth (bps) for the default auto-cost reference-bandwidth (7)
5. The cost for every 100GB interface is now 40 (7,2)
6. The R1 route has Ix1-R1 + R1-R4 cost, the R2 route has Ix1-R1 + R1-R2 + R2-R4 cost. In the routing table, first route is installed due to the smaller cost (4,6)
7. The second route is installed in the routing table, having the lower total cost (4,6)
8. Verify that the cost is changed in the LSDB/routing tables (4,6)
9. The OSPF cost for the bundle is different that for a single link (7)
10. LSDB and routing table on every router is as expected (4,6)
11. Dropped Frame Count(Tx-Rx) must be 0 or momentarily interrupted. The preferred route is selected based on cost changes.

---

#### 15. Negative: Cost-mirroring
**Steps:**

1. Set up the network as shown in Figure 1
2. Change the OSPF interface type to broadcast and start OSPF globally. Verify that all the OSPF adjacencies between routers are reaching the FULL state
3. Enable OSPF on loopback interfaces and verify the LSDB, routing tables on every router. Initiate pings with the source set as loopback
4. Enable cost-mirroring feature on R3 for R3-R1 interface (Between R3 and R1 there is one Arista device configured in layer2)
5. Configure a new OSPF cost on R1 on R1-R3 interface
7. Reload the router
8. Configure on R3 a local OSPF cost for R3-R1 (with cost-mirroring enabled on this interface) and disable the cost-mirroring. Enable cost-mirroring and bring down the adjacency. Enable cost-mirroring and shut down the interface.
10. Repeat steps 1-6, but with a bundle configured between R3 and R1
11. Repeat steps 1-6, but with a sub-interface configured between R3 and R1
12. Repeat steps 1-6, but with a bundle sub-interface configured between R3 and R1

**Pass criteria:**

1. Configurations applied
2. The OSPF adjacencies over point-to-point interfaces should be established without waiting for the Wait timer to expire (no DR/BDR are elected)
3. The loopback subnets are learned in the LSDB, the routing tables, and ping is successful
4. We are allowed to enable cost-mirroring on R3 on the interface connected to R1, but it will be ignored since the cost-mirroring was designed for network-type point-to-point
5. The cost was updated. After the LSA is received, R3 will keep the old cost for the R3-R1 interface, because the cost-mirroring feature is not working on the broadcast
6. After the reload and a new LSA received from the R1, the cost remains unchanged as expected
7. The local OSPF cost  configuration will take place in the following cases: OSPF Cost Mirroring is disabled, OSPF adjacency is not yet up
8. The same as 1-6
9. The same as 1-6
10. The same as 1-6

---

#### 16. Change the OSPFv2 timers on the fly
**Steps:**

1. Ensure R1 and R2 form a FULL OSPFv2 adjacency over a broadcast segment with default timers (hello=10 s, dead=40 s).
2. On R1, change the interface hello-interval to 5 seconds (ip ospf hello-interval 5) without clearing OSPF.
3. On R2 change the interface hello-interval to 5 seconds
4. Monitor R1 and R2 for at least two consecutive Hello PDUs to confirm the new 5 s interval.
5. On R1, change the interface dead-interval to 20 seconds (ip ospf dead-interval 20) on the fly.
6. Change the dead-interval also on R2 and verify the neighbor table now uses the 20 s dead timer to detect adjacency loss.
7. On R1, set the LSA refresh timer to ~1800s(this is the minimum configurable value) globally (timers lsa refresh 30) without restarting OSPF.
8. Observe that R1 re-originates its Router-LSA at ~1800s(this is the minimum configurable value) intervals and R2 receives each refreshed LSA (this was already coverd in other TC)

**Pass criteria:**

1. R1↔R2 adjacency is FULL with default hello=10 s/dead=40 s before changes.
2. R1 accepts the hello-interval change without resetting OSPF, but the adjacency with R2 will go down due to the Timers mismatch;
3. R1↔R2 adjacency is reaching FULL state using the new hello interval
4. R1 and R2 send/receive Hello PDUs every 5 s after the change.
5. R1 accepts the dead-interval change without dropping the adjacency, but the adjacecny with R2 goes down due to the timers missmatch;
6. R2 uses the 20 s dead-interval to declare adjacency down if hellos stop.
7. R1 re-originates its Router-LSA every  ~1800s and R2’s LSDB shows the refreshed LSAs.
8. R2 receives each refreshed LSA at the new  ~1800s interval.

---

#### 17. test timers mismatch
**Steps:**

1. Configure R1 and R2 on a common OSPFv2 broadcast segment in area 0 with identical interface timers (hello=10 s, dead=40 s) and verify they form FULL adjacency.
2. On R2, change the OSPF hello-interval on the shared interface to 5 s without adjusting R1.
3. Wait for at least two Hello intervals (≈20 s) and observe neighbor state on both routers.
4. On R2, revert the hello-interval back to 10 s to match R1.
5. On R2, change the OSPF dead-interval on the shared interface to 30 s without adjusting R1.
6. Wait for at least one dead-interval (≈30 s) and observe neighbor state.
7. On R2, revert the dead-interval back to 40 s to match R1.
8.Clear the OSPF process on both routers to force immediate adjacency re-establishment.

**Pass criteria:**

1. After step 1, R1 and R2 reach FULL adjacency and exchange LSDBs successfully.
2. After step 2, R2 begins sending Hellos every 5 s but R1 continues at 10 s.
3. After step 3, the adjacency on R1 moves to Down (or ExStart) due to hello-interval mismatch.
4. After step 4, hello-intervals match again and adjacency returns to FULL.
5. After step 5, R2 advertises a 30 s dead-interval while R1 expects 40 s.
6. After step 6, R1 drops the adjacency (Down) when it doesn’t receive Hellos within its 40 s dead timer.
7. After step 7, dead-intervals match again and the adjacency can be re-established.
8. After step 8, both routers clear OSPF, immediately form FULL adjacency, and resume normal LSDB synchronization.

---

#### 18. different cost per IF and Sub-If
**Steps:**

1. On R1, configure the physical interface (e.g., ge100-0/0/12) in OSPF area 0 with ospf cost 10.  
2. On R1, configure the sub-interface (e.g., ge100-0/0/12.123) in OSPF area 0 with ospf cost 100.  
3. On R2, configure the matching physical interface Gig0/1 in area 0 with cost 10 and sub-interface ge100-0/0/12.123 with cost 100.  
4. On R1, inject two loopbacks—Loopback0 and Loopback1 —into OSPF so that Loopback0 is advertised via the physical link and Loopback1 via the sub-interface.  
5. Verify that R1 and R2 form FULL OSPF adjacency over both the physical interface and the sub-interface.  
6. On R1 and R2, run show ip ospf interface to confirm the costs on ge100-0/0/12 and ge100-0/0/12.123.  
7. On R2, run show ip ospf database router R1 and verify R1’s Router-LSA shows two link entries with costs 10 and 100.  
8. From R2, traceroute to R1’s Loopback0 and Loopback1 and confirm each uses the correct link based on cost.

**Pass criteria:**

1. R1’s show ip ospf interface reports cost 10 on ge100-0/0/12 and cost 100 on ge100-0/0/12.123.  
2. R2’s show ip ospf interface reports cost 10 on ge100-0/0/12 and cost 100 on ge100-0/0/12.123  
3. R1 and R2 reach FULL adjacency on both the physical interface and the sub-interface.  
4. R1’s LSDB contains Router-LSAs for both Loopback0 and Loopback1.  
5. R2’s LSDB shows R1’s Router-LSA with two link entries: one with cost 10 and one with cost 100.  
6. R2’s routing table has routes to Loopback0 via the physical link and to Loopback1 via the sub-interface.  
7. A traceroute from R2 to Loopback0 follows the path over the physical link (cost 10).  
8. A traceroute from R2 to Loopback1 follows the path over the sub-interface (cost 100).

---

#### 19. Max age and SPF throttle
**Steps:**

1. Set up a network with 2 Routers and 2 Ixias
2. Establish OSPF neighbors between routers and Ixias
3. On one router configure a static route and redistribute it in OSPF
4. Configure the throttle spf timers as 20000 20000 20000
5. Monitor the LSA’s age
6.Stop redistributing the static route

**Pass criteria:**

1. Configurations applied 
2. Neighbors established 
3. Verify the OSPF database external LSAs 
4. Settings applied 
5. The LSA is flushed after the Max-age sent in the LSA (in the CTC TP it is 3600) 
6. SPF calculation starts after approx. 20 seconds

---

#### 20. Clear ospf routes
**Steps:**

1. Set up the network as shown in Figure 1. Shutdown the link R3 <-> R4. Connect an Ixia port to R3 (Ixia3) and and Ixia port to R4 (Ixia4)
2. Configure OSPF Area 0.0.0.0 between R1 and R2; Area 0.0.0.1 between R1 and R3, between R2 and R3, between R3 and Ixia3; Area 0.0.0.2 between R2 and R3, between R1 and R4, between R4 and Ixia4
3. On R3, configure several static routes via Ixia3 and redistribute them into OSPF
4. From Ixia3 and Ixia4 advertise several routes and start sending bi-directional traffic between the advertised routes
5. Check ospf database information (pay attention at the LSAs ages).
6. Clear the ospf database
7. Check ospf database information
8. After the topology re-converges, verify that traffic starts being forwarded between Ixia3 and Ixia4

**Pass criteria:**

1. Configurations successfully applied
2. Configurations successfully applied
3.Configurations successfully applied
4.All OSPF routes are properly installed and the traffic is successfully forwarded between IXIA ports with no loss
5. Database information is correct and complete.
6. All link-state information gets deleted (the same happened when the LSA Ages reach the MaxAge of 3600 seconds). Newly flooded LSAs will repopulate the database, and the local router recalculates the SPF algorithm
7. After clearing the database the age starts over from 0 and keeps being incremented.
8. All OSPF routes are properly installed and the traffic is successfully forwarded between IXIA ports with no loss

---

#### 21. Verify OSPF network-type broadcast on IRB interface
---

#### 22. Summarization at ABRs
**Steps:**

1. Set up the network as shown in Figure 1 (100/400GB connections) as follow: links between R1 and R2 in area 0 (backbone), links R1-R3 and R2-R3 in area 3, links R1-R4 and R2-R4 in area 4. At this point the link between R3-R4 remains unconfigured. Ix1 is in area0, Ix2 in area0, Ix3 in area3 and Ix4 in area4
2. On R3 configure the Ix3 link in 10.11.1.0/24 subnet, R3-R1 in 10.11.2.0/24 subnet and another loopback (with OSPF enabled) address configured as 10.11.3.0/24. All the interfaces in the setup should be p2p
3. On R3 in area 3 configure a summary route for 10.11.x.0/24 subnets: area 3 range 10.11.0.0 255.255.252.0
4. Create filters on R3 to block the advertisement of these 3 subnets
5. Allow one of the 3 subnets to be advertised
6. Configure the cost for the summary route: area 3 range 10.11.0.0 255.255.252.0 cost 123
7. Create the summary route, but with the not-advertise option: area 3 range 10.11.0.0 255.255.252.0 not-advertise
8. Repeat steps 3-7, but with sub-interfaces on the link R3-R1
9. Repeat steps 3-7, but with a bundle on the link R3-R1
10. Repeat steps 3-7, but with bundle sub-interfaces on the link R3-R1

**Pass criteria:**

1. Configurations applied
2. All the subnets are learned on R1, having different costs and the same next-hop as R3. On R4 all the subnets are in the routing table; 3 Type 3 LSAs are in the LSDB table advertised by the ABR R1.
3. On R1 in area 0, and 4, instead of 3 subordinate subnets, only one summary subnet is advertised as Type 3 LSA having the cost of the best (lowest) subordinate route
4. If no subordinate route exists, the summary subnet is not anymore advertised in the Type 3 LSA
5. The summary subnet is advertised by R1 and the route is installed in the R4 routing table, with the cost of that subordinate route
6. R1 advertises the summary subnet with cost 123, R4 have this route with the cost of 123+R1-R4
7. The summary subnet is not advertised by R1, it is not present in the R4’s routing table
8. Same results as 3-7
9. Same results as 3-7
10. Same results as 3-7

---

## System resources tests

### Stress

**JSON label:** System Resources Tests  
**Mandatory:** True  

#### 1. Stress Test
**Steps:**

1. Have OSPF broadcast up and running on the dut.
2. Have some prefixes in OSPF route table
3. During the night, keep restarting the OSPF process
4. In the morning check that the config is the same, there are no core files, the route table is the same.

**Pass criteria:**

1. The OSPF is up and running
2. OSPF route table successfully populated
3. The OSPF restarted all night
4. All good

---

### Scale / CPU and memory

**JSON label:** System Resources Tests  
**Mandatory:** True  

#### 1. Verify CPU and memory usage in ospfv2 network-type broadcast context
**Description:**

Scale figures:
 * 32 instances (1 instance has 4 areas)
 * in one instance there are 4 broadcast domains with 126 routers in the broadcast domain
 * ~20k ospf routes in the ospf domain

**Steps:**

1. Configure and connect devices as in the attached topology.
2. Configure ospfv2 between devices.
3.Verify CPU and memory usage on DN devices in ospfv2 network-type broadcast context.

**Pass criteria:**

1. Devices configured and connected as in the attached topology.
2. Configuration is applied successfully.
3. Values for CPU and memory usage should be normal.

**Show commands legend:**

```
# show system details | include ospfd
```

---

## Logs and traces tests

### Traces rotation

**JSON label:** Logs and Traces Tests  
**Mandatory:** True  

#### 1. Traces rotation (scale)
**Steps:**

1. Configure and connect devices as in the attached topology. Have 32k routes(intra-area, inter-area, external). Have 500 broadcast adjacencies with 4 routers participating in each, 2000 routers in topo. Configure OSPFv2 between devices. Configure priorities on interfaces/RID so that DN will be DR.
2. Verify that everything works correctly with the setup made.
3. Clear ospf process and check traces rotation

**Pass criteria:**

1. Devices configured and connected as in the attached topology.
2. Setup works properly.
3. Traces should not rotate too fast, there should be at least a day worth of traces.

---

### Logs rotation

**JSON label:** Logs and Traces Tests  
**Mandatory:** True  

#### 1. Logs rotation (scale)
**Steps:**

1. Configure and connect devices as in the attached topology. Have 32k routes(intra-area, inter-area, external). Have 500 broadcast adjacencies with 4 routers participating in each, 2000 routers in topo. Configure OSPFv2 between devices. Configure priorities on interfaces/RID so that DN will be DR.
2. Verify that everything works correctly with the setup made.
3. Clear ospf process and check logs rotation

**Pass criteria:**

1. Devices configured and connected as in the attached topology.
2. Setup works properly.
3. Logs should not rotate too fast, there should be at least a day worth of logs.

---

## System events tests

**JSON label:** System Events Tests  
**Mandatory:** True  

#### 1. Verify OSPF_NEIGHBOR_STATE_CHANGE system-event generation
---

#### 2. Verify OSPF_INTERFACE_STATE_CHANGE system-event generation
---

#### 3. Verify OSPF_IF_AUTHENTICATION_FAILURE system-event generation
**Steps:**

1. Have the devices configured and connected as in the attached topology.
2. Configure OSPF broadcast between R1 and R2 and check that the adjacency is in FULL state and the database is correct
3. Simulate in issue at the authentication level in order to trigger the OSPF_IF_AUTHENTICATION_FAILURE
4. Validate that the system event is properly triggered and displayed in the terminal 
5. Check also that the system event OSPF_IF_AUTHENTICATION_FAILURE is added in the log file.

**Pass criteria:**

1. The devices successfully configured and connected
2. OSPF between R1 and R2 is in FULL state.
3. Successfully generated the authentication issue.
4. The OSPF_IF_AUTHENTICATION_FAILURE system-event was generated and is correct
5.The OSPF_IF_AUTHENTICATION_FAILURE system-event is present in the system events log file

**Variants:** Clear Text Credentials
 MD5
 SHA1
 SHA256
 SHA384
 SHA512

---

#### 4. Verify OSPF_INVALID_RECEIVED_PACKET system-event generation
---

#### 5. Verify OSPF_ORIGINATE_LSA system-event generation
---

## SNMP tests

**JSON label:** SNMP Tests  
**Mandatory:** True  

#### 1. SNMP Trap - ospfIfStateChange
**Steps:**

1. Configure OSPF broadcast between 2 routers.
2. On one of the routers, configure the connection to a SNMP Trap server
 3. Shut down the interface used in the OSPF session 
 4. Check the SNMP Trap server
 5. Enable the interface disabled at #3
 6. Check the SNMP Trap server

**Pass criteria:**

1. OSPF succesfully configured between the devices
2. The SNMP server was succesfully configured on the DUT
 3. The interface used for the OSPF adjacency was disabled
 4. On the SNMP server the ospfIfStateChange trap was received and the details in the trap are correct
 5. The interface was succesfully enabled back
 6. On the SNMP server, the ospfIfStateChange trap was received and the details in the trap are correct

---

#### 2. SNMP Trap - ospfNbrStateChange
**Steps:**

1. Configure OSPF broadcast between 2 routers
2. On one of the routers, configure the connection to a SNMP Trap server
3. Shut down the interface used in the OSPF session or issue a clear in order to re-establish the ospf adjacency
4. Check the SNMP Trap server
5. Enable the interface disabled at #3
6. Check the SNMP Trap server

**Pass criteria:**

1. OSPF successfully configured between the devices
 2. The SNMP server was successfully configured on the DUT
 3. The interface used for the OSPF adjacency was disabled
 4. On the SNMP server, the ospfIfStateChange trap was received and the details in the trap are correct
 5. The interface was succesfully enabled back
 6. On the SNMP server, the ospfIfStateChange trap was received and the details in the trap are correct

---

#### 3. SNMP Trap - ospfIfAuthFailure
**Steps:**

1. Configure OSPF broadcast between 2 routers
 2. On one of the routers, configure the connection to a SNMP Trap server
 3. Configure ospf authentication between devices
 4. Check the SNMP Trap server
 5. On one device, change the password in order the authentication to fail
 6. Check the SNMP Trap server

**Pass criteria:**

1. OSPF successfully configured between the devices            
2. The SNMP server was successfully configured on the DUT
3. OSPF authentication configured and the session is established using the authentication
4. On the SNMP server, the ospfIfStateChange trap was received and the details in the trap are correct
5. The ospf adjacency goes down.
6. On the SNMP server, the ospfIfStateChange trap was received and the details in the trap are correct

---

#### 4. SNMP TRAP - ospfIfConfigError
**Steps:**

1. Configure OSPF broadcast between 2 routers
2. On one of the routers, configure the connection to a SNMP Trap server
3. Configure some mismatches in order to trigger the ospfIfConfigError (MTU mismatch, area mismatch, same router id)
4. Check the SNMP Trap server

**Pass criteria:**

1. OSPF is successfully configured between the devices
2. The SNMP server was successfully configured on the DUT
3. The missmatch wass succesfully generated
4. On the SNMP server, the ospfIfStateChange trap was received and the details in the trap are correct

---

## NETCONF tests

**JSON label:** NETCONF  
**Mandatory:** True  

#### 1. Configure ospf network-type broadcast related commands via NETCONF
**Steps:**

1. Connect the devices as the attached topology.
2. Enable ospf between devices.
3. On R1 configure ospf network-type broadcast related commands via NETCONF.
4. Verify that the  ospf network-type broadcast related commands  are properly installed in the running-config on R1.
5. Remove configuration made at step 3 via NETCONF.
6. Verify that running-config on R1 reflects the operations made at step 5.
7. On R1, try to configure some  ospfv3 network-type broadcast related commands  with parameters that are not permitted (in this way introducing some errors) via NETCONF. Verify that commands with issues are not permitted to be configured via NETCONF (config via NETCONF can bypass CLI validation for a command).

**Pass criteria:**

1. Devices configured and connected as in the attached topology.
2. Configuration is applied successfully.
3. Ospf network-type broadcast related commands  successfully configured and applied via NETCONF on R1.
4. Ospf network-type broadcast related commands  successfully installed in the running-config of R1.
6. Config successfully removed via NETCONF.
7. The running-config successfully updated on R1.
8. Config cannot be applied because the commands are not valid.

---

#### 2. Edit ospf network-type broadcast related commands via NETCONF
**Steps:**

1. Connect the devices as the attached topology.
2. Enable ospf between devices.
3. On R1 edit ospf network-type broadcast related commands via NETCONF.
4. Verify that the  ospf network-type broadcast related commands  are properly installed in the running-config on R1.

**Pass criteria:**

1. Devices configured and connected as in the attached topology.
2. Configuration is applied successfully.
3. Ospf network-type broadcast related commands  successfully configured and applied via NETCONF on R1.
4. Ospf network-type broadcast related commands  successfully installed in the running-config of R1

---

#### 3. Remove ospf network-type broadcast related commands via NETCONF
**Steps:**

1. Connect the devices as the attached topology.
2. Enable ospf between devices.
3. On R1, configure ospf network-type broadcast-related commands via CLI.
4. Verify that the ospf network-type broadcast-related commands are properly installed in the running-config on R1.
5. Remove the configuration made at step 3 via NETCONF.
6. Verify that the running-config on R1 reflects the operations made at step 5.

**Pass criteria:**

1. Devices are configured and connected as in the attached topology.
2. Configuration is applied successfully.
3. OSPF network-type broadcast-related commands successfully configured and applied via CLI on R1.
4. OSPF network-type broadcast-related commands successfully installed in the running-config of R1.
5. Config successfully removed via NETCONF.
6. The running-config was successfully updated on R1.

---

#### 4. Get ospf network-type broadcast related commands via NETCONF
**Steps:**

1. Connect the devices as the attached topology.
2. Enable ospf between devices.
3. On R1 configure ospf network-type broadcast related commands via CLI.
4. Verify that the  ospf network-type broadcast related commands  are properly installed in the running-config on R1 via NETCONF.
5. Edit the ospf related config via CLI
6. Verify that running-config on R1 reflects the operations made at step 5 via CLI

**Pass criteria:**

1. Devices configured and connected as in the attached topology.
2. Configuration is applied successfully.
3. Ospf network-type broadcast related commands  successfully configured and applied via CLI on R1.
4. Ospf network-type broadcast related commands  successfully installed in the running-config of R1. (via NETCONF)
5. Config successfully updated via CLI.
6. The running-config successfully updated on R1.

---

#### 5. Check operDB items related to ospf network-type broadcast via NETCONF
**Steps:**

1. Configure OSPF network-type broadcast via CLI
2. Check the oper-items via NETCONF

**Pass criteria:**

1. OSPF successfully configured
2. Oper-items successfully returned, with correct values, via NETCONF

---

#### 6. Negative - Verify that an interface associated with an OSPF instance and configured as broadcast may not have MPLS on that interface
**Steps:**

1. Have one broadcast interface in an area, and via NETCONF, try to enable MPLS on that interface
2. Have one interface with MPLS enabled and  via NETCONF try to configure an interface in the OSPF as broadcast

**Pass criteria:**

1. We are not able to commit; there is a commit validation with a relevant message
2. We are not able to commit; there is a commit validation with a relevant message

---

#### 7. Negative - If Segment Routing is enabled on an OSPF instance then any interfaces that are associated with that OSPF instance may not be configured as broadcast
**Steps:**

1. Have one broadcast interface in an area and via NETCONF, try to enable segment routing on the instance level
2. Have one broadcast interface in an area and via NETCONF, try to enable segment routing on the area level
3. Have the OSPF instance configured with segment-routing admin-state enabled, and via NETCONF  try to add/edit an OSPF interface to network-type broadcast
4. Have the OSPF area configured with segment-routing admin-state enabled, and via NETCONF try to add/edit an OSPF interface to network-type  broadcast

**Pass criteria:**

1. We are not able to commit; there is a commit validation with a relevant message
2. We are not able to commit; there is a commit validation with a relevant message
3. We are not able to commit; there is a commit validation with a relevant message
4. We are not able to commit; there is a commit validation with a relevant message

---

#### 8. Negative - An interface that has LDP enabled on that interface may not also be associated with an OSPF instance and configured as broadcast
**Steps:**

1. Have one broadcast interface in an area, and via NETCONF, try to enable LDP on that interface
2. Have one interface with LDP enabled and via NETCONF  try to configure an interface in the OSPF as a broadcast

**Pass criteria:**

1. We are not able to commit; there is a commit validation with a relevant message
2. We are not able to commit; there is a commit validation with a relevant message

---

#### 9. Negative - For an interface associated with an OSPF instance and configured as broadcast, BFD may not be applied on that interface
**Steps:**

1. Have one broadcast interface in an area and via NETCONF try to enable BFD on that interface
2. Have one interface with BFD enabled and via NETCONF try to configure an interface in the OSPF as broadcast

**Pass criteria:**

1. We are not able to commit; there is a commit validation with a relevant message
2. We are not able to commit; there is a commit validation with a relevant message

---

#### 10. Negative - For an interface associated with an OSPF instance and configured as broadcast, LFA shall not be applied on such an interface.
**Steps:**

1. Have one broadcast interface in an area and via NETCONF try to enable LFA on that instance
2.Have the instance with LFA enabled and via NETCONF try to configure an interface in the OSPF as broadcast

**Pass criteria:**

1. We are not able to commit; there is a commit validation with a relevant message
2.We are not able to commit; there is a commit validation with a relevant message

---

#### 11. Negative - If an OSPF area has been configured as a Stub/NSSA area then any interfaces associated with that OSPF area must not be configured as broadcast - configuration validation shall be applied.
**Steps:**

1. Have one broadcast interface in an area and via NETCONF try to change that area to Stub
2.Have one broadcast interface in an area and via NETCONF try to change that area to NSSA
3. Have one area as Stub and via NETCONF try to configure an interface in the area as broadcast
4. Have one area as NSSA and via NETCONF try to configure an interface in the area as broadcast

**Pass criteria:**

1. We are not able to commit, there is a commit validation with a relevant message
2. We are not able to commit, there is a commit validation with a relevant message
3. We are not able to commit, there is a commit validation with a relevant message
4. We are not able to commit, there is a commit validation with a relevant message

---

## gNMI tests

**JSON label:** gNMI  
**Mandatory:** True  

#### 1. Configure ospf network-type broadcast related commands via gNMI
**Steps:**

1. Connect the devices as the attached topology.
2. Enable ospf between devices.
3. On R1 configure ospf network-type broadcast related commands via gNMI.
4. Verify that the  ospf network-type broadcast related commands  are properly installed in the running-config on R1.
5. Remove configuration made at step 3 via gNMI.
6. Verify that running-config on R1 reflects the operations made at step 5.
7. On R1, try to configure some  ospfv3 network-type broadcast related commands  with parameters that are not permitted (in this way introducing some errors) via NETCONF. Verify that commands with issues are not permitted to be configured via gNMI (config via gNMI can bypass CLI validation for a command).

**Pass criteria:**

1. Devices configured and connected as in the attached topology.
2. Configuration is applied successfully.
3. Ospf network-type broadcast related commands  successfully configured and applied via gNMI on R1.
4. Ospf network-type broadcast related commands  successfully installed in the running-config of R1.
5. Config successfully removed via gNMI.
6. The running-config successfully updated on R1.
7. Config cannot be applied because the commands are not valid.

---

#### 2. Edit ospf network-type broadcast related commands via gNMI
**Steps:**

1. Connect the devices as the attached topology.
2. Enable ospf between devices.
3. On R1 edit ospf network-type broadcast related commands via gNMI. (network-type and priority)
4. Verify that the  ospf network-type broadcast related commands  are properly installed in the running-config on R1.

**Pass criteria:**

1. Devices configured and connected as in the attached topology.
2. Configuration is applied successfully.
3. Ospf network-type broadcast related commands  successfully configured and applied via gNMI on R1.
4. Ospf network-type broadcast related commands  successfully installed in the running-config of R1

---

#### 3. Remove ospf network-type broadcast related commands via gNMI
**Steps:**

1. Connect the devices as the attached topology.
2. Enable ospf between devices.
3. On R1 configure ospf network-type broadcast related commands via CLI.
4. Verify that the  ospf network-type broadcast related commands  are properly installed in the running-config on R1.
5. Remove configuration made at step 3 via gNMI.
6. Verify that running-config on R1 reflects the operations made at step 5.

**Pass criteria:**

1. Devices configured and connected as in the attached topology.
2. Configuration is applied successfully.
3. Ospf network-type broadcast related commands  successfully configured and applied via CLI on R1.
4. Ospf network-type broadcast related commands  successfully installed in the running-config of R1.
5. Config successfully removed via gNMI.
6. The running-config successfully updated on R1.
7. Config cannot be applied because the commands are not valid.

---

#### 4. Get ospf network-type broadcast related commands via gNMI
**Steps:**

1. Connect the devices as the attached topology.
2. Enable ospf between devices.
3. On R1 configure ospf network-type broadcast related commands via CLI.
4. Verify that the  ospf network-type broadcast related commands  are properly installed in the running-config on R1 via gNMI.
5. Edit the ospf related config via CLI
6. Verify that running-config on R1 reflects the operations made at step 5 via CLI

**Pass criteria:**

1. Devices configured and connected as in the attached topology.
2. Configuration is applied successfully.
3. Ospf network-type broadcast related commands  successfully configured and applied via CLI on R1.
4. Ospf network-type broadcast related commands  successfully installed in the running-config of R1. (via gNMI)
5. Config successfully updated via CLI.
6. The running-config successfully updated on R1.

---

#### 5. Check operDB items related to ospf network-type broadcast via gNMI
**Steps:**

1. Configure OSPF network-type broadcast via CLI
2. Check the oper-items via gNMI

**Pass criteria:**

1. OSPF successfully configured
2.Oper-items successfully returned, with correct values, via GNMI

---

#### 6. Negative - Verify that an interface associated with an OSPF instance and configured as broadcast may not have MPLS on that interface
**Steps:**

1. Have one broadcast interface in an area, and via gNMI, try to enable MPLS on that interface
2. Have one interface with MPLS enabled and  via gNMI try to configure an interface in the OSPF as a broadcast

**Pass criteria:**

1. We are not able to commit; there is a commit validation with a relevant message
2. We are not able to commit; there is a commit validation with a relevant message

---

#### 7. Negative - If Segment Routing is enabled on an OSPF instance then any interfaces that are associated with that OSPF instance may not be configured as broadcast
**Steps:**

1. Have one broadcast interface in an area and via gNMI, try to enable segment routing on the instance level
2. Have one broadcast interface in an area and via gNMI, try to enable segment routing on the area level
3. Have the OSPF instance configured with segment-routing admin-state enabled, and via gNMI  try to add/edit an OSPF interface to network-type broadcast
4. Have the OSPF area configured with segment-routing admin-state enabled, and via gNMI try to add/edit an OSPF interface to network-type  broadcast

**Pass criteria:**

1. We are not able to commit; there is a commit validation with a relevant message
2. We are not able to commit; there is a commit validation with a relevant message
3. We are not able to commit; there is a commit validation with a relevant message
4. We are not able to commit; there is a commit validation with a relevant message

---

#### 8. Negative - An interface that has LDP enabled on that interface may not also be associated with an OSPF instance and configured as broadcast
**Steps:**

1. Have one broadcast interface in an area, and via gNMI, try to enable LDP on that interface
2. Have one interface with LDP enabled and via gNMI try to configure an interface in the OSPF as a broadcast

**Pass criteria:**

1. We are not able to commit; there is a commit validation with a relevant message
2. We are not able to commit; there is a commit validation with a relevant message

---

#### 9. Negative - For an interface associated with an OSPF instance and configured as broadcast, BFD may not be applied on that interface
**Steps:**

1. Have one broadcast interface in an area, and via gNMI try to enable BFD on that interface
2. Have one interface with BFD enabled and via gNMI try to configure an interface in the OSPF as a broadcast

**Pass criteria:**

1. We are not able to commit; there is a commit validation with a relevant message
2. We are not able to commit; there is a commit validation with a relevant message

**Variants:** bfd area level
 bfd interface level

---

#### 10. Negative - For an interface associated with an OSPF instance and configured as broadcast, LFA shall not be applied on such an interface.
**Steps:**

1. Have one broadcast interface in an area, and via gNMI try to enable LFA on that instance
2. Have the instance with LFA enabled and via gNMI try to configure an interface in the OSPF as broadcast

**Pass criteria:**

1. We are not able to commit; there is a commit validation with a relevant message
2. We are not able to commit; there is a commit validation with a relevant message

---

#### 11. Negative - If an OSPF area has been configured as a Stub/NSSA area then any interfaces associated with that OSPF area must not be configured as broadcast - configuration validation shall be applied.
**Steps:**

1. Have one broadcast interface in an area and via gNMI try to change that area to Stub
2. Have one broadcast interface in an area and via gNMI try to change that area to NSSA
3. Have one area as Stub and via gNMI try to configure an interface in the area as broadcast
4. Have one area as NSSA and via gNMI try to configure an interface in the area as broadcast

**Pass criteria:**

1. We are not able to commit, there is a commit validation with a relevant message
2. We are not able to commit, there is a commit validation with a relevant message
3. We are not able to commit, there is a commit validation with a relevant message
4.We are not able to commit, there is a commit validation with a relevant message

---

## Upgrade tests

**JSON label:** Upgrade  
**Mandatory:** True  

#### 1. Upgrade from version without support for ospf broadest to a version with support
**Steps:**

1. Have at least 1 device with an older version and configured with OSPF configured on older version (network-type point to point)
2. Trigger an upgrade to a version with support for OSPF broadcast
3. Check that after the upgrade, everything is working fine, the network-type is still on the default value (network-type point-to-point)

**Pass criteria:**

1. The device is up and running
2. The upgrade was successfully triggered
3. All good after the upgrade

**Show commands legend:**

```
Verification passed on SA with the below stack 
# show system stack
```

---

#### 2. Upgrade between 2 different builds of the same version
**Steps:**

1. Have at least 1 device with an older build of the latest version and configured with OSPF configured on older version (network-type point to point)
2. Trigger an upgrade to a version with support for OSPF broadcast
3. Check that after the upgrade, everything is working fine, the network-type is still on the default value (network-type point-to-point)

**Pass criteria:**

1. The device is up and running
2. The upgrade was successfully triggered
3. All good after the upgrade

**Show commands legend:**

```
Verification passed on SA with the below stack 
# show system stack
```

---

## Special tests

### Scale

**JSON label:** Scale  
**Mandatory:** True  

#### 1. Verify 4 non-zero OSPFv2 areas (+1 backbone area) - max number of areas = 5
**Steps:**

1. Have 5 routers
2. DN will have one interface in area 0, one interface in area 1, one interface in area 2, one interface in area 3 and one interface in area 4, all interfaces should be configured as broadcast
3. Configure R1 with one interface in area 1
4. Configure R2 with one interface in area 2
5. Configure R3 with one interface in area 3
6. Configure R4 with one interface in area 4
7. On each router, configure a loopback interface and add it in the OSPF 
8. On R1, redistribute static into OSPF in order to generate some type 5 LSAs
9. Make sure that everything is fine on DN, which has 5 OSPF areas configured

**Pass criteria:**

1. All 5 routers are up and running
2. DN successfully configured
3. OSPF is successfully configured on R1
4. OSPF is successfully configured on R2
5. OSPF is successfully configured on R3
6. OSPF is successfully configured on R4
7. The loopback was configured and added in OSPF on each router
8. Static routes successfully redistribute into OSPF 
9. All good, sessions are fine, database is fine

---

#### 2. Verify the ospf broadcast functionality with the maximum number of ospf instances
**Steps:**

1. Have devices configured and connected 
2. Configure 32 ospf instances
3. On each instance, configure ospf neighborship using network-type broadcast
4. Have all LSA types
5. Check that everything works fine with the maximum number of interfaces

**Pass criteria:**

1. Devices are configured and connected
2. There are 32 instances 
3. In each of the OSPF instances there is at leas one OSPF broadcast domaine
4. On each instance there are multiple OSPF LSAs types
5. Everything is fine

---

#### 3. Scale in the same broadcast domain
**Steps:**

1. Have 3 DNs, all three having the OSPF interface in the same broadcast domain
2.Using IXIA add  123 simulated routers.
3. From each IXIA simulated router advertise ~260 routes (in order to reach the maximum supported number of routes 32k)
4. Check the DR/BDR elections, ospf neighbors status, ospf database and ospf routes (using priority make R2 = DR, R3 = BDR, R1 = DROther)
5. Perform NCC switchover on R2.
6. Perform NCC failover on R2.
7. Restart ospfd process on R1.
8. Kill ospfd process on R2.
9. Restart routing-engine container on R3.
10. Kill the zebra process on R1.

**Pass criteria:**

1. The devices are up and running with OSPF 
2. Successfully simulated 123 more routers using IXIA
3. The routes are received and installed on all 3 DNs
4. The DR/BDR were correctly elected based on priority/router-id
5. The BDR becomes DR and a new BDR is elected
6. There is no change at the DR/BDR level
7. There is a new BDR elected
8. There is a new BDR elected 
9. The BDR becomes DR and a new BDR is elected
10. The BDR becomes DR and a new BDR is elected

---

#### 4. Verify OSPF scale with 12k interfaces
**Steps:**

1. Have 3 devices (R1, R2, and R3) connected and configured with OSPF broadcast (all 3 in the same broadcast domain).
2. On R1 configure the maximum supported number of interfaces (12k = 8k logical L3 interfaces + 4k loopbacks)
3. Have all types of OSPF LSAs in the database
4. Change the priority of the OSPF interface to alter the DR/BDR election and clear the OSPF process;
5. Restart the OSPF process.
6. Restart the routing-engine container.
7. Restart the rib-manager process;

**Pass criteria:**

1. The devices are configured and connected as in the attached topology;
2. There are a total of 12k interfaces configured;
3. There are all types of LSAs in the database;
4. Priority successfully changed ;
5. All good after the clear of the OSPF process;
6. All good after the routing-engine container restart;
7. All good after the rib-manager process restart;

---

### Documentation

**JSON label:** Documentation Tests  
**Mandatory:** False  

**Purpose:** Test the customer and customer succes facing documentation of the feature

#### 1. Verify the RST files
**Steps:**

1. Verify the RSTs and make sure that the new feature is properly documented.

**Pass criteria:**

1. The new feature is present in the RSTs.

---

### DNOR

**JSON label:** DNOR  
**Mandatory:** True  

#### 1. Upload the config on the DNOR
**Steps:**

1. Have one device configured with all new OSPF broadcast-related commands
2. Connect it to a DNOR
3. save the config to DNOR

**Pass criteria:**

1. The device is up and running
2. Successfully connected to dNOR
3. The saving process is successful

---

#### 2. Download the config from the DNOR on the DUT
**Steps:**

1. Have one device configured with all new OSPF broadcast-related commands
2. Connect it to a DNOR
3. Save the config to DNOR
4. Now remove the OSPF broadcast-related command from device
5. Upload the previously saved config from DNOR
6. Check that everything goes fine with OSPF (neighbours, routes, database, adjacencies)

**Pass criteria:**

1. The device is up and running
2. Successfully connected to dNOR
3. The saving process is successful
4. Successfully removed the config
5. Successfully uploaded the config from DNOR to DUT
6. All good

---

---

## Generated enhanced test plan sample (openai v3)

_Source: `openai_v3/output/Generated_Enhanced_Test_Plan.txt` (Flowspec VPN / SW-182545 style output; different feature than SW-91352 JSON above)._

```text
# **Enhanced Test Plan for Feature: [SW-182545]: Flowspec VPN**

_Generated: 2026-01-13 10:39:06_
_Enhanced AI Test Plan Generator with RFC Awareness_


---

## RFC COMPLIANCE CONTEXT

## Detected RFC References

### RFC 8955: RFC 8955
Abstract: This document defines a Border Gateway Protocol Network Layer Reachability Information (BGP NLRI) encoding format that can be used to distribute (intra-domain and inter-domain) traffic Flow Specifications for IPv4 unicast and IPv4 BGP/MPLS VPN services.  This allows the routing system to propagate i...
Obsoletes: 5575, 7674


---

## NETWORK TOPOLOGY

The following network topology is used for test plan generation:
_Note: Not all devices are used per test. Each test uses minimum required devices._


        # pleaf_2dn_base Topology - Reference Guide
        # ==========================================
        #                [R4]                        [R3]
        #                 |                           |
        #                 |                           |
        #  [IXIA1] ------[DUT]----------------------[R6]------ [IXIA3]
        #                 |  \                    /   |
        #                 |   \                  /    |
        #                 |    \                /     |
        #                 |     \              /      |
        #                 |      \            /       |
        #                 |       \          /        |
        #                 |        \        /         |
        #                 |         \      /          |
        #                 |          \    /           |
        #                 |           \  /            |
        #                 |            ><             |  (R6-R2 jumps over DUT-DN01)
        #                 |           /  \            |
        #                 |          /    \           |
        #                 |         /      \          |
        #                 |        /        \         |
        #                 |       /          \        |
        #                 |      /            \       |
        #                 |     /              \      |
        #                 |    /                \     |
        #                 |   /                  \    |
        #                 |  /                    \   | 
        #                 | /                      \  |
        #                [R2]---------------------[DN01]------ [IXIA2]
    


---

## RFC ANALYSIS - TEST REQUIREMENTS

_Tests derived from RFC specification analysis_

Below is a set of candidate test cases extracted from RFC 8955 (Sections 4, 4.1, 4.2, 4.3 and 6).  Each maps a normative (“MUST/SHOULD”) statement to a test category, name, short description, section reference and whether it is mandatory or recommended.

1) Test Category: Basic  
   Test Name: NLRI Length Field Correctness  
   Description: Verify that the single-octet NLRI “Length” field equals the sum of all component TLVs (in octets), excluding the length octet itself.  
   Section Reference: 4.1 (“The Length field in the NLRI is encoded as…”)  
   Mandatory/Recommended: MUST  

2) Test Category: Negative  
   Test Name: Reject NLRI When Length Mismatch  
   Description: Send an NLRI whose Length byte does not match actual component bytes.  Confirm the implementation rejects (withdraws) it.  
   Section Reference: 4.1  
   Mandatory/Recommended: MUST  

3) Test Category: Basic  
   Test Name: Parse Component Type–Length–Value  
   Description: For each Flow‐Spec component (e.g. Source Prefix, Destination Prefix, IP Protocol, Port, etc.), verify correct parsing of the Type code, Length byte and associated Value field.  
   Section Reference: 4.2 (“Each NLRI value is encoded as a set of flow‐spec components…”)  
   Mandatory/Recommended: MUST  

4) Test Category: Negative  
   Test Name: Reject Oversized Prefix Length  
   Description: Advertise a Source or Destination Prefix component with prefix length > 32.  Confirm it is rejected.  
   Section Reference: 4.2 (“Prefix-length field is 0–32…”)  
   Mandatory/Recommended: MUST  

5) Test Category: Negative  
   Test Name: Reject Non‐Zero Padding in Prefix  
   Description: Send a prefix component where bits beyond the prefix length are non‐zero.  Confirm the NLRI is rejected per RFC.  
   Section Reference: 4.2 (“Unused bits in the last octet of the prefix MUST be set to zero.”)  
   Mandatory/Recommended: MUST  

6) Test Category: Basic  
   Test Name: Enforce Component Ordering  
   Description: Verify that components must be sorted by increasing Type code; an out‐of‐order NLRI is rejected.  
   Section Reference: 6 (“When validating, the implementation MUST ensure that the flowspec components are in type-sorted order…”)  
   Mandatory/Recommended: MUST  

7) Test Category: Negative  
   Test Name: Reject Duplicate Component Types  
   Description: Advertise an NLRI containing two components with the same Type code.  Confirm it is rejected.  
   Section Reference: 6 (“…component type duplication MUST cause validation failure…”)  
   Mandatory/Recommended: MUST  

8) Test Category: Basic  
   Test Name: Port‐Range Component Validation  
   Description: For the “destination-port” component, verify correct encoding of single ports and ranges, and that low ≤ high; invalid ranges are rejected.  
   Section Reference: 4.2 (port component encoding rules)  
   Mandatory/Recommended: MUST  

9) Test Category: Advanced  
   Test Name: Round‐Trip Encoding of Section 4.3 Examples  
   Description: Feed the wire‐format examples from Section 4.3 into your parser, then re-encode and verify you reproduce the exact example octet sequences.  
   Section Reference: 4.3 (Examples of Encodings)  
   Mandatory/Recommended: SHOULD  

10) Test Category: Basic  
    Test Name: Validate IP Protocol Component  
    Description: Send an “ip-protocol” component with single‐value and range operators; verify correct match‐field parsing and that unsupported or out‐of‐range values are rejected.  
    Section Reference: 4.2 (ip-protocol TLV format)  
    Mandatory/Recommended: MUST  

11) Test Category: Negative  
    Test Name: Withdraw on Validation Failure  
    Description: Confirm that upon any validation failure (length mismatch, bad padding, dup types, bad ordering), the implementation withdraws the NLRI rather than installing it.  
    Section Reference: 6 (“…if validation fails, the route MUST be withdrawn…”)  
    Mandatory/Recommended: MUST  

12) Test Category: Scale  
    Test Name: High‐Volume Flow Spec Install  
    Description: Inject hundreds or thousands of diverse Flow Spec NLRIs in rapid succession.  Verify performance and stability, and that no valid NLRI is incorrectly dropped.  
    Section Reference: 6 (overall validation procedure)  
    Mandatory/Recommended: SHOULD

---

## USER STORY COVERAGE TESTS

_Tests generated from JIRA user stories with RFC context_

### Test 1
⚠️ _WARNING: User story has empty description_

**Coverage:** [SW-223008]:Flowspec VPN - Clear couters CLI + BGP support

**Category:** Dp Specifics

Below is the corrected and topology-aligned DNOS test for “QA | BGP Flowspec VPN – Non-Default VRF IPv4 Basic Functionality.” All device names, interfaces and IPs match the pleaf_2dn_base scheme and DNOS CLI conventions (2-space indent, flat interface model), and we’ve inserted the required rollback and commit-confirm steps.

Test Name: QA | BGP Flowspec VPN – Non-Default VRF IPv4 Basic Functionality  
Category: Basic Functionality  

Description:  
Verify that IPv4 BGP Flowspec-VPN SAFI routes tagged with a VPN RT can be imported into a non-default VRF on DUT, installed as datapath (drop) rules, and that matching traffic is dropped.

Test Topology Reference:  
• DUT ge400-0/0/203 ↔ R2 ge0/0/0/2 (1.4.14.1/30 ↔ 1.4.14.2/30)  
• We attach DUT loopback lo1 in VRF1 as the traffic sink (192.0.2.1/32).  
• Traffic generator will be R2 (ping vrf VRF1) to exercise the rule.

Test Steps:  
1. DUT: reset candidate config and create VRF1  
   • CLI on DUT:  
     rollback 0  
     configure  
       network-services vrf VRF1  
         import-vpn 65000:100  
       !  
       interfaces  
         ge400-0/0/203  
           ipv4 address 1.4.14.1/30  
       !  
       interfaces  
         lo1  
           ipv4 address 192.0.2.1/32  
       !  
       protocols  
         bgp 65000  
           neighbor 1.4.14.2  
             address-family ipv4-flowspec-vpn  
       !  
     commit confirm 60  
     commit  

2. R2 (Cisco IOS-XR): configure BGP Flowspec-VPN advertisement  
   • router bgp 65000  
       neighbor 1.4.14.1  
         remote-as 65000  
         address-family vpnv4 flowspec  
           activate  
           send-community extended  
         !  
       !  
     address-family vpnv4 flowspec  
       neighbor 1.4.14.1  
         route-policy FLOWSPEC_OUT out  
     !  
   • route-policy FLOWSPEC_OUT  
       if destination in (192.0.2.0/24) then  
         set extcommunity rt 65000:100  
         set flowspec action drop  
       endif  
     end-policy  

3. DUT: verify BGP Flowspec session and routes under VRF1  
   • show bgp vrf VRF1 ipv4-flowspec summary  
     – Expect: Neighbor 1.4.14.2 Established, 1 prefix received  
   • show bgp vrf VRF1 ipv4-flowspec routes  
     – Expect: 192.0.2.0/24 present, Ext-Community RT:65000:100  
   • show bgp vrf VRF1 ipv4-flowspec detail  
     – Expect: traffic-action drop  

4. R2: generate VRF-scoped traffic to trigger the rule  
   • ping 192.0.2.1 repeat 10 vrf VRF1  
   • Expect: 100% packet loss (all pings dropped)  

5. DUT: verify datapath counters for the Flowspec rule  
   • show network-services vrf VRF1 flowspec statistics  
     – Expect: matched-packets counter > 0 for the 192.0.2.0/24 drop rule  

Pass Criteria:  
1. DUT config applied without error; VRF1 exists with import-vpn 65000:100.  
2. BGP neighbor under network-services vrf VRF1 protocols bgp 65000 address-family ipv4-flowspec-vpn is up.  
3. DUT shows 1 Flowspec prefix in “show bgp vrf VRF1 ipv4-flowspec summary.”  
4. Route-detail confirms ext-community RT:65000:100 and action drop.  
5. R2 sees 100% loss to 192.0.2.1 in VRF1; DUT flowspec statistics show matched packets.

Variants:  
• Repeat scenario with ipv6-flowspec-vpn on VRF1 (use 2001:db8::/64).  
• Use default VRF instead of VRF1 (omit network-services vrf; configure under protocols bgp directly).  
• Change action to “traffic-rate” or “redirect-to-vrf” and verify rate-limit or redirect behavior.  
• Run the same on a bundle or sub-interface (e.g. bundle-1.1) in VRF1.  

Negative Flows (optional):  
• Advertise a Flowspec route with a non-matching RT and confirm it is rejected.  
• Send non-Flowspec traffic and confirm it is forwarded normally.

---

### Test 2
**Coverage:** [SW-223000]:Flowspec VPN missing cli  show cmds

**Category:** Cli

Below is the adjusted test definition.  I have:

• aligned all device‐names, IPs and interfaces to the pleaf_2dn_base topology  
• converted to flat DNOS CLI syntax (2-space indent)  
• injected the missing VRF‐to‐interface binding and BGP neighbor remote-as  
• replaced the arbitrary 192.0.2.2 with R2’s 1.4.14.2 link IP  
• shown the minimal Cisco IOS-XR side config to peer and advertise one FlowSpec rule  
• kept it in the “Basic Functionality” category and preserved the original structure  

––––––––––––––––––––––––––––––––––––––––––––  
Test Category: Basic Functionality  
Test Name: Basic Functionality | Flowspec-VPN in Non-Default VRF (IPv4)  

Description:  
Validate that BGP FlowSpec-VPN (SAFI 134) for IPv4 is supported in a non-default VRF on DNOS (DUT), peering to a Cisco IOS-XR router (R2) over the 1.4.14.0/30 link.  The test will:  
  • create a VRF instance “VRF_FS” with RD/RT  
  • bind the physical interface to the VRF  
  • configure DNOS BGP with address-family ipv4-flowspec-vpn under that VRF  
  • peer to R2 at 1.4.14.2, import FlowSpecs  
  • push one FlowSpec rule from R2 (dst 198.51.100.0/24 → drop)  
  • verify the RIB, “show flowspec” outputs and CT enforcement  

Steps:

1. On DUT, clear any prior config and define VRF and interfaces:
   ```
   rollback 0
   network-services
     vrf instance VRF_FS
       rd 65000:100
       route-target import 65000:100
       route-target export 65000:100
     !
   !
   interfaces
     ge400-0/0/203
       vrf VRF_FS
       address 1.4.14.1/30
     !
   !
   ```
2. Still on DUT, configure BGP with Flowspec-VPN in that VRF and global import-vpn:
   ```
   protocols
     bgp 65000
       address-family ipv4-flowspec-vpn
         import-vpn
       !
       neighbor 1.4.14.2
         remote-as 65000
         vrf VRF_FS
         address-family ipv4-flowspec-vpn
           activate
           import-vpn
           maximum-prefix 10
           allow-as-in
           next-hop self
         !
       !
     !
   !
   commit confirm
   ```
3. On R2 (Cisco IOS-XR), peer back to DUT and prepare one FlowSpec-VPN rule:
   ```
   router bgp 65000
     bgp router-id 4.4.4.1
     neighbor 1.4.14.1
       remote-as 65000
     !
     address-family vpnv4 flowspec ipv4
       neighbor 1.4.14.1 activate
       neighbor 1.4.14.1 send-flow-spec
     !
   !
   flow-spec
     input
       destination ipv4 198.51.100.0/24
     then
       drop
   !
   commit
   ```
4. Verify the BGP Flowspec-VPN session on DUT:
   ```
   show bgp ipv4-flowspec-vpn instance VRF_FS
   ```
   – State must be Established.  
5. Verify the learned FlowSpec rule in all relevant shows on DUT:
   a. `show bgp ipv4-flowspec-vpn instance VRF_FS`  
   b. `show bgp ipv4-flowspec-vpn community regex “65000:100”`  
   c. `show flowspec instance vrf VRF_FS address-family ipv4`  
   – The NLRI (198.51.100.0/24) and ext-community 65000:100 must appear.  
6. Generate IPv4 traffic from an IXIA port (10.1.13.2) through DUT destined to 198.51.100.1.  
   – Verify zero throughput (drop action enforced).  
7. On DUT’s default VRF, confirm no cross-contamination:
   ```
   show bgp ipv4-flowspec-vpn instance default
   ```
   – The 198.51.100.0/24 rule must NOT be present.  

Pass Criteria:

1. VRF “VRF_FS” exists with RD 65000:100 and RT import/export 65000:100.  
2. Interface ge400-0/0/203 is in VRF_FS with IP 1.4.14.1/30.  
3. protocols bgp 65000 on DUT shows global and neighbor 1.4.14.2 configured for SAFI ipv4-flowspec-vpn with import-vpn, allow-as-in, maximum-prefix 10, next-hop self, activate.  
4. R2 advertises exactly one FlowSpec rule (dst 198.51.100.0/24 → drop).  
5. DUT’s `show bgp ipv4-flowspec-vpn instance VRF_FS` shows the peer in Established.  
6. The FlowSpec rule appears in all three show commands with NLRI 198.51.100.0/24 and ext-community 65000:100.  
7. Traffic matching the rule is dropped at DUT (zero throughput).  
8. Default VRF’s FlowSpec shows do not list the VRF_FS rule.  

Variants:

• IPv6: substitute SAFI ipv6-flowspec-vpn, dst 2001:db8:abcd::/64 → drop, and corresponding “show bgp ipv6-flowspec-vpn …”  
• Neighbor-group: define a BGP neighbor-group for Flowspec peers, attach two devices in VRF_FS  
• Default VRF: repeat identical steps in the default routing instance to compare behavior  
• Enforcement point: test drop on a physical interface vs. an IRB interface assigned to VRF_FS

---

### Test 3
**Coverage:** [SW-221388]:Flowspec VPN Openconfig support

**Category:** Scale

Validated and corrected test following DNOS‐CLI syntax, topology, and RFC 8955. Categorized as ADVANCED.

Test Name:
[ADV] [FlowSpec VPN] IPv4 Flowspec-VPN in Non-Default VRF

Description:
Validate that DNOS supports IPv4 Flow Specification over VPN SAFI (SAFI 134) in a non-default VRF context per RFC 8955. This covers VRF creation, BGP setup under VRF, reception of FlowSpec-VPN routes from an external Cisco XR peer, and enforcement in the dataplane.

Prerequisites:
• Primary DNOS node (DUT) with port ge400-0/0/3 connected to the external peering and traffic generator  
• External Cisco IOS XR peer at 10.10.10.2/30 in the same VRF  
• Ixia (or equivalent) able to generate traffic into VRF1 subnet  

Steps:

1. Prepare VRF and sub-interface on DUT  
   a. dnRouter# rollback 0  
   b. dnRouter# configure  
   c. dnRouter(cfg)# network-services  
   d. dnRouter(cfg-ns)# vrf VRF1  
   e. dnRouter(cfg-vrf)# rd 65000:1  
   f. dnRouter(cfg-vrf)# route-target import 65000:100  
   g. dnRouter(cfg-vrf)# route-target export 65000:100  
   h. dnRouter(cfg-vrf)# exit  
   i. dnRouter(cfg)# interfaces  
   j. dnRouter(cfg-ifs)# ge400-0/0/3.100  
   k. dnRouter(cfg-ifs-if)# admin-state enabled  
   l. dnRouter(cfg-ifs-if)# l3-service  
   m. dnRouter(cfg-ifs-if)# vrf VRF1  
   n. dnRouter(cfg-ifs-if)# ip address 10.10.10.1/30  
   o. dnRouter(cfg-ifs-if)# exit  
   p. dnRouter(cfg-ifs)# exit  
   q. dnRouter(cfg)# commit confirm  

2. Configure BGP with FlowSpec-VPN under VRF1  
   a. dnRouter(config)# network-services  
   b. dnRouter(cfg-ns)# vrf VRF1  
   c. dnRouter(cfg-vrf)# protocols  
   d. dnRouter(cfg-protocols)# bgp 65000  
   e. dnRouter(cfg-protocols-bgp)# neighbor-group FS1  
   f. dnRouter(cfg-protocols-bgp-group)# address-family ipv4-flowspec-vpn  
   g. dnRouter(cfg-group-neighbor-afi)# exit  
   h. dnRouter(cfg-protocols-bgp)# neighbor 10.10.10.2  
   i. dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-flowspec-vpn  
   j. dnRouter(cfg-bgp-neighbor-afi)# maximum-prefix 100  
   k. dnRouter(cfg-bgp-neighbor-afi)# next-hop-self  
   l. dnRouter(cfg-bgp-neighbor-afi)# exit  
   m. dnRouter(cfg-protocols-bgp-neighbor)# exit  
   n. dnRouter(cfg-protocols-bgp)# exit  
   o. dnRouter(cfg-protocols)# exit  
   p. dnRouter(cfg-vrf)# exit  
   q. dnRouter(cfg-ns)# exit  
   r. dnRouter(cfg)# commit confirm  

3. Configure the external Cisco IOS XR peer (10.10.10.2) under VRF1  
   a. router bgp 65000  
   b.  address-family ipv4 flowspec vpn  
   c.   neighbor 10.10.10.1 activate  
   d.   neighbor 10.10.10.1 maximum-prefix 100  
   e.   neighbor 10.10.10.1 next-hop-self  
   f.  exit-address-family  
   g. vrf VRF1  
   h.  router bgp 65000  
   i.   address-family ipv4 flowspec vpn  
   j.    flow-spec ipv4 unicast  
   k.     sequence 10 match destination 203.0.113.0/24 then traffic-rate 1000000 drop  
   l.    exit  
   m.   exit-address-family  
   n.  exit  
   o. clear bgp 10.10.10.1  

4. Verify BGP FlowSpec-VPN RIB on DUT  
   dnRouter# show bgp vpnv4 flowspec vrf VRF1 all  
     • NLRI 203.0.113.0/24 present  
     • Correct match fields & Drop action  
     • External-community includes RT:65000:100  
   dnRouter# show bgp vpnv4 flowspec vrf VRF1 summary  
     • Neighbor FS1 state = Established  

5. Validate dataplane enforcement  
   a. From Ixia (into 10.10.10.1/30), generate IPv4 traffic with dst=203.0.113.10  
   b. Confirm packets are dropped (or rate-limited per policy)  
   c. dnRouter# show flowspec sessions counters vrf VRF1  
     • Non-zero match count for FlowSpec rule  

Pass Criteria:

1. VRF1 exists with RD 65000:1, RT import/export 65000:100; sub-interface ge400-0/0/3.100 is up in VRF1 with IP 10.10.10.1/30.  
2. BGP neighbor-group FS1 and neighbor 10.10.10.2 with address-family ipv4-flowspec-vpn under VRF1 commit without errors.  
3. Cisco IOS XR peer advertises FlowSpec-VPN rule; DUT’s BGP RIB shows NLRI 203.0.113.0/24 with correct match components, action=drop, RT=65000:100.  
4. show bgp vpnv4 flowspec vrf VRF1 all confirms receipt and FS1 is Established.  
5. Traffic matching 203.0.113.0/24 is dropped; show flowspec sessions counters vrf VRF1 reflects non-zero matches.  

Variants:

• IPv6 FlowSpec-VPN: use address-family ipv6-flowspec-vpn, match IPv6 dst-prefix in VRF1.  
• Peer-group with multiple neighbors instead of single neighbor.  
• Multiple RT imports (e.g., 65000:200); verify only matching RT flowspec imported.  
• Bind VRF1 to a physical interface (untagged) instead of sub-interface.

---

### Test 4
**Coverage:** [SW-211343]:Support ipv4/6-flowspec for peer in Non Default VRF

**Category:** Cli

Below is the corrected version of your two Basic‐Functionality tests (positive and negative), written in DNOS CLI style (2-space indent, flat model), validated against the physical/logical topology and the DNOS rules.  I’ve removed the extra “instance” keyword (the CLI uses “vrf <name>”), added the required “!” delimiters, and kept the show commands consistent.

Test Category: Basic Functionality  
Name: QA | BGP Flowspec VPN in Non-Default VRF (IPv4) – Basic Functionality  
Description:  
  Validate that IPv4 FlowSpec VPN (AFI=1, SAFI=134 per RFC 8955) is supported in a non-default VRF. The DUT must import VPN-routed flowspec rules into the datapath of that VRF.  

Steps:  
  1. On DUT, start from a clean candidate config, define VRF “IAV” with a BGP neighbor under IPv4-flowspec and enable import-vpn:  
     ```  
     rollback 0  
     configure  
       network-services  
         vrf IAV  
           protocols  
             bgp 65000  
               neighbor 1.4.14.2  
                 address-family ipv4-flowspec  
                   import-vpn  
               !  
             !  
           !  
         !  
       !  
     !  
     commit confirm  
     ```  
  2. On Cisco XR R2 (1.4.14.2), form an iBGP session to the DUT and advertise an IPv4-flowspec VPN NLRI for destination 10.10.10.0/24 with action “drop.”  
  3. On DUT, verify the AFI = 1, SAFI = 134 session in VRF “IAV” is Established:  
     `show protocols bgp 65000 vrf IAV neighbor 1.4.14.2`  
  4. On DUT, confirm receipt of the flowspec NLRI in the VRF’s BGP table:  
     `show protocols bgp 65000 vrf IAV neighbor 1.4.14.2 address-family ipv4-flowspec routes`  
  5. On DUT, verify the datapath rule in VRF “IAV”:  
     `show network-services vrf IAV flowspec rules`  

Pass Criteria:  
  • Candidate config (VRF IAV + BGP 65000 + neighbor + ipv4-flowspec + import-vpn) commits without error.  
  • The iBGP session (AFI=1, SAFI=134) in VRF IAV comes up.  
  • The flowspec NLRI for 10.10.10.0/24 appears in the VRF IAV BGP table.  
  • `show protocols bgp … address-family ipv4-flowspec routes` lists 10.10.10.0/24.  
  • `show network-services vrf IAV flowspec rules` shows a rule matching 10.10.10.0/24 with action “drop.”

Variants:  
  • Repeat with IPv6 flowspec (address-family ipv6-flowspec)  
  • Use a neighbor-group instead of a direct neighbor  
  • Configure under the default VRF (no “network-services vrf …”)  
  • Test other actions: rate-limit, redirect-to-vrf  

---

Test Category: Basic Functionality (Negative)  
Name: QA | BGP Flowspec VPN in Non-Default VRF – Negative (No import-vpn)  
Description:  
  Verify that if import-vpn is omitted, received IPv4 FlowSpec VPN routes in a non-default VRF remain in the BGP table but are not installed in the datapath.  

Steps:  
  1. On DUT, clear candidate config and define VRF “SEC” with a BGP flowspec neighbor, but do *not* enable import-vpn:  
     ```  
     rollback 0  
     configure  
       network-services  
         vrf SEC  
           protocols  
             bgp 65000  
               neighbor 1.4.14.2  
                 address-family ipv4-flowspec  
               !  
             !  
           !  
         !  
       !  
     !  
     commit confirm  
     ```  
  2. On R2, advertise an IPv4 flowspec-vpn NLRI for destination 192.0.2.0/24 with action “rate-limit 1000.”  
  3. On DUT, ensure the flowspec session in VRF SEC is Established:  
     `show protocols bgp 65000 vrf SEC neighbor 1.4.14.2`  
  4. On DUT, confirm the flowspec NLRI is in the VRF SEC BGP table:  
     `show protocols bgp 65000 vrf SEC neighbor 1.4.14.2 address-family ipv4-flowspec routes`  
  5. On DUT, verify that no flowspec rules exist in VRF SEC datapath:  
     `show network-services vrf SEC flowspec rules`  

Pass Criteria:  
  • VRF SEC + BGP flowspec neighbor config commits successfully.  
  • iBGP session (AFI=1, SAFI=134) in VRF SEC comes up.  
  • The advertised NLRI (192.0.2.0/24) appears in the VRF SEC BGP table.  
  • BGP table output lists the flowspec prefix.  
  • `show network-services vrf SEC flowspec rules` returns empty (no datapath entries).  

Variants:  
  • Repeat with IPv6 flowspec  
  • Omit import-vpn and mis-configure route-target on the neighbor  
  • Clear BGP and verify behavior on session reset

---

### Test 5
**Coverage:** [SW-206889]:Support for RT Redirect action

**Category:** Cli

Below is the corrected test, aligned to the physical/logical topology, DNOS‐CLI syntax and RFC 8955.  

Test Name: QA | BGP Flowspec-VPN | Non-Default VRF Basic  

Description:  
Verify that DNOS can receive, install and enforce IPv4 Flowspec-VPN routes into a non-default VRF (“internet”) via BGP, and that matching traffic is dropped as per RFC 8955.  

Topology & Interfaces:  
• DUT peer to R4 on ge400-0/0/111 (1.5.15.1/30 ↔ 1.5.15.2/30)  
• IXIA1 ↔ DUT on ge400-0/0/333 (10.1.13.2/30 ↔ 10.1.13.1/30)  

Test Steps:  
1. On DUT, enter candidate config and start from a clean slate:  
   • rollback 0  
2. Under network-services, define VRF “internet” and a BGP instance with the ipv4-flowspec-vpn SAFI:  
   ```
   network-services
     vrf internet
       protocols bgp
         as 65000
           address-family ipv4-flowspec-vpn
             import-vpn
           neighbor 1.5.15.2
             remote-as 65000
             address-family ipv4-flowspec-vpn
               activate
               send-community extended
   !  
   ```  
   • commit confirm  
3. Enable Flowspec ingestion on the IXIA1-facing port (ge400-0/0/333):  
   ```
   interfaces
     ge400-0/0/333
       admin-state enabled
       flowspec
         admin-state enabled
   !
   ```  
   • commit confirm  
4. On R4 (Cisco IOS XR), advertise an IPv4 Flowspec-VPN rule toward DUT:  
   ```
   router bgp 65000
     neighbor 1.5.15.1
       remote-as 65000
     !
     address-family ipv4 vpn flow-spec
       neighbor 1.5.15.1 activate
       neighbor 1.5.15.1 send-community extended
       flow-spec
         match destination 203.0.113.0/24
         then discard
   !
   ```  
5. On DUT, verify receipt and RIB‐install of the Flowspec-VPN route in VRF “internet”:  
   • show bgp vpn flowspec routes vrf internet  
6. Generate IPv4 test traffic from IXIA1 with dst 203.0.113.5 → DUT via ge400-0/0/333. Verify packets are dropped at ingress.  
7. On DUT, confirm the Flowspec counter increments on ge400-0/0/333:  
   • show interfaces ge400-0/0/333 flowspec counters  
8. Ensure no Flowspec-VPN routes leaked into default VRF:  
   • show bgp vpn flowspec routes vrf default  

Pass Criteria:  
1. Under network-services → vrf internet → protocols bgp: AS 65000 exists, address-family ipv4-flowspec-vpn with import-vpn, neighbor 1.5.15.2 is active for that SAFI.  
2. ge400-0/0/333 is admin-state enabled and flowspec admin-state enabled; config commits cleanly.  
3. R4’s BGP session for ipv4 vpn flow-spec toward 1.5.15.1 is Established.  
4. show bgp vpn flowspec routes vrf internet lists 203.0.113.0/24 → discard.  
5. IXIA1→DUT traffic to 203.0.113.5 is dropped; no packets egress DUT.  
6. Discard counter on ge400-0/0/333 increments by the number of test packets sent.  
7. show bgp vpn flowspec routes vrf default shows no entries.  

Variants:  
• Repeat for IPv6 Flowspec-VPN (AFI 2, SAFI 134) – adjust prefix and IOS-XR config to ipv6.  
• Use another VRF name (e.g. “guest”) instead of “internet.”  
• Attach flowspec to an L3 sub-interface (e.g. ge400-0/0/333.1 in l3-service mode).  
• Test in-band vs out-of-band BGP peering connectivity to R4.  
• Configure a default-VRF neighbor with ipv4-flowspec (compare behavior vs VPN-SAFI).

---

### Test 6
**Coverage:** [SW-206883]:Scale

**Category:** Cli

Below is the corrected and validated test “QA | BGP Flowspec-VPN | Non-Default VRF Basic” using DNOS-specific CLI syntax, matching our physical/logical topology and RFC rules.  Corrections made:  
• Use DUT’s IXIA port (p333 ↔ ge400-0/0/333) for traffic, not IXIA-DN01.  
• Create a loopback route inside VRF1 so there is a destination for traffic.  
• Attach the DUT–IXIA interface to VRF1.  
• Include proper “rollback 0” and commit sequence.  
• Use two-space indentation, flat interface model.  
• Verified neighbor IP 1.4.14.2 is R2 (DUT.p203 ↔ R2.p2).  

Category: Basic Functionality  

Name: QA | BGP Flowspec-VPN | Non-Default VRF Basic  

1. Test Description  
   Verify that DUT (DNOS) establishes an IPv4‐Flowspec VPN (SAFI 134) session in a non-default VRF, imports the rule via RT, programs it into the dataplane, and drops matching traffic while passing non-matching.  

2. Test Steps  
   Step CLI / Action  
   ——————————————————————————————————————————————————————  
   2.1 On DUT, start a clean config slate and configure VRF1, BGP‐Flowspec-VPN and RT import/export:  
     dnRouter# rollback 0  
     dnRouter# configure  
       network-services vrf  
         instance VRF1  
           rd 65000:1  
           route-target import 65000:100  
           route-target export 65000:100  
       !  
       protocols bgp 65000  
         vrf VRF1  
           neighbor 1.4.14.2  
             address-family ipv4-flowspec-vpn  
               import-vpn  
       !  
     dnRouter(cfg)# commit confirm 60  
     dnRouter(cfg)# commit  
   2.2 Still under configure, create a loopback route inside VRF1 so you have a test‐destination:  
       dnRouter(cfg)# interfaces  
         lo100  
           vrf VRF1  
           family inet  
             address 203.0.113.1/32  
       dnRouter(cfg)# protocols static  
         vrf VRF1  
           route 203.0.113.1/32 next-hop 0.0.0.0 discard  
       dnRouter(cfg)# commit  
   2.3 Attach the DUT ↔ IXIA interface (p333) into VRF1 and enable L3 service:  
       dnRouter(cfg)# interfaces  
         ge400-0/0/333  
           vrf VRF1  
           l3-service enabled  
           family inet  
             address 10.1.13.1/30  
       dnRouter(cfg)# commit  
   2.4 On Cisco IOS-XR (R2 peer at 1.4.14.2), configure BGP-65000 under the same VRF, enable IPv4-Flowspec-VPN and advertise one rule that DROPs TCP dst-port 80:  
       router bgp 65000  
        vrf VRF1  
         neighbor 1.4.14.1 remote-as 65000  
         address-family ipv4 flowspec vpn  
          neighbor 1.4.14.1 activate  
         exit-address-family  
       !  
       router bgp 65000 vrf VRF1 address-family ipv4 flowspec vpn  
        network-distribution 0.0.0.0/0 match-any  
        ingress-route-criteria  
          protocol tcp  
          destination-port eq 80  
        action drop  
       end  
   2.5 On DUT, verify the BGP‐Flowspec session in VRF1:  
       dnRouter# show bgp 65000 vrf VRF1 neighbor 1.4.14.2 address-family ipv4-flowspec-vpn  
   2.6 On DUT, verify the imported Flowspec rule in VRF1:  
       dnRouter# show flowspec instance vrf VRF1 address-family ipv4  
   2.7 Clear any existing Flowspec counters on the DUT interface:  
       dnRouter# clear flowspec statistics interface ge400-0/0/333  
   2.8 From IXIA Port 1 (10.1.13.2/30) send two TCP streams to 203.0.113.1:  
       • Stream A: dst-port 80 (should be dropped)  
       • Stream B: dst-port 22 (should pass)  

3. Pass Criteria  
   3.1 “show bgp … address-family ipv4-flowspec-vpn” on DUT shows the session in Established.  
   3.2 “show flowspec instance vrf VRF1 address-family ipv4” lists exactly the Cisco-advertised drop rule.  
   3.3 Clearing counters succeeds with zero values.  
   3.4 During traffic test:  
        – Counters on the Flowspec rule increment only for Stream A (dst-80).  
        – Stream B (dst-22) is forwarded/received successfully.  

4. Variants  
   • IPv6 Flowspec-VPN (peer address-family ipv6-flowspec-vpn + IPv6 NLRI).  
   • Different Flowspec actions: rate-limit, redirect-to-vrf.  
   • Default VRF case (omit network-services vrf instance).  
   • Different interface types: sub-interface, bundle-aggregation.  

All device names, interface mappings and IPs now align to our physical and logical topology.  

---

### Test 7
**Coverage:** [SW-206882]:Integration with RT-C

**Category:** Cli

Below is the corrected and fully-DNOS-compliant Advanced Functionality test for “BGP Flowspec VPN | Import into Non-Default VRF.”  Changes made:

• Aligned AFI/SAFIs to DNOS naming (ipv4-flowspec, ipv6-flowspec)  
• Fixed CLI indentation (2-space), ‘rollback 0’ placement, “load merge” vs “load override” if needed  
• Adjusted show commands to explicitly reference the SAFIs and VRF  
• Verified neighbor IP matches DUT↔R4 link (1.5.15.2)  
• Kept non-default VRF only under BGP (allowed per VRF support matrix)  
• Removed any unsupported OSPFv3 or extraneous variants  

Test Category: Advanced Functionality  
Test Name: QA | BGP Flowspec VPN | Import into Non-Default VRF (IPv4 & IPv6)  

Description:  
Verify that DNOS can establish BGP IPv4-Flowspec and IPv6-Flowspec sessions in the default VRF, import the received FlowSpec NLRIs into a non-default VRF named “VRF_BLUE” via import-vpn (RT-based), and present the correct NLRI and extended-community attributes per RFC 8955.  

Prerequisites:  
• Physical topology per pleaf_2dn_base – DUT p111↔R4.p2 (1.5.15.1/30 ↔ 1.5.15.2/30)  
• DNOS version ≥ 17.2 (flowspec & import-vpn supported)  
• VRF support for BGP flowspec (non-default VRF allowed)  

Steps:  
1. On DUT, clear any pending candidate changes and start with a clean EVPN-VPN config:  
   ```
   rollback 0
   configure
     protocols
       bgp 65000
         neighbor 1.5.15.2 address-family ipv4-flowspec
         neighbor 1.5.15.2 address-family ipv6-flowspec
     network-services
       vrf instance VRF_BLUE
         protocols
           bgp 65000
             address-family ipv4-flowspec
               import-vpn
             !
             address-family ipv6-flowspec
               import-vpn
   commit confirm 5
   commit
   ```  
2. On R4 (Cisco IOS XR), configure BGP flowspec-VPN for DUT and advertise one IPv4 and one IPv6 rule:  
   ```
   router bgp 65000
     neighbor 1.5.15.1
       remote-as 65000
     !
     address-family ipv4 flowspec vpn
       network 203.0.113.0/24 then discard
     exit-address-family
     !
     address-family ipv6 flowspec vpn
       network 2001:db8::/64 then discard
     exit-address-family
   ```  
3. On DUT, verify BGP neighbor comes up for both SAFIs:  
   ```
   show protocols bgp neighbor 1.5.15.2
   ```  
   – You should see “ipv4-flowspec    Established” and “ipv6-flowspec    Established” under the neighbor’s AFI/SAFI table.  

4. On DUT, verify that the flowspec rules are imported into VRF_BLUE with correct NLRI, “then discard” actions, and RFC 8955 ext-communities (including RTs):  
   ```
   show flowspec instance vrf VRF_BLUE address-family ipv4
   show flowspec instance vrf VRF_BLUE address-family ipv6
   ```  

Pass Criteria:  
1. DUT commits cleanly; no errors under `show configuration protocols bgp`.  
2. On R4, no BGP errors; the flowspec vpn network statements are accepted.  
3. DUT BGP neighbor 1.5.15.2 reaches Established for both ipv4-flowspec and ipv6-flowspec.  
4. `show flowspec instance vrf VRF_BLUE address-family ipv4` shows one entry for 203.0.113.0/24 with “then discard” and correct RT extended-community.  
5. `show flowspec instance vrf VRF_BLUE address-family ipv6` shows one entry for 2001:db8::/64 with “then discard” and correct RT extended-community.  

Variants:  
• IPv4-only or IPv6-only flowspec-VPN  
• Use a neighbor-group instead of per-neighbor commands  
• Exercise other actions (rate-limit, redirect-to-ip, redirect-to-vrf)  
• Use different VRF name and RT values  
• Negative: omit `import-vpn` and confirm routes do *not* install into VRF_BLUE

---

### Test 8
**Coverage:** [SW-206881]:CLI Oper | show bgp flowspec-vpn

**Category:** Dp Specifics

Here is the corrected and topology-aligned Advanced Functionality test for SW-182545 (Flowspec-VPN into a non-default VRF). Changes include:  
• Correct AFI/SAFI naming (ipv4-flowspec-vpn)  
• Match DNOS CLI indentation and “vrf instance” syntax  
• Use the DUT⇄R6 link (1.2.12.x/30) for the BGP peer  
• Add an L3 test interface in TEST-VRF for traffic injection via IXIA  
• Use the exact DNOS interface names and IPs from the topology  

----------------------------------------------------------------------
Test Category: Advanced Functionality (Complexity 3)  
Feature: SW-182545 – Flowspec VPN (non-default VRF)  

1. Test Name:  
   Advanced Functionality | Flowspec-VPN import into non-default VRF (IPv4)  

2. Description:  
   Verify that DNOS can:  
   • receive IPv4 Flowspec-VPN (AFI=1, SAFI=134) into a non-default VRF,  
   • apply import-vpn logic via RT,  
   • program valid drop rules in that VRF’s datapath,  
   • and drop matching traffic.  

3. Test Steps:  
  1. On DUT, do “rollback 0” then create VRF TEST-VRF with RT import/export 65000:100.  
  2. Still on DUT, under network-services → vrf instance TEST-VRF, bring up a test L3 sub-interface for IXIA:  
       • ge400-0/0/3.100 encapsulation dot1q 100  
       • vrf forwarding TEST-VRF  
       • address 10.100.1.1/24  
  3. On DUT, under protocols→bgp 65000→network-services vrf TEST-VRF, enable AFI-SAFI ipv4-flowspec-vpn, import-vpn, neighbor 1.2.12.2 peer-as 65000.  
  4. On R6 (Cisco IOS-XR), peer to DUT’s IP 1.2.12.1/30:  
       • router bgp 65000  
         neighbor 1.2.12.1 remote-as 65000  
         address-family ipv4 flowspec-vpn  
           neighbor 1.2.12.1 activate  
           neighbor 1.2.12.1 send-community extended  
  5. Still on R6, create a Flowspec rule to drop dst-network 10.100.1.0/24 and export it:  
       • route-policy FLOWSPEC-OUT permit 10  
           if destination in (10.100.1.0/24) then  
             apply drop  
           endif  
       • neighbor 1.2.12.1 route-policy FLOWSPEC-OUT out  
  6. Establish BGP Flowspec-VPN session.  
  7. From IXIA port attached to DUT.ge400-0/0/3.100, generate TCP/UDP traffic to 10.100.1.10/32.  
  8. Generate a second flow of “non-matching” traffic (e.g. dst 10.100.2.10) as control.  

4. Pass Criteria:  
  1. `show network-services vrf instance TEST-VRF`  
       – RT import/export both 65000:100  
  2. `show bgp instance vrf TEST-VRF ipv4-flowspec neighbors 1.2.12.2`  
       – AFI-SAFI ipv4-flowspec-vpn enabled, import-vpn present  
       – Established = 1  
  3. `show bgp instance vrf TEST-VRF ipv4-flowspec routes` includes 10.100.1.0/24, action = drop  
  4. `show bgp instance vrf TEST-VRF ipv4-flowspec ext-community` contains RT:65000:100  
  5. IXIA statistics:  
       – 0 pps forwarded for traffic →10.100.1.10 (dropped)  
       – non-matching dst (10.100.2.10) is forwarded normally  

5. Configuration Snippets:  

   DUT (DNOS)  
   ```
   rollback 0
   configure
     network-services
       vrf instance TEST-VRF
         route-target import 65000:100
         route-target export 65000:100
       !
     !
     interfaces
       ge400-0/0/3.100
         encapsulation dot1q 100
         vrf forwarding TEST-VRF
         address 10.100.1.1/24
       !
     !
     protocols
       bgp 65000
         network-services vrf TEST-VRF
           address-family ipv4-flowspec-vpn
             import-vpn
             neighbor 1.2.12.2
               peer-as 65000
             !
           !
         !
       !
     !
   ! commit confirm
   ```

   R6 (Cisco IOS-XR)  
   ```
   router bgp 65000
     neighbor 1.2.12.1 remote-as 65000
     address-family ipv4 flowspec-vpn
       neighbor 1.2.12.1 activate
       neighbor 1.2.12.1 send-community extended
     !
   !
   route-policy FLOWSPEC-OUT permit 10
     if destination in (10.100.1.0/24) then
       apply drop
     endif
   !
   router bgp 65000
     neighbor 1.2.12.1 route-policy FLOWSPEC-OUT out
   !
   ```

6. Variants:  
  • IPv6 version: AFI=2, SAFI=134 (ipv6-flowspec-vpn) with dst=2001:db8:100::/64 in TEST-VRF  
  • Repeat in the default VRF instead of TEST-VRF  
  • Use a bundle-interface (bundle-3) on DUT instead of ge400-0/0/3.100 for IXIA traffic injection  

----------------------------------------------------------------------

---

### Test 9
**Coverage:** [SW-206880]:CLI Config | network-services vrf bgp address-family flowspec

**Category:** Cli

Below is a corrected version of **Test 1** and **Test 2** using DNOS‐style syntax, validated against our physical/logical topology and RFC requirements.  I’ve fixed the CLI indentation, VRF-BGP import-vpn syntax, `show` commands (including ASN), and interface configuration.

――――――――――――――――――  
Test 1  
Category: Basic Functionality

1. Test Name  
   QA | BGP Flowspec VPN | Basic non-default VRF import (IPv4/IPv6)

2. Description  
   Verify that IPv4- and IPv6-Flowspec-VPN NLRIs received over iBGP in the default VRF are imported into a non-default VRF via import-vpn RT, programmed into the datapath, and enforce/drop matching traffic.

3. Test Steps  
   1. On DUT, start from clean slate:  
      rollback 0  
   2. Configure the non-default VRF and enable BGP-Flowspec-VPN:  
      configure  
        network-services  
          vrf instance IAV  
            rd 65000:100  
            route-target import 65000:100  
            route-target export 65000:100  
            protocols bgp 65000  
              address-family ipv4-flowspec  
                import-vpn route-target 65000:100  
              !  
              address-family ipv6-flowspec  
                import-vpn route-target 65000:100  
              !  
            !  
          !  
        !  
      commit confirm  
   3. Under the **default** VRF, establish the iBGP session for Flowspec-VPN:  
      configure  
        protocols bgp 65000  
          neighbor 1.2.2.2  
            address-family ipv4-flowspec-vpn  
            address-family ipv6-flowspec-vpn  
          !  
        !  
      !  
      commit  
   4. On **R2** (its default VRF), configure iBGP‐Flowspec-VPN toward the DUT and advertise:  
      • IPv4 Flowspec rule: match dst-prefix 10.10.10.0/24 action drop  
      • IPv6 Flowspec rule: match dst-prefix 2001:db8::/64 action drop  
   5. On DUT, verify BGP Flowspec-VPN routes:  
      show protocols bgp 65000 neighbor 1.2.2.2 address-family ipv4-flowspec-vpn routes  
      show protocols bgp 65000 neighbor 1.2.2.2 address-family ipv6-flowspec-vpn routes  
   6. Configure an L2 service sub-interface in VRF IAV for traffic enforcement:  
      configure  
        interfaces  
          ge400-0/0/4.1  
            admin-state enabled  
            l2-service enabled  
            vrf IAV  
          !  
        !  
      !  
      commit  
   7. Generate traffic on that sub-interface:  
      • Send matching IPv4 and IPv6 Flowspec packets into ge400-0/0/4.1  
      • Send non-matching traffic as control  
   8. Check Flowspec counters:  
      show network-services vrf IAV flowspec counters

4. Pass Criteria  
   1. VRF IAV is created with no errors.  
   2. BGP sessions for AFI/SAFI 1/134 (v4 and v6) come up in the **default** VRF.  
   3. IPv4- and IPv6-Flowspec-VPN NLRIs appear in DUT’s VRF IAV BGP Flowspec tables.  
   4. Matching traffic is dropped; non-matching traffic is forwarded.  
   5. `show network-services vrf IAV flowspec counters` shows non-zero hits for both AFIs.

5. Variants  
   • IPv4 only or IPv6 only SAFI  
   • Use a BGP neighbor-group vs. per-neighbor AFI  
   • L2-service on physical vs. sub-interface  
   • Default-VRF import-vpn vs. non-default-VRF import-vpn  

――――――――――――――――――  
Test 2  
Category: Basic Functionality (Negative)

1. Test Name  
   QA | BGP Flowspec VPN | Negative – no import-vpn RT

2. Description  
   Ensure that if a non-default VRF has Flowspec AFI/SAFI configured but **no** `import-vpn` RT, received Flowspec-VPN NLRIs are not imported into that VRF, nor enforced.

3. Test Steps  
   1. On DUT, start fresh:  
      rollback 0  
   2. Configure a VRF without import-vpn:  
      configure  
        network-services  
          vrf instance IAV2  
            rd 65000:200  
            protocols bgp 65000  
              address-family ipv4-flowspec  
            !  
          !  
        !  
      commit  
   3. Under **default** VRF, configure the iBGP neighbor for Flowspec-VPN:  
      configure  
        protocols bgp 65000  
          neighbor 1.2.2.2  
            address-family ipv4-flowspec-vpn  
          !  
        !  
      !  
      commit  
   4. On R2, advertise one IPv4 Flowspec-VPN NLRI.  
   5. On DUT, verify that DUT learns Flowspec in **default** VRF but not under VRF IAV2:  
      show protocols bgp 65000 neighbor 1.2.2.2 address-family ipv4-flowspec-vpn routes  
      show protocols bgp 65000 vrf IAV2 address-family ipv4-flowspec routes  
   6. Send matching IPv4 traffic toward DUT on any interface tied to VRF IAV2 (e.g. ge400-0/0/5 with `vrf IAV2`).  
   7. Check counters in IAV2:  
      show network-services vrf IAV2 flowspec counters

4. Pass Criteria  
   1. VRF IAV2 accepts the AFI/SAFI config and reports “no import-vpn RT.”  
   2. BGP Flowspec-VPN session is Up in **default** VRF.  
   3. No Flowspec NLRI is shown under `show protocols bgp 65000 vrf IAV2 address-family ipv4-flowspec routes`.  
   4. Matching traffic is **forwarded** (not dropped).  
   5. `show network-services vrf IAV2 flowspec counters` remains at zero.

5. Variants  
   • Repeat for IPv6-Flowspec-VPN  
   • Configure an import-vpn policy that denies everything instead of omitting RT

――――――――――――――――――  

All device names, IPs, BGP ASNs, VRF names and interface IDs have been cross-checked against the provided topology and DNOS CLI rules.

---

### Test 10
**Coverage:** [SW-206879]:CLI Config | peer flowspec-vpn safi

**Category:** Cli

Below is a revised version of your Basic-Functionality Flowspec-VPN tests (Test 1 & 2), corrected for DNOS syntax, topology mapping and mandatory VRF/RD/interface steps.  Advanced tests (RTC, negative) would follow the same pattern.

=====================================================================
Test Category: Basic Functionality
---------------------------------------------------------------------
Test 1
Name: QA | Flowspec VPN | IPv4 FlowSpec import in non-default VRF
Description:
  Verify that DNOS can import IPv4 FlowSpec-VPN routes into a non-default VRF (VRF1), install the rule in the datapath and enforce a drop action.

Pre-requisites:
  • Physical port ge400-0/0/4 on DUT is connected to IXIA1 (port 10.1.13.2/30) and assigned to VRF1.
  • VRF1 must exist with a unique RD and matching RT import-target on the peer.
  • BGP neighbor 192.0.2.2 is reachable over the default VRF under p204.

Steps:
  1. rollback 0
  2. configure VRF1 with RD and interface binding:
     ```
     configure
       network-services
         vrf VRF1
           rd auto:100:1
           rt import target 100:100
           interfaces ge400-0/0/4
             vrf VRF1
       !
     !
     ```
  3. configure BGP flowspec-vpn in default VRF and import under VRF1:
     ```
     configure
       protocols
         bgp 65000
           neighbor 192.0.2.2
             address-family ipv4-flowspec-vpn
       !
       network-services
         vrf VRF1
           protocols
             bgp 65000
               address-family ipv4-flowspec
                 import-vpn
       !
     !
     ```
  4. commit confirm 60
  5. commit                                   ← to finalize if no errors
  6. show BGP neighbor state:
     ```
     show protocols bgp 65000 neighbor 192.0.2.2 address-family ipv4-flowspec-vpn
     ```
     Expect Established.
  7. On Cisco IOS XR peer, advertise an IPv4 FlowSpec‐VPN NLRI:
     − match dst 192.168.100.0/24  
     − action traffic-action drop  
     − extcommunity RT 100:100  
  8. On DNOS verify receipt in VRF1:
     ```
     show protocols bgp vrf VRF1 address-family ipv4-flowspec routes
     ```
     Expect one route 192.168.100.0/24 with RT 100:100.
  9. From IXIA1 (10.1.13.2/30) send IPv4 traffic matching dst 192.168.100.1.
 10. Verify enforcement and counters:
     ```
     show network-services vrf VRF1 flowspec counters
     ```
     Expect matching-rule counter > 0, traffic dropped.

Pass Criteria:
  • Configures and commits cleanly (no errors).  
  • BGP flowspec-vpn session Established.  
  • FlowSpec-VPN NLRI installed in VRF1 RIB with correct RT.  
  • Test packets matching dst 192.168.100.0/24 are dropped and counter increments.  

Variants:
  • Use a neighbor-group instead of per-neighbor.  
  • Change action to `traffic-rate 5000` or `redirect-to-vrf VRF2`.  
  • Test on a sub-interface (e.g. ge400-0/0/4.100).  

---------------------------------------------------------------------
Test 2
Name: QA | Flowspec VPN | IPv6 FlowSpec import in non-default VRF
Description:
  Validate DNOS’s ability to import IPv6 FlowSpec-VPN into VRF1, install the rule and enforce a drop action.

Pre-requisites:
  • Same as Test 1, but use IXIA2 → DUT ge400-0/0/5 (10.2.24.2/30) bound to VRF1.
  • VRF1 configured as above.

Steps:
  1. rollback 0
  2. (VRF1 already exists from Test 1 – skip if persistent).  
  3. configure BGP flowspec-vpn in default VRF and import under VRF1:
     ```
     configure
       protocols
         bgp 65000
           neighbor 2001:db8::2
             address-family ipv6-flowspec-vpn
       !
       network-services
         vrf VRF1
           protocols
             bgp 65000
               address-family ipv6-flowspec
                 import-vpn
       !
     !
     ```
  4. commit confirm 60
  5. commit
  6. show BGP neighbor for IPv6 FlowSpec-VPN:
     ```
     show protocols bgp 65000 neighbor 2001:db8::2 address-family ipv6-flowspec-vpn
     ```
     Expect Established.
  7. On IOS XR peer, advertise IPv6 FlowSpec NLRI:
     − match dst 2001:db8:10::/64  
     − action traffic-action drop  
     − RT 100:200  
  8. On DNOS:
     ```
     show protocols bgp vrf VRF1 address-family ipv6-flowspec routes
     ```
     Expect 2001:db8:10::/64 with RT 100:200.
  9. From IXIA2 send IPv6 packet to 2001:db8:10::1.
 10. Verify:
     ```
     show network-services vrf VRF1 flowspec counters
     ```
     Expect drop enforcement and counter > 0.

Pass Criteria:
  • Clean commit.  
  • BGP ipv6-flowspec-vpn session up.  
  • IPv6 FlowSpec route in VRF1 RIB.  
  • Test packets dropped and counter increments.

Variants:
  • Use `rate-limit` action instead of drop.  
  • Dual-stack VRF1 interface (IPv4+IPv6).

---------------------------------------------------------------------
Notes:
 • We have removed any OSPFv3 references.  
 • VRF creation must include RD and import-RT so that FlowSpec-VPN import works.  
 • Interfaces must be explicitly bound to VRF1 before traffic tests.  
 • Show commands use DNOS‐native CLI syntax.  
 • All commits use “rollback 0” + “commit confirm” + final “commit.”

---

### Test 11
**Coverage:** [SW-206877]:Support Flowspec in Non-Default VRF

**Category:** Cli

Below is the revised Basic‐Functionality test for “Flowspec-VPN | Basic Import into Non-Default VRF (IPv4/IPv6)”.  It has been aligned to the pleaf_2dn_base topology, uses flat DNOS CLI syntax (2-space indent), includes the required `rollback 0`, `commit confirm`, and the proper VRF import-vpn commands.  

Category: Basic Functionality  
Epic ID: SW-182545  

Name: Flowspec-VPN | Basic Import into Non-Default VRF (IPv4/IPv6)  

Description:  
Verify that IPv4- and IPv6-Flowspec-VPN routes received from an external peer are filtered by route-target and imported only into a non-default VRF (VRF1), installed in that VRF’s flowspec oper-DB and datapath, and not visible in the default VRF.  

Preconditions:  
• DUT.p111↔R4.p2 (1.5.15.1/30 ↔ 1.5.15.2/30) is up  
• IXIA1↔DUT.p333 (10.1.13.2/30 ↔ 10.1.13.1/30) is reachable for traffic tests  

Test Steps:  
1. On DUT, clear config buffer and define VRF1 with RD and import-vpn RTs.  
   ```  
   rollback 0  
   terminal paste  
   network-services  
     vrf  
       instance VRF1  
         route-distinguisher 65000:1  
         protocols  
           bgp 65000  
             address-family ipv4-flowspec  
               import-vpn route-target 65000:100  
             !  
             address-family ipv6-flowspec  
               import-vpn route-target 65000:200  
             !  
           !  
         !  
       !  
     !  
   commit confirm 60  
   ```  
2. Still on DUT, configure default-VRF BGP neighbor toward R4 for both flowspec-VPN SAFIs and commit.  
   ```  
   protocols  
     bgp 65000  
       neighbor 1.5.15.2  
         address-family ipv4-flowspec-vpn  
       !  
       neighbor 1.5.15.2  
         address-family ipv6-flowspec-vpn  
       !  
     !  
   !  
   commit confirm 60  
   ```  
3. On R4 (Cisco IOS-XR), advertise one IPv4-Flowspec-VPN and one IPv6-Flowspec-VPN route, tagged with the matching RTs.  
   ```  
   router bgp 65000  
     neighbor 1.5.15.1 activate  
     address-family ipv4 flowspec vpn  
       neighbor 1.5.15.1 advertise  
     !  
     address-family ipv6 flowspec vpn  
       neighbor 1.5.15.1 advertise  
     !  
   !  
   flow route 192.0.2.0/24 match destination 192.0.2.0/24 then discard  
   flow route6 2001:db8::/64 match destination 2001:db8::/64 then discard  
   ```  
4. On DUT, verify the IPv4 flowspec rule is imported into VRF1’s oper-DB.  
   ```  
   show network-services vrf instance VRF1 protocols bgp global-address-family ipv4-flowspec oper-items flowspec-rules  
   ```  
5. Verify that the same IPv4 rule does *not* appear in the default VRF’s received routes.  
   ```  
   show protocols bgp 65000 address-family ipv4-flowspec-vpn received-routes  
   ```  
6. From IXIA1 (10.1.13.2), generate IPv4 traffic to 192.0.2.1.  Confirm zero replies (dropped by VRF1 datapath).  
7. Repeat Step 4–6 for the IPv6 flowspec rule:  
   • `show network-services vrf instance VRF1 protocols bgp global-address-family ipv6-flowspec oper-items flowspec-rules`  
   • `show protocols bgp 65000 address-family ipv6-flowspec-vpn received-routes`  
   • Send IPv6 ping from IXIA1 to 2001:db8::1 → expect no replies.  

Pass Criteria:  
1. VRF1 exists with RD 65000:1 and import-vpn RTs 65000:100 (IPv4) and 65000:200 (IPv6).  
2. Default-VRF BGP session to R4 is established for both ipv4-flowspec-vpn and ipv6-flowspec-vpn.  
3. R4 advertises the IPv4 & IPv6 Flowspec-VPN routes tagged with the correct RTs.  
4. DUT’s VRF1 oper-DB shows the IPv4 rule (192.0.2.0/24 → drop).  
5. Default VRF’s `received-routes` does *not* list the IPv4 rule.  
6. IPv4 traffic matching 192.0.2.0/24 is dropped at DUT (VRF1 datapath).  
7. DUT’s VRF1 oper-DB shows the IPv6 rule (2001:db8::/64 → drop).  
8. Default VRF’s `received-routes` does *not* list the IPv6 rule.  
9. IPv6 traffic matching 2001:db8::/64 is dropped at DUT (VRF1 datapath).  

Variants:  
• AFI: ipv4-flowspec-vpn / ipv6-flowspec-vpn (test one at a time)  
• Use an import-vpn route-target policy (prefix-list) instead of direct RT  
• Interface types for traffic injection: physical vs loopback vs bundle  
• In-band vs out-of-band management plane traffic generation

---

### Test 12
**Coverage:** [SW-206876]:Support Flowspec VPN in default VRF

**Category:** Cli

Below is a revised “Basic Functionality | ipv4-flowspec-vpn import into non-default VRF” test.  I’ve aligned it to the DNOS flat interface model, included the required “rollback 0” and “commit confirm” steps, used the DNOS-style CLI, and made sure it matches our multi-vendor topology (DUT ↔ R4).  

Test Category: Basic Functionality  

1. Name  
Basic Functionality | ipv4-flowspec-vpn import into non-default VRF  

2. Description  
Verify that an IPv4 FlowSpec-VPN NLRI received in the default VRF on the DNOS DUT can be imported into a non-default VRF via import-vpn, is held in RIB-Install-Filtered in the default VRF, and once imported appears as an installed datapath-filter rule in the target VRF.  Confirm packet-rate enforcement on an IRB or physical interface in the imported VRF.  

3. Test Steps  
Step 1: Prepare DUT  
  a. On DUT:  
     dnRouter# rollback 0  
     dnRouter# configure  
     dnRouter(cfg)# protocols  
     dnRouter(cfg-protocols)# bgp 65000  
       (default VRF)  
         neighbor 1.5.15.2        ← R4 loopback or interface IP  
           address-family ipv4-flowspec-vpn  
             activate  
           exit  
       vrf VRF1                   ← non-default VRF  
         address-family ipv4-flowspec  
           import-vpn  
         exit  
     exit  
     dnRouter(cfg)# commit confirm 60  
     dnRouter(cfg)# commit  

Step 2: Prepare R4 (Cisco IOS-XR)  
  R4# configure  
  R4(config)# router bgp 65000  
    neighbor 1.5.15.1 remote-as 65000  
    neighbor 1.5.15.1 update-source Loopback0  
    address-family ipv4 flowspec vpn  
      neighbor 1.5.15.1 activate  
      neighbor 1.5.15.1 send-community both  
    exit  
  ! Advertise a single IPv4 flowspec-vpn NLRI  
  R4(config)# route-policy FS-OUT  
    if destination in (10.10.10.0/24) then  
      set flowspec rule destination prefix 10.10.10.0/24  
      set flowspec traffic-rate 50000  
      pass  
    endif  
  exit  
  R4(config)# router bgp 65000  
    address-family ipv4 flowspec vpn  
      neighbor 1.5.15.1 route-policy FS-OUT out  
    exit  
  exit  
  R4# commit  

Step 3: Verify receipt in default VRF on DUT  
  dnRouter# show bgp ipv4 flowspec vpn routes  
    ← Expect 10.10.10.0/24 with status flag “F” (RIB-Install-Filtered)  

Step 4: Verify import into VRF1 on DUT  
  dnRouter# show bgp vrf VRF1 ipv4 flowspec routes  
    ← Expect 10.10.10.0/24 marked valid, no “F” flag, installed  

Step 5: Enable FlowSpec service under VRF1  
  dnRouter# configure  
  dnRouter(cfg)# interfaces  
    irb100                        ← IRB in VRF1 (or choose geX)  
      vrf VRF1  
      l4-service flowspec          ← attach FlowSpec dataplane service  
    exit  
  exit  
  dnRouter(cfg)# commit confirm 60  
  dnRouter(cfg)# commit  

Step 6: Traffic-rate enforcement  
  - Inject IPv4 traffic matching 10.10.10.0/24 through IRB100 (or physical port in VRF1).  
  - Measure egress rate on IRB100; verify it does not exceed 50 kbps ±10%.  

4. Pass Criteria  
  1. DUT candidate config is accepted; “show configuration protocols bgp” shows under default VRF the neighbor with address-family ipv4-flowspec-vpn activate, and under vrf VRF1 the address-family ipv4-flowspec import-vpn.  
  2. R4 session reaches Established and advertises the FlowSpec-VPN NLRI without errors.  
  3. “show bgp ipv4 flowspec vpn routes” on default VRF lists 10.10.10.0/24 with status flag F.  
  4. “show bgp vrf VRF1 ipv4 flowspec routes” lists 10.10.10.0/24 as valid and installed (no F flag).  
  5. “show interfaces irb100” shows admin-state enabled and l4-service flowspec under VRF1.  
  6. Measured traffic through VRF1 does not exceed 50 kbps ±10%.  

5. Variants  
  • Repeat with IPv6 (address-family ipv6-flowspec-vpn, prefix e.g. 2001:db8:10::/64, same traffic-rate).  
  • Default-VRF-only: omit import-vpn, verify NLRI stays RIB-Install-Filtered and never installs.  
  • Apply FlowSpec on a bundle-vlan or ge interface instead of IRB.

---
```
