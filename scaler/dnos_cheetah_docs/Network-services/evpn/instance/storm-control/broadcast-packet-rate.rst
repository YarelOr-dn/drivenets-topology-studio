network-services evpn instance storm-control broadcast-packet-rate
------------------------------------------------------------------

**Minimum user role:** operator

Configure the default value (range: 10..100000000 pps) for the maximum broadcast packet rate allowed. When this limit is reached, packets will be dropped. This limit is per instance and can be overridden by per interface storm-control configurations. If not configured the global evpn storm-control configurations will be applied unless this knob is set to 'disabled'.

**Command syntax: broadcast-packet-rate [broadcast-packet-rate]**

**Command mode:** config

**Hierarchies**

- network-services evpn instance storm-control

**Parameter table**

+-----------------------+------------------------------------------+---------------------------+---------+
| Parameter             | Description                              | Range                     | Default |
+=======================+==========================================+===========================+=========+
| broadcast-packet-rate | Allowed packet rate of broadcast packets | disabled | 10 - 100000000 | \-      |
+-----------------------+------------------------------------------+---------------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# evpn
    dnRouter(cfg-netsrv-evpn)# instance evpn1
    dnRouter(cfg-netsrv-evpn-inst)# storm-control
    dnRouter(cfg-evpn-inst-sc)# broadcast-packet-rate 10000
    dnRouter(cfg-evpn-inst-sc)#


**Removing Configuration**

To remove the broadcast-packet-rate limit.
::

    dnRouter(cfg-evpn-inst-sc)# no broadcast-packet-rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2.1  | Command introduced |
+---------+--------------------+
