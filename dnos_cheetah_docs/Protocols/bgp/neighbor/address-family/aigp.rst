protocols bgp neighbor address-family aigp
------------------------------------------

**Minimum user role:** operator

When enabled, the NCR adds for each route the IGP metric from the BGP next-hop to the current value of the AIGP metric before the route is forwarded to the BGP neighbor, unless the AIGP metric attribute does not exist for the route.

Upon receiving routes with the AIGP metric, the AIGP metric will be considered in best path selection.

When disabled, the received AIGP metric values are ignored and are not advertised in the BGP route.

To enable AIGP with the BGP neighbor:

**Command syntax: aigp [aigp]**

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor address-family
- protocols bgp neighbor-group address-family

**Note**

- This command is applicable to the default VRF only.

**Parameter table**

+-----------+--------------------------------------------+--------------+----------+
| Parameter | Description                                | Range        | Default  |
+===========+============================================+==============+==========+
| aigp      | set use of AIGP metric with a bgp neighbor | | enabled    | disabled |
|           |                                            | | disabled   |          |
+-----------+--------------------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols bgp 65000
    dnRouter(cfg-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-bgp-neighbor)# remote-as 5000
    dnRouter(cfg-bgp-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-bgp-neighbor-afi)# aigp enabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols bgp 65000
    dnRouter(cfg-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-bgp-neighbor)# remote-as 5000
    dnRouter(cfg-bgp-neighbor)# address-family ipv6-unicast
    dnRouter(cfg-bgp-neighbor-afi)# aigp enabled


**Removing Configuration**

To revert to the default admin-state:
::

    dnRouter(cfg-bgp-group-afi)# no aigp

::

    dnRouter(cfg-bgp-neighbor-afi)# no aigp

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 7.0     | Command introduced               |
+---------+----------------------------------+
| 16.1    | Added support for multicast SAFI |
+---------+----------------------------------+
