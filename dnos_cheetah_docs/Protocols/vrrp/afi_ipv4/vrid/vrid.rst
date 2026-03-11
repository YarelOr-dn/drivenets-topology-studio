protocols vrrp interface address-family ipv4 vrid
-------------------------------------------------

**Minimum user role:** operator

To configure a VRRP group and enter its configuration hierarchy:

**Command syntax: vrid [virtual-router-id]**

**Command mode:** config

**Hierarchies**

- protocols vrrp interface address-family ipv4
- network-services vrf instance protocols vrrp interface address-family ipv4

**Parameter table**

+-------------------+-----------------------------------------------------------------+-------+---------+
| Parameter         | Description                                                     | Range | Default |
+===================+=================================================================+=======+=========+
| virtual-router-id | References the configured virtual router id for this VRRP group | 1-255 | \-      |
+-------------------+-----------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# vrrp interface ge100-0/0/0
    dnRouter(cfg-protocols-vrrp-ge100-0/0/0)# address-family ipv4
    dnRouter(cfg-vrrp-ge100-0/0/0-afi)# vrid 1
    dnRouter(cfg-vrrp-ge100-0/0/0-afi-vrid)#

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# vrrp interface ge100-0/0/0
    dnRouter(cfg-protocols-vrrp-ge100-0/0/0)# address-family ipv6
    dnRouter(cfg-vrrp-ge100-0/0/0-afi)# vrid 1
    dnRouter(cfg-vrrp-ge100-0/0/0-afi-vrid)#


**Removing Configuration**

To remove the VRRP group configuration:
::

    dnRouter(cfg-vrrp-ge100-0/0/0-afi)# no vrid 1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
