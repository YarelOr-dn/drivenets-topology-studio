qos traffic-class-map pcp
-------------------------

**Minimum user role:** operator

To configure IEEE 802.1p Priority Code Point (PCP) bits match criteria:

**Command syntax: pcp [pcp]** [, pcp, pcp]

**Command mode:** config

**Hierarchies**

- qos traffic-class-map

**Parameter table**

+-----------+---------------------------------+-------+---------+
| Parameter | Description                     | Range | Default |
+===========+=================================+=======+=========+
| pcp       | IEEE 802.1Q Priority Code Point | 0-7   | \-      |
+-----------+---------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# traffic-class-map MyTrafficClass1
    dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# pcp 1,3,5


**Removing Configuration**

To remove the pcp from the traffic-class-map:
::

    dnRouter(cfg-traffic-class-map-MyTrafficClass1)# no pcp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.2    | Command introduced |
+---------+--------------------+
