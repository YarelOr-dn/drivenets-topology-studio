protocols ospf instance area nssa no-redistribution
---------------------------------------------------

**Minimum user role:** operator

When acting as an ASBR, prevent advertising redistributed routes into the NSSA area.
i.e prevent LSA type 7 advertisments.

**Command syntax: no-redistribution**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area nssa

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# instance 2
    dnRouter(cfg-protocols-ospf-inst)# area 3
    dnRouter(cfg-ospf-inst-area)# nssa
    dnRouter(cfg-inst-area-nssa)# no-redistribution
    dnRouter(cfg-inst-area-nssa)#


**Removing Configuration**

To return the nssa no-redistribution to its default value: 
::

    dnRouter(cfg-ospf-area-nssa)# no no-redistribution

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
