system cprl ospfv3
------------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the OSPFv3 protocol:

**Command syntax: ospfv3**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# ospfv3
    dnRouter(cfg-system-cprl-ospfv3)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the OSPFv3 protocol:
::

    dnRouter(cfg-system-cprl)# no ospfv3

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
