protocols ospf instance area segment-routing admin-state
--------------------------------------------------------

**Minimum user role:** operator

This command enables/disables segment-routing in an OSPF area for source routing using the MPLS SID.
When enabled, segment-routing information is exchanged with all OSPF neighbors.
Default behavior is per the OSPF instance segment-routing settings.
To enable/disable segment-routing:

**Command syntax: segment-routing admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area

**Parameter table**

+-------------+-------------------------------------------------------------------------------+--------------+---------+
| Parameter   | Description                                                                   | Range        | Default |
+=============+===============================================================================+==============+=========+
| admin-state | Enable SR for OSPF in a given area. Default behavior is per instance settings | | enabled    | \-      |
|             |                                                                               | | disabled   |         |
+-------------+-------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# area 0
    dnRouter(cfg-protocols-ospf-area)# segment-routing enabled


**Removing Configuration**

To revert the admin-state to its default value:
::

     dnRouter(cfg-protocols-ospf-area)# no segment-routing

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
