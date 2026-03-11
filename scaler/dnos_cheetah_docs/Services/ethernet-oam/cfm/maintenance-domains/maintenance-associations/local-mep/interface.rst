services ethernet-oam connectivity-fault-management maintenance-domains maintenance-associations local-mep interface
--------------------------------------------------------------------------------------------------------------------

**Minimum user role:** operator

To set the interface of the local MEP:

**Command syntax: interface [interface-name]**

**Command mode:** config

**Hierarchies**

- services ethernet-oam connectivity-fault-management maintenance-domains maintenance-associations local-mep

**Note**

- The command is applicable to L2-service enabled inband network interfaces of the following types:

  - Physical
  - Physical vlan
  - Bundle
  - Bundle vlan

**Parameter table**

+----------------+--------------------------------------------------------------+------------------+---------+
| Parameter      | Description                                                  | Range            | Default |
+================+==============================================================+==================+=========+
| interface-name | The inband network interface associated with this local MEP. | | string         | \-      |
|                |                                                              | | length 1-255   |         |
+----------------+--------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ethernet-oam
    dnRouter(cfg-srv-eoam)# connectivity-fault-management
    dnRouter(cfg-srv-eoam-cfm)# maintenance-domains MyFirstMD
    dnRouter(cfg-eoam-cfm-md)# maintenance-associations MA1
    dnRouter(cfg-cfm-md-ma)# local-mep 2
    dnRouter(cfg-md-ma-lmep-2)# interface ge100-0/0/0


**Removing Configuration**

To remove the associated interface of the local MEP:
::

    dnRouter(cfg-md-ma-lmep-2)# no interface

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
