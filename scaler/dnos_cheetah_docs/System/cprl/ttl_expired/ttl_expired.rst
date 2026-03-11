system cprl ttl-expired
-----------------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the TTL-expired protocol:

**Command syntax: ttl-expired**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# ttl-expired
    dnRouter(cfg-system-cprl-ttl-expired)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the TTL-expired protocol:
::

    dnRouter(cfg-system-cprl)# no ttl-expired

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
