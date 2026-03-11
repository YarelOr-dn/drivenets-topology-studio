services ethernet-oam connectivity-fault-management maintenance-domains maintenance-associations local-mep
----------------------------------------------------------------------------------------------------------

**Minimum user role:** operator

To enter the CFM local MEPs configuration:

**Command syntax: local-mep [mep-id]**

**Command mode:** config

**Hierarchies**

- services ethernet-oam connectivity-fault-management maintenance-domains maintenance-associations

**Note**

- The command is applicable to L2-service enabled inband network interfaces of the following types:

  - Physical
  - Physical vlan
  - Bundle
  - Bundle vlan

**Parameter table**

+-----------+--------------------------+--------+---------+
| Parameter | Description              | Range  | Default |
+===========+==========================+========+=========+
| mep-id    | Local MEPs configuration | 1-8191 | \-      |
+-----------+--------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ethernet-oam
    dnRouter(cfg-srv-eoam)# connectivity-fault-management
    dnRouter(cfg-srv-eoam-cfm)# maintenance-domains MyFirstMD
    dnRouter(cfg-eoam-cfm-md)# maintenance-associations MA1
    dnRouter(cfg-cfm-md-ma)# local-mep 2
    dnRouter(cfg-md-ma-lmep-2)#


**Removing Configuration**

To remove a specific local MEP configuration:
::

    dnRouter(cfg-cfm-md-ma)# no local-mep 2

To remove all local MEPs configuration from a specific Maintenance Association:
::

    dnRouter(cfg-cfm-md-ma)# no local-mep

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
