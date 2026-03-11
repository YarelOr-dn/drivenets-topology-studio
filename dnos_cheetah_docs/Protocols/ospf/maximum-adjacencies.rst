protocols ospf maximum-adjacencies
----------------------------------

**Minimum user role:** operator

You can use the following command to configure the OSPF maximum adjacencies and threshold limit.

**Command syntax: maximum-adjacencies [maximum]** threshold [threshold]

**Command mode:** config

**Hierarchies**

- protocols ospf

**Note**

- When the threshold is crossed, a single system-event OSPF_MAXIMUM_ADJACENCIES_THRESHOLD_EXCEEDED notification is generated.

- When the threshold is cleared, a single system-event OSPF_MAXIMUM_ADJACENCIES_THRESHOLD_CLEARED notification is generated.

- When the maximum threshold is crossed, a system-event OSPF_MAXIMUM_ADJACENCIES_LIMIT_REACHED notification is generated.

- When the maximum threshold is cleared, a single system-event OSPF_MAXIMUM_ADJACENCIES_LIMIT_CLEARED notification is generated.

**Parameter table**

+-----------+-----------------------------------------------------------+---------+---------+
| Parameter | Description                                               | Range   | Default |
+===========+===========================================================+=========+=========+
| maximum   | maximum number of adjacencies.                            | 1-65535 | 500     |
+-----------+-----------------------------------------------------------+---------+---------+
| threshold | threshold as a percentage of maximum allowed adjacencies. | 1-100   | 75      |
+-----------+-----------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# maximum-adjacencies 433
    dnRouter(cfg-protocols-ospf)# maximum-adjacencies 433 threshold 65


**Removing Configuration**

To return the maximum and threshold to their default values: 
::

    dnRouter(cfg-protocols-ospf)# no maximum-adjacencies

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+
