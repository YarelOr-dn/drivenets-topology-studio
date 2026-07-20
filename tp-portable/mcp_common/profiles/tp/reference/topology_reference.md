# Network Topology Reference for TP Generation

## Logical Topology

```
# pleaf_2dn_base Topology - Reference Guide
# ==========================================
# Mixed vendor environment: DNOS (DUT, DN01) + Cisco IOS XR (R4, R2, R3, R6)
# This mermaid diagram describes the network topology. It demonstrates dual-node DNOS deployment with external Cisco routers
# 
# ```mermaid
# DUT --- IXIA1
# DUT --- R4
# DUT --- R2
# DUT --- R6
# DUT --- DN01 
# DN01 --- R2 
# DN01 --- IXIA2
# DN01 --- R6
# R6 --- R3
# R6 --- IXIA3
# R6 --- R2
# ```
#
# ===========================
# DEVICE INVENTORY & TYPES
# ===========================

## DNOS Devices
DUT     = Central Dual Node (DN1)    | Type: pleaf:wb | Primary device
DN01    = Lower Dual Node (DN2)      | Type: pleaf:wb | Secondary device

## Cisco IOS XR Routers
R4      = Edge Router (CISCO_4)      | Type: Cisco IOS XR | Edge router
R2      = Core Router (CISCO_2)      | Type: Cisco IOS XR | Core router  
R3      = Edge Router (CISCO_3)      | Type: Cisco IOS XR | Edge router
R6      = Core Router (CISCO_6)      | Type: Cisco IOS XR | Core router

## IXIA Traffic Generator
IXIA    = Traffic Generator          | Type: IXIA | Multi-port traffic generator
        | Port 1: Connected to DUT  | IP: 10.1.13.2/30
        | Port 2: Connected to DN01 | IP: 10.2.24.2/30  
        | Port 3: Connected to R6   | IP: 10.3.36.2/30

# =============================
# DETAILED CONNECTION MATRIX
# =============================
# This section defines all physical connections and their IP addressing
# All IP addresses and VLAN assignments must match corresponding env.yaml files

## Physical Connections with IP Addressing

### DUT (Central DNOS Device) Connections:
# DUT.p111 ↔ R4.p2       | DUT: 1.5.15.1/30   ↔ R4: 1.5.15.2/30     
# DUT.p203 ↔ R2.p2       | DUT: 1.4.14.1/30   ↔ R2: 1.4.14.2/30     
# DUT.p204 ↔ R6.p2       | DUT: 1.2.12.1/30   ↔ R6: 1.2.12.2/30     
# DUT.p103 ↔ DN01.p203   | DUT: 1.3.13.1/30   ↔ DN01: 1.3.13.2/30   
# DUT.p12  ↔ DN01.p12    | DUT: 100.12.1.1/30 ↔ DN01: 100.12.1.2/30 
# DUT.p13  ↔ DN01.p13    | DUT: 100.12.2.1/30 ↔ DN01: 100.12.2.2/30 

### DN01 (Secondary DNOS Device) Connections:
# DN01.p203 ↔ DUT.p103   | DN01: 1.3.13.2/30  ↔ DUT: 1.3.13.1/30    
# DN01.p222 ↔ R2.p3      | DN01: 2.4.24.1/30  ↔ R2: 2.4.24.2/30     
# DN01.p333 ↔ R6.p3      | DN01: 6.6.66.2/30  ↔ R6: 6.6.66.1/30     
# DN01.p12  ↔ DUT.p12    | DN01: 100.12.1.2/30 ↔ DUT: 100.12.1.1/30 
# DN01.p13  ↔ DUT.p13    | DN01: 100.12.2.2/30 ↔ DUT: 100.12.2.1/30 

### Cisco Router Interconnections:
# R3.p2  ↔ R6.p23        | R3: 1.2.12.6/30    ↔ R6: 1.2.12.5/30     

### IXIA Traffic Generator Connections:
# IXIA.p1 ↔ DUT.p333     | IXIA: 10.1.13.2/30 ↔ DUT: 10.1.13.1/30   
# IXIA.p2 ↔ DN01.p444    | IXIA: 10.2.24.2/30 ↔ DN01: 10.2.24.1/30  
# IXIA.p3 ↔ R6.p4        | IXIA: 10.3.36.2/30 ↔ R6: 10.3.36.1/30    

### Router-to-DNOS Connections:
# R4.p2  ↔ DUT.p111      | R4: 1.5.15.2/30    ↔ DUT: 1.5.15.1/30    
# R2.p2  ↔ DUT.p203      | R2: 1.4.14.2/30    ↔ DUT: 1.4.14.1/30    
# R2.p3  ↔ DN01.p222     | R2: 2.4.24.2/30    ↔ DN01: 2.4.24.1/30   
# R6.p2  ↔ DUT.p204      | R6: 1.2.12.2/30    ↔ DUT: 1.2.12.1/30    
# R6.p3  ↔ DN01.p333     | R6: 6.6.66.1/30    ↔ DN01: 6.6.66.2/30   

# ========================
# LOOPBACK ADDRESSES  
# ========================
# Each device has dedicated loopback interfaces for ISIS routing and connectivity tests
# Device    | IPv4 Loopback     | IPv6 Loopback              
# ------    | -------------     | -------------             
# DUT       | dut.lo0.ipv4      | dut.lo0.ipv6               
# DN01      | DN01.lo0.ipv4     | DN01.lo0.ipv6              
# R4        | 5.5.5.1/32        | 2001:abcd::5555:1/128      
# R2        | 4.4.4.1/32        | 2001:abcd::4444:1/128      
# R3        | 7.7.7.1/32        | 2001:abcd::7777:1/128      
# R6        | 2.2.2.1/32        | 2001:abcd::2222:1/128      
# IXIA-DUT  | 10.10.10.1/32     | N/A                        
# IXIA-DN01 | 10.10.10.2/32     | N/A                        
# IXIA-R6   | 10.10.10.3/32     | N/A     
```

## Logical Topology (User-Friendly)

```
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
```

## Physical Topology

```
# All devices in this topology are physically interconnected through Arista switches acting as Layer 2 VLAN aggregators. 
# The Arista fabric provides transparent L2 connectivity, enabling logical point-to-point connections between devices using VLAN tagging.
# This architecture allows flexible, scalable test topologies without requiring direct physical cables between every device pair.
#
# Physical Topology (Arista-Centric):
#
#               [R4]            [R3]
#                |              |
#                |              |
#             +---------------------+
#   [DUT] --  |   Arista Switches   | -- [R6]
#             |   (L2 Aggregator)   |
#    [R2] --  |                     | -- [DN01]
#             +---------------------+
#                |       |      |     
#                |       |      |
#             [Ixia1] [Ixia2] [Ixia3]
#
# The Arista infrastructure consists of multiple switches:
#  - Arista Leaf Switch: Connects DNOS devices (DUT, DN01) via bundles
#  - Arista Spine Switch: Connects IXIA traffic generator ports
#  - Arista Dynamic Router Switch: Connects all Cisco IOS XR routers (R2, R3, R4, R6)
# Key Insights:
#  - Arista Switches act as L2 VLAN switches - They provide the physical connectivity fabric but remain transparent at L3.
#  - All logical connections defined in scheme.py are implemented via VLAN tagging through the Arista fabric.
#  - Three Arista Switches:
#    - Leaf: Connects DUT, DN01 (all bundles including inband)
#    - Spine: Connects IXIA traffic generator
#    - Dynamic Routers Switch: Connects all Cisco routers
#  - Bundle Architecture:
#    - bundle-1: Direct DUT↔DN01 connection (p101-104 ↔ p5-8)
#    - bundle-2: Inband management through Arista
#    - bundle-3: External connections through Arista
#  - Sub-interfaces on routers allow multiple logical connections over a single physical port using VLAN tags.
```

## Device Allocation Order

1. DUT
2. DN01
3. R2
4. R6
5. R4
6. R3
7. Others
