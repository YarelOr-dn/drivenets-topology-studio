system utilization node-type fd
-------------------------------

**Minimum user role:** operator

Enter the resource utilization file-descriptors related threshold configuration options.

To configure resource utilization file descriptors parameters:


**Command syntax: fd**

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
    dnRouter(cfg-system-util-ncp)# fd
    dnRouter(cfg-system-util-ncp-fd)#


**Removing Configuration**

Remove all configured thresholds
::

    dnRouter(cfg-system-util-ncp-fd)#

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
