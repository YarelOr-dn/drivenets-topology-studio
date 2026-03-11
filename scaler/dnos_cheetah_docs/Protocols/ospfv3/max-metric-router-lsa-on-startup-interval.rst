protocols ospfv3 max-metric router-lsa on-startup interval
----------------------------------------------------------

**Minimum user role:** operator

The OSPF process describes its transit links in its router-LSA as having infinite distance so that other routers will avoid calculating transit paths through the router while still being able to reach networks through the router.
To configure the OSPF protocol to advertise a router-LSA with a maximum metric value (65535) on system startup for all links for the configured time interval:

**Command syntax: max-metric router-lsa on-startup interval [interval]**

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Parameter table**

+-----------+------------------------------------------+---------+---------+
| Parameter | Description                              | Range   | Default |
+===========+==========================================+=========+=========+
| interval  | time in seconds for advertise on startup | 5-86400 | 600     |
+-----------+------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# max-metric router-lsa on-startup
    dnRouter(cfg-protocols-ospfv3-mm-startup)# interval 3600


**Removing Configuration**

To stop the automatic max-metric advertisement and return the interval to its default value:
::

    dnRouter(cfg-protocols-ospfv3)# no max-metric router-lsa on-startup

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
