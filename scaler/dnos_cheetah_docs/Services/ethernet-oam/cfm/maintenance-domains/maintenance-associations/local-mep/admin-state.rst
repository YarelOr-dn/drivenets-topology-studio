services ethernet-oam connectivity-fault-management maintenance-domains maintenance-associations local-mep admin-state
----------------------------------------------------------------------------------------------------------------------

**Minimum user role:** operator

To enable or disable CFM on a local MEP:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- services ethernet-oam connectivity-fault-management maintenance-domains maintenance-associations local-mep

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
| admin-state | The administrative state of the MEP. TRUE indicates that the MEP is to           | | enabled    | enabled |
|             | functional normally, and FALSE indicates that it is to cease functioning.        | | disabled   |         |
+-------------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ethernet-oam
    dnRouter(cfg-srv-eoam)# connectivity-fault-management
    dnRouter(cfg-srv-eoam-cfm)# maintenance-domains MyFirstMD
    dnRouter(cfg-eoam-cfm-md)# maintenance-associations MA1
    dnRouter(cfg-cfm-md-ma)# local-mep 2
    dnRouter(cfg-md-ma-lmep-2)# admin-state disabled


**Removing Configuration**

To revert continuity check admin-state configuration to its default value:
::

    dnRouter(cfg-md-ma-lmep-2)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
