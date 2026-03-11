network-services vrf instance protocols static address-family ipv6-unicast bfd next-hop min-tx
----------------------------------------------------------------------------------------------

**Minimum user role:** operator

To set the bfd minimum transmit interval (min-tx):

**Command syntax: min-tx [min-tx]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols static address-family ipv6-unicast bfd next-hop
- protocols static address-family ipv6-unicast bfd next-hop

**Note**

- Due to a hardware limitation, the maximum supported transmit rate is 1700 msec. A negotiated transmit interval higher than 1700 msec will result in an actual transmit rate of 1700 msec.

**Parameter table**

+-----------+-------------------------------------------------------+--------+---------+
| Parameter | Description                                           | Range  | Default |
+===========+=======================================================+========+=========+
| min-tx    | set desired minimum transmit interval for BFD session | 5-1700 | 300     |
+-----------+-------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# static
    dnRouter(cfg-protocols-static)# address-family ipv6-unicast
    dnRouter(cfg-protocols-static-ipv6)# bfd
    dnRouter(cfg-static-ipv6-bfd)# next-hop 1::1 single-hop
    dnRouter(cfg-static-ipv6-bfd-nh)# min-tx 50
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vrf
    dnRouter(cfg-network-services-vrf)# instance VRF_1
    dnRouter(cfg-network-services-vrf-inst)# protocols
    dnRouter(cfg-vrf-inst-protocols)# static
    dnRouter(cfg-inst-protocols-static)# address-family ipv6-unicast
    dnRouter(cfg-protocols-static-ipv6)# bfd
    dnRouter(cfg-static-ipv6-bfd)# next-hop 1.1.1.1 single-hop
    dnRouter(cfg-static-ipv6-bfd-nh)# min-tx 50


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-static-ipv6-bfd-nh)# no min-tx

**Command History**

+---------+-------------------------------------------------+
| Release | Modification                                    |
+=========+=================================================+
| 12.0    | Command introduced                              |
+---------+-------------------------------------------------+
| 15.1    | Added support for 5 msec interval               |
+---------+-------------------------------------------------+
| 16.1    | Added command to the network services hierarchy |
+---------+-------------------------------------------------+
