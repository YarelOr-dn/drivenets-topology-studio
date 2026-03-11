protocols ospfv3 max-metric router-lsa on-startup external-lsa
--------------------------------------------------------------

**Minimum user role:** operator

If a router learns about a destination from more than one routing protocol, administrative distance is compared and the preference is given to the routes with lower administrative distance.

To change the OSPF administrative distance for all routes:

**Command syntax: max-metric router-lsa on-startup external-lsa** external-lsa-metric [external-lsa-metric]

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Note**

- The 'external-lsa' option is used to override the external-LSA metric with the max-metric value or with the [external-lsa] metric value.

**Parameter table**

+---------------------+---------------------------------------+------------+----------+
| Parameter           | Description                           | Range      | Default  |
+=====================+=======================================+============+==========+
| external-lsa-metric | The external-lsa metric to advertise. | 1-16777215 | 16711680 |
+---------------------+---------------------------------------+------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# max-metric router-lsa on-startup external-lsa external-lsa-metric 120000


**Removing Configuration**

To stop the automatic max-metric advertisement and return the interval to its default value:
::

    dnRouter(cfg-protocols-ospfv3)# no max-metric router-lsa on-startup external-lsa

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
