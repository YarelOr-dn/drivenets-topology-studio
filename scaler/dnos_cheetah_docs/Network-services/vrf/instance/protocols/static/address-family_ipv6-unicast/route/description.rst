network-services vrf instance protocols static address-family ipv6-unicast route description
--------------------------------------------------------------------------------------------

**Minimum user role:** operator

Sets a description for the static route. The same route can have only one description, regardless of how many nexthop options it has. The description is visible under 'show config'. To enter a description for the static route:

**Command syntax: description [route-description]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols static address-family ipv6-unicast route
- protocols static address-family ipv6-unicast route

**Parameter table**

+-------------------+--------------------------------------+------------------+---------+
| Parameter         | Description                          | Range            | Default |
+===================+======================================+==================+=========+
| route-description | static-route destination description | | string         | \-      |
|                   |                                      | | length 1-255   |         |
+-------------------+--------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# static
    dnRouter(cfg-protocols-static)# address-family ipv6-unicast
    dnRouter(cfg-protocols-static-ipv6)# route 232:16::8:0/96
    dnRouter(cfg-static-ipv6-route)# description MY_DESCRIPTION
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vrf
    dnRouter(cfg-network-services-vrf)# instance VRF_1
    dnRouter(cfg-network-services-vrf-inst)# protocols
    dnRouter(cfg-vrf-inst-protocols)# static
    dnRouter(cfg-inst-protocols-static)# address-family ipv6-unicast
    dnRouter(cfg-protocols-static-ipv6)# route 232:16::8:0/96
    dnRouter(cfg-static-ipv6-route)# description MY_DESCRIPTION


**Removing Configuration**

To remove the description:
::

    dnRouter(cfg-static-ipv6-route)# no description

**Command History**

+---------+-------------------------------------------------+
| Release | Modification                                    |
+=========+=================================================+
| 12.0    | Command introduced                              |
+---------+-------------------------------------------------+
| 16.1    | Added command to the network services hierarchy |
+---------+-------------------------------------------------+
