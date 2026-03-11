protocols ospf instance maximum-redistributed-prefixes
------------------------------------------------------

**Minimum user role:** operator

You can use the following command to configure the OSPF maximum redistributed prefixes limit and threshold limit. Scale is aggregated across all address-families. A single system-event notification is generated in the following cases:
•	When the threshold is crossed
•	When the threshold is cleared
•	When the maximum is reached (no further prefixes are redistributed and a system-event notification is generated)
•	When the redistributed prefixes decreases below the maximum.

**Command syntax: maximum-redistributed-prefixes [maximum]** threshold [threshold]

**Command mode:** config

**Hierarchies**

- protocols ospf instance

**Note**
The 'no maximum-redistributed-prefixes' returns the maximum and threshold to their default values.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+---------+---------+
| Parameter | Description                                                                      | Range   | Default |
+===========+==================================================================================+=========+=========+
| maximum   | maximum allowed number prefixes redistribute below which no more prefixes are    | 1-32000 | 10000   |
|           | allowed.                                                                         |         |         |
+-----------+----------------------------------------------------------------------------------+---------+---------+
| threshold | threshold as a percentage of system maximum allowed redistributed prefixes.      | 1-100   | 75      |
+-----------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# maximum-redistributed-prefixes 30000
    dnRouter(cfg-protocols-ospf)# maximum-redistributed-prefixes 30000 threshold 80


**Removing Configuration**

To return the maximum and threshold to their default values: 
::

    dnRouter(cfg-protocols-ospf)# no maximum-redistributed-prefixes

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+
