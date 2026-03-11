network-services evpn-vpws-fxc instance protocols bgp maximum-paths ibgp
------------------------------------------------------------------------

**Minimum user role:** operator

To configure BGP to install multiple paths in the routing table:

**Command syntax: maximum-paths ibgp [ibgp-maximum-paths]**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws-fxc instance protocols bgp

**Note**

- This command is relevant only to unicast and multicast sub-address-families, including label-unicast.

- To view the installed routes, use the various show route commands: "show route", "show route forwarding-table", "show mpls route", and "show mpls forwarding-table".

**Parameter table**

+--------------------+-------------------------------------------------------------------------+-------+---------+
| Parameter          | Description                                                             | Range | Default |
+====================+=========================================================================+=======+=========+
| ibgp-maximum-paths | Maximum number of parallel paths to consider when using iBGP multipath. | 1-32  | 16      |
+--------------------+-------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws-fxc
    dnRouter(cfg-netsrv-evpn-vpws-fxc)# instance evpn-vpws-fxc1
    dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)# protocols
    dnRouter(cfg-evpn-vpws-fxc-inst-protocols)# bgp 65000
    dnRouter(cfg-inst-protocols-bgp)# maximum-paths ibgp 5
    dnRouter(cfg-inst-protocols-bgp)#


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-inst-protocols-bgp)# no maximum-paths ibgp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
