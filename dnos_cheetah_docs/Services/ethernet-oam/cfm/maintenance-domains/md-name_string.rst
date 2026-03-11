services ethernet-oam connectivity-fault-management maintenance-domains md-name string
--------------------------------------------------------------------------------------

**Minimum user role:** operator

To configure the CFM maintenance domain name in a string format:

**Command syntax: md-name string [char-string]**

**Command mode:** config

**Hierarchies**

- services ethernet-oam connectivity-fault-management maintenance-domains

**Note**

- The command is applicable to L2-service enabled inband network interfaces of the following types:

  - Physical
  - Physical vlan
  - Bundle
  - Bundle vlan

- ASCII DEC 34 character " (quotation mark) is not supported

**Parameter table**

+-------------+----------------------------------------------------------------------------------+-----------------+---------+
| Parameter   | Description                                                                      | Range           | Default |
+=============+==================================================================================+=================+=========+
| char-string | RFC2579 DisplayString, except that the character codes 0-31 (decimal) are not    | | string        | \-      |
|             | used.                                                                            | | length 1-43   |         |
+-------------+----------------------------------------------------------------------------------+-----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ethernet-oam
    dnRouter(cfg-srv-eoam)# connectivity-fault-management
    dnRouter(cfg-srv-eoam-cfm)# maintenance-domains MyFirstMD
    dnRouter(cfg-eoam-cfm-md)# md-name string MyFirstMD


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
