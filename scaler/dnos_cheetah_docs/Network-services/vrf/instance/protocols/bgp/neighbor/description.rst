network-services vrf instance protocols bgp neighbor description
----------------------------------------------------------------

**Minimum user role:** operator

To set a description for the BGP neighbor, BGP peer group, or BGP neighbor within a peer group:

**Command syntax: description [description]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp neighbor
- protocols bgp neighbor
- protocols bgp neighbor-group
- protocols bgp neighbor-group neighbor
- network-services vrf instance protocols bgp neighbor-group
- network-services vrf instance protocols bgp neighbor-group neighbor

**Note**

- When applied on a group, this property is inherited by all group members. Applying this property on a neighbor within a group overrides the group setting.

**Parameter table**

+-------------+--------------------------+------------------+---------+
| Parameter   | Description              | Range            | Default |
+=============+==========================+==================+=========+
| description | a neighbors' description | | string         | \-      |
|             |                          | | length 1-255   |         |
+-------------+--------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# description my-description

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 2001::66
    dnRouter(cfg-protocols-bgp-neighbor)# description my-description

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# description my-description

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# neighbor 12.170.4.1
    dnRouter(cfg-bgp-group-neighbor)# description my-unique-description


**Removing Configuration**

To remove the description:
::

    dnRouter(cfg-protocols-bgp-neighbor)# no description

::

    dnRouter(cfg-protocols-bgp-group)# no description

::

    dnRouter(cfg-bgp-group-neighbor)# no description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
