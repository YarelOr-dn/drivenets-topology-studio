system utilization node-type memory process warning-threshold
-------------------------------------------------------------

**Minimum user role:** operator

"Configure the warning level memory utilization threshold of a specific process per node type in MBytes."


**Command syntax: warning-threshold [warning-threshold]**

**Command mode:** config

**Hierarchies**

- system utilization node-type memory process

**Parameter table**

+-------------------+--------------------------------------------------------+--------------+---------+
| Parameter         | Description                                            | Range        | Default |
+===================+========================================================+==============+=========+
| warning-threshold | Memory utilization per process warning level threshold | 0-4294967295 | \-      |
+-------------------+--------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# utilization
    dnRouter(cfg-system-util)# node-type ncp
    dnRouter(cfg-system-util-ncp)# memory
    dnRouter(cfg-system-util-ncp-memory)# proc bgpd
    dnRouter(cfg-system-util-ncp-memory-bgpd)# warning-threshold 34


**Removing Configuration**

To remove specific process threshold
::

    dnRouter(cfg-system-util-ncp-memory-bgpd) no warning-threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
