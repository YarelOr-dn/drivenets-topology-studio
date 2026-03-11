interfaces priority-flow-control traffic-class
----------------------------------------------

**Minimum user role:** operator

To enter PFC configuration level on the interface for a specific traffic class:

**Command syntax: traffic-class [traffic-class]**

**Command mode:** config

**Hierarchies**

- interfaces priority-flow-control

**Parameter table**

+---------------+---------------------------------------+-------+---------+
| Parameter     | Description                           | Range | Default |
+===============+=======================================+=======+=========+
| traffic-class | thresholds per specific traffic class | 0-7   | \-      |
+---------------+---------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-1/0/1
    dnRouter(cfg-if-ge100-1/0/1)# priority-flow-control
    dnRouter(cfg-if-ge100-1/0/1-pfc)# traffic-class 3
    dnRouter(cfg-ge100-1/0/1-pfc-tc3)#


**Removing Configuration**

To revert to the default value for a specific traffic class (inherited from global configuration)
::

    dnRouter(cfg-if-ge100-1/0/13-pfc)# no traffic-class 3

To revert to the default value for all traffic classes on the interface (inherited from global configuration)
::

    dnRouter(cfg-if-ge100-1/0/13-pfc)# no traffic-class

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
