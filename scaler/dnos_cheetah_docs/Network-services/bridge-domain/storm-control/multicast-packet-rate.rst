network-services bridge-domain storm-control multicast-packet-rate
------------------------------------------------------------------

**Minimum user role:** operator

Configure the default value (range: 10..100000000 pps) for the maximum multicast packet rate allowed. When this limit is reached, packets will be dropped. This limit can be overridden by per instance or per interface storm-control configurations.

**Command syntax: multicast-packet-rate [multicast-packet-rate]**

**Command mode:** config

**Hierarchies**

- network-services bridge-domain storm-control

**Parameter table**

+-----------------------+------------------------------------------+--------------+---------+
| Parameter             | Description                              | Range        | Default |
+=======================+==========================================+==============+=========+
| multicast-packet-rate | Allowed packet rate of multicast packets | 10-100000000 | \-      |
+-----------------------+------------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# bridge-domain
    dnRouter(cfg-netsrv-bd)# storm-control
    dnRouter(cfg-netsrv-bd-sc)# multicast-packet-rate 10000
    dnRouter(cfg-netsrv-bd-sc)#


**Removing Configuration**

To remove the multicast-packet-rate limit.
::

    dnRouter(cfg-netsrv-bd-sc)# no multicast-packet-rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2.1  | Command introduced |
+---------+--------------------+
