Link Layer Discovery Protocol (LLDP) Overview
---------------------------------------------

LLDP is a neighbor discovery protocol that is used for network devices to advertise information about themselves to other devices on the network and learn about each other. The information gathered with LLDP is stored in the device and can be queried. The topology of an LLDP-enabled network can be discovered by crawling the hosts and querying this database.

The information that can be retrieved include:

- System name and description
- Port name and description
- IP management address
- System capabilities (switching, routing, etc.)

LLDP information is sent by the devices from each of their interfaces at fixed interval in the form of an Ethernet frame. Each frame contains one LLDP data unit (LLDPDU), which is a sequence of type, length, and value (TLV) attributes carrying configuration information, device capabilities, and device identity.

For transmitted LLDPDU, the interfaces from which LLDP information is collected are:

- Physical interfaces with admin-state "enabled"
- Interfaces with LLDP admin-state "enabled"
- LLDP Tx per interface is "enabled"

For received LLDPDU, the interfaces from which LLDP information is collected are:

- Physical interfaces with admin-state "enabled"
- Interfaces with LLDP admin-state "enabled"
- LLDP Rx per interface is "enabled"

Tx and Rx states per interface are independent. Each interface can send without receiving or receive without sending LLDPDUs.

The Ethernet frame used in LLDP includes:

- The destination MAC address - typically set to a special multicast address that 802.1D -compliant bridges do not forward
- The EtherType field set to 0x88cc
- Mandatory TLV attributes:

   - Chassis ID
   - Port ID
   - Time to Live

- Optional TLV attributes
- End of LLDPDU TLV - with type and length fields set to 0

+-------------------------------------------------+-------------------+-----------+----------------+-------------+------------------+---------------+----------------------+
| Destination MAC                                 | Source MAC        | EtherType | Chassis ID TLV | Port ID TLV | Time to live TLV | Optional TLVs | End of LLDPDU TLV    |
+-------------------------------------------------+-------------------+-----------+----------------+-------------+------------------+---------------+----------------------+
| 01:80:c2:00:00:0e (we send) or (can receive)    | Station's address | 0x88cc    | Type = 1       | Type = 2    | Type = 3         | Zero or more  | Type = 0. Length = 0 |
| 01:80:c2:00:00:03 or 01:80:c2:00:00:00          |                   |           |                |             |                  | complete TLVs |                      |
+-------------------------------------------------+-------------------+-----------+----------------+-------------+------------------+---------------+----------------------+

Each TLV component has the following basic structure:

+--------+--------+--------------+
| Type   | Length | Value        |
+--------+--------+--------------+
| 7 bits | 9 bits | 0-511 octets |
+--------+--------+--------------+

DNOS supports the following TLVs:

+----------+---------------------+-----------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------+
| TLV Type | TLV Name            | Values and Origin                                                                                   | YANG Path                                                                        |
+----------+---------------------+-----------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------+
| 1        | Chassis ID          | Chassis ID Subtype: MAC address (val = 4)                                                           | Chassis_id: dn-top:drivenets-top/dn-proto:protocols/                             |
|          |                     | Chassis ID: Station's_MAC_address (MAC Address pattern)                                             | dn-lacp:lacp/dn-lacp:config-items/dn-lacp-private:actual-system-id               |
|          |                     | This value is identical for all interfaces in the cluster and is                                    |                                                                                  |
|          |                     | taken from the system-id defined in LAG control - LACP (in the private yang)                        |                                                                                  |
+----------+---------------------+-----------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------+
| 2        | Port ID             | Port ID Subtype: Interface name (val = 5)                                                           | Interface_name: dn-if:interfaces/dn-if:interface*/dn-if:oper-items/dn-if:name    |
|          |                     | Port ID: Interface_name (string)                                                                    |                                                                                  |
+----------+---------------------+-----------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------+
| 3        | Time To Live        | Seconds: hold_time (uint_16)                                                                        | Hold_time: dn-top:drivenets-top/dn-proto:protocols/dn-lldp:lldp/dn-lldp:         |
|          |                     |                                                                                                     | oper-items/dn-lldp:timers/dn-lldp:hold-time                                      |
+----------+---------------------+-----------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------+
| 4        | Port description    | Port Description: Interface_description (string) If value not configured,                           | Interface_description: dn-top:drivenets-top/dn-if:interfaces/dn-if:              |
|          |                     | this TLV type not sent                                                                              | interface*/dn-if:oper-items/dn-if:description                                    |
+----------+---------------------+-----------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------+
| 5        | System name         | System Name: System_name (string)                                                                   | System_name: dn-top: drivenets-top/dn-sys:system/dn-sys:oper-items/dn-sys:name   |
+----------+---------------------+-----------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------+
| 6        | System description  | System Description: DRIVENETS                                                                       | System_description: dn-top:drivenets-top/dn-sys:system/dn-sys:oper-items/dn-sys: |
|          |                     | LTD. System_description, DNOS_version (string) Concatenated string of fixed                         | system-info/dn-sys:description                                                   |
|          |                     | and configurable values                                                                             |                                                                                  |
+----------+---------------------+-----------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------+
| 7        | System capabilities | Capabilities:                                                                                       | dn-top:drivenets-top/dn-proto:protocols/dn-lldp:lldp/dn-lldp:oper-items/dn-      |
|          |                     |                                                                                                     |                                                                                  |
|          |                     |     - Other: Not capable (0)                                                                        | lldp:capabilities/dn-lldp:capability*                                            |
|          |                     |     - Repeater: Not capable (0)                                                                     |                                                                                  |
|          |                     |     - Bridge: Capable (1)                                                                           |                                                                                  |
|          |                     |     - WLAN access point: Not capable (0)                                                            |                                                                                  |
|          |                     |     - Router: Capable (1)                                                                           |                                                                                  |
|          |                     |     - Telephone: Not capable (0)                                                                    |                                                                                  |
|          |                     |     - DOCSIS cable device: Not capable (0)                                                          |                                                                                  |
|          |                     |     - Station only: Not capable (0)                                                                 |                                                                                  |
|          |                     |                                                                                                     |                                                                                  |
|          |                     |  Enabled Capabilities:                                                                              |                                                                                  |
|          |                     |     - Other: Not capable (0)                                                                        |                                                                                  |
|          |                     |     - Repeater: Not capable (0)                                                                     |                                                                                  |
|          |                     |     - Bridge: Capable (1)                                                                           |                                                                                  |
|          |                     |     - WLAN access point: Not capable (0)                                                            |                                                                                  |
|          |                     |     - Router: Capable (1)                                                                           |                                                                                  |
|          |                     |     - Telephone: Not capable (0)                                                                    |                                                                                  |
|          |                     |     - DOCSIS cable device: Not capable (0)                                                          |                                                                                  |
|          |                     |     - Station only: Not capable (0)                                                                 |                                                                                  |
+----------+---------------------+-----------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------+
| 8        | Management address  |     - Address String Length: len(Address Subtype) + len(Management Address)                         | Inband-management source-interface: dn-top:drivenets-top/dn-sys:system/dn-sys:   |
|          |                     |     - Address Subtype: IPv4 (1) / IPv6 (2)                                                          | oper-items/dn-sys:inband-management/dn-sys:source-interface                      |
|          |                     |     - Management Address: ipv4_address / ipv6_address                                               |                                                                                  |
|          |                     |     - Interface Subtype: ifIndex (2)                                                                | IPv4 Management Address: dn-top:drivenets-top/dn-if:interfaces/dn-if:            |
|          |                     |     - Interface Number: ifindex                                                                     | interface*/dn-ip:ipv4/dn-ip:addresses/dn-ip:address*/dn-ip:oper-items/dn-ip:ip   |
|          |                     |     - OID String Length: 0                                                                          |                                                                                  |
|          |                     |                                                                                                     |                                                                                  |   
|          |                     |      By default for DP interfaces, the management address will be taken                             | IPv6 Management Address: dn-top:drivenets-top/dn-if:interfaces/dn-if:            |
|          |                     |      from the in-band-management source-interface configuration to be advertised.                   | interface*/dn-ip:ipv6/dn-ip:addresses/dn-ip:address*/dn-ip:oper-items/dn-ip:ip   |
|          |                     |      By default for mgmt interfaces, the management address will be taken from the                  |                                                                                  |
|          |                     |      configured interface address.                                                                  | Interface_ifindex: dn-top:drivenets-top/dn-if:interfaces/dn-if:interface*/dn-    |
|          |                     |      If there is no any address configuration, this TLV type will be sent with                      | if:oper-items/dn-if:if-index                                                     |
|          |                     |      the following values:                                                                          |                                                                                  |
|          |                     |      - Address String Length: len(Address Subtype) + len(Management Address)                        | Station's_MAC_address: dn-top:drivenets-top/dn-if:interfaces/dn-if:interface*/dn-|
|          |                     |      - Address Subtype: 802 (includes all 802 media plus Ethernet "canonical format") (value - 6)   | eth:ethernet/dn-eth:oper-items/dn-eth:mac-address                                |
|          |                     |      - Management Address: Station's_MAC_address (MAC Address pattern)                              |                                                                                  |
|          |                     |      - Interface Subtype: ifIndex (2)                                                               |                                                                                  |
|          |                     |      - Interface Number: ifindex                                                                    |                                                                                  |
|          |                     |      - OID String Length: 0                                                                         |                                                                                  |
|          |                     |                                                                                                     |                                                                                  |   
+----------+---------------------+-----------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------+
| 0        | End of LLDPDU       | 0x0000                                                                                              | N/A                                                                              |
+----------+---------------------+-----------------------------------------------------------------------------------------------------+----------------------------------------------------------------------------------+




The parsing of the TLV is handled separately for each received LLDP packet.

- TLV types that are not supported, are discarded. They are counted as unrecognized TLVs.
- Supported TLV types that are malformed are discarded. They are counted as discarded TLVs.
- When duplicate TLV types are received in the same packet, the last received TLV overrides any previous TLV.

Each Network Cloud node (NCP, NCF, NCC) includes a container with the node_manager process running the LLDP protocol on that node. This process is responsible for sending and receiving LLDP TLVs per node interface:

**NCP:**

- Data Path interfaces (UNI/NNI) - geX-Y.Z.W
- Management interfaces for OOB - mgmt-ncc/0/0 mgmt-ncp/x/y
- Control interfaces for cluster connectivity- ctrl-ncp/x/y

**NCF:**

- Management interfaces for OOB - mgmt-ncf/x/y
- Control interfaces for cluster connectivity- ctrl-ncf/x/y

**NCC:**

- Management interfaces for OOB - mgmt-ncc/x/y
- Control interfaces for cluster connectivity- ctrl-ncc/x/y

All gathered LLDP information is sent to the NCC (Centralized functionality). All LLDP configuration is maintained in the NCC, which distributes it to all cluster nodes.

To manage the internal cluster link detection before container deployment, the host OS contains an LLDP process (lldpd-os) only for the internal management interfaces:

**NCP:**

- Management interfaces for OOB - mgmt-ncp/x/y
- Control interfaces for cluster connectivity- ctrl-ncp/x/y

**NCF:**

- Management interfaces for OOB - mgmt-ncf/x/y
- Control interfaces for cluster connectivity- ctrl-ncf/x/y

**NCC:**

- Management interfaces for OOB - mgmt-ncc/x/y
- Control interfaces for cluster connectivity- ctrl-ncc/x/y

The lldpd-os process performs "hand-out" to the custom node_manager process when deployed.

The collected LLDP information is stored in the database in case of NCC switchover or reset. Due to performance considerations, up to 10 simultaneous active neighbors are supported per LLDP interface.

**LLDP Configuration**


To configure LLDP follow these general steps:

1. Enter LLDP configuration mode. See protocols lldp.
2. Enable/Disable LLDP globally. See lldp admin-state.
3. Enable/Disable LLDP on an interface. See lldp interface.
4. Configure LLDP timers. See lldp timers.
