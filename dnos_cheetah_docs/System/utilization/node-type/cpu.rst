system utilization node-type cpu
--------------------------------

**Minimum user role:** operator

Enter the resource utilization cpu related threshold configuration options.

To configure resource utilization cpu parameters:


**Command syntax: cpu**

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
    dnRouter(cfg-system-util-ncp)# cpu
    dnRouter(cfg-system-util-ncp-cpu)#


**Removing Configuration**

Remove all configured thresholds
::

    dnRouter(cfg-system-util-ncp-cpu)# 

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
