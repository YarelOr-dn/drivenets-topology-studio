system utilization node-type memory mem-util-threshold
------------------------------------------------------

**Minimum user role:** operator

"To configure the memory utilization rate threshold:"


**Command syntax: mem-util-threshold [mem-util-threshold]**

**Command mode:** config

**Hierarchies**

- system utilization node-type memory

**Note**
- "The command is applicable to the platform memory utilization threshold."


**Parameter table**

+--------------------+-------------+-------+---------+
| Parameter          | Description | Range | Default |
+====================+=============+=======+=========+
| mem-util-threshold | percentage  | 0-100 | 90      |
+--------------------+-------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# utilization
    dnRouter(cfg-system-util)# node-type ncp
    dnRouter(cfg-system-util-ncp)# memory
    dnRouter(cfg-system-util-ncp-memory)# mem-util-threshold 90


**Removing Configuration**

To set memory utilization rate threshold to default:
::

    dnRouter(cfg-system-util-ncp-memory)# no mem-util-threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
