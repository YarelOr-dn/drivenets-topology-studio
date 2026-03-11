system utilization node-type memory process
-------------------------------------------

**Minimum user role:** operator

"Configure the specific process memory resource utilization threshold per node type."


**Command syntax: process [process]**

**Command mode:** config

**Hierarchies**

- system utilization node-type memory

**Parameter table**

+-----------+--------------+------------------+---------+
| Parameter | Description  | Range            | Default |
+===========+==============+==================+=========+
| process   | Process name | | string         | \-      |
|           |              | | length 1-255   |         |
+-----------+--------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# utilization
    dnRouter(cfg-system-util)# node-type ncp
    dnRouter(cfg-system-util-ncp)# memory
    dnRouter(cfg-system-util-ncp-memory)# process bgpd
    dnRouter(cfg-system-util-ncp-memory-bgpd)#


**Removing Configuration**

To remove specific process threshold
::

    dnRouter(cfg-system-util-ncp-memory) no bgpd

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
