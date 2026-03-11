protocols ospf instance area stub
---------------------------------

**Minimum user role:** operator

To set an OSPFv2 area as a stub.

**Command syntax: stub**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area

**Note**

- For a given NON BACKBONE area the user will be able to set  the area as either stub or NSSA.

- Configuration will be mutually exclusive (i.e setting one will cancel the other).

- A commit validation is required to ensure the stub/NSSA is set for the area not equal to 0 or 0.0.0.0.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# instance 1
    dnRouter(cfg-protocols-ospf-inst)# area 2
    dnRouter(cfg-ospf-inst-area)# stub
    dnRouter(cfg-inst-area-stub)# admin-state enabled
    dnRouter(cfg-inst-area-stub)#


**Removing Configuration**

To revert all stub configuration to default:
::

    dnRouter(cfg-ospf-inst-area)# no stub

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
