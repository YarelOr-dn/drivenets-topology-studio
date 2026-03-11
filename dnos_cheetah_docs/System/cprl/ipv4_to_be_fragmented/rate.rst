system cprl ipv4-to-be-fragmented rate
--------------------------------------

**Minimum user role:** operator

To set the rate limit of control traffic for the IPv4-to-be-fragmented protocol:

**Command syntax: rate [rate-limit]**

**Command mode:** config

**Hierarchies**

- system cprl ipv4-to-be-fragmented

**Parameter table**

+------------+-----------------------------------------------------------+------------+---------+
| Parameter  | Description                                               | Range      | Default |
+============+===========================================================+============+=========+
| rate-limit | Rate limit for specific control protocol traffic in [pps] | 0-67108863 | 1000    |
+------------+-----------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# ipv4-to-be-fragmented
    dnRouter(cfg-system-cprl-ipv4-to-be-fragmented)# rate 1000


**Removing Configuration**

To revert to the default CPRL rate value for the IPv4-to-be-fragmented protocol:
::

    dnRouter(cfg-system-cprl-ipv4-to-be-fragmented)# no rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+
