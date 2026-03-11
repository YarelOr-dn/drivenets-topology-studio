protocols bgp address-family ipv4-unicast aggregate-route policy
----------------------------------------------------------------

**Minimum user role:** operator

Sets a policy to modify the aggregate route attributes.
A user may deny the aggregate route creation when matching a given aggregate route attribute.

**Command syntax: policy [policy-name]**

**Command mode:** config

**Hierarchies**

- protocols bgp address-family ipv4-unicast aggregate-route
- protocols bgp address-family ipv4-multicast aggregate-route
- protocols bgp address-family ipv6-unicast aggregate-route
- network-services vrf instance protocols bgp address-family ipv4-unicast aggregate-route
- network-services vrf instance protocols bgp address-family ipv6-unicast aggregate-route

**Parameter table**

+-------------+-----------------------------------------------------+------------------+---------+
| Parameter   | Description                                         | Range            | Default |
+=============+=====================================================+==================+=========+
| policy-name | impose policy to update aggregate prefix attributes | | string         | \-      |
|             |                                                     | | length 1-255   |         |
+-------------+-----------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv4-unicast
    dnRouter(cfg-protocols-bgp-afi)# aggregate-address 10.108.0.0/16
    dnRouter(cfg-bgp-afi-aggr)# policy AGGR_POL

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv6-unicast
    dnRouter(cfg-protocols-bgp-afi)# aggregate-address 2001::66/90
    dnRouter(cfg-bgp-afi-aggr)# policy AGGR_POL


**Removing Configuration**

To remove the policy:
::

    dnRouter(cfg-bgp-afi-aggr)# no policy

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
