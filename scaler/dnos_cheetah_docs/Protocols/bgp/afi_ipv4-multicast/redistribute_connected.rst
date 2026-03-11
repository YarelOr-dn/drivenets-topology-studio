protocols bgp address-family ipv4-multicast redistribute connected
------------------------------------------------------------------

**Minimum user role:** operator

You can set the router to advertise directly connected routes:

**Command syntax: redistribute connected** metric [metric] policy [policy] [, policy, policy]

**Command mode:** config

**Hierarchies**

- protocols bgp address-family ipv4-multicast
- protocols bgp address-family ipv4-unicast
- protocols bgp address-family ipv6-unicast
- network-services vrf instance protocols bgp address-family ipv4-unicast
- network-services vrf instance protocols bgp address-family ipv6-unicast

**Note**

- This command is only applicable to unicast and multicast sub-address-families.

- Can set multiple policies. In case multiple policies are set policies are evaluated one after the other according to user input order

**Parameter table**

+-----------+------------------------------+------------------+---------+
| Parameter | Description                  | Range            | Default |
+===========+==============================+==================+=========+
| metric    | update route metric          | 0-4294967295     | \-      |
+-----------+------------------------------+------------------+---------+
| policy    | redistribute by policy rules | | string         | \-      |
|           |                              | | length 1-255   |         |
+-----------+------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv4-unicast
    dnRouter(cfg-protocols-bgp-afi)# redistribute connected

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv6-unicast
    dnRouter(cfg-protocols-bgp-afi)# redistribute connected metric 1000 policy My_Policy, My_Policy2

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv4-unicast
    dnRouter(cfg-protocols-bgp-afi)# redistribute connected metric 1000


**Removing Configuration**

To stop redistribution of all route types:
::

    dnRouter(cfg-protocols-bgp-afi)# no redistribute

To stop redistribution of routes by type:
::

    dnRouter(cfg-protocols-bgp-afi)# no redistribute connected

To revert metric to its default value:
::

    dnRouter(cfg-protocols-bgp-afi)# no redistribute connected metric 

**Command History**

+---------+-----------------------------------------------------------------------------------------------------------+
| Release | Modification                                                                                              |
+=========+===========================================================================================================+
| 6.0     | Command introduced                                                                                        |
+---------+-----------------------------------------------------------------------------------------------------------+
| 13.2    | Updated command syntax to support ISIS                                                                    |
+---------+-----------------------------------------------------------------------------------------------------------+
| 16.1    | Extended command to support redistribution of connected routes from MRPF table to BGP IPv4 multicast SAFI |
+---------+-----------------------------------------------------------------------------------------------------------+
| 17.2    | Added support for multiple policies attachments                                                           |
+---------+-----------------------------------------------------------------------------------------------------------+
