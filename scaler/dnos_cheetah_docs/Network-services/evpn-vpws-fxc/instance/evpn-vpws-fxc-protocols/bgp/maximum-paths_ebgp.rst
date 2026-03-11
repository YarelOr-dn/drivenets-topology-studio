network-services evpn-vpws-fxc instance protocols bgp maximum-paths ebgp
------------------------------------------------------------------------

**Minimum user role:** operator

To configure BGP to install multiple equal cost paths in the routing table, when some paths are eBGP and others are iBGP:

**Command syntax: maximum-paths ebgp [ebgp-maximum-paths]**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws-fxc instance protocols bgp

**Note**

- BGP will only advertise one best path to its eBGP neighbors.

- This command is relevant only to unicast and multicast sub-address-families, including label-unicast.

- To view the installed routes, use the various show route commands: "show route", "show route forwarding-table", "show mpls route", and "show mpls forwarding-table".

- ECMP between eBGP and iBGP paths are only possible if all paths are imported from other VRFs.

**Parameter table**

+--------------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter          | Description                                                                      | Range | Default |
+====================+==================================================================================+=======+=========+
| ebgp-maximum-paths | Maximum number of parallel paths to consider when using eBGP multipath. The      | 1-32  | 1       |
|                    | default is to use a single path                                                  |       |         |
+--------------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws-fxc
    dnRouter(cfg-netsrv-evpn-vpws-fxc)# instance evpn-vpws-fxc1
    dnRouter(cfg-netsrv-evpn-vpws-fxc-inst)# protocols
    dnRouter(cfg-evpn-vpws-fxc-inst-protocols)# bgp 65000
    dnRouter(cfg-inst-protocols-bgp)# maximum-paths ebgp 5
    dnRouter(cfg-inst-protocols-bgp)#


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-inst-protocols-bgp)# no maximum-paths ebgp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
