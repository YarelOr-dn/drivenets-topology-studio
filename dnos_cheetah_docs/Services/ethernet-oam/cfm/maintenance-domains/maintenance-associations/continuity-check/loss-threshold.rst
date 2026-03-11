services ethernet-oam connectivity-fault-management maintenance-domains maintenance-associations continuity-check loss-threshold
--------------------------------------------------------------------------------------------------------------------------------

**Minimum user role:** operator

Continuity check messages are expected to be received periodically by each remote MEP in the MA. Once the consecutive number of CCM frames
lost, exceeds the loss-threshold, a connectivity loss is declared for a remote MEP.

To configure the loss threshold:

**Command syntax: loss-threshold [loss-threshold]**

**Command mode:** config

**Hierarchies**

- services ethernet-oam connectivity-fault-management maintenance-domains maintenance-associations continuity-check

**Note**

- The command is applicable to L2-service enabled inband network interfaces of the following types:

  - Physical
  - Physical vlan
  - Bundle
  - Bundle vlan

**Parameter table**

+----------------+-------------------------------------------------------------------------+-------+---------+
| Parameter      | Description                                                             | Range | Default |
+================+=========================================================================+=======+=========+
| loss-threshold | The lost CCMs threshold for declaring connectiviy loss of a remote MEP. | 3-255 | 3       |
+----------------+-------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ethernet-oam
    dnRouter(cfg-srv-eoam)# connectivity-fault-management
    dnRouter(cfg-srv-eoam-cfm)# maintenance-domains MyFirstMD
    dnRouter(cfg-eoam-cfm-md)# maintenance-associations MA1
    dnRouter(cfg-cfm-md-ma)# continuity-check
    dnRouter(cfg-md-ma-ccm)# loss-threshold 120


**Removing Configuration**

To revert continuity check loss-threshold configuration to its default value:
::

    dnRouter(cfg-md-ma-ccm)# no loss-threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
