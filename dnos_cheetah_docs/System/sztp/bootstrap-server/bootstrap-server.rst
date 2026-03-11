system sztp bootstrap-server
----------------------------

**Minimum user role:** admin

To configure the bootstrap server:

**Command syntax: bootstrap-server [bootstrap-server]**

**Command mode:** config

**Hierarchies**

- system sztp

**Note**

- Up to 16 bootstrap servers can be configured in general.

- Bootstrap servers cannot be modified during SZTP flow. If the user needs to change servers, they need to stop any SZTP flow (By changing admin-state to disabled) and then make the desired changes.

**Parameter table**

+------------------+------------------+-------+---------+
| Parameter        | Description      | Range | Default |
+==================+==================+=======+=========+
| bootstrap-server | bootstrap-server | \-    | \-      |
+------------------+------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# sztp
    dnRouter(cfg-system-sztp)# bootstrap-server ::1
    dnRouter(cfg-system-sztp-bootsrv)# !
    dnRouter(cfg-system-sztp)# bootstrap-server 2001:1:2:3:4:5:6:7
    dnRouter(cfg-system-sztp-bootsrv)# !


**Removing Configuration**

To delete the configuration under bootstrap-server:
::

    dnRouter(cfg-system-sztp)# no bootstrap-server 2001:1:2:3:4:5:6:7

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
