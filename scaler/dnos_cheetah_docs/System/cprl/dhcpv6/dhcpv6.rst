system cprl dhcpv6
------------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the IPv6 DHCP protocol:

**Command syntax: dhcpv6**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# dhcpv6
    dnRouter(cfg-system-cprl-dhcpv6)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the IPv6 DHCP protocol:
::

    dnRouter(cfg-system-cprl)# no dhcpv6

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
