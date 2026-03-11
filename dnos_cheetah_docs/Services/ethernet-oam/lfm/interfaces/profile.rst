services ethernet-oam link-fault-management interface profile
-------------------------------------------------------------

**Minimum user role:** operator

To apply the 802.3ah EFM OAM profile to the specified interface:

**Command syntax: profile [profile-name]**

**Command mode:** config

**Hierarchies**

- services ethernet-oam link-fault-management interface

**Parameter table**

+--------------+------------------------------------------------+------------------+---------+
| Parameter    | Description                                    | Range            | Default |
+==============+================================================+==================+=========+
| profile-name | Apply 802.3ah EFM OAM profile to the interface | | string         | \-      |
|              |                                                | | length 1-255   |         |
+--------------+------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ethernet-oam
    dnRouter(cfg-srv-eoam)# link-fault-management
    dnRouter(cfg-srv-eoam-lfm)# interface ge100-0/0/0
    dnRouter(cfg-eoam-lfm-if)# profile lfm-profile-1


**Removing Configuration**

To remove 802.3ah EFM OAM profile from the interface:
::

    dnRouter(cfg-eoam-lfm-if)# no profile

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
