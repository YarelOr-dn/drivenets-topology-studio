system ldap ldap-servers ldap-server priority search-timeout
------------------------------------------------------------

**Minimum user role:** admin

To set the search timeout (in seconds):

**Command syntax: search-timeout [search-timeout]**

**Command mode:** config

**Hierarchies**

- system ldap ldap-servers ldap-server priority

**Parameter table**

+----------------+-----------------------------------+--------+---------+
| Parameter      | Description                       | Range  | Default |
+================+===================================+========+=========+
| search-timeout | Set the search timeout in seconds | 1-1000 | 5       |
+----------------+-----------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ldap
    dnRouter(cfg-system-ldap)# ldap-servers
    dnRouter(cfg-system-ldap)# ldap-server priority 3
    dnRouter(cfg-ldap-servers-server)# search-timeout 60


**Removing Configuration**

To revert the search-timeout to the default value:
::

    dnRouter(cfg-ldap-servers-server)# no search-timeout

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
