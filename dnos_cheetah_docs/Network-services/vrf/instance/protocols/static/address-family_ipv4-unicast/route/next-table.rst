network-services vrf instance protocols static address-family ipv4-unicast route next-table
-------------------------------------------------------------------------------------------

**Minimum user role:** operator

Sets a static IP routing entry, where the next-hop information is taken from another VRF (VRF Leakage). To configure the static IP entry:

**Command syntax: next-table [next-table]** admin-distance [admin-distance]

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols static address-family ipv4-unicast route
- protocols static address-family ipv4-unicast route

**Note**

- An IP static route must comply with its address family. e.g, in address family "ipv4-unicast" you can only set ipv4 addresses

- when user sets a non /32 ip-prefix, the route installed will be the matching subnet network address. For example if user set route 192.168.1.19  **7**/26 next-hop 10.173.2.65 the configured static route will be 192.168.1.19  **2**/26. The same rule applies for ipv6-prefix.

- the ip static route cannot be

- -  a limited broadcast address

- -  a multicast address

- route designated to next-table cannot have any other static route configuration that is not also configured to the same next-table vrf.

- no command removes the static route from RIB

**Parameter table**

+----------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter      | Description                                                                      | Range            | Default |
+================+==================================================================================+==================+=========+
| next-table     | next-hop target is a reference to another vrf - the next hop should be taken     | | string         | \-      |
|                | from that vrf                                                                    | | length 1-255   |         |
+----------------+----------------------------------------------------------------------------------+------------------+---------+
| admin-distance | administrative-distance for protocol preference when choosing a route for static | 1-255            | 1       |
|                | ip route administrative distance if 1 by default                                 |                  |         |
+----------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vrf
    dnRouter(cfg-network-services-vrf)# instance VRF_1
    dnRouter(cfg-network-services-vrf-inst)# protocols
    dnRouter(cfg-vrf-inst-protocols)# static
    dnRouter(cfg-inst-protocols-static)# address-family ipv4-unicast
    dnRouter(cfg-protocols-static-ipv4)# route 172.16.172.16/32
    dnRouter(cfg-static-ipv4-route)# next-table other-vrf admin-distance 20


**Removing Configuration**

::

    dnRouter(cfg-static-ipv4-route)# no next-table other-vrf

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
