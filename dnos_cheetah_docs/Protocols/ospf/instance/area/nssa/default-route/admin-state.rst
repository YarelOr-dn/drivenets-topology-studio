protocols ospf instance area nssa default-route admin-state
-----------------------------------------------------------

**Minimum user role:** operator

This command enables/disables a default-route for NSSA in the OSPF area.

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area nssa default-route

**Parameter table**

+-------------+-----------------------------------------------------+--------------+----------+
| Parameter   | Description                                         | Range        | Default  |
+=============+=====================================================+==============+==========+
| admin-state | Enable default-route for nssa in a given OSPF area. | | enabled    | disabled |
|             |                                                     | | disabled   |          |
+-------------+-----------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols-ospf)# instance 1
    dnRouter(cfg-protocols-ospf-inst)# area 2
    dnRouter(cfg-ospf-inst-area)# nssa
    dnRouter(cfg-inst-area-nssa)# admin-state enabled
    dnRouter(cfg-inst-area-nssa)# default-route
    dnRouter(cfg-area-nssa-default-route)# admin-state enabled
    dnRouter(cfg-area-nssa-default-route)#


**Removing Configuration**

To revert the admin-state to its default value:
::

    dnRouter(cfg-area-nssa-default-route)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
