system cprl pim
---------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the PIM protocol:

**Command syntax: pim**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# pim
    dnRouter(cfg-system-cprl-pim)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the PIM protocol:
::

    dnRouter(cfg-system-cprl)# no pim

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
