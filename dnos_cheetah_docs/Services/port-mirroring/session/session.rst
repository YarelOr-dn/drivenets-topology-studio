services port-mirroring session
-------------------------------

**Minimum user role:** operator

A port-mirroring session can be used to replicate traffic from given interfaces for the purpose of debugging, security or performance monitoring.

To configure a new port-mirroring session:

**Command syntax: session [port-mirroring-session]**

**Command mode:** config

**Hierarchies**

- services port-mirroring

**Parameter table**

+------------------------+-----------------------------+------------------+---------+
| Parameter              | Description                 | Range            | Default |
+========================+=============================+==================+=========+
| port-mirroring-session | Port mirroring session name | | string         | \-      |
|                        |                             | | length 1-255   |         |
+------------------------+-----------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# port-mirroring
    dnRouter(cfg-srv-port-mirroring)# session IDS-Debug


**Removing Configuration**

To remove a specific session:
::

    dnRouter(cfg-srv-port-mirroring)# no session IDS-Debug

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
