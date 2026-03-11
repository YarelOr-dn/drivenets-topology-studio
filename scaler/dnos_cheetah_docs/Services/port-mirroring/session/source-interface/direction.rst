services port-mirroring session source-interface direction
----------------------------------------------------------

**Minimum user role:** operator

To configure source-interface direction:

**Command syntax: direction [direction]**

**Command mode:** config

**Hierarchies**

- services port-mirroring session source-interface

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-------------+---------+
| Parameter | Description                                                                      | Range       | Default |
+===========+==================================================================================+=============+=========+
| direction | replicated traffic direction of the source interface for the given port          | | ingress   | both    |
|           | mirroring session                                                                | | egress    |         |
|           |                                                                                  | | both      |         |
+-----------+----------------------------------------------------------------------------------+-------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# port-mirroring
    dnRouter(cfg-srv-port-mirroring)# session IDS-Debug
    dnRouter(cfg-srv-port-mirroring-session)# source-interface ge100-1/0/1
    dnRouter(cfg-srv-port-mirroring-session-src-interface)# direction ingress


**Removing Configuration**

To remove the specified source-interface from the list of monitored interfaces:
::

    dnRouter(cfg-srv-port-mirroring-session-src-interface)# no direction

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
