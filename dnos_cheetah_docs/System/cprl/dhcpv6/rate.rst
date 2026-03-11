system cprl dhcpv6 rate
-----------------------

**Minimum user role:** operator

To set the rate limit of control traffic for the IPv6 DHCP protocol:

**Command syntax: rate [rate-limit]**

**Command mode:** config

**Hierarchies**

- system cprl dhcpv6

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
    dnRouter(cfg-system-cprl)# dhcpv6
    dnRouter(cfg-system-cprl-dhcpv6)# rate 1000


**Removing Configuration**

To revert to the default CPRL rate value for the IPv6 DHCP protocol:
::

    dnRouter(cfg-system-cprl-dhcpv6)# no rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
