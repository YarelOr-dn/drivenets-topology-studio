services ethernet-oam connectivity-fault-management maintenance-domains md-name null
------------------------------------------------------------------------------------

**Minimum user role:** operator

To configure the CFM maintenance domain without a maintenance domain name:

**Command syntax: md-name null**

**Command mode:** config

**Hierarchies**

- services ethernet-oam connectivity-fault-management maintenance-domains

**Note**

- The command is applicable to L2-service enabled inband network interfaces of the following types:

  - Physical
  - Physical vlan
  - Bundle
  - Bundle vlan

- For interoperability with Y.1731 the MD name must be null

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ethernet-oam
    dnRouter(cfg-srv-eoam)# connectivity-fault-management
    dnRouter(cfg-srv-eoam-cfm)# maintenance-domains MyFirstMD
    dnRouter(cfg-eoam-cfm-md)# md-name null


**Removing Configuration**

To remove the MD name for a specific Maintenance Domain:
::

    dnRouter(cfg-eoam-cfm-md)# no md-name

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
