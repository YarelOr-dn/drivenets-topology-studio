system alarms
-------------

**Minimum user role:** operator

Alarms hierarchy of configuration. The alarms can be collcted based on the network management interface (gNMI).

To configure alarms, enter the alarms configuration mode:

**Command syntax: alarms**

**Command mode:** config

**Hierarchies**

- system

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# alarms
    dnRouter(cfg-system-alarms)#


**Removing Configuration**

To revert all alarms configuration to default:
::

    dnRouter(cfg-system)# no alarms

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
