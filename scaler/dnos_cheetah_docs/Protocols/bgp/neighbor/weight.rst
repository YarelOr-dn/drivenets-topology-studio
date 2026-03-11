protocols bgp neighbor weight
-----------------------------

**Minimum user role:** operator

To specify a weight that the BGP router will add to routes that are received from the specified BGP neighbor, BGP peer group, or BGP neighbor in a peer group:

**Command syntax: weight [weight]**

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor
- protocols bgp neighbor-group
- protocols bgp neighbor-group neighbor
- network-services vrf instance protocols bgp neighbor
- network-services vrf instance protocols bgp neighbor-group
- network-services vrf instance protocols bgp neighbor-group neighbor

**Note**

- To apply new neighbor weight settings, restart the bgp neighbor session. A user can invoke clear soft to avoid any traffic impact.

- When applied on a group, this property is inherited by all group members. Applying this property on a neighbor within a group overrides the group setting.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+---------+---------+
| Parameter | Description                                                                      | Range   | Default |
+===========+==================================================================================+=========+=========+
| weight    | Specifies a weight that the device will add to routes that are received from the | 0-65535 | 0       |
|           | specified BGP neighbor.                                                          |         |         |
+-----------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# weight 50

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# weight 10

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# weight 10
    dnRouter(cfg-protocols-bgp-group)# neighbor 30:128::107
    dnRouter(cfg-bgp-group-neighbor)# weight 50


**Removing Configuration**

To revert to the default weight value:
::

    dnRouter(cfg-protocols-bgp-neighbor)# no weight

::

    dnRouter(cfg-protocols-bgp-group)# no weight

::

    dnRouter(cfg-bgp-group-neighbor)# no weight

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
