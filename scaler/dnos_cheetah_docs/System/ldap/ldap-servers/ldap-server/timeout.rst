system ldap ldap-servers ldap-server priority timeout
-----------------------------------------------------

**Minimum user role:** admin

To set the connection timeout in seconds on responses from the LDAP server:

**Command syntax: timeout [timeout]**

**Command mode:** config

**Hierarchies**

- system ldap ldap-servers ldap-server priority

**Parameter table**

+-----------+----------------------------------------------------------------------+--------+---------+
| Parameter | Description                                                          | Range  | Default |
+===========+======================================================================+========+=========+
| timeout   | Set the connect timeout in seconds on responses from the LDAP server | 1-1000 | 5       |
+-----------+----------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ldap
    dnRouter(cfg-system-ldap)# ldap-servers
    dnRouter(cfg-system-ldap)# ldap-server priority 3
    dnRouter(cfg-ldap-servers-server)# timeout 60


**Removing Configuration**

To revert the timeout to the default value:
::

    dnRouter(cfg-ldap-servers-server)# no timeout

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
