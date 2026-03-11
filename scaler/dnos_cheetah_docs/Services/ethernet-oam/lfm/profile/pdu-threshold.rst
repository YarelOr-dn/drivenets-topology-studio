services ethernet-oam link-fault-management profile pdu-threshold
-----------------------------------------------------------------

**Minimum user role:** operator

To set the 802.3ah EFM OAM protocol's connection timeout in terms of missed OAMPDUs from the peer:

**Command syntax: pdu-threshold [pdu-threshold]**

**Command mode:** config

**Hierarchies**

- services ethernet-oam link-fault-management profile

**Note**

- The session timeout is calculated as the configured pdu-interval multiplied by the pdu-threshold.

**Parameter table**

+---------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter     | Description                                                                      | Range | Default |
+===============+==================================================================================+=======+=========+
| pdu-threshold | Specifies how many OAMPDUs need to be lost before declaring adjacency loss with  | 3-10  | 3       |
|               | the peer.                                                                        |       |         |
+---------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ethernet-oam
    dnRouter(cfg-srv-eoam)# link-fault-management
    dnRouter(cfg-srv-eoam-lfm)# profile AH_default1
    dnRouter(cfg-eoam-lfm-profile)# pdu-tthreshold 5


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-eoam-lfm-profile)# no pdu-threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
