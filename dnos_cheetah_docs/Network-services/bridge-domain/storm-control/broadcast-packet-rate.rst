network-services bridge-domain storm-control broadcast-packet-rate
------------------------------------------------------------------

**Minimum user role:** operator

Configure the default value (range: 10..100000000 pps) for the maximum broadcast packet rate allowed. When this limit is reached, packets will be dropped. This limit can be overridden by per instance or per interface storm-control configurations.

**Command syntax: broadcast-packet-rate [broadcast-packet-rate]**

**Command mode:** config

**Hierarchies**

- network-services bridge-domain storm-control

**Parameter table**

+-----------------------+------------------------------------------+--------------+---------+
| Parameter             | Description                              | Range        | Default |
+=======================+==========================================+==============+=========+
| broadcast-packet-rate | Allowed packet rate of broadcast packets | 10-100000000 | \-      |
+-----------------------+------------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# bridge-domain
    dnRouter(cfg-netsrv-bd)# storm-control
    dnRouter(cfg-netsrv-bd-sc)# broadcast-packet-rate 10000
    dnRouter(cfg-netsrv-bd-sc)#


**Removing Configuration**

To remove the broadcast-packet-rate limit.
::

    dnRouter(cfg-netsrv-bd-sc)# no broadcast-packet-rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2.1  | Command introduced |
+---------+--------------------+
