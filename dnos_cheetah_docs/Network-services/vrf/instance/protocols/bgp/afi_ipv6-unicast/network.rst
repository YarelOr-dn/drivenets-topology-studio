network-services vrf instance protocols bgp address-family ipv6-unicast network
-------------------------------------------------------------------------------

**Minimum user role:** operator

This command instructs BGP to advertise a network to all neighbors. The network will be generated according to the "bgp network import-check" on page 2290 settings. If "bgp network import-check" is enabled, the network will be generated only when the route is found on the RIB. If "bgp network import-check" is disabled, the network will be generated regardless of whether or not the route is found in the RIB.

**Command syntax: network [ip-prefix]** policy [policy-name]

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp address-family ipv6-unicast
- protocols bgp address-family ipv4-unicast
- protocols bgp address-family ipv4-multicast
- protocols bgp address-family ipv6-unicast
- network-services vrf instance protocols bgp address-family ipv4-unicast

**Note**

- This command is only applicable to unicast and multicast sub-address-families.

- You can configure multiple networks in an address-family.

- The prefix cannot be a link-local address.

- When setting a non /32 prefix, the route installed is the matching subnet network address. For example, for route 192.168.1.197/26 next-hop 10.173.2.65, the configured static route will be 192.168.1.192/26. The same applies for IPv6 prefixes.

**Parameter table**

+-------------+----------------------------------------------------+------------------+---------+
| Parameter   | Description                                        | Range            | Default |
+=============+====================================================+==================+=========+
| ip-prefix   | network ipv6 prefix                                | X:X::X:X/x       | \-      |
+-------------+----------------------------------------------------+------------------+---------+
| policy-name | policy to apply a route-map policy for the network | | string         | \-      |
|             |                                                    | | length 1-255   |         |
+-------------+----------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv4-unicast
    dnRouter(cfg-protocols-bgp-afi)# network 10.108.0.0/24
    dnRouter(cfg-protocols-bgp-afi)# network 10.90.0.0/16 policy RM_POL

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv6-unicast
    dnRouter(cfg-protocols-bgp-afi)# network 2001::66/90 policy RM_POL


**Removing Configuration**

To stop all network advertisements:
::

    dnRouter(cfg-protocols-bgp-afi)# no network

To stop advertisement of a specific network:
::

    dnRouter(cfg-protocols-bgp-afi)# no network 12001::66/90

To remove policy filtering for the network:
::

    dnRouter(cfg-protocols-bgp-afi)# no network 10.108.0.0/24 policy

**Command History**

+---------+---------------------------------------------------------+
| Release | Modification                                            |
+=========+=========================================================+
| 6.0     | Command introduced                                      |
+---------+---------------------------------------------------------+
| 9.0     | Added option to remove policy filtering for the network |
+---------+---------------------------------------------------------+
| 16.1    | Extended command to support BGP IPv4 multicast SAFI     |
+---------+---------------------------------------------------------+
