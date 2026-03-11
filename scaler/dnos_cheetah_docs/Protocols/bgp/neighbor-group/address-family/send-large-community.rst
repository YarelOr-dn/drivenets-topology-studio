protocols bgp neighbor-group address-family send-large-community
----------------------------------------------------------------

**Minimum user role:** operator

The following command ensures that the large community attribute is sent in updates to the specified neighbor or group.

**Command syntax: send-large-community [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor-group address-family
- protocols bgp neighbor address-family
- network-services vrf instance protocols bgp neighbor address-family
- network-services vrf instance protocols bgp neighbor-group address-family

**Note**
The default behavior of the system is to not send the large-community attribute.

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                                      | Range        | Default  |
+=============+==================================================================================+==============+==========+
| admin-state | Enables sending the large community attribute in updates to the specified BGP    | | enabled    | disabled |
|             | neighbor                                                                         | | disabled   |          |
+-------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-bgp-neighbor-afi)# send-large-community enabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# address-family ipv6-vpn
    dnRouter(cfg-bgp-group-afi)# send-large-community disabled


**Removing Configuration**

To disable this option:
::

    dnRouter(cfg-bgp-group-afi)# no send-large-community

::

    dnRouter(cfg-bgp-neighbor-afi)# no send-large-community

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 15.1    | Command introduced               |
+---------+----------------------------------+
| 16.1    | Added support for multicast SAFI |
+---------+----------------------------------+
