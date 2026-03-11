interfaces ipv6-address dhcpv6
------------------------------

**Minimum user role:** operator

To dynamically allocate an IPv6 address for an interface, use the following command:

**Command syntax: ipv6-address dhcpv6**

**Command mode:** config

**Hierarchies**

- interfaces

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# mgmt0
    dnRouter(cfg-if-mgmt0)# ipv6-address dhcpv6


**Removing Configuration**

To revert to default:
::

    dnRouter(cfg-if-mgmt0)# no ipv6-address

**Command History**

+---------+------------------------------------------------+
| Release | Modification                                   |
+=========+================================================+
| 11.0    | Command introduced                             |
+---------+------------------------------------------------+
| 13.1    | Changed dhcp with dhcpv6 in the command syntax |
+---------+------------------------------------------------+
| 16.2    | Management physical interfaces removed         |
+---------+------------------------------------------------+
| 19.1    | Added support for in-band network interfaces   |
+---------+------------------------------------------------+
