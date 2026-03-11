services ethernet-oam connectivity-fault-management maintenance-domains maintenance-associations continuity-check transmit
--------------------------------------------------------------------------------------------------------------------------

**Minimum user role:** operator

To enable or disable the transmission of CCM messages by the local MEPs:

**Command syntax: transmit [admin-state]**

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

+-------------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter   | Description                                                                      | Range        | Default |
+=============+==================================================================================+==============+=========+
| admin-state | Indicates whether the MEP can generate CCMs. If TRUE, the MEP will generate CCM  | | enabled    | enabled |
|             | PDUs.                                                                            | | disabled   |         |
+-------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ethernet-oam
    dnRouter(cfg-srv-eoam)# connectivity-fault-management
    dnRouter(cfg-srv-eoam-cfm)# maintenance-domains MyFirstMD
    dnRouter(cfg-eoam-cfm-md)# maintenance-associations MA1
    dnRouter(cfg-cfm-md-ma)# continuity-check
    dnRouter(cfg-md-ma-ccm)# transmit disabled


**Removing Configuration**

To revert continuity check transmit configuration to its default value:
::

    dnRouter(cfg-md-ma-ccm)# no transmit

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
