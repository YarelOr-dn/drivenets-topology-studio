system cprl ttl-expired rate
----------------------------

**Minimum user role:** operator

To set the rate limit of control traffic for the TTL-expired protocol:

**Command syntax: rate [rate-limit]**

**Command mode:** config

**Hierarchies**

- system cprl ttl-expired

**Parameter table**

+------------+-----------------------------------------------------------+------------+---------+
| Parameter  | Description                                               | Range      | Default |
+============+===========================================================+============+=========+
| rate-limit | Rate limit for specific control protocol traffic in [pps] | 0-67108863 | 500     |
+------------+-----------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# ttl-expired
    dnRouter(cfg-system-cprl-ttl-expired)# rate 1000


**Removing Configuration**

To revert to the default CPRL rate value for the Telnet protocol:
::

    dnRouter(cfg-system-cprl-ttl-expired)# no rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.0    | Command introduced |
+---------+--------------------+
