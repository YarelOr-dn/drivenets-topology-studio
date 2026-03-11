services ethernet-oam connectivity-fault-management maintenance-domains maintenance-associations continuity-check interval
--------------------------------------------------------------------------------------------------------------------------

**Minimum user role:** operator

To configure the interval for transmission of continuity check messages:

**Command syntax: interval [ccm-interval]**

**Command mode:** config

**Hierarchies**

- services ethernet-oam connectivity-fault-management maintenance-domains maintenance-associations continuity-check

**Note**

- The command is applicable to L2-service enabled inband network interfaces of the following types:

  - Physical
  - Physical vlan
  - Bundle
  - Bundle vlan

**Parameter table**

+--------------+----------------------------------------------------------------------------------+-----------+---------+
| Parameter    | Description                                                                      | Range     | Default |
+==============+==================================================================================+===========+=========+
| ccm-interval | The interval between CCM transmissions to be used by all MEPs in the Maintenance | | 3.3ms   | 1sec    |
|              | Association.                                                                     | | 10ms    |         |
|              |                                                                                  | | 100ms   |         |
|              |                                                                                  | | 1sec    |         |
|              |                                                                                  | | 10sec   |         |
|              |                                                                                  | | 1min    |         |
|              |                                                                                  | | 10min   |         |
+--------------+----------------------------------------------------------------------------------+-----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ethernet-oam
    dnRouter(cfg-srv-eoam)# connectivity-fault-management
    dnRouter(cfg-srv-eoam-cfm)# maintenance-domains MyFirstMD
    dnRouter(cfg-eoam-cfm-md)# maintenance-associations MA1
    dnRouter(cfg-cfm-md-ma)# continuity-check
    dnRouter(cfg-md-ma-ccm)# interval 100ms


**Removing Configuration**

To revert continuity check interval configuration to its default value:
::

    dnRouter(cfg-md-ma-ccm)# no interval

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
