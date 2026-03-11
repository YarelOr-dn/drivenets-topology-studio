system cprl ipv4-pmtud rate
---------------------------

**Minimum user role:** operator

To set the rate limit of control traffic for the IPv4 PMTUD protocol:

**Command syntax: rate [rate-limit]**

**Command mode:** config

**Hierarchies**

- system cprl ipv4-pmtud

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
    dnRouter(cfg-system-cprl)# ipv4-pmtud
    dnRouter(cfg-system-cprl-ipv4-pmtud)# rate 1000


**Removing Configuration**

To revert to the default CPRL rate value for the IPv4 PMTUD protocol:
::

    dnRouter(cfg-system-cprl-ipv4-pmtud)# no rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+
