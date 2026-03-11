network-services vpws instance pw pw-id
---------------------------------------

**Minimum user role:** operator

Configure a unique Pseudowire identifier which is sent using FEC type 128 to establish a Pseudowire connection. PW-ID is a mandatory configuration. Changing the PW-ID will result in service interruption.

**Command syntax: pw-id [pw-id]**

**Command mode:** config

**Hierarchies**

- network-services vpws instance pw

**Note**

- The reconfiguration of PW-ID causes the Pseudowire to flap.

- The Pseudowire neighbor-address and PW-ID must be unique across all L2VPN services.

**Parameter table**

+-----------+----------------------------------------------------+--------------+---------+
| Parameter | Description                                        | Range        | Default |
+===========+====================================================+==============+=========+
| pw-id     | The pw unique identifier to be signaled in FEC 128 | 1-4294967295 | \-      |
+-----------+----------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# network-services
    dnRouter(cfg-network-services)# vpws
    dnRouter(cfg-network-services-vpws)# instance VPWS_1
    dnRouter(cfg-network-services-vpws-inst)# pw 1.1.1.1
    dnRouter(cfg-vpws-inst-pw)# pw-id 8


**Removing Configuration**

The command can't be reverted
::


**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
