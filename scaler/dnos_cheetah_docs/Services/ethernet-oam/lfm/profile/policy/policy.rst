services ethernet-oam link-fault-management profile policy
----------------------------------------------------------

**Minimum user role:** operator

To configure the 802.3ah EFM OAM policies:"

**Command syntax: policy**

**Command mode:** config

**Hierarchies**

- services ethernet-oam link-fault-management profile

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-protocols)# ethernet-oam
    dnRouter(cfg-srv-eoam)# link-fault-management
    dnRouter(cfg-srv-eoam-lfm)# profile AH_default1
    dnRouter(cfg-eoam-lfm-profile)# policy
    dnRouter(cfg-lfm-profile-policies)#


**Removing Configuration**

To remove the 802.3ah EFM OAM policies configuration under the specified profile:
::

    dnRouter(cfg-eoam-lfm-profile)# no policy

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
