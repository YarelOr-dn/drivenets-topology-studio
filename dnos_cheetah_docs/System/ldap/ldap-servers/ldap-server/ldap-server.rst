system ldap ldap-servers ldap-server priority
---------------------------------------------

**Minimum user role:** admin

Defines the LDAP server priority. When multiple servers are set, DNOS accesses the LDAP servers according to their priority (e.g., DNOS will first attempt the LDAP server with the lowest priority.) To define the LDAP server priority:

**Command syntax: ldap-server priority [ldap-server]**

**Command mode:** config

**Hierarchies**

- system ldap ldap-servers

**Parameter table**

+-------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter   | Description                                                                      | Range | Default |
+=============+==================================================================================+=======+=========+
| ldap-server | LDAP server priority. When multiple LDAP servers are enabled, DNOS queries them  | 1-255 | \-      |
|             | in the order of their priority. If DNOS doesn't receive a response, it tries a   |       |         |
|             | server with the next lowest priority among servers enabled for that LDAP         |       |         |
|             | function.                                                                        |       |         |
+-------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ldap
    dnRouter(cfg-system-ldap)# ldap-servers
    dnRouter(cfg-system-ldap-servers)# ldap-server priority 23


**Removing Configuration**

To revert the ldap-server:
::

    dnRouter(cfg-system-ldap)# no ldap-server

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
