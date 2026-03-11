system cprl ospf
----------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the OSPF protocol:

**Command syntax: ospf**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# ospf
    dnRouter(cfg-system-cprl-ospf)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the OSPF protocol:
::

    dnRouter(cfg-system-cprl)# no ospf

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
