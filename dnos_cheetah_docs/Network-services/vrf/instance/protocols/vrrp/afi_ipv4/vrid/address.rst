network-services vrf instance protocols vrrp interface address-family ipv4 vrid address
---------------------------------------------------------------------------------------

**Minimum user role:** operator

To configure virtual IP addresses for the VRRP group:

**Command syntax: address [ip-address]** [, ip-address, ip-address]

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols vrrp interface address-family ipv4 vrid
- protocols vrrp interface address-family ipv4 vrid

**Note**

- Both IPv4 and IPv6 prefixes are supported, but cannot be mixed in the same group.

- For IPv6 address family IPv6 link local address is auto-generated, configuration applies to IPv6 global unicast addresses

**Parameter table**

+------------+---------------------------------------------------+--------------+---------+
| Parameter  | Description                                       | Range        | Default |
+============+===================================================+==============+=========+
| ip-address | Configure virtual IP addresses for the VRRP group | | A.B.C.D    | \-      |
|            |                                                   | | X:X::X:X   |         |
+------------+---------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# vrrp interface ge100-0/0/0
    dnRouter(cfg-protocols-vrrp-ge100-0/0/0)# address-family ipv4
    dnRouter(cfg-vrrp-ge100-0/0/0-afi)# vrid 1
    dnRouter(cfg-vrrp-ge100-0/0/0-afi-vrid)# address 200.10.10.6/32

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# vrrp interface ge100-0/0/0
    dnRouter(cfg-protocols-vrrp-ge100-0/0/0)# address-family ipv4
    dnRouter(cfg-vrrp-ge100-0/0/0-afi)# vrid 1
    dnRouter(cfg-vrrp-ge100-0/0/0-afi-vrid)# address 200.10.10.6/32, 200.10.20.6/32


**Removing Configuration**

To remove all virtual IP addresses from the VRRP group:
::

    dnRouter(cfg-vrrp-ge100-0/0/0-afi-vrid)# no address

To remove a specific virtual IP address from the VRRP group:
::

    dnRouter(cfg-vrrp-ge100-0/0/0-afi-vrid)# no address 200.10.10.6/32

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
