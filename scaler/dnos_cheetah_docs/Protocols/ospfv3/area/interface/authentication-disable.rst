protocols ospfv3 area interface authentication disable
------------------------------------------------------

**Minimum user role:** operator

If OSPFv3 authentication is configured, you must set the OSPF authentication key to a cryptographic password for the interface.
To configure the interface authentication key:

**Command syntax: authentication disable**

**Command mode:** config

**Hierarchies**

- protocols ospfv3 area interface

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# area 0
    dnRouter(cfg-protocols-ospfv3-area)# interface ge100-2/1/1
    dnRouter(cfg-ospfv3-area-if)# authentication disabled

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# area 0
    dnRouter(cfg-protocols-ospfv3-area)# interface ge100-2/1/1
    dnRouter(cfg-ospfv3-area-if)# authentication disabled
    Enter password:
    Enter password for verification:


**Removing Configuration**

To remove the disable option on authentication requirement for OSPFv3 packets on the interface:
::

    dnRouter(cfg-ospfv3-area-if)# no authentication

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
