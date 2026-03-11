services ethernet-oam connectivity-fault-management maintenance-domains maintenance-associations local-mep pcp
--------------------------------------------------------------------------------------------------------------

**Minimum user role:** operator

To set the PCP value for outgoing CFM PDUs on the local MEP:

**Command syntax: pcp [priority]**

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

+-----------+----------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                      | Range | Default |
+===========+==================================================================================+=======+=========+
| priority  | The priority value for CCMs and LTMs transmitted by the MEP. The default value   | 0-7   | 7       |
|           | is the highest priority allowed to pass through the Bridge Port for any of the   |       |         |
|           | MEPs VID(s).                                                                     |       |         |
+-----------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ethernet-oam
    dnRouter(cfg-srv-eoam)# connectivity-fault-management
    dnRouter(cfg-srv-eoam-cfm)# maintenance-domains MyFirstMD
    dnRouter(cfg-eoam-cfm-md)# maintenance-associations MA1
    dnRouter(cfg-cfm-md-ma)# local-mep 2
    dnRouter(cfg-md-ma-lmep-2)# pcp 7


**Removing Configuration**

To revert the PCP configuration to its default value:
::

    dnRouter(cfg-md-ma-lmep-2)# no pcp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
