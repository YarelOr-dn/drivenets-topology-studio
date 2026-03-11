protocols bgp address-family ipv4-multicast add-path send
---------------------------------------------------------

**Minimum user role:** operator

BGP Additional Paths is a BGP extension that provides the ability to advertise multiple paths for the same prefix without the new paths replacing previous paths. 
This helps reduce route repetition, and achieve faster re-convergence as an alternative path is available immediately upon failure of a primary path.
To enter the add-path send configuration level:

**Command syntax: add-path send**

**Command mode:** config

**Hierarchies**

- protocols bgp address-family ipv4-multicast
- protocols bgp address-family ipv4-unicast
- protocols bgp address-family ipv6-unicast
- protocols bgp address-family ipv4-vpn
- protocols bgp address-family ipv6-vpn

**Note**

- This command is only applicable to unicast and multicast sub-address-families.

- This command is only applicable to the default VRF and only for iBGP neighbors.

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv4-unicast
    dnRouter(cfg-protocols-bgp-afi)# add-path send
    dnRouter(cfg-bgp-afi-add-path-send)#

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv6-unicast
    dnRouter(cfg-protocols-bgp-afi)# add-path send
    dnRouter(cfg-bgp-afi-add-path-send)#


**Removing Configuration**

To revert the add-path send configurations to default state:
::

    dnRouter(cfg-protocols-bgp-afi)# no add-path send

**Command History**

+---------+-----------------------------------------------------+
| Release | Modification                                        |
+=========+=====================================================+
| 15.1    | Command introduced                                  |
+---------+-----------------------------------------------------+
| 16.1    | Extended command to support BGP IPv4 multicast SAFI |
+---------+-----------------------------------------------------+
