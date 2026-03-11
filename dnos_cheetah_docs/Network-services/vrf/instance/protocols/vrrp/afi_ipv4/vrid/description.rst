network-services vrf instance protocols vrrp interface address-family ipv4 vrid description
-------------------------------------------------------------------------------------------

**Minimum user role:** operator

To set a description for the VRRP group:

**Command syntax: description [description]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols vrrp interface address-family ipv4 vrid
- protocols vrrp interface address-family ipv4 vrid

**Parameter table**

+-------------+------------------------+------------------+---------+
| Parameter   | Description            | Range            | Default |
+=============+========================+==================+=========+
| description | VRRP group description | | string         | \-      |
|             |                        | | length 1-255   |         |
+-------------+------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# vrrp interface ge100-0/0/0
    dnRouter(cfg-protocols-vrrp-ge100-0/0/0)# address-family ipv4
    dnRouter(cfg-vrrp-ge100-0/0/0-afi)# vrid 1
    dnRouter(cfg-vrrp-ge100-0/0/0-afi-vrid)# description MyFirstVirtual_Router-1


**Removing Configuration**

To remove the description:
::

    dnRouter(cfg-vrrp-ge100-0/0/0-afi-vrid)# no description

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
