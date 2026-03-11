system utilization node-type disk
---------------------------------

**Minimum user role:** operator

Enter the resource utilization storage disk related threshold configuration options.

To configure the resource utilization disk parameters:


**Command syntax: disk**

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
    dnRouter(cfg-system-util-ncp)# disk
    dnRouter(cfg-system-util-ncp-disk)#


**Removing Configuration**

Remove all configured thresholds
::

    dnRouter(cfg-system-util-ncp-disk)# 

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
