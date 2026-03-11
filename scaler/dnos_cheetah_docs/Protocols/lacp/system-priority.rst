protocols lacp system-priority
------------------------------

**Minimum user role:** operator

The significant Part of LACP system identifier (2 bytes), Priority for the system.
A lower value is higher priority.

The actor with the higher priority is the master after negotiation with other systems.

**Command syntax: system-priority [system-priority]**

**Command mode:** config

**Hierarchies**

- protocols lacp

**Parameter table**

+-----------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter       | Description                                                                      | Range   | Default |
+=================+==================================================================================+=========+=========+
| system-priority | Sytem priority used by the node on this LAG interface. Lower value is higher     | 0-65535 | 1       |
|                 | priority for determining which node is the controlling system.                   |         |         |
+-----------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# lacp
    dnRouter(cfg-protocols-lacp)# system-priority 10


**Removing Configuration**

To revert the priority to the default value:
::

    dnRouter(cfg-protocols-lacp)# no system-priority

**Command History**

+---------+--------------------------+
| Release | Modification             |
+=========+==========================+
| 6.0     | Command introduced       |
+---------+--------------------------+
| 9.0     | Updated priority default |
+---------+--------------------------+
