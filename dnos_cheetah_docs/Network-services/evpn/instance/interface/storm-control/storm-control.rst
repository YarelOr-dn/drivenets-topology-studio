network-services evpn instance interface storm-control
------------------------------------------------------

**Minimum user role:** operator

Storm Control rate separately limits each of the broadcast, multicast and unknown-unicast packets.
As these packets are replicated to flood all the interfaces attached to the service, it is important
to ensure that these packets are rate limited. The rate limits configured at this interface level are applied
to the specific interface.

**Command syntax: storm-control**

**Command mode:** config

**Hierarchies**

- network-services evpn instance interface

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# evpn
    dnRouter(cfg-netsrv-evpn)# instance evpn1
    dnRouter(cfg-netsrv-evpn-inst)# interface ge100-0/0/0
    dnRouter(cfg-evpn-inst-ge100-0/0/0)# storm-control
    dnRouter(cfg-inst-ge100-0/0/0-sc)#


**Removing Configuration**

To remove all global storm control configurations
::

    dnRouter(cfg-evpn-inst-ge100-0/0/0)# no storm-control

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2.1  | Command introduced |
+---------+--------------------+
