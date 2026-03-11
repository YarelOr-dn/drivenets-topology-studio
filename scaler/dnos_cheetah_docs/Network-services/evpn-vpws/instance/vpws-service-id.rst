network-services evpn-vpws instance vpws-service-id local remote
----------------------------------------------------------------

**Minimum user role:** operator

The local and remote VPWS Service IDs are a mandatory configuration. Changing their values will result in service interruption.

**Command syntax: vpws-service-id local [local-vpws-service-id] remote [remote-vpws-service-id]**

**Command mode:** config

**Hierarchies**

- network-services evpn-vpws instance

**Note**

- The reconfiguration of the VPWS service IDs causes the Pseudowire to flap.

- The VPWS Service ID and neighbor-address & Ethernet Segment ID must be unique across all L2VPN services.

**Parameter table**

+------------------------+--------------------------------------+------------+---------+
| Parameter              | Description                          | Range      | Default |
+========================+======================================+============+=========+
| local-vpws-service-id  | The vpws-service-id of the local PE  | 1-16777215 | \-      |
+------------------------+--------------------------------------+------------+---------+
| remote-vpws-service-id | The vpws-service-id of the remote PE | 1-16777215 | \-      |
+------------------------+--------------------------------------+------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn-vpws
    dnRouter(cfg-netsrv-evpn-vpws)# instance evpn-vpws1
    dnRouter(cfg-netsrv-evpn-vpws-inst)# vpws-service-id local 1000 remote 5000
    dnRouter(cfg-netsrv-evpn-vpws-inst)#


**Removing Configuration**

To remove the vpws-service-id
::

    dnRouter(cfg-netsrv-evpn-vpws-inst)# no vpws-service-id

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
