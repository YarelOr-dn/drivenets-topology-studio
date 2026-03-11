services ethernet-oam connectivity-fault-management maintenance-domains maintenance-associations
------------------------------------------------------------------------------------------------

**Minimum user role:** operator

To configure CFM maintenance associations:

**Command syntax: maintenance-associations [maintenance-association]**

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

+-------------------------+------------------------------------------------+-------+---------+
| Parameter               | Description                                    | Range | Default |
+=========================+================================================+=======+=========+
| maintenance-association | The index to the Maintenance Association list. | \-    | \-      |
+-------------------------+------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ethernet-oam
    dnRouter(cfg-srv-eoam)# connectivity-fault-management
    dnRouter(cfg-srv-eoam-cfm)# maintenance-domains MyFirstMD
    dnRouter(cfg-eoam-cfm-md)# maintenance-associations MA1
    dnRouter(cfg-cfm-md-ma)#


**Removing Configuration**

To remove CFM OAM configuration for a specific Maintenance Association:
::

    dnRouter(cfg-eoam-cfm-md)# no maintenance-associations MA1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
