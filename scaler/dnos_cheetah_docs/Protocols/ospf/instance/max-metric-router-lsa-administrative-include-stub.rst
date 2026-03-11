protocols ospf instance max-metric router-lsa administrative include-stub
-------------------------------------------------------------------------

**Minimum user role:** operator

The OSPF process describes its transit links in its router-LSA as having infinite distance so that other routers will avoid calculating transit paths through the router while still being able to reach networks through the router.
To configure the OSPF protocol to advertise a router-LSA with a maximum metric value (65535) on system startup for all links for the configured time interval:

**Command syntax: max-metric router-lsa administrative include-stub**

**Command mode:** config

**Hierarchies**

- protocols ospf instance

**Note**

- The 'include-stub' option is used to advertise stub-links in router-LSA with the max-metric value.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# max-metric router-lsa administrative include-stub


**Removing Configuration**

To stop the automatic max-metric advertisement:
::

    dnRouter(cfg-protocols-ospf)# no max-metric router-lsa administrative

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
