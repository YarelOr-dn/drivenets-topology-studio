protocols bgp neighbor address-family allow-as-in
-------------------------------------------------

**Minimum user role:** operator

The following command instructs the BGP router whether or not to disable the AS PATH check function for routes learned from the specific neighbor, so as not to reject routes that contain the recipient's AS number.

**Command syntax: allow-as-in [admin-state]** duplicate [as-duplicate-number]

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor address-family
- protocols bgp neighbor-group address-family
- protocols bgp neighbor-group neighbor address-family
- network-services vrf instance protocols bgp neighbor address-family
- network-services vrf instance protocols bgp neighbor-group address-family
- network-services vrf instance protocols bgp neighbor-group neighbor address-family

**Note**

- When applied on a group, this property is inherited by all group members. Applying this property on a neighbor within a group overrides the group setting.

- This command is applicable to eBGP and iBGP neighbors.

**Parameter table**

+---------------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter           | Description                                                                      | Range        | Default  |
+=====================+==================================================================================+==============+==========+
| admin-state         | enable this configuration                                                        | | enabled    | disabled |
|                     |                                                                                  | | disabled   |          |
+---------------------+----------------------------------------------------------------------------------+--------------+----------+
| as-duplicate-number | Specifies the number of times that the AS path of a received route may contain   | 1-10         | 1        |
|                     | the recipient BGP speaker's AS number and still be accepted                      |              |          |
+---------------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-bgp-neighbor-afi)# allow-as-in enabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-vpn
    dnRouter(cfg-protocols-bgp-neighbor)# allow-as-in enabled duplicate 3

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# address-family ipv6-unicast
    dnRouter(cfg-bgp-group-afi)# allow-as-in enabled duplicate 10

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-group)# address-family ipv6-unicast
    dnRouter(cfg-bgp-group-afi)# allow-as-in disabled duplicate 10
    dnRouter(cfg-bgp-group-afi)# exit
    dnRouter(cfg-bgp-group-neighbor)# address-family ipv6-vpn
    dnRouter(cfg-group-neighbor-afi)# allow-as-in enabled duplicate 2

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-group)# address-family ipv6-unicast
    dnRouter(cfg-bgp-group-afi)# allow-as-in enabled duplicate 10
    dnRouter(cfg-bgp-group-afi)# exit
    dnRouter(cfg-bgp-group-neighbor)# address-family ipv6-vpn
    dnRouter(cfg-group-neighbor-afi)# allow-as-in disabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.3
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-flowspec
    dnRouter(cfg-bgp-neighbor-afi)# allow-as-in enabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-bgp-neighbor-afi)# no allow-as-in duplicate

::

    dnRouter(cfg-bgp-group-afi)# no allow-as-in

::

    dnRouter(cfg-group-neighbor-afi)# no allow-as-in

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 6.0     | Command introduced               |
+---------+----------------------------------+
| 16.1    | Added support for multicast SAFI |
+---------+----------------------------------+
