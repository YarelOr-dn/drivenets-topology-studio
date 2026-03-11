network-services bridge-domain instance storm-control
-----------------------------------------------------

**Minimum user role:** operator

Storm Control rate separately limits each of the broadcast, multicast and unknown-unicast packets.
As these packets are replicated to flood all the interfaces attached to the service, it is important
to ensure that these packets are rate limited. The rate limits configured at this instance level are applied
to all interfaces within the specific instance as their default unless configured otherwise at the interface level.

**Command syntax: storm-control**

**Command mode:** config

**Hierarchies**

- network-services bridge-domain instance

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# bridge-domain
    dnRouter(cfg-netsrv-bd)# instance bd1
    dnRouter(cfg-netsrv-bd-inst)# storm-control
    dnRouter(cfg-bd-inst-sc)#


**Removing Configuration**

To remove all global storm control configurations
::

    dnRouter(cfg-netsrv-bd-inst)# no storm-control

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2.1  | Command introduced |
+---------+--------------------+
