protocols ospf instance area stub no-summary
--------------------------------------------

**Minimum user role:** operator

When a given area is stub and the area is set with a "no-summary" option, the ABR will prevent propagation of the inter-area routes (LSA type 3) into the area.

This will result in the area becoming totally-stub.

**Command syntax: no-summary**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area stub

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# instance 1
    dnRouter(cfg-protocols-ospf-inst)# area 1
    dnRouter(cfg-ospf-inst-area)# stub
    dnRouter(cfg-inst-area-stub)# no-summary
    dnRouter(cfg-inst-area-stub)#


**Removing Configuration**

To return the no-summary to its default value: 
::

    dnRouter(cfg-inst-area-stub)# no no-summary

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
