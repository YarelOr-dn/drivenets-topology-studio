protocols bgp neighbor-group neighbor address-family add-path receive
---------------------------------------------------------------------

**Minimum user role:** operator

Typically, BGP routers advertise only the best path for each route. The advertisement of a prefix replaces the previous announcement of that prefix.

To allow the device to receive multiple paths for the same route from the BGP neighbor/group:

**Command syntax: add-path receive [add-path-receive]**

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor-group neighbor address-family
- protocols bgp neighbor address-family
- protocols bgp neighbor-group address-family

**Note**

- This command is only applicable to unicast sub-address-families.

- This command is only applicable to the default VRF and only for iBGP neighbors.

**Parameter table**

+------------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter        | Description                                                                      | Range        | Default |
+==================+==================================================================================+==============+=========+
| add-path-receive | Enables additional paths to be received for the same route from a bgp neighbor.  | | enabled    | \-      |
|                  | Applies default vrf neighbor with in group for unicast safi                      | | disabled   |         |
+------------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-bgp-neighbor-afi)# add-path receive enabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv6-unicast
    dnRouter(cfg-protocols-bgp-afi)# add-path receive enabled
    dnRouter(cfg-protocols-bgp-afi)# exit
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# address-family ipv6-unicast
    dnRouter(cfg-bgp-group-afi)# add-path receive disabled
    dnRouter(cfg-bgp-group-afi)# exit
    dnRouter(cfg-protocols-bgp-group)# neighbor 12.170.4.1
    dnRouter(cfg-bgp-group-neighbor)# address-family ipv6-unicast
    dnRouter(cfg-group-neighbor-afi)# add-path receive enabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-bgp-neighbor-afi)# no add-path receive

::

    dnRouter(cfg-bgp-group-afi)# no add-path receive

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 9.0     | Command introduced               |
+---------+----------------------------------+
| 16.1    | Added support for multicast SAFI |
+---------+----------------------------------+
