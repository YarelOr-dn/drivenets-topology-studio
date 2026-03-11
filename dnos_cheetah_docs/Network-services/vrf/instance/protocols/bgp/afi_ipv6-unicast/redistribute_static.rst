network-services vrf instance protocols bgp address-family ipv6-unicast redistribute static
-------------------------------------------------------------------------------------------

**Minimum user role:** operator

You can set the router to advertise static routes:

**Command syntax: redistribute static** metric [metric] policy [policy] [, policy, policy]

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp address-family ipv6-unicast
- protocols bgp address-family ipv4-unicast
- protocols bgp address-family ipv6-unicast
- network-services vrf instance protocols bgp address-family ipv4-unicast

**Note**

- This command is only applicable to unicast sub-address-families.

- Can set multiple policies. In case multiple policies are set policies are evaluated one after the other according to user input order.

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
    dnRouter(cfg-protocols-bgp-afi)# redistribute static

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv6-unicast
    dnRouter(cfg-protocols-bgp-afi)# redistribute static metric 1000 policy My_Policy, My_Policy2

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv4-unicast
    dnRouter(cfg-protocols-bgp-afi)# redistribute static metric 1000


**Removing Configuration**

To stop redistribution of all route types:
::

    dnRouter(cfg-protocols-bgp-afi)# no redistribute

To stop redistribution of routes by type:
::

    dnRouter(cfg-protocols-bgp-afi)# no redistribute static

To revert metric to its default value:
::

    dnRouter(cfg-protocols-bgp-afi)# no redistribute static metric 

**Command History**

+---------+-------------------------------------------------+
| Release | Modification                                    |
+=========+=================================================+
| 6.0     | Command introduced                              |
+---------+-------------------------------------------------+
| 17.2    | Added support for multiple policies attachments |
+---------+-------------------------------------------------+
