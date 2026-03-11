qos traffic-class-map mpls-exp
------------------------------

**Minimum user role:** operator

To configure the MPLS experimental bits match criteria:

**Command syntax: mpls-exp [mpls-exp]** [, mpls-exp, mpls-exp]

**Command mode:** config

**Hierarchies**

- qos traffic-class-map

**Parameter table**

+-----------+--------------------------+-------+---------+
| Parameter | Description              | Range | Default |
+===========+==========================+=======+=========+
| mpls-exp  | MPLS EXP bits (TC field) | 0-7   | \-      |
+-----------+--------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# traffic-class-map MyTrafficClass1
    dnRouter(cfg-qos-traffic-class-map-MyTrafficMap1)# mpls-exp 1,3,5


**Removing Configuration**

To remove the mpls-exp from the traffic-class-map:
::

    dnRouter(cfg-traffic-class-map-MyTrafficClass1)# no mpls-exp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.2    | Command introduced |
+---------+--------------------+
