services ethernet-oam connectivity-fault-management maintenance-domains maintenance-associations mip interface
--------------------------------------------------------------------------------------------------------------

**Minimum user role:** operator

To set the interface of the MIP:

**Command syntax: interface [interface-name]**

**Command mode:** config

**Hierarchies**

- services ethernet-oam connectivity-fault-management maintenance-domains maintenance-associations mip

**Note**

- 1. Multiple interfaces can be set as MIP for same <MA, MD>, same interface can be MIP in different <MA, MD>.   
- 2. The command is applicable to L2-service enabled inband network interfaces of the following types:

  - Physical
  - Physical vlan
  - Bundle
  - Bundle vlan

**Parameter table**

+----------------+--------------------------------------------------------+------------------+---------+
| Parameter      | Description                                            | Range            | Default |
+================+========================================================+==================+=========+
| interface-name | The inband network interface associated with this MIP. | | string         | \-      |
|                |                                                        | | length 1-255   |         |
+----------------+--------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ethernet-oam
    dnRouter(cfg-srv-eoam)# connectivity-fault-management
    dnRouter(cfg-srv-eoam-cfm)# maintenance-domains MyFirstMD
    dnRouter(cfg-eoam-cfm-md)# maintenance-associations MA1
    dnRouter(cfg-cfm-md-ma)# mip mymip2
    dnRouter(cfg-md-ma-mip-Mymip2)# interface ge100-0/0/0


**Removing Configuration**

To remove the associated interface of the MIP:
::

    dnRouter(cfg-md-ma-mip-Mymip2)# no interface

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
