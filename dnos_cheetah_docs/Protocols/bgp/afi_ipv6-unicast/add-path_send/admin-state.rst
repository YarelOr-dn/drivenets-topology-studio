protocols bgp address-family ipv6-unicast add-path send admin-state
-------------------------------------------------------------------

**Minimum user role:** operator

To enable the add-path send behavior for a specific neighbor:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols bgp address-family ipv6-unicast add-path send
- protocols bgp address-family ipv4-unicast add-path send
- protocols bgp address-family ipv4-multicast add-path send
- protocols bgp address-family ipv4-vpn add-path send
- protocols bgp address-family ipv6-vpn add-path send

**Note**

- This command is only applicable to unicast and multicast sub-address-families.

- This command is only applicable to the default VRF and only for iBGP neighbors.

**Parameter table**

+-------------+--------------------------------+--------------+----------+
| Parameter   | Description                    | Range        | Default  |
+=============+================================+==============+==========+
| admin-state | add path send enabled/disabled | | enabled    | disabled |
|             |                                | | disabled   |          |
+-------------+--------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv4-unicast
    dnRouter(cfg-protocols-bgp-afi)# add-path send
    dnRouter(cfg-bgp-afi-add-path-send)# admin-state enabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv6-unicast
    dnRouter(cfg-protocols-bgp-afi)# add-path send
    dnRouter(cfg-bgp-afi-add-path-send)# admin-state enabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-bgp-afi-add-path-send)# no admin-state

**Command History**

+---------+-----------------------------------------------------+
| Release | Modification                                        |
+=========+=====================================================+
| 15.1    | Command introduced                                  |
+---------+-----------------------------------------------------+
| 16.1    | Extended command to support BGP IPv4 multicast SAFI |
+---------+-----------------------------------------------------+
