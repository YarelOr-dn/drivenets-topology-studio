network-services evpn-vpws instance l2-mtu
------------------------------------------

**Minimum user role:** operator

Configure the MTU value of this instance to be sent (signaled) in the BGP, which must be identical with the peer value. If zero is used, no mtu check is carried out.

**Command syntax: l2-mtu [l2-mtu]**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws instance

**Note**

- The reconfiguration of Pseudowire MTU causes the Pseudowire to flap.

**Parameter table**

+-----------+---------------------------------+--------------+---------+
| Parameter | Description                     | Range        | Default |
+===========+=================================+==============+=========+
| l2-mtu    | MTU value to be signaled in BGP | 0, 1514-9300 | \-      |
+-----------+---------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# evpn-vpws
    dnRouter(cfg-netsrv-evpn-vpws)# instance evpn-vpws1
    dnRouter(cfg-netsrv-evpn-vpws-inst)# l2-mtu 2000
    dnRouter(cfg-network-services-evpn-vpws)#


**Removing Configuration**

To revert the MTU to the default value:
::

    dnRouter(cfg-network-services-evpn-vpws)# no mtu

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
