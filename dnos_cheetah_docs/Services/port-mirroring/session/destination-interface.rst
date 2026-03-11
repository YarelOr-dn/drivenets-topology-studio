services port-mirroring session destination-interface
-----------------------------------------------------

**Minimum user role:** operator

You can configure the destination interfaces for a specific port-mirroring session.

To configure a destination interface for a port-mirroring session:

**Command syntax: destination-interface [destination-interface]**

**Command mode:** config

**Hierarchies**

- services port-mirroring session

**Note**
- The command is applicable to physical interfaces.

- A port-mirroring session can only have a single destination interface, which can only belong to one session.

**Parameter table**

+-----------------------+---------------------------------------------------------------------+------------------+---------+
| Parameter             | Description                                                         | Range            | Default |
+=======================+=====================================================================+==================+=========+
| destination-interface | a unique destination interface for the given port mirroring session | | string         | \-      |
|                       |                                                                     | | length 1-255   |         |
+-----------------------+---------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# port-mirroring
    dnRouter(cfg-srv-port-mirroring)# session IDS-Debug
    dnRouter(cfg-srv-port-mirroring-session)# destination-interface ge100-1/0/28


**Removing Configuration**

To remove the specified destination-interface from the list of monitored interfaces:
::

    dnRouter(cfg-srv-port-mirroring-session)# no destination-interface

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
