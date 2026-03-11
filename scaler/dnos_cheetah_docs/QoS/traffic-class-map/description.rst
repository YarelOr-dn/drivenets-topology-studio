qos traffic-class-map description
---------------------------------

**Minimum user role:** operator

To add a meaningful description for a traffic-class-map:

**Command syntax: description [descr]**

**Command mode:** config

**Hierarchies**

- qos traffic-class-map

**Parameter table**

+-----------+-------------------------------+------------------+---------+
| Parameter | Description                   | Range            | Default |
+===========+===============================+==================+=========+
| descr     | Traffic class map description | | string         | \-      |
|           |                               | | length 1-255   |         |
+-----------+-------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# traffic-class-map MyTrafficClass1
    dnRouter(cfg-traffic-class-map-MyTrafficClass1)# description "Emergency Traffic"


**Removing Configuration**

To remove the description from the traffic-class-map:
::

    dnRouter(cfg-traffic-class-map-MyTrafficClass1)# no description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.2    | Command introduced |
+---------+--------------------+
