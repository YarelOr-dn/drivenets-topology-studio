network-services vrf instance protocols bgp neighbor-group address-family attribute-unchanged
---------------------------------------------------------------------------------------------

**Minimum user role:** operator

The following command enables BGP to send updates to eBGP peers with the attribute unchanged.

**Command syntax: attribute-unchanged** next-hop med as-path

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp neighbor-group address-family
- protocols bgp neighbor address-family
- protocols bgp neighbor-group address-family
- network-services vrf instance protocols bgp neighbor address-family

**Note**

- If you do not specify attributes, all attributes will remain unchanged.

- For flowspec SAFI, the next-hop attribute remains unchanged by default.

**Parameter table**

+-----------+--------------------+---------+---------+
| Parameter | Description        | Range   | Default |
+===========+====================+=========+=========+
| next-hop  | next-hop attribute | Boolean | False   |
+-----------+--------------------+---------+---------+
| med       | med attribute      | Boolean | False   |
+-----------+--------------------+---------+---------+
| as-path   | as-path attribute  | Boolean | False   |
+-----------+--------------------+---------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-bgp-neighbor-afi)# attribute-unchanged

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-bgp-neighbor-afi)# attribute-unchanged next-hop med

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv6-unicast
    dnRouter(cfg-bgp-neighbor-afi)# attribute-unchanged next-hop med as-path

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# address-family ipv4-unicast
    dnRouter(cfg-bgp-group-afi)# attribute-unchanged med

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# address-family ipv4-unicast
    dnRouter(cfg-bgp-group-afi)# attribute-unchanged as-path


**Removing Configuration**

To disable this option for all attributes:
::

    dnRouter(cfg-bgp-neighbor-afi)# no attribute-unchanged

::

    dnRouter(cfg-bgp-neighbor-afi)# no attribute-unchanged med next-hop

::

    dnRouter(cfg-protocols-bgp-group)# no attribute-unchanged med next-hop

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 6.0     | Command introduced               |
+---------+----------------------------------+
| 11.0    | Removed the as-path option       |
+---------+----------------------------------+
| 16.1    | Added support for multicast SAFI |
+---------+----------------------------------+
| 17.1    | Added as-path support            |
+---------+----------------------------------+
