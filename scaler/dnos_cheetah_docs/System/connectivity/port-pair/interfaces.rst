system connectivity port-pair interfaces
----------------------------------------

**Minimum user role:** operator

Command to map physical connection between ncs port and ncp port

**Command syntax: interfaces [ncs-port] [ncp-port]**

**Command mode:** config

**Hierarchies**

- system connectivity port-pair

**Parameter table**

+-----------+--------------------------------------+------------------+---------+
| Parameter | Description                          | Range            | Default |
+===========+======================================+==================+=========+
| ncs-port  | Gigabit port connected from NCS side | | string         | \-      |
|           |                                      | | length 1-255   |         |
+-----------+--------------------------------------+------------------+---------+
| ncp-port  | Gigabit port connected from NCP side | | string         | \-      |
|           |                                      | | length 1-255   |         |
+-----------+--------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# connectivity
    dnRouter(cfg-system-conn)# port-pair pp0
    dnRouter(cfg-system-conn-pp0)# interfaces sge100-0/0/0 ge100-0/0/0


**Removing Configuration**

To remove port mapping
::

    dnRouter(cfg-system-conn-pp0)# no interfaces sge100-0/0/0 ge100-0/0/0

**Command History**

+----------+--------------------+
| Release  | Modification       |
+==========+====================+
| 18.0.11  | Command introduced |
+----------+--------------------+
