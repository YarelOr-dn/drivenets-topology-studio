protocols vrrp interface address-family ipv4 vrid tracking
----------------------------------------------------------

**Minimum user role:** operator

To enter VRRP objects tracking configuration hierarchy:

**Command syntax: tracking**

**Command mode:** config

**Hierarchies**

- protocols vrrp interface address-family ipv4 vrid
- network-services vrf instance protocols vrrp interface address-family ipv4 vrid

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# vrrp interface ge100-0/0/0
    dnRouter(cfg-protocols-vrrp-ge100-0/0/0)# address-family ipv4
    dnRouter(cfg-vrrp-ge100-0/0/0-afi)# vrid 1
    dnRouter(cfg-vrrp-ge100-0/0/0-afi-vrid)# tracking
    dnRouter(cfg-afi-vrid-tracking)#


**Removing Configuration**

To remove the objects tracking configuration from the VRRP group:
::

    dnRouter(cfg-vrrp-ge100-0/0/0-afi-vrid)# no tracking

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
