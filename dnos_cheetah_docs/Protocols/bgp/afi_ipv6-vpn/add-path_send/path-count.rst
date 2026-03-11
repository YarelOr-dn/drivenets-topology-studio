protocols bgp address-family ipv6-vpn add-path send path-count
--------------------------------------------------------------

**Minimum user role:** operator

You can set the number of paths to be sent when add-path send is enabled:

**Command syntax: path-count [path-count]**

**Command mode:** config

**Hierarchies**

- protocols bgp address-family ipv6-vpn add-path send
- protocols bgp address-family ipv4-unicast add-path send
- protocols bgp address-family ipv4-multicast add-path send
- protocols bgp address-family ipv6-unicast add-path send
- protocols bgp address-family ipv4-vpn add-path send

**Parameter table**

+------------+----------------------------------------+-------+---------+
| Parameter  | Description                            | Range | Default |
+============+========================================+=======+=========+
| path-count | maximum number of path allowed to send | 2-32  | 2       |
+------------+----------------------------------------+-------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv4-unicast
    dnRouter(cfg-protocols-bgp-afi)# add-path send
    dnRouter(cfg-bgp-afi-add-path-send)# path-count 10

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv6-unicast
    dnRouter(cfg-protocols-bgp-afi)# add-path send
    dnRouter(cfg-bgp-afi-add-path-send)# path-count 10


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-bgp-afi-add-path-send)# no path-count

**Command History**

+---------+-----------------------------------------------------+
| Release | Modification                                        |
+=========+=====================================================+
| 15.1    | Command introduced                                  |
+---------+-----------------------------------------------------+
| 16.1    | Extended command to support BGP IPv4 multicast SAFI |
+---------+-----------------------------------------------------+
