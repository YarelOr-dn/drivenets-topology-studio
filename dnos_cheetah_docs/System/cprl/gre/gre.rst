system cprl gre
---------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the GRE protocol:

**Command syntax: gre**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# gre
    dnRouter(cfg-system-cprl-gre)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the GRE protocol:
::

    dnRouter(cfg-system-cprl)# no gre

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
