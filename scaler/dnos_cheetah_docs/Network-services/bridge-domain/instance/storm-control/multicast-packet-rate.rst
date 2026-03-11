network-services bridge-domain instance storm-control multicast-packet-rate
---------------------------------------------------------------------------

**Minimum user role:** operator

Configure the default value (range: 10..100000000 pps) for the maximum multicast packet rate allowed. When this limit is reached, packets will be dropped. This limit is per instance and can be overridden by per interface storm-control configurations. If not configured the global bridge-domain storm-control configurations will be applied unless this knob is set to 'disabled'.

**Command syntax: multicast-packet-rate [multicast-packet-rate]**

**Command mode:** config

**Hierarchies**

- network-services bridge-domain instance storm-control

**Parameter table**

+-----------------------+------------------------------------------+---------------------------+---------+
| Parameter             | Description                              | Range                     | Default |
+=======================+==========================================+===========================+=========+
| multicast-packet-rate | Allowed packet rate of multicast packets | disabled | 10 - 100000000 | \-      |
+-----------------------+------------------------------------------+---------------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# bridge-domain
    dnRouter(cfg-netsrv-bd)# instance bd1
    dnRouter(cfg-netsrv-bd-inst)# storm-control
    dnRouter(cfg-bd-inst-sc)# multicast-packet-rate 10000
    dnRouter(cfg-bd-inst-sc)#


**Removing Configuration**

To remove the multicast-packet-rate limit.
::

    dnRouter(cfg-bd-inst-sc)# no multicast-packet-rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2.1  | Command introduced |
+---------+--------------------+
