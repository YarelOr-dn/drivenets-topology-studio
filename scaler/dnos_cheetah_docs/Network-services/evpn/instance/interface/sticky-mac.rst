network-services evpn instance interface sticky-mac
---------------------------------------------------

**Minimum user role:** operator

Configure an interface for the EVPN service

 - Interface must be a l2-service enabled interface.

 - An Interface cannot be assigned to multiple services

**Command syntax: sticky-mac [sticky-mac]**

**Command mode:** config

**Hierarchies**

- network-services evpn instance interface

**Parameter table**

+------------+-----------------------------------------------------------------+-------+---------+
| Parameter  | Description                                                     | Range | Default |
+============+=================================================================+=======+=========+
| sticky-mac | The MAC Address which is configured as sticky on this interface | \-    | \-      |
+------------+-----------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# instance evpn1
    dnRouter(cfg-netsrv-evpn-inst)# interface ge100-0/0/0
    dnRouter(cfg-netsrv-evpn-inst)# sticky-mac 1a:2b:3c:4d:5e:6f
    dnRouter(cfg-netsrv-evpn-inst)# sticky-mac f1:e2:d3:c4:b5:a6


**Removing Configuration**

To remove the mac-address from the list of sticky macs
::

    dnRouter(cfg-netsrv-evpn-inst)# no sticky-mac 1a:2b:3c:4d:5e:6f

To remove all the mac-addresses on this interface, from the list of sticky macs
::

    dnRouter(cfg-netsrv-evpn-inst)# no sticky-mac

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
