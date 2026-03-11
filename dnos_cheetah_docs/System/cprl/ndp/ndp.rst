system cprl ndp
---------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the NDP protocol:

**Command syntax: ndp**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# ndp
    dnRouter(cfg-system-cprl-ndp)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the NDP protocol:
::

    dnRouter(cfg-system-cprl)# no ndp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
