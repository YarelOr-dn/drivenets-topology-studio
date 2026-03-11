network-services bridge-domain instance storm-control unknown-unicast-packet-rate
---------------------------------------------------------------------------------

**Minimum user role:** operator

Configure the default value (range: 10..100000000 pps) for the maximum unknown-unicast packet rate allowed. When this limit is reached, packets will be dropped. This limit is per instance and can be overridden by per interface storm-control configurations. If not configured the global bridge-domain storm-control configurations will be applied unless this knob is set to 'disabled'.

**Command syntax: unknown-unicast-packet-rate [unknown-unicast-packet-rate]**

**Command mode:** config

**Hierarchies**

- network-services bridge-domain instance storm-control

**Parameter table**

+-----------------------------+------------------------------------------------+---------------------------+---------+
| Parameter                   | Description                                    | Range                     | Default |
+=============================+================================================+===========================+=========+
| unknown-unicast-packet-rate | Allowed packet rate of unknown-unicast packets | disabled | 10 - 100000000 | \-      |
+-----------------------------+------------------------------------------------+---------------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# bridge-domain
    dnRouter(cfg-netsrv-bd)# instance bd1
    dnRouter(cfg-netsrv-bd-inst)# storm-control
    dnRouter(cfg-bd-inst-sc)# unknown-unicast-packet-rate 10000
    dnRouter(cfg-bd-inst-sc)#


**Removing Configuration**

To remove the unknown-unicast-packet-rate limit.
::

    dnRouter(cfg-bd-inst-sc)# no unknown-unicast-packet-rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2.1  | Command introduced |
+---------+--------------------+
