services ethernet-oam connectivity-fault-management maintenance-domains maintenance-associations short-ma-name string
---------------------------------------------------------------------------------------------------------------------

**Minimum user role:** operator

To configure the CFM maintenance association name:

**Command syntax: short-ma-name string [char-string]**

**Command mode:** config

**Hierarchies**

- services ethernet-oam connectivity-fault-management maintenance-domains maintenance-associations

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
|             | used.                                                                            | | length 1-45   |         |
+-------------+----------------------------------------------------------------------------------+-----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ethernet-oam
    dnRouter(cfg-srv-eoam)# connectivity-fault-management
    dnRouter(cfg-srv-eoam-cfm)# maintenance-domains MyFirstMD
    dnRouter(cfg-eoam-cfm-md)# maintenance-associations MA1
    dnRouter(cfg-cfm-md-ma)# short-ma-name string FirstMA


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
