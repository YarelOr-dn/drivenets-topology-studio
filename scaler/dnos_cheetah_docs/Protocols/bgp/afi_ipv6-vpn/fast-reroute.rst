protocols bgp address-family ipv6-vpn fast-reroute
--------------------------------------------------

**Minimum user role:** operator

BGP Loop-Free Alternate (LFA) Fast Reroute (FRR) allows BGP to quickly switch to a backup path when a primary path fails. With LFA FRR, BGP pre-computes a backup path and installs the backup next hop in the forwarding table when a multipath solution is not available.

For example, when the NH interface to an NC-Edge fails, a pre-installed alternate path will provide fast rerouting of the traffic. The other NC-Core devices will continue sending traffic as usual.

To enable/disable fast reroute for the BGP protocol:

**Command syntax: fast-reroute [fast-reroute]**

**Command mode:** config

**Hierarchies**

- protocols bgp address-family ipv6-vpn
- protocols bgp address-family ipv4-unicast
- protocols bgp address-family ipv4-multicast
- protocols bgp address-family ipv6-unicast
- protocols bgp address-family ipv4-vpn
- network-services vrf instance protocols bgp address-family ipv4-unicast
- network-services vrf instance protocols bgp address-family ipv6-unicast

**Note**

- BGP fast-reroute applies only to bgp unicast and multicast sessions, and only to default VRF.

- LFA FRR is supported for both directly connected and remote nexthops. It does not apply to nexthops that are learned via BGP.

**Parameter table**

+--------------+-----------------------------------------------------------------------+--------------+----------+
| Parameter    | Description                                                           | Range        | Default  |
+==============+=======================================================================+==============+==========+
| fast-reroute | Enables bgp nexthop fast reroute for directly connected eBGP neighbor | | enabled    | disabled |
|              |                                                                       | | disabled   |          |
+--------------+-----------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv4-unicast
    dnRouter(cfg-protocols-bgp-afi)# fast-reroute enabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv6-unicast
    dnRouter(cfg-protocols-bgp-afi)# fast-reroute enabled



**Removing Configuration**

To revert to the default admin-state:
::

    dnRouter(cfg-protocols-bgp-afi)# no fast-reroute enabled

**Command History**

+---------+-----------------------------------------------------+
| Release | Modification                                        |
+=========+=====================================================+
| 10.0    | Command introduced                                  |
+---------+-----------------------------------------------------+
| 16.1    | Extended command to support BGP IPv4 multicast SAFI |
+---------+-----------------------------------------------------+
