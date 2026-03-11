services l2-cross-connect admin-state
-------------------------------------

**Minimum user role:** operator

To enable/disable an L2 cross-connect service:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- services l2-cross-connect

**Parameter table**

+-------------+--------------------------------------+--------------+----------+
| Parameter   | Description                          | Range        | Default  |
+=============+======================================+==============+==========+
| admin-state | L2 cross-connect service admin-state | | enabled    | disabled |
|             |                                      | | disabled   |          |
+-------------+--------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# l2-cross-connect XC-To-Boston-CRS
    dnRouter(cfg-srv-l2xc)# admin-state enabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-srv-l2xc)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
