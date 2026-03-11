system cprl icmp rate
---------------------

**Minimum user role:** operator

To set the rate limit of control traffic for the ICMP protocol:

**Command syntax: rate [rate-limit]**

**Command mode:** config

**Hierarchies**

- system cprl icmp

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
    dnRouter(cfg-system-cprl)# icmp
    dnRouter(cfg-system-cprl-icmp)# rate 1000


**Removing Configuration**

To revert to the default CPRL rate value for the ICMP protocol:
::

    dnRouter(cfg-system-cprl-icmp)# no rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
