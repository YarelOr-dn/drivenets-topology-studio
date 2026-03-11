system cprl https
-----------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the HTTPS protocol:

**Command syntax: https**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# https
    dnRouter(cfg-system-cprl-https)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the HTTPS protocol:
::

    dnRouter(cfg-system-cprl)# no https

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
