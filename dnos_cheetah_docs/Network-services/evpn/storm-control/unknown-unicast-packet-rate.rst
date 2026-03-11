network-services evpn storm-control unknown-unicast-packet-rate
---------------------------------------------------------------

**Minimum user role:** operator

Configure the default value (range: 10..100000000 pps) for the maximum unknown-unicast packet rate allowed. When this limit is reached, packets will be dropped. This limit can be overridden by per instance or per interface storm-control configurations.

**Command syntax: unknown-unicast-packet-rate [unknown-unicast-packet-rate]**

**Command mode:** config

**Hierarchies**

- network-services evpn storm-control

**Parameter table**

+-----------------------------+------------------------------------------------+--------------+---------+
| Parameter                   | Description                                    | Range        | Default |
+=============================+================================================+==============+=========+
| unknown-unicast-packet-rate | Allowed packet rate of unknown-unicast packets | 10-100000000 | \-      |
+-----------------------------+------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-netsrv)# bridge-domain
    dnRouter(cfg-netsrv-evpn)# storm-control
    dnRouter(cfg-netsrv-evpn-sc)# unknown-unicast-packet-rate 10000
    dnRouter(cfg-netsrv-evpn-sc)#


**Removing Configuration**

To remove the unknown-unicast-packet-rate limit.
::

    dnRouter(cfg-netsrv-evpn-sc)# no unknown-unicast-packet-rate

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2.1  | Command introduced |
+---------+--------------------+
