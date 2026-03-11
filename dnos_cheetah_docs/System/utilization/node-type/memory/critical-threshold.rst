system utilization node-type memory process critical-threshold
--------------------------------------------------------------

**Minimum user role:** operator

"Configure the critical level memory utilization threshold of a specific process per node type in MBytes."


**Command syntax: critical-threshold [critical-threshold]**

**Command mode:** config

**Hierarchies**

- system utilization node-type memory process

**Parameter table**

+--------------------+---------------------------------------------------------+--------------+---------+
| Parameter          | Description                                             | Range        | Default |
+====================+=========================================================+==============+=========+
| critical-threshold | Memory utilization per process critical level threshold | 0-4294967295 | \-      |
+--------------------+---------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# utilization
    dnRouter(cfg-system-util)# node-type ncp
    dnRouter(cfg-system-util-ncp)# memory
    dnRouter(cfg-system-util-ncp-memory)# proc bgpd
    dnRouter(cfg-system-util-ncp-memory-bgpd)# critical-threshold 34


**Removing Configuration**

To remove specific process threshold
::

    dnRouter(cfg-system-util-ncp-memory-bgpd) no critical-threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
