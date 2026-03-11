protocols ospfv3 max-metric router-lsa on-startup
-------------------------------------------------

**Minimum user role:** operator

The OSPF process describes its transit links in its router-LSA as having infinite distance so that other routers will avoid calculating transit paths through the router while still being able to reach networks through the router.
To configure the OSPF protocol to advertise a router-LSA with a maximum metric value (65535) on system startup for all links for the configured time interval:

**Command syntax: max-metric router-lsa on-startup**

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Note**

- This option is disabled by default.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# max-metric router-lsa on-startup
    dnRouter(cfg-protocols-ospfv3-mm-startup)#


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
