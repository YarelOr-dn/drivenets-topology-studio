protocols ospf instance area nssa translate-type7-always
--------------------------------------------------------

**Minimum user role:** operator

When acting as an ABR, the router should always support type 7 to type 5 LSA translation, regardless of the translator election logic.

**Command syntax: translate-type7-always**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area nssa

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# instance 1
    dnRouter(cfg-protocols-ospf-inst)# area 2
    dnRouter(cfg-ospf-inst-area)# nssa
    dnRouter(cfg-inst-area-nssa)# admin-state enabled
    dnRouter(cfg-inst-area-nssa)# translate-type7-always
    dnRouter(ccfg-inst-area-nssa)#


**Removing Configuration**

To return the translate-type7-always to its default value: 
::

    dnRouter(cfg-ospf-area-nssa)# no translate-type7-always

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
