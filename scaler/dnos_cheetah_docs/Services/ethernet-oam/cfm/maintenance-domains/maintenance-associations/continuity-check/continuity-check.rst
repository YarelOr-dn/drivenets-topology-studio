services ethernet-oam connectivity-fault-management maintenance-domains maintenance-associations continuity-check
-----------------------------------------------------------------------------------------------------------------

**Minimum user role:** operator

To enter the CFM continuity check configuration:

**Command syntax: continuity-check**

**Command mode:** config

**Hierarchies**

- services ethernet-oam connectivity-fault-management maintenance-domains maintenance-associations

**Note**

- The command is applicable to L2-service enabled inband network interfaces of the following types:

  - Physical
  - Physical vlan
  - Bundle
  - Bundle vlan

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ethernet-oam
    dnRouter(cfg-srv-eoam)# connectivity-fault-management
    dnRouter(cfg-srv-eoam-cfm)# maintenance-domains MyFirstMD
    dnRouter(cfg-eoam-cfm-md)# maintenance-associations MA1
    dnRouter(cfg-cfm-md-ma)# continuity-check
    dnRouter(cfg-md-ma-ccm)#


**Removing Configuration**

To revert the Continuity Check configuration for a specific Maintenance Association to its default values:
::

    dnRouter(cfg-cfm-md-ma)# no continuity-check

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
