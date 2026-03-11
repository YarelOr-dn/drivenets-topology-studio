system alarms inventory
-----------------------

**Minimum user role:** operator

To configure the alarms inventory, enter the inventory configuration mode:

**Command syntax: inventory**

**Command mode:** config

**Hierarchies**

- system alarms

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# alarms
    dnRouter(cfg-system-alarms)# inventory
    dnRouter(cfg-system-alarms-inventory)#


**Removing Configuration**

To revert all alarms configuration to default:
::

    dnRouter(cfg-system-alarms)# no inventory

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
