protocols ospf instance microloop-avoidance admin-state
-------------------------------------------------------

**Minimum user role:** operator

To enable microloop avoidance:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance microloop-avoidance

**Parameter table**

+-------------+----------------------------+--------------+----------+
| Parameter   | Description                | Range        | Default  |
+=============+============================+==============+==========+
| admin-state | Enable microloop avoidance | | enabled    | disabled |
|             |                            | | disabled   |          |
+-------------+----------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ospf
    dnRouter(cfg-protocols-ospf)# instance INSTANCE_1
    dnRouter(cfg-protocols-ospf-inst)# microloop-avoidance
    dnRouter(cfg-ospf-inst-uloop)# admin-state enabled


**Removing Configuration**

To revert admin-state to default:
::

    dnRouter(cfg-ospf-inst-uloop)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
