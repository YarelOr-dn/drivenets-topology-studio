system cprl ipv6-pmtud burst
----------------------------

**Minimum user role:** operator

To set the burst limit of control traffic for the IPv6 PMTUD protocol:

**Command syntax: burst [burst-size]**

**Command mode:** config

**Hierarchies**

- system cprl ipv6-pmtud

**Parameter table**

+------------+---------------------------------------------------------------+---------+---------+
| Parameter  | Description                                                   | Range   | Default |
+============+===============================================================+=========+=========+
| burst-size | Burst size for specific control protocol traffic in [packets] | 2-65024 | 1000    |
+------------+---------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# ipv6-pmtud
    dnRouter(cfg-system-cprl-ipv6-pmtud)# burst 1000


**Removing Configuration**

To revert to the default CPRL burst value for the IPv6 PMTUD protocol:
::

    dnRouter(cfg-system-cprl-ipv6-pmtud)# no burst

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+
