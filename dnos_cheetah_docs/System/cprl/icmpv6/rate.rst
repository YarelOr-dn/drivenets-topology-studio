system cprl icmpv6 rate
-----------------------

**Minimum user role:** operator

To set the rate limit of control traffic for the ICMPv6 protocol:

**Command syntax: rate [rate-limit]**

**Command mode:** config

**Hierarchies**

- system cprl icmpv6

**Parameter table**

+------------+-----------------------------------------------------------+------------+---------+
| Parameter  | Description                                               | Range      | Default |
+============+===========================================================+============+=========+
| rate-limit | Rate limit for specific control protocol traffic in [pps] | 0-67108863 | 250     |
+------------+-----------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# icmpv6
    dnRouter(cfg-system-cprl-icmpv6)# rate 1000


**Removing Configuration**

To revert to the default CPRL rate value for the ICMPv6 protocol:
::

    dnRouter(cfg-system-cprl-icmpv6)# no rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+
