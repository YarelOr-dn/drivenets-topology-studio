protocols bgp address-family ipv6-unicast next-hop-tracking policy
------------------------------------------------------------------

**Minimum user role:** operator

BGP next-hop tracking monitors changes in the BGP next-hop address in the RIB. When a change is detected, it is immediately reported to the BGP process to adjust the next-hop in the BGP table. This reduces the BGP convergence time. The next-hop tracking policy validates the prefix that solves the BGP next-hop address.

Once the policy is attached, when BGP receives from the RIB the prefix that solves the next-hop address, it checks the validity of this prefix against the next-hop policy.

If the peer's state is "established", but its next-hop is not valid due to the applied next-hop-tracking policy for BGP, then all the received routes from the peer next-hop will not be selected as the best, and those routes will not be advertised further to other peers accordingly.

To configure next-hop-tracking to a routing policy:

**Command syntax: next-hop-tracking policy [policy-name]**

**Command mode:** config

**Hierarchies**

- protocols bgp address-family ipv6-unicast
- protocols bgp address-family ipv4-unicast
- protocols bgp address-family ipv4-multicast
- network-services vrf instance protocols bgp address-family ipv4-unicast
- network-services vrf instance protocols bgp address-family ipv6-unicast

**Note**

- This command is only applicable to unicast, VPN and multicast sub-address-families.

**Parameter table**

+-------------+----------------------------------------+------------------+---------+
| Parameter   | Description                            | Range            | Default |
+=============+========================================+==================+=========+
| policy-name | set nexthop tracking validation policy | | string         | \-      |
|             |                                        | | length 1-255   |         |
+-------------+----------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv4-unicast
    dnRouter(cfg-protocols-bgp-afi)# next-hop-tracking policy BGP-NEXT-HOP-IPV4

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv6-unicast
    dnRouter(cfg-protocols-bgp-afi)# next-hop-tracking policy BGP-NEXT-HOP-IPV6

    *** Policy configuration example ***
    routing-policy
      policy BGP-NEXT-HOP-IPV4
        rule 10 allow
          match ipv4 prefix IPV4_NHT_PREFIX
        !
      !
      prefix-list ipv4 IPV4_NHT_PREFIX
        rule 1 allow 201.0.0.0/8 matching-len ge 32
        rule 2 allow 100.0.0.11/32
      !
    !

**Removing Configuration**

To remove the policy attachment:
::

    dnRouter(cfg-protocols-bgp-afi)# no next-hop-tracking

**Command History**

+---------+-----------------------------------------------------+
| Release | Modification                                        |
+=========+=====================================================+
| 13.0    | Command introduced                                  |
+---------+-----------------------------------------------------+
| 16.1    | Extended command to support BGP IPv4 multicast SAFI |
+---------+-----------------------------------------------------+
