protocols ospf instance segment-routing admin-state
---------------------------------------------------

**Minimum user role:** operator

This command enables/disables segment-routing in OSPF for source routing using the MPLS SID.
When enabled, segment-routing information is exchanged with all OSPF neighbors.
To enable/disable segment-routing:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance segment-routing

**Parameter table**

+-------------+--------------------+--------------+----------+
| Parameter   | Description        | Range        | Default  |
+=============+====================+==============+==========+
| admin-state | Enable SR for OSPF | | enabled    | disabled |
|             |                    | | disabled   |          |
+-------------+--------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# segment-routing
    dnRouter(cfg-protocols-ospf-sr)# admin-state disabled


**Removing Configuration**

To revert the admin-state to its default value:
::

    dnRouter(cfg-protocols-ospf-sr)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
