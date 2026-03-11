qos priority-flow-control admin-state
-------------------------------------

**Minimum user role:** operator

To enable/disable priority-based flow control:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- qos priority-flow-control

**Parameter table**

+-------------+----------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                          | Range        | Default  |
+=============+======================================================================+==============+==========+
| admin-state | The administrative state of the priority-based flow control feature. | | enabled    | disabled |
|             |                                                                      | | disabled   |          |
+-------------+----------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# priority-flow-control
    dnRouter(cfg-qos-pfc)# admin-state enabled
    dnRouter(cfg-qos-pfc)#


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-qos-pfc)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
