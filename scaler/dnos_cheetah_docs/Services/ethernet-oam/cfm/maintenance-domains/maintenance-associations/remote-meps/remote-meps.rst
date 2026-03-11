services ethernet-oam connectivity-fault-management maintenance-domains maintenance-associations remote-meps
------------------------------------------------------------------------------------------------------------

**Minimum user role:** operator

To enter the CFM remote MEPs configuration:

**Command syntax: remote-meps**

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
    dnRouter(cfg-cfm-md-ma)# remote-meps
    dnRouter(cfg-md-ma-rmeps)#


**Removing Configuration**

To remove the remote MEPs configuration for a specific Maintenance Association:
::

    dnRouter(cfg-cfm-md-ma)# no remote-meps

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
