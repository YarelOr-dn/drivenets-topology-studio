interfaces priority-flow-control admin-state
--------------------------------------------

**Minimum user role:** operator

To enable/disable priority-based flow control on the interface:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- interfaces priority-flow-control

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter   | Description                                                                      | Range        | Default |
+=============+==================================================================================+==============+=========+
| admin-state | The administrative state of the priority-based flow control feature for the      | | enabled    | \-      |
|             | specific interface.                                                              | | disabled   |         |
+-------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-1/0/1
    dnRouter(cfg-if-ge100-1/0/1)# priority-flow-control
    dnRouter(cfg-if-ge100-1/0/1-pfc)# admin-state enabled
    dnRouter(cfg-if-ge100-1/0/1-pfc)#

    dnRouter# configure
    dnRouter(cfg)# interfaces bundle-2
    dnRouter(cfg-if-bundle-2)# priority-flow-control
    dnRouter(cfg-if-bundle-2-pfc)# admin-state disabled
    dnRouter(cfg-if-bundle-2-pfc)#


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-if-ge100-1/0/12-pfc)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
