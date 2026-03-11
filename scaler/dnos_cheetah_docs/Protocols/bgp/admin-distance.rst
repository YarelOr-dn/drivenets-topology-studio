protocols bgp administrative-distance
-------------------------------------

**Minimum user role:** operator

If a router learns of a destination from more than one routing protocol, the administrative distance is compared and the preference is given to the routes with lower administrative distance.

To change the BGP administrative distance for all routes:

**Command syntax: administrative-distance {external [external-route-distance], internal [internal-route-distance], local [local-route-distance]}**

**Command mode:** config

**Hierarchies**

- protocols bgp
- network-services vrf instance protocols bgp

**Note**

- An administrative-distance of 255 will cause the router to remove the route from the routing table.

**Parameter table**

+-------------------------+----------------------------------------------------------------------+-------+---------+
| Parameter               | Description                                                          | Range | Default |
+=========================+======================================================================+=======+=========+
| external-route-distance | Administrative distance for routes learned from external BGP (eBGP). | 1-255 | 20      |
+-------------------------+----------------------------------------------------------------------+-------+---------+
| internal-route-distance | Administrative distance for routes learned from internal BGP (iBGP). | 1-255 | 200     |
+-------------------------+----------------------------------------------------------------------+-------+---------+
| local-route-distance    | Administrative distance for routes learned from local peers          | 1-255 | 110     |
+-------------------------+----------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# administrative-distance external 120 internal 200 local 150
    dnRouter(cfg-protocols-bgp)# administrative-distance local 60


**Removing Configuration**

To revert all distances to their default value:
::

    dnRouter(cfg-protocols-bgp)# no administrative-distance

To revert a specific distance to its default value:
::

    dnRouter(cfg-protocols-bgp)# no administrative-distance local

**Command History**

+---------+-----------------------------------------------------+
| Release | Modification                                        |
+=========+=====================================================+
| 6.0     | Command introduced                                  |
+---------+-----------------------------------------------------+
| 15.1    | Updated command syntax from admin to administrative |
+---------+-----------------------------------------------------+
