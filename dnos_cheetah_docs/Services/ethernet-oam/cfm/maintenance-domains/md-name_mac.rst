services ethernet-oam connectivity-fault-management maintenance-domains md-name mac-address
-------------------------------------------------------------------------------------------

**Minimum user role:** operator

To configure the CFM maintenance domain name in a MAC address + 2 byte unsigned integer format:

**Command syntax: md-name mac-address [mac-address] [integer]**

**Command mode:** config

**Hierarchies**

- services ethernet-oam connectivity-fault-management maintenance-domains

**Note**

- The command is applicable to L2-service enabled inband network interfaces of the following types:

  - Physical
  - Physical vlan
  - Bundle
  - Bundle vlan

**Parameter table**

+-------------+--------------------------------------------+-------------------+---------+
| Parameter   | Description                                | Range             | Default |
+=============+============================================+===================+=========+
| mac-address | The MAC address.                           | xx:xx:xx:xx:xx:xx | \-      |
+-------------+--------------------------------------------+-------------------+---------+
| integer     | The additional 2-octet (unsigned) integer. | 0-65535           | \-      |
+-------------+--------------------------------------------+-------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ethernet-oam
    dnRouter(cfg-srv-eoam)# connectivity-fault-management
    dnRouter(cfg-srv-eoam-cfm)# maintenance-domains MyFirstMD
    dnRouter(cfg-eoam-cfm-md)# md-name mac-address 10:22:33:44:55:00 55555


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
