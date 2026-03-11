services port-mirroring session admin-state
-------------------------------------------

**Minimum user role:** operator

To enable/disable a specific port-mirroring session:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- services port-mirroring session

**Parameter table**

+-------------+---------------------------------------------+--------------+----------+
| Parameter   | Description                                 | Range        | Default  |
+=============+=============================================+==============+==========+
| admin-state | port mirroring session administrative state | | enabled    | disabled |
|             |                                             | | disabled   |          |
+-------------+---------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# port-mirroring
    dnRouter(cfg-srv-port-mirroring)# session IDS-Debug
    dnRouter(cfg-srv-port-mirroring-session)# admin-state enabled
    dnRouter(cfg-srv-port-mirroring-session)# admin-state disabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-srv-port-mirroring-session)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
