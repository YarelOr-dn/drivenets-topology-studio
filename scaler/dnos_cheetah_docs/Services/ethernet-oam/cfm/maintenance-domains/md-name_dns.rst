services ethernet-oam connectivity-fault-management maintenance-domains md-name dns
-----------------------------------------------------------------------------------

**Minimum user role:** operator

To configure the CFM maintenance domain name in DNS format:

**Command syntax: md-name dns [dns-like-name]**

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

+---------------+-------------------------------------------------------------------------------+-----------------+---------+
| Parameter     | Description                                                                   | Range           | Default |
+===============+===============================================================================+=================+=========+
| dns-like-name | Domain name like string, globally unique text string derived from a DNS name. | | string        | \-      |
|               |                                                                               | | length 1-43   |         |
+---------------+-------------------------------------------------------------------------------+-----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ethernet-oam
    dnRouter(cfg-srv-eoam)# connectivity-fault-management
    dnRouter(cfg-srv-eoam-cfm)# maintenance-domains MyFirstMD
    dnRouter(cfg-eoam-cfm-md)# md-name dns cfm.drivenets.com


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
