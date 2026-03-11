network-services vrf instance protocols bgp neighbor-group remote-as
--------------------------------------------------------------------

**Minimum user role:** operator

The neighbor (not under neighbor-group) must be configured with remote-as.
For neighbor-groups:
A group can be configured with or without remote-as. If the group is not configured with remote-as, it is mandatory for each of the neighbors under the group to have remote-as.
The group and the neighbor remote-as must be from the same type, meaning iBGP, eBGP or Confederation.

To configure the remote AS number for the neighbor or peer group:

**Command syntax: remote-as [remote-as]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp neighbor-group
- protocols bgp neighbor
- protocols bgp neighbor-group
- protocols bgp neighbor-group neighbor
- network-services vrf instance protocols bgp neighbor
- network-services vrf instance protocols bgp neighbor-group neighbor

**Note**

- The AS number of the neighbor. BGP uses the AS number for identifying the BGP connection as internal (iBGP) or external (eBGP).

**Parameter table**

+-----------+------------------------+--------------+---------+
| Parameter | Description            | Range        | Default |
+===========+========================+==============+=========+
| remote-as | AS number of the peer. | 1-4294967295 | \-      |
+-----------+------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# remote-as 5000

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 2001::66
    dnRouter(cfg-protocols-bgp-neighbor)# remote-as 5000

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# remote-as 5000
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# neighbor 1.2.3.4
    dnRouter(cfg-bgp-group-neighbor)# remote-as 123


**Removing Configuration**

It is not possible to delete the remote-as of a neighbor or group. You need to remove the neighbor or the group. You can change the assigned remote-as.
::


**Command History**

+---------+--------------------------------------------------+
| Release | Modification                                     |
+=========+==================================================+
| 6.0     | Command introduced                               |
+---------+--------------------------------------------------+
| 18.0    | Added remote-as under neighbor of neighbor-group |
+---------+--------------------------------------------------+
