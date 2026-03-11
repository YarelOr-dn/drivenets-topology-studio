system utilization node-type disk disk-write-bw-util-threshold
--------------------------------------------------------------

**Minimum user role:** operator

"To configure the disk max write bandwidth utilization threshold:"


**Command syntax: disk-write-bw-util-threshold [disk-write-bw-util-threshold]**

**Command mode:** config

**Hierarchies**

- system utilization node-type disk

**Note**
- "The command is applicable to the platform disk write bandwidth utilization threshold."


**Parameter table**

+------------------------------+-------------+-------+---------+
| Parameter                    | Description | Range | Default |
+==============================+=============+=======+=========+
| disk-write-bw-util-threshold | percentage  | 0-100 | 90      |
+------------------------------+-------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# utilization
    dnRouter(cfg-system-util)# node-type ncp
    dnRouter(cfg-system-util-ncp)# disk
    dnRouter(cfg-system-util-ncp-disk)# disk-write-bw-util-threshold 90


**Removing Configuration**

To set disk write bandwidth utilization threshold to default:
::

    dnRouter(cfg-system-util-ncp-disk)# no disk-write-bw-util-threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
