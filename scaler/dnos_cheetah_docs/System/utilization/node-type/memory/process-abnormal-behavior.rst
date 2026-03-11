system utilization node-type memory process process-abnormal-behavior
---------------------------------------------------------------------

**Minimum user role:** operator

"Disable the triggering memory abnormal events  for this process."


**Command syntax: process-abnormal-behavior [process-abnormal-behavior]**

**Command mode:** config

**Hierarchies**

- system utilization node-type memory process

**Parameter table**

+---------------------------+------------------------+--------------+---------+
| Parameter                 | Description            | Range        | Default |
+===========================+========================+==============+=========+
| process-abnormal-behavior | Disable process alerts | | enabled    | enabled |
|                           |                        | | disabled   |         |
+---------------------------+------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# utilization
    dnRouter(cfg-system-util)# node-type ncp
    dnRouter(cfg-system-util-ncp)# memory
    dnRouter(cfg-system-util-ncp-memory)# proc bgpd
    dnRouter(cfg-system-util-ncp-memory-bgp)# process-abnormal-behavior disabled


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-system-util-ncp-memory-bgp)# no process-abnormal-behavior

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
