system cprl all-hosts
---------------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for all hosts:

**Command syntax: all-hosts**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# all-hosts
    dnRouter(cfg-system-cprl-all-hosts)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for all hosts:
::

    dnRouter(cfg-system-cprl)# no all-hosts

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
