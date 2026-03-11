network-services vrf instance protocols bgp neighbor strict-capability-match
----------------------------------------------------------------------------

**Minimum user role:** operator

This command directs the router to strictly match remote capabilities and local capabilities. If the capabilities are different, the router will issue an "Unsupported Capability" error and will reset the connection.

To set strict capability match:

**Command syntax: strict-capability-match [strict-capability-match]**

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

- This command cannot be set together with the override-capability configuration. See "bgp neighbor override-capability"

**Parameter table**

+-------------------------+--------------------------------------------------------------+--------------+----------+
| Parameter               | Description                                                  | Range        | Default  |
+=========================+==============================================================+==============+==========+
| strict-capability-match | Strictly compares remote capabilities and local capabilities | | enabled    | disabled |
|                         |                                                              | | disabled   |          |
+-------------------------+--------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# strict-capability-match enabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# strict-capability-match enabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# strict-capability-match enabled
    dnRouter(cfg-protocols-bgp-group)# neighbor 30:128::107
    dnRouter(cfg-bgp-group-neighbor)# strict-capability-match disabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# override-capability enabled
    dnRouter(cfg-protocols-bgp-group)# neighbor 30:128::107
    dnRouter(cfg-bgp-group-neighbor)# override-capability disabled
    dnRouter(cfg-bgp-group-neighbor)# strict-capability-match enabled


**Removing Configuration**

To remove the strict capability match configuration:
::

    dnRouter(cfg-protocols-bgp-neighbor)# no strict-capability-match

::

    dnRouter(cfg-bgp-group-neighbor)# no strict-capability-match

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
