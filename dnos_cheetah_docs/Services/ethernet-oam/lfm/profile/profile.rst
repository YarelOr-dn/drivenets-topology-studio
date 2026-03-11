services ethernet-oam link-fault-management profile
---------------------------------------------------

**Minimum user role:** operator

To configure the 802.3ah EFM OAM profiles:

**Command syntax: profile [profile]**

**Command mode:** config

**Hierarchies**

- services ethernet-oam link-fault-management

**Note**

- Up to 5 profiles may be configured.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter | Description                                                                      | Range            | Default |
+===========+==================================================================================+==================+=========+
| profile   | The profile name of the EFM link OAM service. The profile is attached to an OAM  | | string         | \-      |
|           | enabled interface                                                                | | length 1-255   |         |
+-----------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ethernet-oam
    dnRouter(cfg-srv-eoam)# link-fault-management
    dnRouter(cfg-srv-eoam-lfm)# profile AH_default1
    dnRouter(cfg-eoam-lfm-profile)#


**Removing Configuration**

To delete a certain profile:
::

    dnRouter(cfg-srv-eoam-lfm)# # no profile AH_default1

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
