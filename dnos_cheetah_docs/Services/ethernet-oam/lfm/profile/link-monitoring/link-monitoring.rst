services ethernet-oam link-fault-management profile link-monitoring
-------------------------------------------------------------------

**Minimum user role:** operator

To configure the 802.3ah EFM OAM link-monitoring:"

**Command syntax: link-monitoring**

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
    dnRouter(cfg-eoam-lfm-profile)# link-monitoring
    dnRouter(cfg-lfm-profile-lm)#


**Removing Configuration**

To remove the 802.3ah EFM OAM link-monitoring configuration under the specified profile:
::

    dnRouter(cfg-eoam-lfm-profile)# no link-monitoring

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
