qos traffic-class-map qos-tag
-----------------------------

**Minimum user role:** operator

To Configure QoS tag match criteria:

**Command syntax: qos-tag [qos-tag]** [, qos-tag, qos-tag]

**Command mode:** config

**Hierarchies**

- qos traffic-class-map

**Parameter table**

+-----------+------------------------+-------+---------+
| Parameter | Description            | Range | Default |
+===========+========================+=======+=========+
| qos-tag   | QoS-tag priority level | 0-7   | \-      |
+-----------+------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# traffic-class-map MyTrafficClass1
    dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# qos-tag 1,3,5


**Removing Configuration**

To remove the qos-tag from the traffic-class-map:
::

    dnRouter(cfg-traffic-class-map-MyTrafficClass1)# no qos-tag

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.2    | Command introduced |
+---------+--------------------+
