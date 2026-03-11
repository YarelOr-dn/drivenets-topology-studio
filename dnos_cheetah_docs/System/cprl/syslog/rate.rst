system cprl syslog rate
-----------------------

**Minimum user role:** operator

To set the rate limit of control traffic for the Syslog protocol:

**Command syntax: rate [rate-limit]**

**Command mode:** config

**Hierarchies**

- system cprl syslog

**Parameter table**

+------------+-----------------------------------------------------------+------------+---------+
| Parameter  | Description                                               | Range      | Default |
+============+===========================================================+============+=========+
| rate-limit | Rate limit for specific control protocol traffic in [pps] | 0-67108863 | 110     |
+------------+-----------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# syslog
    dnRouter(cfg-system-cprl-syslog)# rate 1000


**Removing Configuration**

To revert to the default CPRL rate value for the Syslog protocol:
::

    dnRouter(cfg-system-cprl-syslog)# no rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
