interfaces port-priority
------------------------

**Minimum user role:** operator

Port priority is used to dynamically group ports into bundles. The priority of the port within the bundle determines which ports have precedence in participating in the bundle interface.

To configure the port priority:

**Command syntax: port-priority [port-priority]**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to the physical interfaces

**Parameter table**

+---------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter     | Description                                                                      | Range   | Default |
+===============+==================================================================================+=========+=========+
| port-priority | The priority withing the bundle to give to the interface.  A lower value denotes | 0-65535 | 32768   |
|               | a higher priority.                                                               |         |         |
+---------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-0/0/0
    dnRouter(cfg-if-ge100-0/0/0)# port-priority 0


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-if-ge100-0/0/0)# no port-priority

**Command History**

+---------+-----------------------------------+
| Release | Modification                      |
+=========+===================================+
| 6.0     | Command introduced                |
+---------+-----------------------------------+
| 10.0    | Command moved hierarchy from LACP |
+---------+-----------------------------------+
