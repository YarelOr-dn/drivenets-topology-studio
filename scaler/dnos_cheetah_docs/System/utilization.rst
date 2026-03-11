system utilization
------------------

**Minimum user role:** operator

Enter the resource utilization related threshold configuration options.

To configure the resource utilization parameters:


**Command syntax: utilization**

**Command mode:** config

**Hierarchies**

- system

**Note**

- Notice the change in prompt.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# utilization
    dnRouter(cfg-system-util)#


**Removing Configuration**

Remove all configured thresholds
::

    dnRouter(cfg-system-util)# 

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
