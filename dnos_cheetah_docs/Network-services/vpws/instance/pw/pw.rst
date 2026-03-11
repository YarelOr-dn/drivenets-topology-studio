network-services vpws instance pw
---------------------------------

**Minimum user role:** operator

When establishing a Pseudowire, two circuits are created, one circuit carries outbound traffic, and the other carries inbound traffic, creating bidirectional packet flow. The Pseudowire is signaled using FEC type 128 toward a Targeted LDP neighbor.

To add a remote PEs IPv4 address and enter the Pseudowire (PW) configuration hierarchy:

**Command syntax: pw [neighbor-address]**

**Command mode:** config

**Hierarchies**

- network-services vpws instance

**Note**

- The reconfiguration of the Pseudowire neighbor-address causes the Pseudowire to flap.

- The Pseudowire neighbor-address and PW-ID must be unique across all L2VPN services.

**Parameter table**

+------------------+------------------------------+---------+---------+
| Parameter        | Description                  | Range   | Default |
+==================+==============================+=========+=========+
| neighbor-address | The pw neighbor ipv4 address | A.B.C.D | \-      |
+------------------+------------------------------+---------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vpws
    dnRouter(cfg-network-services-vpws)# instance VPWS_1
    dnRouter(cfg-network-services-vpws-inst)# pw 1.1.1.1
    dnRouter(cfg-network-services-vpws-inst-pw)#


**Removing Configuration**

To revert the Pseudowire configuration to default:
::

    dnRouter(cfg-network-services-vpws-inst)# no pw 1.1.1.1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
