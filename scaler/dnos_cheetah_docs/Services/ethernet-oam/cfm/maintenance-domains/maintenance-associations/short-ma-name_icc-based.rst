services ethernet-oam connectivity-fault-management maintenance-domains maintenance-associations short-ma-name icc-based
------------------------------------------------------------------------------------------------------------------------

**Minimum user role:** operator

To configure the CFM Maintenance Association name:

**Command syntax: short-ma-name icc-based [icc] [umc]**

**Command mode:** config

**Hierarchies**

- services ethernet-oam connectivity-fault-management maintenance-domains maintenance-associations

**Note**

- The combined length of both ICC and UMC strings is 13 characters (with trailing nulls).

- The command is applicable to L2-service enabled inband network interfaces of the following types:

  - Physical
  - Physical vlan
  - Bundle
  - Bundle vlan

**Parameter table**

+-----------+-----------------------------------------------------------------+-----------------+---------+
| Parameter | Description                                                     | Range           | Default |
+===========+=================================================================+=================+=========+
| icc       | ITU Carrier Code (ICC) of the ICC-based short-ma-name format.   | | string        | \-      |
|           |                                                                 | | length 1-6    |         |
+-----------+-----------------------------------------------------------------+-----------------+---------+
| umc       | Unique MEG-ID Code (UMC) of the ICC-based short-ma-name format. | | string        | \-      |
|           |                                                                 | | length 7-12   |         |
+-----------+-----------------------------------------------------------------+-----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ethernet-oam
    dnRouter(cfg-srv-eoam)# connectivity-fault-management
    dnRouter(cfg-srv-eoam-cfm)# maintenance-domains MyFirstMD
    dnRouter(cfg-eoam-cfm-md)# md-name null
    dnRouter(cfg-eoam-cfm-md)# maintenance-associations MA1
    dnRouter(cfg-cfm-md-ma)# short-ma-name icc-based DTAG msa1234


**Removing Configuration**

To remove the short MA name for a specific Maintenance Association:
::

    dnRouter(cfg-cfm-md-ma)# no short-ma-name

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
