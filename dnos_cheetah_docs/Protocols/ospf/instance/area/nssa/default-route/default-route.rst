protocols ospf instance area nssa default-route
-----------------------------------------------

**Minimum user role:** operator

When acting as an ABR for the NSSA area, by default the ABR will not advertise the inter-area default-route (LSA type 3).
The user can choose to advertise the inter-area default-route.

**Command syntax: default-route**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area nssa

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# instance 1
    dnRouter(cfg-ospf-area-inst)# area 2
    dnRouter(cfg-ospf-inst-area)# nssa
    dnRouter(cfg-inst-area-nssa)# default-route
    dnRouter(cfg-area-nssa-default-route)#


**Removing Configuration**

To revert all default-route configuration to default:
::

    dnRouter(cfg-inst-area-nssa)# no default-route

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
