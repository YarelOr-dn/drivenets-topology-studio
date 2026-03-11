protocols vrrp interface address-family ipv4 vrid admin-state
-------------------------------------------------------------

**Minimum user role:** operator

To set the administrative state of the VRRP group:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols vrrp interface address-family ipv4 vrid
- network-services vrf instance protocols vrrp interface address-family ipv4 vrid

**Parameter table**

+-------------+------------------------+--------------+---------+
| Parameter   | Description            | Range        | Default |
+=============+========================+==============+=========+
| admin-state | VRRP group admin-state | | enabled    | enabled |
|             |                        | | disabled   |         |
+-------------+------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# vrrp interface ge100-0/0/0
    dnRouter(cfg-protocols-vrrp-ge100-0/0/0)# address-family ipv4
    dnRouter(cfg-vrrp-ge100-0/0/0-afi)# vrid 1
    dnRouter(cfg-vrrp-ge100-0/0/0-afi-vrid)# admin-state enabled


**Removing Configuration**

To return the admin-state to its default value:
::

    dnRouter(cfg-vrrp-ge100-0/0/0-afi-vrid)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
