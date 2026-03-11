network-services vrf instance protocols bgp neighbor ebgp-multihop
------------------------------------------------------------------

**Minimum user role:** operator

To configure a maximum number of hops to an eBGP neighbor, to an eBGP peer group, or to a neighbor within a peer group:

**Command syntax: ebgp-multihop [ebgp-multihop]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp neighbor
- protocols bgp neighbor
- protocols bgp neighbor-group
- protocols bgp neighbor-group neighbor
- network-services vrf instance protocols bgp neighbor-group
- network-services vrf instance protocols bgp neighbor-group neighbor

**Note**

- If you set a value greater than 1, the neighbor will always be considered as an indirectly connected neighbor, regardless of the actual reachability.

- When applied on a group, this property is inherited by all group members. Applying this property on a neighbor within a group overrides the group setting.

**Parameter table**

+---------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter     | Description                                                                      | Range | Default |
+===============+==================================================================================+=======+=========+
| ebgp-multihop | set eBGP neighbors that are not on directly connected networks and sets an       | 1-255 | 1       |
|               | optional maximum hop count                                                       |       |         |
+---------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# ebgp-multihop

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 2001::66
    dnRouter(cfg-protocols-bgp-neighbor)# ebgp-multihop 20

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# ebgp-multihop 20

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# neighbor 12.170.4.1
    dnRouter(cfg-bgp-group-neighbor)# ebgp-multihop 16


**Removing Configuration**

To revert to the default configuration:
::

    dnRouter(cfg-protocols-bgp-neighbor)# no ebgp-multihop

::

    dnRouter(cfg-protocols-bgp-group)# no ebgp-multihop

::

    dnRouter(cfg-bgp-group-neighbor)# no ebgp-multihop

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
