services ethernet-oam link-fault-management
-------------------------------------------

**Minimum user role:** operator

To enter the 802.3ah EFM OAM configuration mode:

**Command syntax: link-fault-management**

**Command mode:** config

**Hierarchies**

- services ethernet-oam

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-protocols)# ethernet-oam
    dnRouter(cfg-services-eoam)# link-fault-management


**Removing Configuration**

To remove the 802.3ah EFM OAM service:
::

    dnRouter(cfg-services-eoam)# no link-fault-management

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
