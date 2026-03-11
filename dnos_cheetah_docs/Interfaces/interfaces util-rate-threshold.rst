interfaces util-rate-threshold
------------------------------

**Minimum user role:** operator

To configure the interface bandwidth utilization rate threshold:

**Command syntax: util-rate-threshold [util-rate-threshold]**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to physical interfaces.
- Set threshold is applicable to both input and output directions independently.

**Parameter table**

+---------------------+-------------+-------+---------+
| Parameter           | Description | Range | Default |
+=====================+=============+=======+=========+
| util-rate-threshold | percentage  | 0-100 | 100     |
+---------------------+-------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge400-0/0/0
    dnRouter(cfg-if-ge400-0/0/0)# util-rate-threshold 90


**Removing Configuration**

To set interface utilization threshold rate to default:
::

    dnRouter(cfg-if-ge400-0/0/0)# no util-rate-threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
