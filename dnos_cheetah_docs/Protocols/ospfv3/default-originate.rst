protocols ospfv3 default-originate
----------------------------------

**Minimum user role:** operator

To force the router to generate an OSPFv3 AS-External (type-5) LSA, describing a default route into all external-routing capable areas, of the specified metric and metric type:

**Command syntax: default-originate** always metric [metric] metric-type [metric-type] policy [policy-name]

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Note**

- default-originate is disabled by default.

- no default-originate - disables default-information originate.

- no default-originate [attribute] - return attribute to default state.

**Parameter table**

+-------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter   | Description                                                                      | Range            | Default |
+=============+==================================================================================+==================+=========+
| always      | when true, the default is always advertised, even when there is no default       | Boolean          | False   |
|             | present in the routing table                                                     |                  |         |
+-------------+----------------------------------------------------------------------------------+------------------+---------+
| metric      | Used for generating the default route, this parameter specifies the cost for     | 0-16777214       | \-      |
|             | reaching the rest of the world through this route.                               |                  |         |
+-------------+----------------------------------------------------------------------------------+------------------+---------+
| metric-type | Specifies how the cost of a neighbor metric is determined                        | | 1              | 2       |
|             |                                                                                  | | 2              |         |
+-------------+----------------------------------------------------------------------------------+------------------+---------+
| policy-name | set routing policy                                                               | | string         | \-      |
|             |                                                                                  | | length 1-255   |         |
+-------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# default-originate
    dnRouter(cfg-protocols-ospfv3)# default-originate metric 10000
    dnRouter(cfg-protocols-ospfv3)# default-originate metric 10000 metric-type 2
    dnRouter(cfg-protocols-ospfv3)# default-originate metric 10000 metric-type 2 policy MY_POL
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# default-originate always
    dnRouter(cfg-protocols-ospfv3)# default-originate always metric 10000
    dnRouter(cfg-protocols-ospfv3)# default-originate always metric 10000 metric-type 2
    dnRouter(cfg-protocols-ospfv3)# default-originate metric-type 2 metric 3000 always
    dnRouter(cfg-protocols-ospfv3)# default-originate always metric 10000 metric-type 2 policy MY_POL  - dnRouter# configure


**Removing Configuration**

default-originate is disabled by default
::

    no default-originate - disables default-information originate

**Command History**

+---------+--------------------------+
| Release | Modification             |
+=========+==========================+
| 11.6    | Command introduced       |
+---------+--------------------------+
| 13.1    | Added support for OSPFv3 |
+---------+--------------------------+
