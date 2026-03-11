network-services bridge-domain instance interface storm-control unknown-unicast-packet-rate
-------------------------------------------------------------------------------------------

**Minimum user role:** operator

Configure the default value (range: 10..100000000 pps) for the maximum unknown-unicast packet rate allowed. When this limit is reached, packets will be dropped. This limit is per specific interface. If not configured the per instance or per global bridge-domain storm-control configurations will be applied unless this knob is set to 'disabled'.

**Command syntax: unknown-unicast-packet-rate [unknown-unicast-packet-rate]**

**Command mode:** config

**Hierarchies**

- network-services bridge-domain instance interface storm-control

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
    dnRouter(cfg-netsrv-bd-inst)# interface ge100-0/0/0
    dnRouter(cfg-bd-inst-ge100-0/0/0)# storm-control
    dnRouter(cfg-inst-ge100-0/0/0-sc)# unknown-unicast-packet-rate 10000
    dnRouter(cfg-inst-ge100-0/0/0-sc)#


**Removing Configuration**

To remove the unknown-unicast-packet-rate limit.
::

    dnRouter(cfg-inst-ge100-0/0/0-sc)# no unknown-unicast-packet-rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2.1  | Command introduced |
+---------+--------------------+
