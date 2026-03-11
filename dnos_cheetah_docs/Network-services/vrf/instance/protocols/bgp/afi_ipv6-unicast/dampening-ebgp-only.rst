network-services vrf instance protocols bgp address-family ipv6-unicast dampening-ebgp-only
-------------------------------------------------------------------------------------------

**Minimum user role:** operator

To limit dampening logic for routes received from eBGP peers only:

**Command syntax: dampening-ebgp-only**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp address-family ipv6-unicast
- protocols bgp address-family ipv4-unicast
- protocols bgp address-family ipv6-unicast
- protocols bgp address-family ipv4-vpn
- protocols bgp address-family ipv6-vpn
- network-services vrf instance protocols bgp address-family ipv4-unicast

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv4-unicast
    dnRouter(cfg-protocols-bgp-afi)# dampening-ebgp-only

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv6-unicast
    dnRouter(cfg-protocols-bgp-afi)# dampening-ebgp-only


**Removing Configuration**

To revert to the default admin-state with all optional parameters set to their default values:
::

    dnRouter(cfg-protocols-bgp-afi)# no dampening-ebgp-only

**Command History**

+---------+--------------------------------------------------------------+
| Release | Modification                                                 |
+=========+==============================================================+
| 19.0    | Add support for dampening-ebgp-only in most address families |
+---------+--------------------------------------------------------------+
