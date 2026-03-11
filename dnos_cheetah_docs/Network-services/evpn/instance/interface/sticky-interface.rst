network-services evpn instance interface sticky-interface
---------------------------------------------------------

**Minimum user role:** operator

When an interface is set to sticky, all MAC addresses learnt on that interface will be treated as sticky and will not be able to Move to another interface.

**Command syntax: sticky-interface [sticky-interface]**

**Command mode:** config

**Hierarchies**

- network-services evpn instance interface

**Parameter table**

+------------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter        | Description                                                                      | Range        | Default  |
+==================+==================================================================================+==============+==========+
| sticky-interface | If enabled The whole interface will be sticky - all Macs learnt on the interface | | enabled    | disabled |
|                  | will be sticky                                                                   | | disabled   |          |
+------------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# instance evpn1
    dnRouter(cfg-netsrv-evpn-inst)# interface ge100-0/0/0
    dnRouter(cfg-evpn-inst-ge100-0/0/0)# sticky-interface enabled
    dnRouter(cfg-evpn-inst-ge100-0/0/0)#


**Removing Configuration**

To revert the sticky-interface setting to disabled.
::

    dnRouter(cfg-evpn-inst-ge100-0/0/0)# no sticky-interface

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
