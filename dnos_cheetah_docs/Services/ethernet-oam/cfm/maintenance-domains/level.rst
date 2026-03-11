services ethernet-oam connectivity-fault-management maintenance-domains level
-----------------------------------------------------------------------------

**Minimum user role:** operator

To configure the level of the CFM maintenance domain:

**Command syntax: level [md-level]**

**Command mode:** config

**Hierarchies**

- services ethernet-oam connectivity-fault-management maintenance-domains

**Note**

- The command is applicable to L2-service enabled inband network interfaces of the following types:

  - Physical
  - Physical vlan
  - Bundle
  - Bundle vlan

**Parameter table**

+-----------+-------------------------------+-------+---------+
| Parameter | Description                   | Range | Default |
+===========+===============================+=======+=========+
| md-level  | The Maintenance Domain level. | 0-7   | \-      |
+-----------+-------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ethernet-oam
    dnRouter(cfg-srv-eoam)# connectivity-fault-management
    dnRouter(cfg-srv-eoam-cfm)# maintenance-domains MyFirstMD
    dnRouter(cfg-eoam-cfm-md)# level 5


**Removing Configuration**

To remove the level for a specific Maintenance Domain:
::

    dnRouter(cfg-eoam-cfm-md)# no level

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
