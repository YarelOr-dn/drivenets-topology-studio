system cprl is-is
-----------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the IS-IS protocol:

**Command syntax: is-is**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# is-is
    dnRouter(cfg-system-cprl-is-is)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the IS-IS protocol:
::

    dnRouter(cfg-system-cprl)# no is-is

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
