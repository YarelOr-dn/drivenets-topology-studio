protocols bgp neighbor-group neighbor
-------------------------------------

**Minimum user role:** operator

When configuring a BGP neighbor, you must first define it using one of the following commands.

To define a BGP neighbor and enter its configuration mode:

When configuring neighbors within a peer group, the neighbors inherit the settings from the group.

**Command syntax: neighbor [neighbor-ip-address]**

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor-group
- protocols bgp
- network-services vrf instance protocols bgp
- network-services vrf instance protocols bgp neighbor-group

**Note**

- Notice the change in prompt.

- When configuring neighbors within a peer group, the neighbors inherit the settings from the group.

**Parameter table**

+---------------------+-------------------------------------------------+--------------+---------+
| Parameter           | Description                                     | Range        | Default |
+=====================+=================================================+==============+=========+
| neighbor-ip-address | Address of the BGP peer, either in IPv4 or IPv6 | | A.B.C.D    | \-      |
|                     |                                                 | | X:X::X:X   |         |
+---------------------+-------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)#

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 2001::66
    dnRouter(cfg-protocols-bgp-neighbor)#

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# neighbor 12.170.4.1
    dnRouter(cfg-bgp-group-neighbor)#

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# neighbor 2001::66
    dnRouter(cfg-bgp-group-neighbor)#


**Removing Configuration**

To remove a neighbor:
::

    dnRouter(cfg-protocols-bgp)# no neighbor 12.170.4.1

To remove a neighbor from the group:
::

    dnRouter(cfg-protocols-bgp-group)# no neighbor 2001::66

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
