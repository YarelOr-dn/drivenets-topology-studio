network-services vrf instance protocols bgp neighbor-group address-family orf-prefix-list-ipv4
----------------------------------------------------------------------------------------------

**Minimum user role:** operator

The Prefix-list is sent when the ORF send capability is enabled. To configure the prefix list to be sent to the peer to be used as an outbound-route-filter:

**Command syntax: orf-prefix-list-ipv4 [ipv4-prefix-list]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp neighbor-group address-family
- protocols bgp neighbor address-family
- protocols bgp neighbor-group address-family
- protocols bgp neighbor-group neighbor address-family
- network-services vrf instance protocols bgp neighbor address-family
- network-services vrf instance protocols bgp neighbor-group neighbor address-family

**Note**

- The prefix-list type (IPv4 / IPv6) must match the address-family type.

- The prefix-list must use a configured prefix-list from the routing-policy. It can be within the same commit.

- This command is only valid for unicast sub-address families.

- Neighbors within a neighbor-group can use the neighbor-group configuration or a configuration from the group.

**Parameter table**

+------------------+---------------------------------------------------+------------------+---------+
| Parameter        | Description                                       | Range            | Default |
+==================+===================================================+==================+=========+
| ipv4-prefix-list | IPv4 ORF prefix list sent to ORF capable neighbor | | string         | \-      |
|                  |                                                   | | length 1-255   |         |
+------------------+---------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-bgp-neighbor-afi)# orf-prefix-list ORF_PL_IPv4
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group GROUP_1
    dnRouter(cfg-protocols-bgp-group)# address-family ipv4-unicast
    dnRouter(cfg-bgp-group-afi)# orf-prefix-list ORF_PL_IPv4
    dnRouter(cfg-protocols-bgp-group)# neighbor 1.1.1.1
    dnRouter(cfg-bgp-group-neighbor)# address-family ipv6-unicast
    dnRouter(cfg-group-neighbor-afi)# orf-prefix-list ORF_PL_IPv6
    dnRouter(cfg-protocols-bgp-group)# neighbor 2:2::2:2
    dnRouter(cfg-bgp-group-neighbor)# address-family ipv6-unicast
    dnRouter(cfg-group-neighbor-afi)# orf-prefix-list ORF_PL_IPv6


**Removing Configuration**

To remove the prefix-list:
::

    dnRouter(cfg-bgp-neighbor-afi)# no orf-prefix-list

::

    dnRouter(cfg-bgp-group-afi)# no orf-prefix-list

::

    dnRouter(cfg-group-neighbor-afi)# no orf-prefix-list

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
