qos traffic-class-map dscp-ipv4
-------------------------------

**Minimum user role:** operator

To Configure the traffic-class map dscp-ipv4:

**Command syntax: dscp-ipv4 [dscp-ipv4]**

**Command mode:** config

**Hierarchies**

- qos traffic-class-map

**Parameter table**

+-----------+---------------------+-------+---------+
| Parameter | Description         | Range | Default |
+===========+=====================+=======+=========+
| dscp-ipv4 | Match DSCP for IPv4 | 0-63  | \-      |
+-----------+---------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# traffic-class-map MyTrafficClass1
    dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# dscp-ipv4 10,12,14


**Removing Configuration**

To remove the dscp-ipv4 from the traffic-class-map:
::

    dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# no dscp-ipv4

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
