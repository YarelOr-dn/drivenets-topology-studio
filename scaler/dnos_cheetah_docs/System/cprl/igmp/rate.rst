system cprl igmp rate
---------------------

**Minimum user role:** operator

To set the rate limit of control traffic for the IGMP protocol:

**Command syntax: rate [rate-limit]**

**Command mode:** config

**Hierarchies**

- system cprl igmp

**Parameter table**

+------------+-----------------------------------------------------------+------------+---------+
| Parameter  | Description                                               | Range      | Default |
+============+===========================================================+============+=========+
| rate-limit | Rate limit for specific control protocol traffic in [pps] | 0-67108863 | 300     |
+------------+-----------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# igmp
    dnRouter(cfg-system-cprl-igmp)# rate 1000


**Removing Configuration**

To revert to the default CPRL rate value for the IGMP protocol:
::

    dnRouter(cfg-system-cprl-igmp)# no rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
