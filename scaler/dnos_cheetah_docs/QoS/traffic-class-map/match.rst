qos traffic-class-map match
---------------------------

**Minimum user role:** operator

To configure the match type:

**Command syntax: match [match-type]**

**Command mode:** config

**Hierarchies**

- qos traffic-class-map

**Parameter table**

+------------+----------------------------------------------------+-------+---------+
| Parameter  | Description                                        | Range | Default |
+============+====================================================+=======+=========+
| match-type | Define how multiple match criteria will be handled | any   | any     |
+------------+----------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# traffic-class-map MyTrafficClass1
    dnRouter(cfg-traffic-class-map-MyTrafficClass1)# match any


**Removing Configuration**

To remove the match type from the traffic-class-map:
::

    dnRouter(cfg-traffic-class-map-MyTrafficClass1)# no match

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.2    | Command introduced |
+---------+--------------------+
