protocols ospf instance ti-fast-reroute admin-state
---------------------------------------------------

**Minimum user role:** operator

To enable ti-lfa fast-reroute:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance ti-fast-reroute

**Parameter table**

+-------------+---------------------------------------+--------------+----------+
| Parameter   | Description                           | Range        | Default  |
+=============+=======================================+==============+==========+
| admin-state | Set to enable ti-lfa in a given level | | enabled    | disabled |
|             |                                       | | disabled   |          |
+-------------+---------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ospf
    dnRouter(cfg-protocols-ospf)# ti-fast-reroute
    dnRouter(cfg-protocols-ospf-ti-frr)# admin-state enabled


**Removing Configuration**

To revert the admin-state to the default value:
::

    dnRouter(cfg-protocols-ospf-ti-frr)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
