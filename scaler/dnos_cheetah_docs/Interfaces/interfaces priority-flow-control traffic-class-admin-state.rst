interfaces priority-flow-control traffic-class admin-state
----------------------------------------------------------

**Minimum user role:** operator

To enable/disable priority-based flow control on an interface:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- interfaces priority-flow-control traffic-class

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter   | Description                                                                      | Range        | Default |
+=============+==================================================================================+==============+=========+
| admin-state | The administrative state of the priority-based flow control feature for the      | | enabled    | \-      |
|             | specific traffic-class.                                                          | | disabled   |         |
+-------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-1/0/1
    dnRouter(cfg-if-ge100-1/0/1)# priority-flow-control
    dnRouter(cfg-if-ge100-1/0/1-pfc)# traffic-class 5
    dnRouter(cfg-if-ge100-1/0/1-pfc-tc5)# admin-state enabled


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-if-ge100-1/0/1-pfc-tc5)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
