protocols bgp address-family ipv4-multicast aggregate-route as-set
------------------------------------------------------------------

**Minimum user role:** operator

Sets the aggregate route to include AS PATH information for all contributing routes in its AS PATH.
To configure the aggregate route setting:

**Command syntax: as-set**

**Command mode:** config

**Hierarchies**

- protocols bgp address-family ipv4-multicast aggregate-route
- protocols bgp address-family ipv4-unicast aggregate-route
- protocols bgp address-family ipv6-unicast aggregate-route
- network-services vrf instance protocols bgp address-family ipv4-unicast aggregate-route
- network-services vrf instance protocols bgp address-family ipv6-unicast aggregate-route

**Note**

- By default, the aggregate route AS PATH only has local AS when advertised.

- If the aggregate route has reduced the attribute information, then for all contributing routes the ATOMIC AGGREGATE attribute will be advertised.

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv4-unicast
    dnRouter(cfg-protocols-bgp-afi)# aggregate-address 10.108.0.0/16
    dnRouter(cfg-bgp-afi-aggr)# as-set

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv6-unicast
    dnRouter(cfg-protocols-bgp-afi)# aggregate-address 2001::66/90
    dnRouter(cfg-bgp-afi-aggr)# as-set


**Removing Configuration**

To stop the as-set behavior:
::

    dnRouter(cfg-bgp-afi-aggr)# no as-set

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
