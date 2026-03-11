protocols vrrp interface address-family ipv4
--------------------------------------------

**Minimum user role:** operator

To enter the VRRP IPv4 address-family configuration on the interface:

**Command syntax: address-family ipv4**

**Command mode:** config

**Hierarchies**

- protocols vrrp interface
- network-services vrf instance protocols vrrp interface

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# vrrp interface ge100-0/0/0
    dnRouter(cfg-protocols-vrrp-ge100-0/0/0)# address-family ipv4
    dnRouter(cfg-vrrp-ge100-0/0/0-afi)#


**Removing Configuration**

To remove the address-family configuration:
::

    dnRouter(cfg-protocols-vrrp-ge100-0/0/0)# no address-family ipv4

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
