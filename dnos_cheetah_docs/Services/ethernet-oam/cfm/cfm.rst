services ethernet-oam connectivity-fault-management
---------------------------------------------------

**Minimum user role:** operator

To enter the CFM OAM configuration mode:

**Command syntax: connectivity-fault-management**

**Command mode:** config

**Hierarchies**

- services ethernet-oam

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-services)# ethernet-oam
    dnRouter(cfg-services-eoam)# connectivity-fault-management


**Removing Configuration**

To remove the CFM OAM service:
::

    dnRouter(cfg-services-eoam)# no connectivity-fault-management

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
