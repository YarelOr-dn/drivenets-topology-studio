protocols segment-routing pcep pce priority address authentication password
---------------------------------------------------------------------------

**Minimum user role:** operator

To protect PCEP TCP sessions between PCE and PCC using MD5 authentication algorithm:

**Command syntax: authentication [admin-state] password [password]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing pcep pce priority address

**Parameter table**

+-------------+---------------------------------------------------------+------------+---------+
| Parameter   | Description                                             | Range      | Default |
+=============+=========================================================+============+=========+
| admin-state | set whether authentication is enabled                   | enabled    | \-      |
|             |                                                         | disabled   |         |
+-------------+---------------------------------------------------------+------------+---------+
| password    | pcep authentication password. saved Encypeted in the DB | \-         | \-      |
+-------------+---------------------------------------------------------+------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# pcep
    dnRouter(cfg-protocols-sr-pcep)# pce priority 1 address 1.1.1.1
    dnRouter(cfg-sr-pcep-pce)# authentication enabled password
    Enter password
    Enter password for verifications
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# pcep
    dnRouter(cfg-protocols-sr-pcep)#  pce priority 1 address 1.1.1.1
    dnRouter(cfg-sr-pcep-pce)# authentication enabled password enc-gAAAAABduqxChJ4bui9rSfwefF6MglPHuX8clLpAbLjXAEdzVH-sJWVIkKxVx2ukbwSq6_T79AR8oXJfw5ugGjKE95gv3ggatw==


**Removing Configuration**

To remove authentication usage:
::

    dnRouter(cfg-sr-pcep-pce)# no authentication

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
