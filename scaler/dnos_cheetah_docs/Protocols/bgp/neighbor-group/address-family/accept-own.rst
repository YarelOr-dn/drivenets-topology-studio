protocols bgp neighbor-group address-family accept-own
------------------------------------------------------

**Minimum user role:** operator

To instruct the router whether or not to handle self-originated VPN routes containing the accept-own community attribute:

**Command syntax: accept-own [accept-own]**

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor-group address-family
- protocols bgp neighbor address-family
- protocols bgp neighbor-group neighbor address-family

**Note**

- When applied on a group, this property is inherited by all group members. Applying this property on a neighbor within a group overrides the group setting.

- This command is only applicable to vpn address-families.

**Parameter table**

+------------+----------------------------------------------+--------------+----------+
| Parameter  | Description                                  | Range        | Default  |
+============+==============================================+==============+==========+
| accept-own | Enable accept-own handling for this neighbor | | enabled    | disabled |
|            |                                              | | disabled   |          |
+------------+----------------------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv6-vpn
    dnRouter(cfg-bgp-neighbor-afi)# accept-own enabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# address-family ipv4-vpn
    dnRouter(cfg-bgp-group-afi)# accept-own enabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# address-family ipv6-vpn
    dnRouter(cfg-bgp-group-afi)# accept-own enabled
    dnRouter(cfg-bgp-group-afi)# exit
    dnRouter(cfg-protocols-bgp-group)# neighbor 12.170.4.1
    dnRouter(cfg-bgp-group-neighbor)# address-family ipv6-vpn
    dnRouter(cfg-group-neighbor-afi)# accept-own disabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-bgp-neighbor-afi)# no accept-own

::

    dnRouter(cfg-bgp-group-afi)# no accept-own

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
