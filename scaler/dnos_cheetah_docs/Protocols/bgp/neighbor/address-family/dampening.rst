protocols bgp neighbor address-family dampening
-----------------------------------------------

**Minimum user role:** operator

To instruct the router whether or not to enable route flap dampening suppression from neighbor, peer group or a neighbor in a peer group:

**Command syntax: dampening [dampening]**

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

- This command is only relevant if global address-family dampening is enabled. See "bgp address-family dampening"

**Parameter table**

+-----------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter | Description                                                                      | Range        | Default |
+===========+==================================================================================+==============+=========+
| dampening | route flap dampening supersession from neighbor, thus disables the global        | | enabled    | enabled |
|           | dampening configuration for neighbor or group                                    | | disabled   |         |
+-----------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv6-unicast
    dnRouter(cfg-protocols-bgp-afi)# dampening enabled
    dnRouter(cfg-protocols-bgp-afi)# exit
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-bgp-neighbor-afi)# dampening enabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv6-unicast
    dnRouter(cfg-protocols-bgp-afi)# dampening enabled
    dnRouter(cfg-protocols-bgp-afi)# exit
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# address-family ipv6-unicast
    dnRouter(cfg-bgp-group-afi)# dampening disabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# address-family ipv6-unicast
    dnRouter(cfg-bgp-group-afi)# dampening enabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP6:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)# address-family ipv6-vpn
    dnRouter(cfg-bgp-group-afi)# dampening enabled
    dnRouter(cfg-bgp-group-afi)# exit
    dnRouter(cfg-protocols-bgp-group)# neighbor 12.170.4.1
    dnRouter(cfg-bgp-group-neighbor)# address-family ipv6-vpn
    dnRouter(cfg-group-neighbor-afi)# dampening disabled


**Removing Configuration**

To revert dampening to its default state:
::

    dnRouter(cfg-bgp-group-afi)# no dampening

::

    dnRouter(cfg-bgp-neighbor-afi)# no dampening

::

    dnRouter(cfg-group-neighbor-afi)# no dampening

**Command History**

+---------+---------------------------------------------------------------------------------+
| Release | Modification                                                                    |
+=========+=================================================================================+
| 6.0     | Command introduced                                                              |
+---------+---------------------------------------------------------------------------------+
| 11.4    | Changed the default admin-state from the global AFI configuration to "Enabled". |
+---------+---------------------------------------------------------------------------------+
