network-services evpn-vpws-fxc l2-mtu
-------------------------------------

**Minimum user role:** operator

Configure the default (can be modified per instance) MTU value to be sent (signaled) in the BGP, which must be identical with the peer value. If zero is used no mtu check is carried out.

**Command syntax: l2-mtu [l2-mtu]**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws-fxc

**Note**

- The reconfiguration of Pseudowire MTU causes the Pseudowire to flap.

**Parameter table**

+-----------+---------------------------------+--------------+---------+
| Parameter | Description                     | Range        | Default |
+===========+=================================+==============+=========+
| l2-mtu    | MTU value to be signaled in BGP | 0, 1514-9300 | 0       |
+-----------+---------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# evpn-vpws-fxc
    dnRouter(cfg-network-services-evpn-vpws-fxc)# l2-mtu 2000
    dnRouter(cfg-network-services-evpn-vpws-fxc)#


**Removing Configuration**

To revert the MTU to the default value:
::

    dnRouter(cfg-network-services-evpn-vpws-fxc)# no mtu

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
