services ethernet-oam connectivity-fault-management maintenance-domains maintenance-associations mip
----------------------------------------------------------------------------------------------------

**Minimum user role:** operator

To enter the CFM MIPs configuration:

**Command syntax: mip [mip-name]**

**Command mode:** config

**Hierarchies**

- services ethernet-oam connectivity-fault-management maintenance-domains maintenance-associations

**Note**

- 1. Multiple interfaces can be set as MIP for same <MA, MD>, same interface can be MIP in different <MA, MD>. 
- 2. The command is applicable to L2-service enabled inband network interfaces of the following types:

  - Physical
  - Physical vlan
  - Bundle
  - Bundle vlan

**Parameter table**

+-----------+--------------------+------------------+---------+
| Parameter | Description        | Range            | Default |
+===========+====================+==================+=========+
| mip-name  | MIPs configuration | | string         | \-      |
|           |                    | | length 1-255   |         |
+-----------+--------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ethernet-oam
    dnRouter(cfg-srv-eoam)# connectivity-fault-management
    dnRouter(cfg-srv-eoam-cfm)# maintenance-domains MyFirstMD
    dnRouter(cfg-eoam-cfm-md)# maintenance-associations MA1
    dnRouter(cfg-cfm-md-ma)# mip mymip2
    dnRouter(cfg-md-ma-mip-mymmip2)#


**Removing Configuration**

To remove a specific MIP configuration:
::

    dnRouter(cfg-cfm-md-ma)# no mip mymip2

To remove all MIPs configuration from a specific Maintenance Association:
::

    dnRouter(cfg-cfm-md-ma)# no mip

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
