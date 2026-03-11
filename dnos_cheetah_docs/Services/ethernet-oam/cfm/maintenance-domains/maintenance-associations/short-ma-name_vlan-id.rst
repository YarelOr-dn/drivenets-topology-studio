services ethernet-oam connectivity-fault-management maintenance-domains maintenance-associations short-ma-name vlan-id
----------------------------------------------------------------------------------------------------------------------

**Minimum user role:** operator

To configure the CFM maintenance association name:

**Command syntax: short-ma-name vlan-id [primary-vid]**

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

+-------------+------------------------------------------------------------+--------+---------+
| Parameter   | Description                                                | Range  | Default |
+=============+============================================================+========+=========+
| primary-vid | Primary VLAN ID. 12 bits represented in a 2-octet integer. | 1-4094 | \-      |
+-------------+------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ethernet-oam
    dnRouter(cfg-srv-eoam)# connectivity-fault-management
    dnRouter(cfg-srv-eoam-cfm)# maintenance-domains MyFirstMD
    dnRouter(cfg-eoam-cfm-md)# maintenance-associations MA1
    dnRouter(cfg-cfm-md-ma)# short-ma-name vlan-id 100


**Removing Configuration**

To remove the short MA name for a specific Maintenance Association:
::

    dnRouter(cfg-cfm-md-ma)# no short-ma-name

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
