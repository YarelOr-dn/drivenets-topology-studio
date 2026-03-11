services ethernet-oam link-fault-management auto-recovery
---------------------------------------------------------

**Minimum user role:** operator

Sets the automatic interfaces recovery interval time for disabled interfaces due to 802.3ah EFM OAM policies.

**Command syntax: auto-recovery [recovery-interval]**

**Command mode:** config

**Hierarchies**

- services ethernet-oam link-fault-management

**Parameter table**

+-------------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter         | Description                                                                      | Range   | Default |
+===================+==================================================================================+=========+=========+
| recovery-interval | The auto-recovery interval time used to automatically attempt recovering         | 5-86400 | 300     |
|                   | disabled interfaces due to 802.3ah EFM OAM policies.                             |         |         |
+-------------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# ethernet-oam
    dnRouter(cfg-srv-eoam)# link-fault-management
    dnRouter(cfg-srv-eoam-lfm)# auto-recovery 300


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-srv-eoam-lfm)# no auto-recovery

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
