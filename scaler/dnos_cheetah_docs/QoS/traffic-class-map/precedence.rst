qos traffic-class-map precedence
--------------------------------

**Minimum user role:** operator

To configure IP precedence bits match criteria:

**Command syntax: precedence [precedence]** [, precedence, precedence]

**Command mode:** config

**Hierarchies**

- qos traffic-class-map

**Parameter table**

+------------+---------------------+-------+---------+
| Parameter  | Description         | Range | Default |
+============+=====================+=======+=========+
| precedence | Match IP precedence | 0-7   | \-      |
+------------+---------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# traffic-class-map MyTrafficClass1
    dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# precedence 1,3,5


**Removing Configuration**

To remove the precedence from the traffic-class-map:
::

    dnRouter(cfg-traffic-class-map-MyTrafficClass1)# no precedence

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.2    | Command introduced |
+---------+--------------------+
