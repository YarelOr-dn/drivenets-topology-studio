system utilization node-type
----------------------------

**Minimum user role:** operator

Enter the node type for setting the resource utilization options.

To configure the node type for the resource utilization parameters:


**Command syntax: node-type [node-type]**

**Command mode:** config

**Hierarchies**

- system utilization

**Note**

- Notice the change in prompt.

**Parameter table**

+-----------+-------------+---------+---------+
| Parameter | Description | Range   | Default |
+===========+=============+=========+=========+
| node-type | Node type   | | ncc   | \-      |
|           |             | | ncp   |         |
|           |             | | ncf   |         |
+-----------+-------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# utilization
    dnRouter(cfg-system-util)# node-type ncp
    dnRouter(cfg-system-util-ncp)#


**Removing Configuration**

Not applicable
::

    dnRouter(cfg-system-util-ncp)# 

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
