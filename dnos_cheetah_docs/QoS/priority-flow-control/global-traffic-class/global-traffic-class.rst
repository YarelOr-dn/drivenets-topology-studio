qos priority-flow-control global-traffic-class
----------------------------------------------

**Minimum user role:** operator

To enter the Priority Flow Control configuration on an interface for a specific traffic class:

**Command syntax: global-traffic-class [global-traffic-class]**

**Command mode:** config

**Hierarchies**

- qos priority-flow-control

**Parameter table**

+----------------------+---------------------------------------+-------+---------+
| Parameter            | Description                           | Range | Default |
+======================+=======================================+=======+=========+
| global-traffic-class | thresholds per specific traffic class | 0-7   | \-      |
+----------------------+---------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-qos)# priority-flow-control
    dnRouter(cfg-qos-pfc)# traffic-class 2
    dnRouter(cfg-qos-pfc-tc2)#


**Removing Configuration**

To revert to the default value for a specific traffic class (inherited from global configuration):
::

    dnRouter(cfg-qos-pfc)# no traffic-class 2

To revert to the default value for all traffic classes on the interface (inherited from global configuration):
::

    dnRouter(cfg-qos-pfc)# no traffic-class

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
