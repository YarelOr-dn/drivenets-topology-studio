services ethernet-oam connectivity-fault-management maintenance-domains
-----------------------------------------------------------------------

**Minimum user role:** operator

To configure CFM maintenance domains:

**Command syntax: maintenance-domains [maintenance-domain]**

**Command mode:** config

**Hierarchies**

- services ethernet-oam connectivity-fault-management

**Note**

- The command is applicable to L2-service enabled inband network interfaces of the following types:

  - Physical
  - Physical vlan
  - Bundle
  - Bundle vlan

**Parameter table**

+--------------------+-------------------------------------------+-------+---------+
| Parameter          | Description                               | Range | Default |
+====================+===========================================+=======+=========+
| maintenance-domain | The index to the Maintenance Domain list. | \-    | \-      |
+--------------------+-------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ethernet-oam
    dnRouter(cfg-srv-eoam)# connectivity-fault-management
    dnRouter(cfg-srv-eoam-cfm)# maintenance-domains MyFirstMD
    dnRouter(cfg-eoam-cfm-md)#


**Removing Configuration**

To remove the CFM OAM configuration for a specific Maintenance Domain:
::

    dnRouter(cfg-srv-eoam-cfm)# no maintenance-domains MyFirstMD

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
