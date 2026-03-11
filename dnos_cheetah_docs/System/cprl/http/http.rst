system cprl http
----------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the HTTP protocol:

**Command syntax: http**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# http
    dnRouter(cfg-system-cprl-http)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the HTTP protocol:
::

    dnRouter(cfg-system-cprl)# no http

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
