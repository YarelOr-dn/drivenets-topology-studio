qos traffic-class-map dscp
--------------------------

**Minimum user role:** operator

To Configure the traffic-class map dscp:

**Command syntax: dscp [dscp]**

**Command mode:** config

**Hierarchies**

- qos traffic-class-map

**Parameter table**

+-----------+-------------+-------+---------+
| Parameter | Description | Range | Default |
+===========+=============+=======+=========+
| dscp      | Match DSCP  | 0-63  | \-      |
+-----------+-------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# traffic-class-map MyTrafficClass1
    dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# dscp 10,12,14


**Removing Configuration**

To remove the dscp from the traffic-class-map:
::

    dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# no dscp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.2    | Command introduced |
+---------+--------------------+
