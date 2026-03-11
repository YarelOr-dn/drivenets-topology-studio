protocols bgp neighbor override-capability
------------------------------------------

**Minimum user role:** operator

This command instructs the BGP router whether or not to establish a peering session with a neighbor that does not support capability negotiation, neighbors that are members of a peer group, or with a neighbor in a peer group. To configure this option:

**Command syntax: override-capability [override-capability]**

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor
- protocols bgp neighbor-group
- protocols bgp neighbor-group neighbor
- network-services vrf instance protocols bgp neighbor
- network-services vrf instance protocols bgp neighbor-group
- network-services vrf instance protocols bgp neighbor-group neighbor

**Note**

- When applied on a group, this property is inherited by all group members. Applying this property on a neighbor within a group overrides the group setting.

- This command cannot be enabled with the strict-capability-match configuration. See "bgp neighbor strict-capability-match"

**Parameter table**

+---------------------+---------------------------------------------------+--------------+----------+
| Parameter           | Description                                       | Range        | Default  |
+=====================+===================================================+==============+==========+
| override-capability | allow peer session without capability negotiation | | enabled    | disabled |
|                     |                                                   | | disabled   |          |
+---------------------+---------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# override-capability enabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# override-capability enabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# override-capability enabled
    dnRouter(cfg-protocols-bgp-group)# neighbor 30:128::107
    dnRouter(cfg-bgp-group-neighbor)# override-capability disabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# strict-capability-match enabled
    dnRouter(cfg-protocols-bgp-group)# neighbor 30:128::107
    dnRouter(cfg-bgp-group-neighbor)# strict-capability-match disabled
    dnRouter(cfg-bgp-group-neighbor)# override-capability enabled


**Removing Configuration**

To remove this configuration:
::

    dnRouter(cfg-protocols-bgp-neighbor)# no override-capability 

::

    dnRouter(cfg-protocols-bgp-group)# no override-capability

::

    dnRouter(cfg-bgp-group-neighbor)# no override-capability

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
