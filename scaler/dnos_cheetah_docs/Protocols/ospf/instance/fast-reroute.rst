protocols ospf instance fast-reroute
------------------------------------

**Minimum user role:** operator

Enables fast reroute per prefix for OSPF:

**Command syntax: fast-reroute [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance

**Note**
- Cannot be enabled together with the ti-fast-reroute.

**Parameter table**

+-------------+----------------------------------------+--------------+----------+
| Parameter   | Description                            | Range        | Default  |
+=============+========================================+==============+==========+
| admin-state | Enable OSPF LFA (fast-reroute) setting | | enabled    | disabled |
|             |                                        | | disabled   |          |
+-------------+----------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# instance INSTANCE_1
    dnRouter(cfg-protocols-ospf-inst)# fast-reroute enabled


**Removing Configuration**

To revert to the default admin-state and level:
::

    dnRouter(cfg-protocols-ospf-inst)# no fast-reroute

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
