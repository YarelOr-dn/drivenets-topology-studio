network-services vrf instance protocols bgp address-family ipv6-unicast redistribute ike
----------------------------------------------------------------------------------------

**Minimum user role:** operator

You can set the router to advertise ike routes:

**Command syntax: redistribute ike** metric [metric] policy [policy] [, policy, policy]

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp address-family ipv6-unicast
- protocols bgp address-family ipv4-unicast
- protocols bgp address-family ipv6-unicast
- network-services vrf instance protocols bgp address-family ipv4-unicast

**Note**

- This command is only applicable to the unicast sub-address-families.

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
    dnRouter(cfg-protocols-bgp-afi)# redistribute ike

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv6-unicast
    dnRouter(cfg-protocols-bgp-afi)# redistribute ike metric 1000 policy My_Policy

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv4-unicast
    dnRouter(cfg-protocols-bgp-afi)# redistribute ike metric 1000


**Removing Configuration**

To stop redistribution of all route types:
::

    dnRouter(cfg-protocols-bgp-afi)# no redistribute

To stop redistribution of routes by type:
::

    dnRouter(cfg-protocols-bgp-afi)# no redistribute ike

To revert metric to its default value:
::

    dnRouter(cfg-protocols-bgp-afi)# no redistribute ike metric 

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
