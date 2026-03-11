network-services bridge-domain storm-control
--------------------------------------------

**Minimum user role:** operator

Storm Control rate separately limits each of the broadcast, multicast and unknown-unicast packets.
As these packets are replicated to flood all the interfaces attached to the service, it is important
to ensure that these packets are rate limited. The rate limits configured at this level are applied
to all instances as their default unless configured otherwise at the instance or interface levels.

**Command syntax: storm-control**

**Command mode:** config

**Hierarchies**

- network-services bridge-domain

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# bridge-domain
    dnRouter(cfg-netsrv-bd)# storm-control
    dnRouter(cfg-netsrv-bd-sc)


**Removing Configuration**

To remove all global storm control configurations
::

    dnRouter(cfg-netsrv-bd)# no storm-control

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2.1  | Command introduced |
+---------+--------------------+
