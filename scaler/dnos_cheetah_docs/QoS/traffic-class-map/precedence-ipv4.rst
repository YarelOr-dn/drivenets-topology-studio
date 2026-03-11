qos traffic-class-map precedence-ipv4
-------------------------------------

**Minimum user role:** operator

To configure IP precedence-ipv4 bits match criteria:

**Command syntax: precedence-ipv4 [precedence-ipv4]** [, precedence-ipv4, precedence-ipv4]

**Command mode:** config

**Hierarchies**

- qos traffic-class-map

**Parameter table**

+-----------------+------------------------------+-------+---------+
| Parameter       | Description                  | Range | Default |
+=================+==============================+=======+=========+
| precedence-ipv4 | Match IP precedence for IPv4 | 0-7   | \-      |
+-----------------+------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# traffic-class-map MyTrafficClass1
    dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# precedence-ipv4 1,3,5


**Removing Configuration**

To remove the precedence-ipv4 from the traffic-class-map:
::

    dnRouter(cfg-traffic-class-map-MyTrafficClass1)# no precedence-ipv4

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
