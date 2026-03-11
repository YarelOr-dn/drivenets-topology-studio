system cprl ip-options
----------------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for IP Options:

**Command syntax: ip-options**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# ip-options
    dnRouter(cfg-system-cprl-ip-options)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for IP Options:
::

    dnRouter(cfg-system-cprl)# no ip-options

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.4    | Command introduced |
+---------+--------------------+
