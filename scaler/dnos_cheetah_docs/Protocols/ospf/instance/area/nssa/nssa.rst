protocols ospf instance area nssa
---------------------------------

**Minimum user role:** operator

DNOS supports participating in the OSPFv2 backbone area (Area 0), non-backbone areas (Other than area 0), backbone-area (Area 0, in multiple areas – acting as an area border router), and NSSa and stub areas. NSSA and stub are supported both for ABR roles and for non-ABR roles.

**Command syntax: nssa**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area

**Note**

- Configuration will be mutually exclusive (i.e setting one will cancel the other).

- A commit validation is required to ensure the stub/NSSA is set for the area not equal to 0 or 0.0.0.0.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# instance 1
    dnRouter(cfg-protocols-ospf-inst)# area 2
    dnRouter(cfg-ospf-inst-area)# nssa
    dnRouter(cfg-inst-area-nssa)# admin-state enabled
    dnRouter(cfg-inst-area-nssa)#


**Removing Configuration**

To revert all nssa configuration to default:
::

    dnRouter(cfg-ospf-inst-area)# no nssa

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
