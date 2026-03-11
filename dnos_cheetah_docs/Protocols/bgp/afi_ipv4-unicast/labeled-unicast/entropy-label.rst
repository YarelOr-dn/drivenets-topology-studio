protocols bgp address-family ipv4-unicast labeled-unicast entropy-label
-----------------------------------------------------------------------

**Minimum user role:** operator

Entropy Label is added to the MPLS stack to allow P-Routers to effectively load-balance the traffic without having to perform deep packet inspection.
By enabling this knob BGP will request from the BGP-LU Peer that an Entropy Label be added to the traffic being sent to this router.

**Command syntax: entropy-label [entropy-label]**

**Command mode:** config

**Hierarchies**

- protocols bgp address-family ipv4-unicast labeled-unicast
- protocols bgp address-family ipv6-unicast labeled-unicast

**Note**

- This command only supports Labeled-Unicast routes.

**Parameter table**

+---------------+-----------------------------------------------+--------------+----------+
| Parameter     | Description                                   | Range        | Default  |
+===============+===============================================+==============+==========+
| entropy-label | Request entropy-label for labled-unicast safi | | enabled    | disabled |
|               |                                               | | disabled   |          |
+---------------+-----------------------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv4-unicast
    dnRouter(cfg-protocols-bgp-afi)# labeled-unicast
    dnRouter(cfg-bgp-afi-lu)# entropy-label enabled

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols bgp 65000
    dnRouter(cfg-protocols-bgp)# address-family ipv6-unicast
    dnRouter(cfg-protocols-bgp-afi)# labeled-unicast
    dnRouter(cfg-bgp-afi-lu)# entropy-label enabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-bgp-afi-lu)# no entropy-label

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
