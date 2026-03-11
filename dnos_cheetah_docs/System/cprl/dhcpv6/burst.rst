system cprl dhcpv6 burst
------------------------

**Minimum user role:** operator

To set the burst limit of control traffic for the IPv6 DHCP protocol:

**Command syntax: burst [burst-size]**

**Command mode:** config

**Hierarchies**

- system cprl dhcpv6

**Parameter table**

+------------+---------------------------------------------------------------+---------+---------+
| Parameter  | Description                                                   | Range   | Default |
+============+===============================================================+=========+=========+
| burst-size | Burst size for specific control protocol traffic in [packets] | 2-65024 | 500     |
+------------+---------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# dhcpv6
    dnRouter(cfg-system-cprl-dhcpv6)# burst 1000


**Removing Configuration**

To revert to the default CPRL burst value for the IPv6 DHCP protocol:
::

    dnRouter(cfg-system-cprl-dns)# no burst

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
