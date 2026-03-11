services ethernet-oam connectivity-fault-management maintenance-domains maintenance-associations local-mep direction
--------------------------------------------------------------------------------------------------------------------

**Minimum user role:** operator

To set the direction of the local MEP:

**Command syntax: direction [direction]**

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

+-----------+-------------------------------------------------------------------------------+----------+---------+
| Parameter | Description                                                                   | Range    | Default |
+===========+===============================================================================+==========+=========+
| direction | The direction in which the MEP faces on the Bridge Port. Example, up or down. | | down   | \-      |
|           |                                                                               | | up     |         |
+-----------+-------------------------------------------------------------------------------+----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ethernet-oam
    dnRouter(cfg-srv-eoam)# connectivity-fault-management
    dnRouter(cfg-srv-eoam-cfm)# maintenance-domains MyFirstMD
    dnRouter(cfg-eoam-cfm-md)# maintenance-associations MA1
    dnRouter(cfg-cfm-md-ma)# local-mep 2
    dnRouter(cfg-md-ma-lmep-2)# direction up


**Removing Configuration**

To remove the direction configuration of the local MEP:
::

    dnRouter(cfg-md-ma-lmep-2)# no direction

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
