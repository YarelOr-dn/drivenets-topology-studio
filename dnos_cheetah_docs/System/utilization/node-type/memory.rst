system utilization node-type memory
-----------------------------------

**Minimum user role:** operator

Enter the resource utilization memory related threshold configuration options.

To configure the resource utilization memory parameters:


**Command syntax: memory**

**Command mode:** config

**Hierarchies**

- system utilization node-type

**Note**

- Notice the change in prompt.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# utilization
    dnRouter(cfg-system-util)# node-type ncp
    dnRouter(cfg-system-util-ncp)# memory
    dnRouter(cfg-system-util-ncp-memory)#


**Removing Configuration**

Remove all configured thresholds
::

    dnRouter(cfg-system-util-ncp-memory)# 

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
