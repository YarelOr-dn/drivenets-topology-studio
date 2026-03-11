system ldap ldap-servers ldap-server priority bind-dn
-----------------------------------------------------

**Minimum user role:** admin

To configure the bind flags for the LDAP server connection

**Command syntax: bind-dn [bind-dn]**

**Command mode:** config

**Hierarchies**

- system ldap ldap-servers ldap-server priority

**Parameter table**

+-----------+-------------------------------------------+------------------+---------+
| Parameter | Description                               | Range            | Default |
+===========+===========================================+==================+=========+
| bind-dn   | The bind flags for LDAP server connection | | string         | \-      |
|           |                                           | | length 1-255   |         |
+-----------+-------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ldap
    dnRouter(cfg-system-ldap)# ldap-servers
    dnRouter(cfg-system-ldap)# ldap-server priority 1
    dnRouter(cfg-ldap-servers-server)# bind-dn 60


**Removing Configuration**

To revert the bind flag to the default:
::

    dnRouter(cfg-ldap-servers-server)# no bind-dn

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
