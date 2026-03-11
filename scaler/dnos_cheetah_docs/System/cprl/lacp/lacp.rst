system cprl lacp
----------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the LACP protocol:

**Command syntax: lacp**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# lacp
    dnRouter(cfg-system-cprl-lacp)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the LACP protocol:
::

    dnRouter(cfg-system-cprl)# no lacp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
