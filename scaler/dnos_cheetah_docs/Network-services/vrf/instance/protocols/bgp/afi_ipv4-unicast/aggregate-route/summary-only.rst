network-services vrf instance protocols bgp address-family ipv4-unicast aggregate-route summary-only
----------------------------------------------------------------------------------------------------

**Minimum user role:** operator

To Filter for more specific routes from updates:

**Command syntax: summary-only**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp address-family ipv4-unicast aggregate-route
- protocols bgp address-family ipv4-unicast aggregate-route
- protocols bgp address-family ipv4-multicast aggregate-route
- protocols bgp address-family ipv6-unicast aggregate-route
- network-services vrf instance protocols bgp address-family ipv6-unicast aggregate-route

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv4-unicast
    dnRouter(cfg-protocols-bgp-afi)# aggregate-address 10.108.0.0/16
    dnRouter(cfg-bgp-afi-aggr)# summary-only

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv6-unicast
    dnRouter(cfg-protocols-bgp-afi)# aggregate-address 2001::66/90
    dnRouter(cfg-bgp-afi-aggr)# summary-only


**Removing Configuration**

To stop the summary-only behavior:
::

    dnRouter(cfg-bgp-afi-aggr)# no summary-only

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
