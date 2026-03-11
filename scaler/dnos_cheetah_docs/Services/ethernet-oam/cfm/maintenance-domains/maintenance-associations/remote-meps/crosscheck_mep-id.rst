services ethernet-oam connectivity-fault-management maintenance-domains maintenance-associations remote-meps crosscheck mep-id
------------------------------------------------------------------------------------------------------------------------------

**Minimum user role:** operator

To statically configure remote MEPs to be cross-checked:

**Command syntax: crosscheck mep-id [remote-mep]**

**Command mode:** config

**Hierarchies**

- services ethernet-oam connectivity-fault-management maintenance-domains maintenance-associations remote-meps

**Note**

- The command is applicable to L2-service enabled inband network interfaces of the following types:

  - Physical
  - Physical vlan
  - Bundle
  - Bundle vlan

**Parameter table**

+------------+--------------------------------------------------------------------------------+--------+---------+
| Parameter  | Description                                                                    | Range  | Default |
+============+================================================================================+========+=========+
| remote-mep | Integer that is unique among all the MEPs in the same Maintenance Association. | 1-8191 | \-      |
+------------+--------------------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ethernet-oam
    dnRouter(cfg-srv-eoam)# connectivity-fault-management
    dnRouter(cfg-srv-eoam-cfm)# maintenance-domains MyFirstMD
    dnRouter(cfg-eoam-cfm-md)# maintenance-associations MA1
    dnRouter(cfg-cfm-md-ma)# remote-meps
    dnRouter(cfg-md-ma-rmeps)# crosscheck mep-id 3, 5


**Removing Configuration**

To remove a specific remote MEP from the crosscheck list:
::

    dnRouter(cfg-md-ma-rmeps)# no crosscheck mep-id 3

To remove the list of remote MEPs altogether:
::

    dnRouter(cfg-md-ma-rmeps)# no crosscheck mep-id

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
