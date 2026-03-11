system utilization node-type disk disk-util-threshold
-----------------------------------------------------

**Minimum user role:** operator

"To configure the disk utilization threshold:"


**Command syntax: disk-util-threshold [disk-util-threshold]**

**Command mode:** config

**Hierarchies**

- system utilization node-type disk

**Note**
- "The command is applicable to the platform disk utilization threshold."


**Parameter table**

+---------------------+-------------+-------+---------+
| Parameter           | Description | Range | Default |
+=====================+=============+=======+=========+
| disk-util-threshold | percentage  | 0-100 | 80      |
+---------------------+-------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# utilization
    dnRouter(cfg-system-util)# node-type ncp
    dnRouter(cfg-system-util-ncp)# disk
    dnRouter(cfg-system-util-ncp-disk)# disk-util-threshold 90


**Removing Configuration**

To set disk utilization threshold to default:
::

    dnRouter(cfg-system-util-ncp-disk)# no disk-util-threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
