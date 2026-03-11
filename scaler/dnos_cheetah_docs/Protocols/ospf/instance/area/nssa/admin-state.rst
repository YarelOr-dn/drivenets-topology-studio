protocols ospf instance area nssa admin-state
---------------------------------------------

**Minimum user role:** operator

This command enables/disables NSSA for the OSPF area.

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area nssa

**Parameter table**

+-------------+---------------------------------------+--------------+----------+
| Parameter   | Description                           | Range        | Default  |
+=============+=======================================+==============+==========+
| admin-state | Enable NSSA for OSPF in a given area. | | enabled    | disabled |
|             |                                       | | disabled   |          |
+-------------+---------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols-ospf)# instance 1
    dnRouter(cfg-protocols-ospf-inst)# area 2
    dnRouter(cfg-ospf-inst-area)# nssa admin-state enabled
    dnRouter(cfg-inst-area-nssa)#


**Removing Configuration**

To revert the admin-state to its default value:
::

    dnRouter(cfg-inst-area-nssa)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
