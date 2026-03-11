services ethernet-oam
---------------------

**Minimum user role:** operator

To enter Ethernet OAM configuration mode:

**Command syntax: ethernet-oam**

**Command mode:** config

**Hierarchies**

- services

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-protocols)# ethernet-oam
    dnRouter(cfg-services-eoam)#


**Removing Configuration**

To remove the Ethernet OAM services:
::

    dnRouter(cfg-services)# no ethernet-oam

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
