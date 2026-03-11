multicast rpf-intact admin-state
--------------------------------

**Minimum user role:** operator

To select the multicast RPF check mode:

**Command syntax: rpf-intact admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- multicast

**Note**

- The multicast RPF RIB table is always generated and populated with connected routes, and routes installed from the routing protocols' multicast SAFI.

- When the admin-state is disabled, the RPF check is performed against the unicast RIB table.

- When the admin-state is enabled, the RIB manager copies the IGP entries to the MRPF RIB table as well as BGP /32 and static /32 entries that are not resolved via tunnels. In this mode, the RPF check is performed against the MRPF RIB table while ignoring routes installed from the routing protocols' multicast SAFI.

- When in MRPF mode, the RPF check is performed against the MRPF RIB table, which contains the connected routes and routes installed from the routing protocols' multicast SAFI.

**Parameter table**

+-------------+---------------------------------+--------------+----------+
| Parameter   | Description                     | Range        | Default  |
+=============+=================================+==============+==========+
| admin-state | Select multicast RPF check mode | | enabled    | disabled |
|             |                                 | | disabled   |          |
|             |                                 | | mrpf       |          |
+-------------+---------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# multicast
    dnRouter(cfg-multicast)# rpf-intact admin-state enabled

    dnRouter# configure
    dnRouter(cfg)# multicast
    dnRouter(cfg-multicast)# rpf-intact admin-state disabled

    dnRouter# configure
    dnRouter(cfg)# multicast
    dnRouter(cfg-multicast)# rpf-intact admin-state mrpf


**Removing Configuration**

To revert to the default:
::

    dnRouter(cfg-multicast)# no rpf-intact admin-state

**Command History**

+---------+------------------------------------------------------------+
| Release | Modification                                               |
+=========+============================================================+
| 13.0    | Command introduced                                         |
+---------+------------------------------------------------------------+
| 16.1    | Multicast RPF check mode now supports a third state (MRPF) |
+---------+------------------------------------------------------------+
