protocols bgp neighbor address-family send-community
----------------------------------------------------

**Minimum user role:** operator

The following command ensures that the community attribute is sent in updates to the specified neighbor or group.

**Command syntax: send-community** community-type [community-type]

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor address-family
- protocols bgp neighbor-group address-family
- network-services vrf instance protocols bgp neighbor address-family
- network-services vrf instance protocols bgp neighbor-group address-family

**Note**

- The default behavior of the system is to not send the community attribute.

**Parameter table**

+----------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter      | Description                                                                      | Range        | Default |
+================+==================================================================================+==============+=========+
| community-type | both - Sends both standard and extended attributes extended - Sends extended     | | both       | both    |
|                | attributes standard - Sends standard attributes                                  | | extended   |         |
|                |                                                                                  | | standard   |         |
+----------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-bgp-neighbor-afi)# send-community
    dnRouter(cfg-bgp-neighbor-afi)# send-community community-type standard

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# address-family ipv6-vpn
    dnRouter(cfg-bgp-group-afi)# send-community community-type both

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# address-family ipv4-flowspec
    dnRouter(cfg-bgp-group-afi)# send-community community-type both


**Removing Configuration**

To disable this option:
::

    dnRouter(cfg-bgp-group-afi)# no send-community

::

    dnRouter(cfg-bgp-neighbor-afi)# no send-community community-type standard

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 6.0     | Command introduced               |
+---------+----------------------------------+
| 16.1    | Added support for multicast SAFI |
+---------+----------------------------------+
