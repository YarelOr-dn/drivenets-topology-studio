network-services vrf instance protocols vrrp interface address-family ipv6
--------------------------------------------------------------------------

**Minimum user role:** operator

To enter the VRRP IPv6 address-family configuration on the interface:

**Command syntax: address-family ipv6**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols vrrp interface
- protocols vrrp interface

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols vrrp
    dnRouter(cfg-protocols-vrrp)# interface ge100-0/0/0
    dnRouter(cfg-protocols-vrrp-ge100-0/0/0)# address-family ipv6
    dnRouter(cfg-vrrp-ge100-0/0/0-afi)#


**Removing Configuration**

To remove the address-family configuration:
::

    dnRouter(cfg-protocols-vrrp-ge100-0/0/0)# no address-family ipv6

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
