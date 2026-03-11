system connectivity port-pair
-----------------------------

**Minimum user role:** operator

Command to map between internally connected ports in the cluster

**Command syntax: port-pair [port-pair]**

**Command mode:** config

**Hierarchies**

- system connectivity

**Parameter table**

+-----------+-----------------------+----------------+---------+
| Parameter | Description           | Range          | Default |
+===========+=======================+================+=========+
| port-pair | Name of the port-pair | | string       | \-      |
|           |                       | | length 1-8   |         |
+-----------+-----------------------+----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# connectivity
    dnRouter(cfg-system-conn)# port-pair pp0
    dnRouter(cfg-system-conn-pp0)#


**Removing Configuration**

To remove a specific port mapping:
::

    dnRouter(cfg-system-conn)# no port-pair pp0

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
