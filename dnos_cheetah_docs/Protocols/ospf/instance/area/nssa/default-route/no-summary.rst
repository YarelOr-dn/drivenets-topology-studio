protocols ospf instance area nssa default-route no-summary
----------------------------------------------------------

**Minimum user role:** operator

When a given area is NSSA and the inter-area default-route is desired, the user can set the area with  a "no-summary" option.

When set, the ABR will prevent propagation of inter-area routes (LSA type 3) into the area.

This will result in the area becoming totally-nssa.

**Command syntax: no-summary**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area nssa default-route

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# instance 2
    dnRouter(cfg-protocols-ospf-inst)# area 1
    dnRouter(cfg-ospf-inst-area)# nssa
    dnRouter(cfg-inst-area-nssa)# default-route
    dnRouter(cfg-area-nssa-default-route)# admin-state enabled
    dnRouter(cfg-area-nssa-default-route)# no-summary
    dnRouter(cfg-area-nssa-default-route)#


**Removing Configuration**

To return the no-summary to its default value: 
::

    dnRouter(cfg-area-nssa-default-route)# no no-summary

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
