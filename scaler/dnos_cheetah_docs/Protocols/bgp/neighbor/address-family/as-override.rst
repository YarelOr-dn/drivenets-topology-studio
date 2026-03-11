protocols bgp neighbor address-family as-override
-------------------------------------------------

**Minimum user role:** operator

The following command replaces the AS number of the originating device with the AS number of the sending BGP device.

**Command syntax: as-override**

**Command mode:** config

**Hierarchies**

- protocols bgp neighbor address-family
- protocols bgp neighbor-group address-family
- network-services vrf instance protocols bgp neighbor address-family
- network-services vrf instance protocols bgp neighbor-group address-family

**Note**

- AS-override is supported for eBGP and iBGP neighbors

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor 12.170.4.1
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-unicast
    dnRouter(cfg-bgp-neighbor-afi)# as-override
    dnRouter(cfg-bgp-neighbor-afi)# exit
    dnRouter(cfg-protocols-bgp-neighbor)# address-family ipv4-flowspec
    dnRouter(cfg-bgp-neighbor-afi)# as-override

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp-group)# address-family ipv6-unicast
    dnRouter(cfg-bgp-group-afi)# as-override


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-bgp-neighbor-afi)# no as-override

::

    dnRouter(cfg-bgp-group-afi)# no as-override

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 6.0     | Command introduced               |
+---------+----------------------------------+
| 16.1    | Added support for multicast SAFI |
+---------+----------------------------------+
