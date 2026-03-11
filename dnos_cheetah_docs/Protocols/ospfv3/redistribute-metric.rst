protocols ospfv3 redistribute-metric
------------------------------------

**Minimum user role:** operator

You can use the following command to configure the OSPFV3 maximum redistributed prefixes limit and threshold limit. Scale is aggregated across all address-families. A single system-event notification is generated in the following cases:

•	When the threshold is crossed
•	When the threshold is cleared
•	When the maximum is reached (no further prefixes are redistributed and a system-event notification is generated)
•	When the redistributed prefixes decreases below the maximum.

**Command syntax: redistribute-metric [redistribute-metric]**

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Note**

- No command returns metric to its default value.

**Parameter table**

+---------------------+-------------------------------------------------------------------------+------------+---------+
| Parameter           | Description                                                             | Range      | Default |
+=====================+=========================================================================+============+=========+
| redistribute-metric | Sets the default metric value for the OSPFv2 or OSPFv3 routing protocol | 0-16777214 | \-      |
+---------------------+-------------------------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# redistribute-metric 1


**Removing Configuration**

To return the metric to its default value: 
::

    dnRouter(cfg-protocols-ospfv3)# no redistribute-metric

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
