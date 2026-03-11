qos traffic-class-map precedence-ipv6
-------------------------------------

**Minimum user role:** operator

To configure IP precedence-ipv6 bits match criteria:

**Command syntax: precedence-ipv6 [precedence-ipv6]** [, precedence-ipv6, precedence-ipv6]

**Command mode:** config

**Hierarchies**

- qos traffic-class-map

**Parameter table**

+-----------------+------------------------------+-------+---------+
| Parameter       | Description                  | Range | Default |
+=================+==============================+=======+=========+
| precedence-ipv6 | Match IP precedence for IPv6 | 0-7   | \-      |
+-----------------+------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# traffic-class-map MyTrafficClass1
    dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# precedence-ipv6 1,3,5


**Removing Configuration**

To remove the precedence-ipv6 from the traffic-class-map:
::

    dnRouter(cfg-traffic-class-map-MyTrafficClass1)# no precedence-ipv6

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
