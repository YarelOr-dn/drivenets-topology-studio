qos traffic-class-map dscp-ipv6
-------------------------------

**Minimum user role:** operator

To Configure the traffic-class map dscp-ipv6:

**Command syntax: dscp-ipv6 [dscp-ipv6]**

**Command mode:** config

**Hierarchies**

- qos traffic-class-map

**Parameter table**

+-----------+---------------------+-------+---------+
| Parameter | Description         | Range | Default |
+===========+=====================+=======+=========+
| dscp-ipv6 | Match DSCP for IPv6 | 0-63  | \-      |
+-----------+---------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# traffic-class-map MyTrafficClass1
    dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# dscp-ipv6 10,12,14


**Removing Configuration**

To remove the dscp-ipv6 from the traffic-class-map:
::

    dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# no dscp-ipv6

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
