system cprl punted-ip-multicast rate
------------------------------------

**Minimum user role:** operator

To set the rate limit of control traffic for the Punted-IP-Multicast protocol:

**Command syntax: rate [rate-limit]**

**Command mode:** config

**Hierarchies**

- system cprl punted-ip-multicast

**Parameter table**

+------------+-----------------------------------------------------------+------------+---------+
| Parameter  | Description                                               | Range      | Default |
+============+===========================================================+============+=========+
| rate-limit | Rate limit for specific control protocol traffic in [pps] | 0-67108863 | 3000    |
+------------+-----------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# punted-ip-multicast
    dnRouter(cfg-system-cprl-punted-ip-multicast)# rate 1000


**Removing Configuration**

To revert to the default CPRL rate value for the Punted-IP-Multicast protocol:
::

    dnRouter(cfg-system-cprl-punted-ip-multicast)# no rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
