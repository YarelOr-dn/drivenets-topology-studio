protocols lacp interface priority
---------------------------------

**Minimum user role:** operator

The significant part of the per interface LACP system identifier (2 bytes) priority.
A lower value is a higher priority.

The actor with the higher priority is the master after negotiation with other systems.

**Command syntax: priority [priority]**

**Command mode:** config

**Hierarchies**

- protocols lacp interface

**Parameter table**

+-----------+----------------------------------------------------------------------------------+---------+---------+
| Parameter | Description                                                                      | Range   | Default |
+===========+==================================================================================+=========+=========+
| priority  | Sytem priority used by the node on this LAG interface. Lower value is higher     | 0-65535 | \-      |
|           | priority for determining which node is the controlling system.                   |         |         |
+-----------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# lacp
    dnRouter(cfg-protocols-lacp)# interface bundle-2
    dnRouter(cfg-protocols-lacp-if)# priority 10
    dnRouter(cfg-protocols-lacp-if)#


**Removing Configuration**

To revert the priority to the global value:
::

    dnRouter(cfg-protocols-lacp-if)# no priority

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
