protocols bgp neighbor-group neighbor graceful-restart
------------------------------------------------------

**Minimum user role:** operator

To configure the BGP graceful restart capability for a specific neighbor, a peer group, or for a neighbor in a peer group:

**Command syntax: graceful-restart [graceful-restart-admin-state]**

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor-group neighbor
- protocols bgp neighbor
- protocols bgp neighbor-group
- network-services vrf instance protocols bgp neighbor
- network-services vrf instance protocols bgp neighbor-group
- network-services vrf instance protocols bgp neighbor-group neighbor

**Note**

- When applied on a group, this property is inherited by all group members. Applying this property on a neighbor within a group overrides the group setting.

- When bgp graceful-restart is disabled, no graceful-restart is done regardless of the bgp neighbor graceful-restart state.

- Disabled: disables graceful-restart for the neighbor.

**Parameter table**

+------------------------------+------------------------------------------+-----------------+---------+
| Parameter                    | Description                              | Range           | Default |
+==============================+==========================================+=================+=========+
| graceful-restart-admin-state | global graceful-restart capability state | | enabled       | \-      |
|                              |                                          | | disabled      |         |
|                              |                                          | | helper-only   |         |
+------------------------------+------------------------------------------+-----------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# graceful-restart enabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 2001:3::65
    dnRouter(cfg-protocols-bgp-neighbor)# graceful-restart helper-only

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 2001:3::65
    dnRouter(cfg-protocols-bgp-neighbor)# graceful-restart disabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# graceful-restart enabled
    dnRouter(cfg-protocols-bgp-group)# graceful-restart helper-only
    dnRouter(cfg-protocols-bgp-group)# graceful-restart disabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-protocols-bgp-neighbor)# no graceful-restart

::

    dnRouter(cfg-protocols-bgp-group)# no graceful-restart

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
