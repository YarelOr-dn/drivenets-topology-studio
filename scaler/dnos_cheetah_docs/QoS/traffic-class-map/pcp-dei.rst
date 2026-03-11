qos traffic-class-map pcp-dei
-----------------------------

**Minimum user role:** operator

To configure IEEE 802.1p Priority Code Point (PCP) and Drop Eligible Indicator (DEI) bits match criteria:

**Command syntax: pcp-dei [pcp-dei]** [, pcp-dei, pcp-dei]

**Command mode:** config

**Hierarchies**

- qos traffic-class-map

**Parameter table**

+-----------+--------------------------------------------------------------+-------+---------+
| Parameter | Description                                                  | Range | Default |
+===========+==============================================================+=======+=========+
| pcp-dei   | IEEE 802.1Q Priority Code Point and Drop eligible indicator. | 0-15  | \-      |
+-----------+--------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# traffic-class-map MyTrafficClass1
    dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# pcp-dei 1,3,5


**Removing Configuration**

To remove the pcp-dei from the traffic-class-map:
::

    dnRouter(cfg-traffic-class-map-MyTrafficClass1)# no pcp-dei

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.2    | Command introduced |
+---------+--------------------+
